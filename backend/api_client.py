import os
import sys
import threading
import pandas as pd
import numpy as np
from typing import Dict, Any, List
import warnings
import joblib

warnings.filterwarnings('ignore')

# ==================== CONFIGURATION ====================
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Prefer env variable; avoids blocking the whole API when syncing OneDrive/local paths drift.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBtOMDUQFoZ2zBQinccfU3gq8dbWxmOEaw").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
RULES_FILE = os.path.join(_PROJECT_ROOT, 'data', 'dummy_railway_rules.txt')
CSV_FILE = os.path.join(_PROJECT_ROOT, 'data', 'indian_railway_data.csv')
_default_chat_dir = os.path.join(os.path.dirname(_PROJECT_ROOT), 'chatbot train data')
CHATBOT_DATA_DIR = os.getenv("CHATBOT_DATA_DIR", _default_chat_dir).strip()
CHATBOT_MAX_PDFS = int(os.getenv("CHATBOT_MAX_PDFS", "6"))
TRAIN_SUMMARY_MAX_LINES = int(os.getenv("TRAIN_SUMMARY_MAX_LINES", "35"))

# ==================== TRAIN OPTIONS ====================

_TRAIN_OPTIONS_CACHE = None

def get_train_options() -> List[Dict[str, Any]]:
    """
    Read the CSV and return unique train options for the dropdown.
    """
    global _TRAIN_OPTIONS_CACHE
    if _TRAIN_OPTIONS_CACHE is not None:
        return _TRAIN_OPTIONS_CACHE

    try:
        df = pd.read_csv(CSV_FILE)
        # Strip whitespace
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()

        # Get unique trains (by Train_name + Train_no combo)
        trains = df.groupby(['Train_name', 'Train_no']).first().reset_index()
        
        options = []
        for _, row in trains.iterrows():
            options.append({
                'Train_name': row['Train_name'],
                'Train_no': str(row['Train_no']),
                'Source': row['Source'],
                'Destitnation': row['Destitnation'],
                'Distance_Km': float(row['Distance(Km)']),
                'Sc_arr__time': str(row['Sc_arr__time']),
                'Run_frequency': row['Run_frequency'],
                'Train_id': row['Train_id'],
            })
        
        _TRAIN_OPTIONS_CACHE = options
        return options
    except Exception as e:
        print(f"Error reading train options: {str(e)}")
        return []


# ==================== DELAY PREDICTION ====================

def load_prediction_model():
    """
    Load the pre-trained XGBoost model and artifacts.
    """
    try:
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'xgboost_artifact.pkl')
        artifact = joblib.load(model_path)
        return artifact
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return None

