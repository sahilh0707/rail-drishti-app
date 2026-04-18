import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_client import predict_delay, send_chat_message

# Page configuration
st.set_page_config(
    page_title="Rail-Drishti",
    page_icon="🚂",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        padding: 0.75rem;
        border-radius: 8px;
    }
    .stButton>button:hover {
        background-color: #145a8c;
    }
    .prediction-box {
        padding: 2rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Load dataset
@st.cache_data
def load_data():
    """Load and cache the railway dataset."""
    try:
        df = pd.read_csv('data/indian_railway_data.csv')
        return df
    except FileNotFoundError:
        st.error("❌ Dataset not found. Please ensure 'data/indian_railway_data.csv' exists.")
        st.stop()

# Extract unique values for dropdowns
@st.cache_data
def get_unique_values(df):
    """Extract unique values for each field from the dataset."""
    return {
        'Train_id': sorted(df['Train_id'].unique().tolist()),
        'Train_no': sorted(df['Train_no'].unique().tolist()),
        'Source': sorted(df['Source'].unique().tolist()),
        'Destitnation': sorted(df['Destitnation'].unique().tolist()),
        'Distance(Km)': sorted(df['Distance(Km)'].unique().tolist()),
        'Sc_arr__time': sorted(df['Sc_arr__time'].unique().tolist()),
        'Season': sorted(df['Season'].unique().tolist()),
        'Run_frequency': sorted(df['Run_frequency'].unique().tolist())
    }

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Sidebar navigation
st.sidebar.title("🚂 Rail-Drishti")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation",
    ["🔮 Train Delay Predictor", "💬 Railway Assistant"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**About Rail-Drishti**\n\n"
    "Rail-Drishti is an intelligent railway assistance platform powered by ML.\n\n"
    "* Predict train delays\n"
    "* Get instant answers to railway queries"
)

# ==================== TRAIN DELAY PREDICTOR PAGE ====================
if page == "🔮 Train Delay Predictor":
    # Header
    st.markdown('<div class="main-header">🔮 Train Delay Predictor</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Predict train delays using advanced machine learning</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Load data
    df = load_data()
    unique_values = get_unique_values(df)
    
    # Create form
    with st.form("prediction_form"):
        st.subheader("📋 Enter Train Details")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            train_id = st.selectbox(
                "Train ID",
                options=unique_values['Train_id'],
                help="Select the train identifier"
            )
            
            source = st.selectbox(
                "Source Station",
                options=unique_values['Source'],
                help="Select the source station"
            )
            
            scheduled_time = st.selectbox(
                "Scheduled Arrival Time",
                options=unique_values['Sc_arr__time'],
                help="Select scheduled arrival time"
            )
        
        with col2:
            train_no = st.selectbox(
                "Train Number",
                options=unique_values['Train_no'],
                help="Select the train number"
            )
            
            destination = st.selectbox(
                "Destination Station",
                options=unique_values['Destitnation'],
                help="Select the destination station"
            )
            
            season = st.selectbox(
                "Season",
                options=unique_values['Season'],
                help="Select the season"
            )
        
        with col3:
            distance = st.selectbox(
                "Distance (Km)",
                options=unique_values['Distance(Km)'],
                help="Select the distance in kilometers"
            )
            
            date = st.date_input(
                "Travel Date",
                value=datetime.now(),
                help="Select the travel date"
            )
            
            frequency = st.selectbox(
                "Run Frequency",
                options=unique_values['Run_frequency'],
                help="Select how often the train runs"
            )
        
        st.divider()
        
        # Submit button
        submitted = st.form_submit_button(
            "🎯 Predict Delay",
            use_container_width=True
        )
    
    # Handle form submission
    if submitted:
        with st.spinner("🔄 Analyzing train data and predicting delay..."):
            # Prepare input data
            input_data = {
                'Train_id': str(train_id),
                'Train_no': str(train_no),
                'Source': source,
                'Destitnation': destination,
                'Date': date.strftime('%Y-%m-%d'),
                'Distance(Km)': float(distance),
                'Sc_arr__time': scheduled_time,
                'Season': season,
                'Run_frequency': frequency
            }
            
            # Make prediction
            result = predict_delay(input_data)
            
            if result['success']:
                delay_minutes = result['delay_minutes']
                
                st.success("✅ Prediction Complete!")
                
                # Display result
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col2:
                    st.markdown(
                        f'<div class="prediction-box">'
                        f'⏱️ Predicted Delay: {delay_minutes:.2f} Minutes'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    
                    # Additional metrics
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    
                    with metric_col1:
                        st.metric(
                            "Delay Category",
                            "On Time" if delay_minutes < 5 else "Delayed",
                            delta=f"{delay_minutes:.0f} min"
                        )
                    
                    with metric_col2:
                        hours = int(delay_minutes // 60)
                        mins = int(delay_minutes % 60)
                        st.metric(
                            "Delay Duration",
                            f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
                        )
                    
                    with metric_col3:
                        confidence = "High" if delay_minutes < 30 else "Medium"
                        st.metric("Confidence", confidence)
                
                st.divider()
                
                # Show input summary
                with st.expander("📊 View Input Details"):
                    input_df = pd.DataFrame([input_data]).T
                    input_df.columns = ['Value']
                    st.dataframe(input_df, use_container_width=True)
            else:
                st.error(f"❌ Prediction Failed: {result.get('error', 'Unknown error')}")

# ==================== RAILWAY ASSISTANT PAGE ====================
else:
    # Header
    st.markdown('<div class="main-header">💬 Railway Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ask me anything about Indian Railways</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.chat_history:
            st.info(
                "👋 Hello! I'm your Railway Assistant. I can help you with:\n\n"
                "* Train schedules and timings\n"
                "* Ticket booking information\n"
                "* Station facilities\n"
                "* Railway rules and regulations\n"
                "* Refund and cancellation policies\n\n"
                "Ask me anything!"
            )
        else:
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
    
    # Chat input
    user_input = st.chat_input("Type your railway question here...")
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = send_chat_message(user_input)
                
                if response['success']:
                    st.markdown(response['message'])
                    
                    # Add assistant response to history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response['message']
                    })
                else:
                    error_msg = f"❌ Error: {response.get('error', 'Unknown error')}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_msg
                    })
    
    # Clear chat button
    if st.session_state.chat_history:
        st.divider()
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
