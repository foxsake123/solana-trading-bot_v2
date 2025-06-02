# ml_enhancement_strategy.py

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score
import joblib
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class EnhancedMLTrainer:
    """Enhanced ML trainer with advanced features and better data handling"""
    
    def __init__(self):
        self.models = {
            'entry_classifier': None,
            'exit_predictor': None,
            'risk_assessor': None
        }
        self.scalers = {}
        self.feature_importance = {}
        
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create comprehensive feature set for ML training"""
        
        features = pd.DataFrame()
        
        # Price-based features
        features['price_change_1h'] = df['price'].pct_change(6)  # 6 x 10min = 1h
        features['price_change_6h'] = df['price'].pct_change(36)
        features['price_change_24h'] = df['price'].pct_change(144)
        
        # Volatility features
        features['volatility_1h'] = df['price'].rolling(6).std() / df['price'].rolling(6).mean()
        features['volatility_24h'] = df['price'].rolling(144).std() / df['price'].rolling(144).mean()
        
        # Volume features
        features['volume_ratio'] = df['volume'] / df['volume'].rolling(24).mean()
        features['volume_trend'] = df['volume'].rolling(12).mean() / df['volume'].rolling(48).mean()
        
        # Liquidity features
        features['liquidity_ratio'] = df['liquidity'] / df['liquidity'].rolling(24).mean()
        features['liquidity_stability'] = 1 / (df['liquidity'].rolling(24).std() / df['liquidity'].rolling(24).mean() + 1)
        
        # Market cap features
        features['mcap_growth'] = df['market_cap'].pct_change(24)
        features['mcap_to_volume'] = df['market_cap'] / (df['volume'] + 1)
        
        # Technical indicators
        features['rsi'] = self._calculate_rsi(df['price'])
        features['macd_signal'] = self._calculate_macd_signal(df['price'])
        features['bb_position'] = self._calculate_bollinger_position(df['price'])
        
        # Holder metrics
        features['holder_growth'] = df['holders'].pct_change(24)
        features['holder_concentration'] = df['holders'] / (df['market_cap'] / 1000000 + 1)
        
        # Time-based features
        features['hour_of_day'] = df.index.hour
        features['day_of_week'] = df.index.dayofweek
        
        # Interaction features
        features['price_volume_interaction'] = features['price_change_24h'] * features['volume_ratio']
        features['volatility_liquidity_ratio'] = features['volatility_24h'] / (features['liquidity_ratio'] + 0.1)
        
        return features.fillna(0)
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI technical indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)
    
    def _calculate_macd_signal(self, prices: pd.Series) -> pd.Series:
        """Calculate MACD signal"""
        ema12 = prices.ewm(span=12, adjust=False).mean()
        ema26 = prices.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        return (macd - signal).fillna(0)
    
    def _calculate_bollinger_position(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """Calculate position within Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        position = (prices - lower) / (upper - lower)
        return position.fillna(0.5)
    
    def prepare_training_data(self, db) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare comprehensive training dataset"""
        
        # Fetch historical data
        query = """
        SELECT 
            t.contract_address,
            t.timestamp,
            tk.price_usd as price,
            tk.volume_24h as volume,
            tk.liquidity_usd as liquidity,
            tk.mcap as market_cap,
            tk.holders,
            tr.action,
            tr.price as trade_price,
            tr.amount,
            tr.profit_loss
        FROM tokens tk
        JOIN trades tr ON tk.contract_address = tr.contract_address
        ORDER BY t.timestamp
        """
        
        df = pd.read_sql_query(query, db.conn)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Create features
        features = self.create_features(df)
        
        # Create labels (profitable trade: 1, loss: 0)
        df['profitable'] = (df['profit_loss'] > 0).astype(int)
        
        return features, df['profitable']
    
    def train_entry_classifier(self, X: pd.DataFrame, y: pd.Series):
        """Train model to predict good entry points"""
        
        # Split data
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers['entry'] = scaler
        
        # Train model
        model = GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=6,
            min_samples_split=50,
            subsample=0.8,
            random_state=42
        )
        
        # Cross-validation
        scores = []
        for train_idx, val_idx in tscv.split(X_scaled):
            X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)
            
            scores.append({
                'accuracy': accuracy_score(y_val, y_pred),
                'precision': precision_score(y_val, y_pred),
                'recall': recall_score(y_val, y_pred)
            })
        
        # Final training on all data
        model.fit(X_scaled, y)
        self.models['entry_classifier'] = model
        
        # Feature importance
        self.feature_importance['entry'] = dict(zip(
            X.columns, 
            model.feature_importances_
        ))
        
        logger.info(f"Entry classifier trained - Avg accuracy: {np.mean([s['accuracy'] for s in scores]):.3f}")
        
        return scores
    
    def train_exit_predictor(self, X: pd.DataFrame, y: pd.Series):
        """Train model to predict optimal exit points"""
        
        # For exit prediction, we predict the best profit percentage
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers['exit'] = scaler
        
        model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=6,
            min_samples_split=50,
            subsample=0.8,
            random_state=42
        )
        
        model.fit(X_scaled, y)
        self.models['exit_predictor'] = model
        
        logger.info("Exit predictor trained")
    
    def predict_entry(self, features: Dict) -> Dict:
        """Predict if current conditions are good for entry"""
        
        if self.models['entry_classifier'] is None:
            return {'should_enter': False, 'confidence': 0.0}
        
        # Prepare features
        feature_df = pd.DataFrame([features])
        X_scaled = self.scalers['entry'].transform(feature_df)
        
        # Get prediction and probability
        prediction = self.models['entry_classifier'].predict(X_scaled)[0]
        probability = self.models['entry_classifier'].predict_proba(X_scaled)[0, 1]
        
        # Get top contributing features
        importances = self.feature_importance.get('entry', {})
        top_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'should_enter': bool(prediction),
            'confidence': float(probability),
            'top_factors': top_features,
            'risk_score': self._calculate_risk_score(features)
        }
    
    def _calculate_risk_score(self, features: Dict) -> float:
        """Calculate risk score based on multiple factors"""
        
        risk_score = 0.0
        
        # High volatility increases risk
        if features.get('volatility_24h', 0) > 0.5:
            risk_score += 30
        
        # Low liquidity increases risk
        if features.get('liquidity_ratio', 1) < 0.5:
            risk_score += 25
        
        # Extreme price movements increase risk
        if abs(features.get('price_change_24h', 0)) > 0.5:
            risk_score += 20
        
        # Low holder count increases risk
        if features.get('holders', 0) < 100:
            risk_score += 25
        
        return min(risk_score, 100)
    
    def save_models(self, directory: str):
        """Save trained models and scalers"""
        import os
        
        os.makedirs(directory, exist_ok=True)
        
        # Save models
        for name, model in self.models.items():
            if model is not None:
                joblib.dump(model, f"{directory}/{name}.pkl")
        
        # Save scalers
        for name, scaler in self.scalers.items():
            joblib.dump(scaler, f"{directory}/{name}_scaler.pkl")
        
        # Save feature importance
        import json
        with open(f"{directory}/feature_importance.json", 'w') as f:
            json.dump(self.feature_importance, f, indent=2)
    
    def load_models(self, directory: str):
        """Load saved models and scalers"""
        import os
        
        # Load models
        for name in self.models.keys():
            model_path = f"{directory}/{name}.pkl"
            if os.path.exists(model_path):
                self.models[name] = joblib.load(model_path)
        
        # Load scalers
        for name in ['entry', 'exit']:
            scaler_path = f"{directory}/{name}_scaler.pkl"
            if os.path.exists(scaler_path):
                self.scalers[name] = joblib.load(scaler_path)


# Training script
def train_enhanced_models(db_path: str):
    """Train all ML models with enhanced features"""
    
    from database import Database
    
    db = Database(db_path)
    trainer = EnhancedMLTrainer()
    
    # Prepare data
    X, y = trainer.prepare_training_data(db)
    
    # Train models
    trainer.train_entry_classifier(X, y)
    
    # Save models
    trainer.save_models("data/models/enhanced")
    
    logger.info("Enhanced ML models trained and saved")


if __name__ == "__main__":
    train_enhanced_models("data/sol_bot.db")
