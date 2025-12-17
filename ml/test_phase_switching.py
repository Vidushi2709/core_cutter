"""
Test script for phase switching predictions using trained ML model
Loads the saved model and makes switch/not_switch decisions
"""

import pickle
import numpy as np
import os

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, 'phase_balancing_model.pkl')
ENCODER_PATH = os.path.join(SCRIPT_DIR, 'label_encoder.pkl')


def load_model():
    """Load the trained model and label encoder"""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Train the model first!")
    
    if not os.path.exists(ENCODER_PATH):
        raise FileNotFoundError(f"Label encoder not found at {ENCODER_PATH}. Train the model first!")
    
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    
    with open(ENCODER_PATH, 'rb') as f:
        encoder = pickle.load(f)
    
    return model, encoder


def predict_switch(model, encoder, l1_kw, l2_kw, l3_kw):
    """
    Predict whether phase switching is needed
    
    Args:
        model: Trained XGBoost model
        encoder: Label encoder
        l1_kw: Power on L1 phase in kW
        l2_kw: Power on L2 phase in kW
        l3_kw: Power on L3 phase in kW
    
    Returns:
        dict: {
            'should_switch': bool,
            'prediction': str ('switch' or 'not_switch'),
            'confidence': float,
            'imbalance': float,
            'phase_powers': dict
        }
    """
    # Prepare input
    features = np.array([[l1_kw, l2_kw, l3_kw]])
    
    # Make prediction
    prediction = model.predict(features)[0]
    prediction_proba = model.predict_proba(features)[0]
    prediction_label = encoder.inverse_transform([prediction])[0]
    
    # Get confidence (probability of predicted class)
    confidence = prediction_proba[prediction]
    
    # Calculate imbalance
    imbalance = max(l1_kw, l2_kw, l3_kw) - min(l1_kw, l2_kw, l3_kw)
    
    return {
        'should_switch': prediction_label == 'switch',
        'prediction': prediction_label,
        'confidence': float(confidence),
        'imbalance': float(imbalance),
        'phase_powers': {
            'L1': l1_kw,
            'L2': l2_kw,
            'L3': l3_kw
        }
    }


def test_scenario(model, encoder, name, l1, l2, l3):
    """Test a single scenario and display results"""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"{'='*70}")
    print(f"Phase Powers: L1={l1:.2f} kW, L2={l2:.2f} kW, L3={l3:.2f} kW")
    
    result = predict_switch(model, encoder, l1, l2, l3)
    
    imbalance = result['imbalance']
    prediction = result['prediction']
    confidence = result['confidence']
    should_switch = result['should_switch']
    
    print(f"Imbalance: {imbalance:.2f} kW")
    print(f"\n{' DECISION: SWITCH PHASE' if should_switch else ' DECISION: NO SWITCHING NEEDED'}")
    print(f"Prediction: {prediction}")
    print(f"Confidence: {confidence:.2%}")
    
    # Show reasoning
    if should_switch:
        print(f"\n Reasoning: Imbalance of {imbalance:.2f} kW detected.")
        print(f"   Phase switching recommended to balance the load.")
    else:
        print(f"\n Reasoning: System is balanced with only {imbalance:.2f} kW imbalance.")
        print(f"   No switching needed.")
    
    return result


def main():
    print("="*70)
    print("PHASE SWITCHING ML PREDICTION TEST")
    print("="*70)
    
    # Load model
    print("\n Loading trained model...")
    try:
        model, encoder = load_model()
        print(" Model loaded successfully!")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    
    # Test scenarios
    test_cases = [
        ("Balanced System", 2.5, 2.6, 2.4),
        ("Light Imbalance", 2.0, 2.3, 2.1),
        ("Moderate Imbalance", 2.0, 4.5, 2.5),
        ("Critical Imbalance", 0.8, 6.2, 2.0),
        ("Export Balanced", -1.1, -1.2, -1.3),
        ("Export Imbalanced", -0.5, -3.8, -1.5),
        ("High Load Balanced", 5.5, 5.6, 5.4),
        ("High Load Imbalanced", 5.0, 2.0, 3.5),
        ("Low Load Balanced", 0.8, 0.9, 0.85),
        ("One Phase Very High", 1.0, 6.5, 2.0),
    ]
    
    results = []
    for name, l1, l2, l3 in test_cases:
        result = test_scenario(model, encoder, name, l1, l2, l3)
        results.append((name, result))
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    switch_count = sum(1 for _, r in results if r['should_switch'])
    no_switch_count = len(results) - switch_count
    
    print(f"\nTotal scenarios tested: {len(results)}")
    print(f"Switch recommended: {switch_count} ({switch_count/len(results)*100:.1f}%)")
    print(f"No switching needed: {no_switch_count} ({no_switch_count/len(results)*100:.1f}%)")
    
    print(f"\n{'='*70}")
    print("Scenario Details:")
    print(f"{'='*70}")
    for name, result in results:
        status = "SWITCH" if result['should_switch'] else "NO SWITCH"
        print(f"{status:15} | {name:25} | Imbalance: {result['imbalance']:5.2f} kW | Confidence: {result['confidence']:6.2%}")
    
    print("\n✅ Testing complete!")


if __name__ == "__main__":
    main()
