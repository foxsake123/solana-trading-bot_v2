# ml/models/ml_predictor.py
import joblib
import numpy as np
from typing import Dict, Optional

class MLPredictor:
    """Wrapper for ML predictions"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.is_loaded = False
    
    def load_models(self, model_dir: str):
        """Load trained models"""
        try:
            self.models['entry'] = joblib.load(f'{model_dir}/entry_classifier.pkl')
            self.scalers['entry'] = joblib.load(f'{model_dir}/entry_scaler.pkl')
            self.is_loaded = True
        except:
            self.is_loaded = False
    
    def predict_entry(self, features: Dict) -> Dict:
        """Predict entry signal"""
        if not self.is_loaded:
            return {'should_enter': False, 'confidence': 0.0}
        
        # Convert features to array
        feature_array = np.array([list(features.values())])
        scaled_features = self.scalers['entry'].transform(feature_array)
        
        prediction = self.models['entry'].predict(scaled_features)[0]
        confidence = self.models['entry'].predict_proba(scaled_features)[0, 1]
        
        return {
            'should_enter': bool(prediction),
            'confidence': float(confidence)
        }