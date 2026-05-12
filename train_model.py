import pandas as pd
import joblib
import os
from xgboost import XGBRegressor

def train_and_save_model():
    print("Loading data...")
    df = pd.read_csv('data/indian_railway_data.csv')
    
    print("Preprocessing data...")
    # Strip whitespace from string columns
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip()
    
    # Dealy_min is already numeric (minutes) after CSV preprocessing
    df['Dealy_min'] = pd.to_numeric(df['Dealy_min'], errors='coerce').fillna(0)
    
    # Handle time strings
    def time_to_minutes(val):
        try:
            parts = str(val).split(':')
            return float(int(parts[0]) * 60 + int(parts[1]))
        except:
            return 0.0
            
    if 'Sc_arr__time' in df.columns:
        df['Sc_arr__time_min'] = df['Sc_arr__time'].apply(time_to_minutes)
    if 'Act_arr_time' in df.columns:
        df['Act_arr_time_min'] = df['Act_arr_time'].apply(time_to_minutes)
        
    # Handle dates
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Month'] = df['Date'].dt.month.fillna(0)
        df['DayOfWeek'] = df['Date'].dt.dayofweek.fillna(0)
        
    # Drop raw columns
    cols_to_drop = ['Train_name', 'Date', 'Sc_arr__time', 'Act_arr_time']
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    
    # Save category mapping
    category_mappings = {}
    for col in df.select_dtypes(include=['object', 'category']).columns:
        df[col] = df[col].astype('category')
        # Store as dictionary for saving
        category_mappings[col] = dict(enumerate(df[col].cat.categories))
        df[col] = df[col].cat.codes
        
    X = df.drop(columns=['Dealy_min'])
    y = df['Dealy_min'].astype(float)
    
    model_cols = X.columns.tolist()
    
    print(f"Training XGBoost on {len(X)} samples...")
    print(f"Features: {model_cols}")
    print(f"Target range: {y.min():.1f} - {y.max():.1f} minutes")
    
    model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
    model.fit(X, y)
    
    print("Saving model...")
    os.makedirs('models', exist_ok=True)
    
    artifact = {
        'model': model,
        'model_cols': model_cols,
        'category_mappings': category_mappings
    }
    joblib.dump(artifact, 'models/xgboost_artifact.pkl')
    print("[OK] Model saved successfully to models/xgboost_artifact.pkl")
    print(f"[OK] Category mappings: {category_mappings}")

if __name__ == "__main__":
    train_and_save_model()
