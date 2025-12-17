# ML-Based Phase Balancing

This module integrates machine learning predictions into the phase balancing system.

## Files

- **`model.ipynb`** - Jupyter notebook for model training and evaluation
- **`train_and_save_model.py`** - Script to train and save the XGBoost model
- **`ml_predictor.py`** - Model loader and prediction interface
- **`ml_integration.py`** - Integration layer with core balancing logic
- **Data files:**
  - `phase_balancing_training_data.csv` - Training dataset
  - `phase_balancing_test_data.csv` - Test dataset

## Quick Start

### 1. Train the Model

```bash
cd ml
python train_and_save_model.py
```

This will create:
- `xgboost_model.pkl` - Trained model
- `label_encoder.pkl` - Label encoder for predictions

### 2. Use ML in Your Code

```python
from ml.ml_integration import get_ml_balancer

# Initialize ML balancer
ml_balancer = get_ml_balancer(enable_ml=True)

# Get phase stats from your system
phase_stats = [
    {'phase': 'L1', 'total_power_kw': 2.5, 'house_count': 10, 'avg_voltage': 230},
    {'phase': 'L2', 'total_power_kw': 5.2, 'house_count': 15, 'avg_voltage': 228},
    {'phase': 'L3', 'total_power_kw': 2.8, 'house_count': 12, 'avg_voltage': 231}
]

# Get ML decision
decision = ml_balancer.should_balance(phase_stats)

if decision['balance_needed']:
    print(f"Switch needed! {decision['reason']}")
    print(f"Confidence: {decision['ml_confidence']:.2%}")
    # Proceed with phase switching logic
else:
    print(f"System balanced: {decision['reason']}")
```

### 3. Direct Prediction

```python
from ml.ml_predictor import get_predictor

predictor = get_predictor()
result = predictor.predict(L1_kw=2.5, L2_kw=5.2, L3_kw=2.8)

print(f"Should switch: {result['should_switch']}")
print(f"Prediction: {result['prediction']}")
print(f"Imbalance: {result['imbalance']} kW")
```

## Integration with Backend

To integrate with your main backend (`backend/main.py`), modify the phase balancing controller to check ML predictions before making switching decisions.

## Model Performance

- **Model**: XGBoost Classifier
- **Cross-Validation Accuracy**: ~97%
- **Training Samples**: 300
- **Features**: L1, L2, L3 power values (kW)
- **Output**: `switch` or `not_switch`

## Fallback Behavior

If the ML model is not available or encounters an error:
- Automatically falls back to rule-based logic
- Uses threshold: imbalance >= 0.15 kW requires switch
- No interruption to system operation
