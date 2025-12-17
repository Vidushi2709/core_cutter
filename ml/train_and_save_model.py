"""
Train XGBoost model and save it for production use
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import pickle

def train_and_save_model():
    """Train model on training data and save it along with label encoder"""
    # Load training data
    train_df = pd.read_csv('phase_balancing_training_data.csv')
    
    # Prepare features and labels
    X_train = train_df[['L1', 'L2', 'L3']].to_numpy()
    y_train = train_df['switch'].to_numpy()
    
    # Encode labels
    le = LabelEncoder()
    y_train_encoded = le.fit_transform(y_train)
    
    # Train XGBoost model
    model = xgb.XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss')
    model.fit(X_train, y_train_encoded)
    
    # Save model
    with open('xgboost_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    # Save label encoder
    with open('label_encoder.pkl', 'wb') as f:
        pickle.dump(le, f)
    
    print("✅ Model trained and saved successfully!")
    print(f"   - Model: xgboost_model.pkl")
    print(f"   - Label Encoder: label_encoder.pkl")
    print(f"   - Training samples: {len(X_train)}")
    print(f"   - Classes: {le.classes_}")

if __name__ == "__main__":
    train_and_save_model()