def predict_delay(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predict train delay based on input parameters.
    """
    try:
        artifact = load_prediction_model()
        
        if artifact is None:
            return {
                'success': False,
                'error': 'Failed to load prediction model. Make sure you run train_model.py first.'
            }
            
        model = artifact['model']
        model_cols = artifact['model_cols']
        category_mappings = artifact['category_mappings']
        
        # Strip whitespace from string values
        for k, v in input_data.items():
            if isinstance(v, str):
                input_data[k] = v.strip()
        
        df = pd.DataFrame([input_data])
        
        def time_to_minutes(val):
            try:
                parts = str(val).split(':')
                return float(int(parts[0]) * 60 + int(parts[1]))
            except:
                return 0.0
                
        if 'Sc_arr__time' in df.columns:
            df['Sc_arr__time_min'] = df['Sc_arr__time'].apply(time_to_minutes)
        
        # Also handle Act_arr_time if present (use scheduled time as placeholder)
        if 'Sc_arr__time' in df.columns:
            df['Act_arr_time_min'] = df['Sc_arr__time'].apply(time_to_minutes)
            
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df['Month'] = df['Date'].dt.month.fillna(1)
            df['DayOfWeek'] = df['Date'].dt.dayofweek.fillna(0)
            
        cols_to_drop = ['Train_name', 'Date', 'Sc_arr__time', 'Act_arr_time']
        df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
        
        # Apply categorical encodings
        for col, mapping_dict in category_mappings.items():
            if col in df.columns:
                # mapping_dict is {code: category_value}
                reverse_mapping = {v: k for k, v in mapping_dict.items()}
                df[col] = df[col].map(reverse_mapping).fillna(-1).astype(int)
                
        for col in model_cols:
            if col not in df.columns:
                df[col] = 0
        df = df[model_cols].astype(float)
        
        prediction = model.predict(df)
        delay_minutes = max(0, float(prediction[0]))
        
        return {
            'success': True,
            'delay_minutes': delay_minutes,
            'input_data': input_data
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

# ==================== CHATBOT ====================

# Cache the knowledge base in memory (mutex avoids duplicate PDF extraction on warmup + concurrent chat).
_KNOWLEDGE_BASE = None
_KB_LOCK = threading.Lock()

def _extract_pdf_text(pdf_path: str) -> str:
    """Extract text from a single PDF file."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)
    except Exception as e:
        print(f"Error extracting PDF {pdf_path}: {str(e)}")
        return ""

def _build_knowledge_base() -> str:
    """
    Build the knowledge base from:
    1. dummy_railway_rules.txt
    2. All PDFs in the chatbot train data directory
    """
    global _KNOWLEDGE_BASE
    if _KNOWLEDGE_BASE is not None:
        return _KNOWLEDGE_BASE

    with _KB_LOCK:
        if _KNOWLEDGE_BASE is not None:
            return _KNOWLEDGE_BASE

        print("Building chatbot knowledge base...")
        sections = []

        # 1. Load the rules file
        if os.path.exists(RULES_FILE):
            with open(RULES_FILE, 'r', encoding='utf-8') as f:
                rules_content = f.read().strip()
                if rules_content:
                    sections.append("=== RAILWAY RULES & POLICIES ===\n" + rules_content)
                    print(f"  Loaded rules file: {len(rules_content)} chars")

        # 2. Load PDFs from chatbot train data directory (cap count — full scans block workers)
        if os.path.exists(CHATBOT_DATA_DIR):
            pdf_names = sorted(
                f for f in os.listdir(CHATBOT_DATA_DIR) if f.lower().endswith('.pdf')
            )[:CHATBOT_MAX_PDFS]
            for filename in pdf_names:
                pdf_path = os.path.join(CHATBOT_DATA_DIR, filename)
                print(f"  Extracting PDF: {filename}...")
                text = _extract_pdf_text(pdf_path)
                if text:
                    max_chars = 20000  # keeps warmup + Gemini payload smaller
                    if len(text) > max_chars:
                        text = text[:max_chars] + "\n[... document truncated for context limit ...]"
                    sections.append(f"=== FROM: {filename} ===\n{text}")
                    print(f"    Extracted {len(text)} chars")
        else:
            print(f"  Warning: Chatbot data dir not found: {CHATBOT_DATA_DIR}")

        # 3. Load train delay data as context too
        if os.path.exists(CSV_FILE):
            try:
                df = pd.read_csv(CSV_FILE)
                for col in df.select_dtypes(include=['object']).columns:
                    df[col] = df[col].str.strip()
                train_summary = "=== TRAIN DELAY DATABASE ===\n"
                train_summary += "Available trains and their historical delay data:\n"
                rows_added = 0
                n_train_names = df['Train_name'].nunique()
                for name, group in df.groupby('Train_name'):
                    if rows_added >= TRAIN_SUMMARY_MAX_LINES:
                        rest = max(0, n_train_names - rows_added)
                        train_summary += (
                            f"\n… and more trains omitted for brevity ({rest} others in CSV).\n"
                        )
                        break
                    rows_added += 1
                    avg_delay = group['Dealy_min'].mean()
                    max_delay = group['Dealy_min'].max()
                    train_no = group['Train_no'].iloc[0]
                    source = group['Source'].iloc[0]
                    dest = group['Destitnation'].iloc[0]
                    dist = group['Distance(Km)'].iloc[0]
                    freq = group['Run_frequency'].iloc[0]
                    train_summary += f"\n- {name} (#{train_no}): {source} to {dest}, {dist}km, {freq}"
                    train_summary += f"  | Avg delay: {avg_delay:.0f} min, Max delay: {max_delay:.0f} min"
                sections.append(train_summary)
                print("  Added train database summary")
            except Exception as e:
                print(f"  Error loading train data: {e}")

        kb = "\n\n".join(sections)
        _KNOWLEDGE_BASE = kb
        print(f"Knowledge base built: {len(_KNOWLEDGE_BASE)} total chars")
        return _KNOWLEDGE_BASE


def warm_knowledge_base() -> None:
    """Pre-fill the cached knowledge base so the first chat reply is faster."""
    _build_knowledge_base()


def send_chat_message(message: str) -> Dict[str, Any]:
    """
    Send a message to the railway chatbot and get a response.
    Uses Gemini with comprehensive railway knowledge context.
    Acts like a Google Gemini chatbot but with deep railway expertise.
    """
    try:
        import google.generativeai as genai
        
        if not GEMINI_API_KEY or GEMINI_API_KEY.strip() == "":
            return {
                'success': False,
                'error': 'Gemini API key not configured'
            }
        
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Build knowledge base (cached after first call)
        knowledge = _build_knowledge_base()
        
        # Truncate knowledge if it exceeds Gemini's comfortable context
        max_knowledge_chars = 180000  # ~45k tokens, well within Gemini 2.0 Flash limits
        if len(knowledge) > max_knowledge_chars:
            knowledge = knowledge[:max_knowledge_chars] + "\n[... additional content truncated ...]"
        
        system_prompt = """You are Rail Drishti AI - an intelligent, friendly, and highly knowledgeable Indian Railways assistant. 

Your personality and behavior:
- You are conversational, warm, and helpful - similar to Google Gemini in tone
- You have DEEP expertise in Indian Railways based on official documents, rules, and regulations
- You can answer BOTH railway-specific questions AND general questions
- For railway questions, you prioritize information from your knowledge base documents
- For general questions, you respond helpfully like any good AI assistant
- You format your responses beautifully using markdown when appropriate (bold, bullet points, headers)
- You keep responses concise but informative
- If you're not sure about something, you say so honestly
- You proactively offer related information that might be helpful

When answering railway questions, cite the relevant rule or document section when possible.
For train delay questions, reference the historical delay data you have access to."""

        prompt = f"""KNOWLEDGE BASE (Indian Railways Documents & Data):
{knowledge}

---

USER QUESTION: {message}

Provide a helpful, well-formatted response. If the question is about railways, use the knowledge base above. If it's a general question, answer it conversationally like a smart AI assistant would."""
        
        model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=system_prompt)
        response = model.generate_content(
            prompt,
            generation_config={
                'max_output_tokens': 1536,
                'temperature': 0.75,
            },
        )
        
        if hasattr(response, 'text'):
            answer = response.text
        elif hasattr(response, 'candidates') and len(response.candidates) > 0:
            answer = response.candidates[0].content.parts[0].text
        else:
            answer = "I apologize, but I couldn't generate a response. Please try again."
            
        return {
            'success': True,
            'message': answer,
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'message': f"I encountered an error: {str(e)}\n\nPlease try again or rephrase your question."
        }
