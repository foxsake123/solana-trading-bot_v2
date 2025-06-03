#!/usr/bin/env python3
"""
Train ML model from collected trading data
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import sqlite3
import json
from datetime import datetime

def prepare_training_data():
    """Prepare features and labels from trading history"""
    print("Loading trading data...")
    
    conn = sqlite3.connect('data/db/sol_bot.db')
    
    # Get all completed trades with their outcomes
    query = """
    SELECT 
        t1.contract_address,
        t1.price as buy_price,
        t1.timestamp as buy_time,
        t2.price as sell_price,
        t2.timestamp as sell_time,
        t2.gain_loss_sol,
        t2.percentage_change,
        tk.volume_24h,
        tk.liquidity_usd,
        tk.mcap,
        tk.holders,
        tk.safety_score
    FROM trades t1
    JOIN trades t2 ON t1.contract_address = t2.contract_address
    LEFT JOIN tokens tk ON t1.contract_address = tk.contract_address
    WHERE t1.action = 'BUY' AND t2.action = 'SELL'
    AND t1.timestamp < t2.timestamp
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("No completed trades found for training")
        return None, None
    
    print(f"Found {len(df)} completed trades for training")
    
    # Create features
    features = pd.DataFrame()
    
    # Basic token metrics
    features['volume_24h'] = df['volume_24h'].fillna(0)
    features['liquidity_usd'] = df['liquidity_usd'].fillna(0)
    features['mcap'] = df['mcap'].fillna(0)
    features['holders'] = df['holders'].fillna(0)
    features['safety_score'] = df['safety_score'].fillna(50)
    
    # Normalized features
    features['volume_to_mcap'] = features['volume_24h'] / (features['mcap'] + 1)
    features['liquidity_to_mcap'] = features['liquidity_usd'] / (features['mcap'] + 1)
    features['holders_normalized'] = features['holders'] / 1000
    
    # Create labels (1 for profitable, 0 for loss)
    labels = (df['gain_loss_sol'] > 0).astype(int)
    
    return features, labels

def train_model(features, labels):
    """Train the ML model"""
    print("\nTraining ML model...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.2, random_state=42
    )
    
    # Train Random Forest
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    print("\nModel Performance:")
    print(classification_report(y_test, y_pred))
    
    # Feature importance
    importance = pd.DataFrame({
        'feature': features.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nFeature Importance:")
    print(importance)
    
    return model, importance

def save_model(model, features_info):
    """Save the trained model"""
    # Create models directory
    import os
    os.makedirs('data/models', exist_ok=True)
    
    # Save model
    joblib.dump(model, 'data/models/ml_model.pkl')
    
    # Save model info
    model_info = {
        'trained_date': datetime.now().isoformat(),
        'model_type': 'RandomForestClassifier',
        'features': list(features_info.columns),
        'feature_importance': features_info.to_dict('records'),
        'performance_notes': 'Model trained on simulation data'
    }
    
    with open('data/models/ml_model_info.json', 'w') as f:
        json.dump(model_info, f, indent=2)
    
    print("\n✅ Model saved to data/models/ml_model.pkl")
    print("✅ Model info saved to data/models/ml_model_info.json")

def main():
    print("="*60)
    print("ML MODEL TRAINING FOR SOLANA TRADING BOT")
    print("="*60)
    
    # Prepare data
    features, labels = prepare_training_data()
    
    if features is None:
        print("\n❌ Not enough data for training yet.")
        print("Let the bot run more to collect trading data.")
        return
    
    if len(features) < 50:
        print(f"\n⚠️  Only {len(features)} trades available.")
        print("Recommendation: Wait for at least 50-100 trades for better results.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Train model
    model, importance = train_model(features, labels)
    
    # Save model
    save_model(model, features)
    
    print("\n" + "="*60)
    print("✅ ML Model Training Complete!")
    print("The bot will now use this model for better trade decisions.")
    print("\nNext steps:")
    print("1. Restart the bot to load the new model")
    print("2. Monitor if win rate improves")
    print("3. Retrain periodically as more data accumulates")

if __name__ == "__main__":
    main()
