"""
ML Integration - Connect ML predictions to phase balancing logic

This module provides a decision layer that uses ML predictions
to determine when phase switching should occur.
"""
from typing import List, Optional, Dict
from ml.ml_predictor import get_predictor

class MLPhaseBalancer:
    """
    Integrates ML model predictions with phase balancing system
    """
    
    def __init__(self, enable_ml: bool = True):
        """
        Initialize ML integration
        
        Args:
            enable_ml: If False, always use rule-based logic
        """
        self.enable_ml = enable_ml
        self.predictor = get_predictor() if enable_ml else None
        
        if enable_ml:
            print("[ML Integration] ML-based phase balancing enabled")
        else:
            print("[ML Integration] ML disabled, using rule-based only")
    
    def should_balance(self, phase_stats: List[Dict]) -> dict:
        """
        Determine if phase balancing is needed based on current phase stats
        
        Args:
            phase_stats: List of phase statistics, each containing:
                - phase: str (e.g., 'L1', 'L2', 'L3')
                - total_power_kw: float
                - house_count: int
                - avg_voltage: float
                
        Returns:
            dict with decision:
                - balance_needed: bool
                - reason: str
                - imbalance_kw: float
                - prediction_method: str ('ml_model' or 'rule_based')
                - ml_confidence: float or None
        """
        if not self.enable_ml or self.predictor is None:
            return self._rule_based_decision(phase_stats)
        
        # Extract phase powers
        phase_powers = {ps['phase']: ps['total_power_kw'] for ps in phase_stats}
        L1_kw = phase_powers.get('L1', 0.0)
        L2_kw = phase_powers.get('L2', 0.0)
        L3_kw = phase_powers.get('L3', 0.0)
        
        # Get ML prediction
        ml_result = self.predictor.predict(L1_kw, L2_kw, L3_kw)
        
        return {
            'balance_needed': ml_result['should_switch'],
            'reason': self._generate_reason(ml_result, L1_kw, L2_kw, L3_kw),
            'imbalance_kw': ml_result['imbalance'],
            'prediction_method': ml_result['method'],
            'ml_confidence': ml_result.get('confidence'),
            'phase_powers': {'L1': L1_kw, 'L2': L2_kw, 'L3': L3_kw}
        }
    
    def _generate_reason(self, ml_result: dict, L1: float, L2: float, L3: float) -> str:
        """Generate human-readable reason for decision"""
        if ml_result['should_switch']:
            powers = [L1, L2, L3]
            max_phase = ['L1', 'L2', 'L3'][powers.index(max(powers))]
            min_phase = ['L1', 'L2', 'L3'][powers.index(min(powers))]
            
            if ml_result.get('confidence'):
                return (f"ML model predicts switch needed (confidence: {ml_result['confidence']:.2%}). "
                       f"Imbalance: {ml_result['imbalance']:.2f} kW between {max_phase} and {min_phase}")
            else:
                return (f"ML/Rule-based: Switch needed. "
                       f"Imbalance: {ml_result['imbalance']:.2f} kW between {max_phase} and {min_phase}")
        else:
            return f"System balanced. Imbalance: {ml_result['imbalance']:.2f} kW (within acceptable range)"
    
    def _rule_based_decision(self, phase_stats: List[Dict]) -> dict:
        """Fallback to rule-based decision"""
        phase_powers = {ps['phase']: ps['total_power_kw'] for ps in phase_stats}
        L1_kw = phase_powers.get('L1', 0.0)
        L2_kw = phase_powers.get('L2', 0.0)
        L3_kw = phase_powers.get('L3', 0.0)
        
        powers = [L1_kw, L2_kw, L3_kw]
        imbalance = max(powers) - min(powers)
        balance_needed = imbalance >= 0.15
        
        return {
            'balance_needed': balance_needed,
            'reason': f"Rule-based: Imbalance {imbalance:.2f} kW ({'exceeds' if balance_needed else 'within'} threshold)",
            'imbalance_kw': round(imbalance, 3),
            'prediction_method': 'rule_based',
            'ml_confidence': None,
            'phase_powers': {'L1': L1_kw, 'L2': L2_kw, 'L3': L3_kw}
        }

# Global instance
_ml_balancer = None

def get_ml_balancer(enable_ml: bool = True) -> MLPhaseBalancer:
    """Get or create global ML balancer instance"""
    global _ml_balancer
    if _ml_balancer is None:
        _ml_balancer = MLPhaseBalancer(enable_ml=enable_ml)
    return _ml_balancer
