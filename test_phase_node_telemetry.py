"""
Test script to send phase-level telemetry directly to the new endpoint.

This simulates an edge node that aggregates all house loads per phase
and sends the totals to the balancing controller.
"""
import requests
import time
from datetime import datetime

API_BASE = "http://localhost:8000"

def send_phase_telemetry(L1_kw, L2_kw, L3_kw):
    """Send phase totals to the new phase telemetry endpoint."""
    response = requests.post(
        f"{API_BASE}/telemetry/phases",
        json={
            "L1_kw": L1_kw,
            "L2_kw": L2_kw,
            "L3_kw": L3_kw
        }
    )
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Phase Telemetry Sent:")
    print(f"  L1: {L1_kw:.2f} kW")
    print(f"  L2: {L2_kw:.2f} kW")
    print(f"  L3: {L3_kw:.2f} kW")
    print(f"  Response: {response.json()}")
    return response.json()

def scenario_imbalanced():
    """Test scenario: L1 is heavily loaded, L2 is light"""
    print("\n" + "="*60)
    print("SCENARIO: Imbalanced System")
    print("="*60)
    
    for i in range(5):
        # L1 overloaded, L2 underloaded, L3 balanced
        send_phase_telemetry(
            L1_kw=4.5,  # Heavy load
            L2_kw=1.2,  # Light load
            L3_kw=2.8   # Medium load
        )
        time.sleep(3)

def scenario_balanced():
    """Test scenario: All phases balanced"""
    print("\n" + "="*60)
    print("SCENARIO: Balanced System")
    print("="*60)
    
    for i in range(5):
        # All phases roughly equal
        send_phase_telemetry(
            L1_kw=2.1,
            L2_kw=2.0,
            L3_kw=2.2
        )
        time.sleep(3)

def scenario_export_mode():
    """Test scenario: System exporting power"""
    print("\n" + "="*60)
    print("SCENARIO: Export Mode (Negative Power)")
    print("="*60)
    
    for i in range(5):
        # Negative = export
        send_phase_telemetry(
            L1_kw=-3.5,
            L2_kw=-1.2,
            L3_kw=-2.8
        )
        time.sleep(3)

def scenario_mixed():
    """Test scenario: Some phases export, some import"""
    print("\n" + "="*60)
    print("SCENARIO: Mixed Export/Import")
    print("="*60)
    
    for i in range(5):
        send_phase_telemetry(
            L1_kw=-2.5,  # Exporting
            L2_kw=1.8,   # Importing
            L3_kw=0.3    # Nearly balanced
        )
        time.sleep(3)

def scenario_gradual_change():
    """Test scenario: Load gradually shifts from L1 to L2"""
    print("\n" + "="*60)
    print("SCENARIO: Gradual Load Shift")
    print("="*60)
    
    for i in range(10):
        l1_power = 4.0 - (i * 0.3)
        l2_power = 1.5 + (i * 0.3)
        send_phase_telemetry(
            L1_kw=l1_power,
            L2_kw=l2_power,
            L3_kw=2.5
        )
        time.sleep(2)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("PHASE NODE TELEMETRY TEST")
    print("="*60)
    print("This script sends phase-level totals directly to the controller.")
    print("It bypasses individual house telemetry and tests the new endpoint.")
    print("="*60)
    
    try:
        # Run test scenarios
        scenario_imbalanced()
        time.sleep(2)
        
        scenario_balanced()
        time.sleep(2)
        
        scenario_export_mode()
        time.sleep(2)
        
        scenario_mixed()
        time.sleep(2)
        
        scenario_gradual_change()
        
        print("\n" + "="*60)
        print("✓ ALL SCENARIOS COMPLETED")
        print("="*60)
        print("Check the dashboard to see how the system responded!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server")
        print("Make sure the FastAPI server is running: python app.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
