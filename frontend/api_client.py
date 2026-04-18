import os
import sys
import io
import pandas as pd
import numpy as np
from typing import Dict, Any
import warnings

warnings.filterwarnings('ignore')

# ==================== CONFIGURATION ====================
# Gemini API Key for chatbot (replace with your key)
GEMINI_API_KEY = "AIzaSyDvLDAirzQi_sE9pMQDk3u8ev5IyiIZoVE"

# Databricks configuration
CATALOG = "workspace"
SCHEMA = "default"
VECTOR_SEARCH_ENDPOINT = "railway_vs_endpoint"
VECTOR_INDEX_NAME = f"{CATALOG}.{SCHEMA}.railway_vector_index"

# ==================== DELAY PREDICTION ====================

def load_prediction_model():
    """
    Load the trained XGBoost model from Databricks notebook.
    In production, this should load from MLflow or a saved model file.
    """
    try:
        from xgboost import XGBRegressor
        from pyspark.sql import SparkSession
        
        # Initialize Spark
        spark = SparkSession.builder.getOrCreate()
        
        # Load training data
        TABLE_NAME = "workspace.default.indian_railway_delay_data"
        df = spark.table(TABLE_NAME).toPandas()
        
        # Process data using the same pipeline
        df_final = force_numeric_pipeline(df)
        X = df_final.drop(columns=['Dealy_min'])
        y = df_final['Dealy_min'].astype(float)
        
        # Train model
        model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
        model.fit(X, y)
        
        # Save column order
        model_cols = X.columns.tolist()
        
        return model, model_cols
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return None, None

def force_numeric_pipeline(df_input, is_training=True, train_columns=None):
    """
    Transform raw input data into numeric features for the model.
    """
    data = df_input.copy()
    
    # Handle time strings
    def time_to_minutes(val):
        try:
            parts = str(val).split(':')
            return float(int(parts[0]) * 60 + int(parts[1]))
        except:
            return 0.0
    
    time_cols = ['Sc_arr__time', 'Act_arr_time']
    for col in time_cols:
        if col in data.columns:
            data[col + '_min'] = data[col].apply(time_to_minutes)
    
    # Handle dates
    if 'Date' in data.columns:
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        data['Month'] = data['Date'].dt.month.fillna(0)
        data['DayOfWeek'] = data['Date'].dt.dayofweek.fillna(0)
    
    # Drop non-numeric columns
    cols_to_drop = ['Train_name', 'Date', 'Sc_arr__time', 'Act_arr_time']
    data = data.drop(columns=[c for c in cols_to_drop if c in data.columns])
    
    # Categorical encoding
    for col in data.select_dtypes(include=['object', 'category']).columns:
        data[col] = data[col].astype('category').cat.codes
    
    # Ensure column alignment
    if not is_training and train_columns is not None:
        for col in train_columns:
            if col not in data.columns:
                data[col] = 0
        data = data[train_columns]
    
    return data

def predict_delay(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predict train delay based on input parameters.
    
    Args:
        input_data: Dictionary containing train details
    
    Returns:
        Dictionary with prediction results or error message
    """
    try:
        # Load model (in production, cache this)
        model, model_cols = load_prediction_model()
        
        if model is None:
            return {
                'success': False,
                'error': 'Failed to load prediction model'
            }
        
        # Convert input to DataFrame
        input_df = pd.DataFrame([input_data])
        
        # Process input
        input_processed = force_numeric_pipeline(
            input_df, 
            is_training=False, 
            train_columns=model_cols
        )
        
        # Make prediction
        prediction = model.predict(input_processed)
        delay_minutes = float(prediction[0])
        
        return {
            'success': True,
            'delay_minutes': delay_minutes,
            'input_data': input_data
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# ==================== CHATBOT ====================

def retrieve_relevant_chunks(query: str, top_k: int = 5):
    """
    Retrieve relevant chunks from Vector Search for RAG.
    """
    try:
        from sentence_transformers import SentenceTransformer
        from databricks.vector_search.client import VectorSearchClient
        
        # Load embedding model
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Generate query embedding
        query_embedding = embedding_model.encode(query).tolist()
        
        # Suppress Vector Search client notices
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            # Initialize Vector Search client
            vsc = VectorSearchClient(disable_notice=True)
            index = vsc.get_index(
                endpoint_name=VECTOR_SEARCH_ENDPOINT,
                index_name=VECTOR_INDEX_NAME
            )
            
            # Search for similar chunks
            results = index.similarity_search(
                query_vector=query_embedding,
                columns=["chunk_id", "text", "source_file"],
                num_results=top_k
            )
        finally:
            sys.stdout = old_stdout
        
        # Extract chunks
        chunks = []
        if hasattr(results, 'data_array'):
            for row in results.data_array:
                chunks.append({
                    'text': row[1],
                    'source': row[2]
                })
        
        return chunks
        
    except Exception as e:
        print(f"Error retrieving chunks: {str(e)}")
        return []

def send_chat_message(message: str) -> Dict[str, Any]:
    """
    Send a message to the railway chatbot and get a response.
    
    Args:
        message: User's question
    
    Returns:
        Dictionary with chatbot response or error message
    """
    try:
        import google.generativeai as genai
        
        # Configure Gemini
        if not GEMINI_API_KEY or GEMINI_API_KEY == " ":
            return {
                'success': False,
                'error': 'Gemini API key not configured'
            }
        
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Retrieve relevant context
        relevant_chunks = retrieve_relevant_chunks(message, top_k=5)
        
        # Build context
        if relevant_chunks:
            context = "\n\n".join([
                f"[From {chunk['source']}]\n{chunk['text']}"
                for chunk in relevant_chunks
            ])
        else:
            context = "No specific railway documents found for this query."
        
        # Build prompt
        prompt = f"""You are a helpful Railway Assistant chatbot for Indian Railways.

Context from railway documents:
{context}

User Question: {message}

Provide a clear, concise, and accurate answer based on the context above. If the information is not in the context, politely say so and provide general railway information if applicable."""
        
        # Generate response
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        # Extract response text
        if hasattr(response, 'text'):
            answer = response.text
        elif hasattr(response, 'candidates') and len(response.candidates) > 0:
            answer = response.candidates[0].content.parts[0].text
        else:
            answer = "I apologize, but I couldn't generate a response. Please try again."
        
        # Add sources
        if relevant_chunks:
            sources = set([chunk['source'] for chunk in relevant_chunks])
            answer += "\n\n" + "="*60
            answer += "\n**Sources consulted:**\n"
            for i, source in enumerate(sources, 1):
                answer += f"{i}. {source}\n"
        
        return {
            'success': True,
            'message': answer,
            'sources': [chunk['source'] for chunk in relevant_chunks] if relevant_chunks else []
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f"I apologize, but I encountered an error: {str(e)}\n\nPlease try again or rephrase your question."
        }

# ==================== REST API ENDPOINTS (Optional) ====================
# If deploying as a REST API, uncomment and use Flask/FastAPI

# from flask import Flask, request, jsonify
# 
# app = Flask(__name__)
# 
# @app.route('/predict', methods=['POST'])
# def api_predict():
#     data = request.json
#     result = predict_delay(data)
#     return jsonify(result)
# 
# @app.route('/chat', methods=['POST'])
# def api_chat():
#     data = request.json
#     message = data.get('message', '')
#     result = send_chat_message(message)
#     return jsonify(result)
# 
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)
