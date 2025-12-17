"""
ML Predictor - Load trained model and make predictions
"""
import pickle
import numpy as np
from pathlib import Path

class PhaseBalancingPredictor:
    """Predicts whether phase switching is needed based on L1, L2, L3 power values"""
    
    def __init__(self, model_path='ml/xgboost_model.pkl', encoder_path='ml/label_encoder.pkl'):
        """
        Initialize predictor by loading trained model and label encoder
        
        Args:
            model_path: Path to saved XGBoost model
            encoder_path: Path to saved label encoder
        """
        self.model_path = Path(model_path)
        self.encoder_path = Path(encoder_path)
        self.model = None
        self.label_encoder = None
        self.loaded = False
    
    def load_model(self):
        """Load the trained model and label encoder"""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            with open(self.encoder_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
            
            self.loaded = True
            print(f"[ML] Model loaded successfully from {self.model_path}")
            return True
        except FileNotFoundError as e:
            print(f"[ML] Error: Model files not found. Please train the model first.")
            print(f"[ML] Run: python ml/train_and_save_model.py")
            return False
        except Exception as e:
            print(f"[ML] Error loading model: {e}")
            return False
    
    def predict(self, L1_kw: float, L2_kw: float, L3_kw: float) -> dict:
        """
        Predict whether switching is needed based on phase powers
        
        Args:
            L1_kw: Power on L1 phase in kW
            L2_kw: Power on L2 phase in kW
            L3_kw: Power on L3 phase in kW
            
        Returns:
            dict with prediction results:
                - should_switch: bool (True if switch recommended)
                - prediction: str ('switch' or 'not_switch')
                - confidence: float (model confidence, if available)
                - imbalance: float (max - min power)
        """
        # Load model if not already loaded
        if not self.loaded:
            if not self.load_model():
                # Fallback to rule-based if model not available
                return self._rule_based_prediction(L1_kw, L2_kw, L3_kw)
        
        try:
            # Verify model and encoder are loaded
            if self.model is None or self.label_encoder is None:
                return self._rule_based_prediction(L1_kw, L2_kw, L3_kw)
            
            # Prepare input features
            X = np.array([[L1_kw, L2_kw, L3_kw]])
            
            # Make prediction
            prediction_encoded = self.model.predict(X)[0]
            prediction_label = self.label_encoder.inverse_transform([prediction_encoded])[0]
            
            # Get confidence if model supports it
            try:
                if self.model is not None and hasattr(self.model, 'predict_proba'):
                    probabilities = self.model.predict_proba(X)[0]
                    confidence = float(max(probabilities))
                else:
                    confidence = None
            except:
                confidence = None
            
            # Calculate imbalance
            powers = [L1_kw, L2_kw, L3_kw]
            imbalance = max(powers) - min(powers)
            
            return {
                'should_switch': prediction_label == 'switch',
                'prediction': prediction_label,
                'confidence': confidence,
                'imbalance': round(imbalance, 3),
                'method': 'ml_model'
            }
        
        except Exception as e:
            print(f"[ML] Prediction error: {e}, falling back to rule-based")
            return self._rule_based_prediction(L1_kw, L2_kw, L3_kw)
    
    def _rule_based_prediction(self, L1_kw: float, L2_kw: float, L3_kw: float) -> dict:
        """
        Fallback rule-based prediction if ML model is unavailable
        Uses simple threshold: imbalance >= 0.15 kW requires switch
        """
        powers = [L1_kw, L2_kw, L3_kw]
        imbalance = max(powers) - min(powers)
        should_switch = imbalance >= 0.15
        
        return {
            'should_switch': should_switch,
            'prediction': 'switch' if should_switch else 'not_switch',
            'confidence': None,
            'imbalance': round(imbalance, 3),
            'method': 'rule_based_fallback'
        }

# Global predictor instance
_predictor = None

def get_predictor() -> PhaseBalancingPredictor:
    """Get or create the global predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = PhaseBalancingPredictor()
    return _predictor