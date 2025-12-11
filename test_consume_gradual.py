"""
Test Case: Gradual Load Increase
Tests system response as load gradually increases on one phase
Sends multiple rounds with increasing load
"""
import requests
import time

API_BASE = "http://localhost:8000"

def send_telemetry(house_id, voltage, current, power_kw, phase):
    """Send telemetry data to the API."""
    try:
        response = requests.post(f"{API_BASE}/telemetry", json={
            "house_id": house_id,
            "voltage": voltage,
            "current": current,
            "power_kw": power_kw,
            "phase": phase
        })
        response.raise_for_status()
        result = response.json()
        print(f"✓ {house_id:4s} | Phase: {result['new_phase']} | {power_kw:+.2f} kW | {voltage:.0f}V")
        return result.get("new_phase", phase)
    except Exception as e:
        print(f"❌ Error sending data for {house_id}: {e}")
        return phase

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST CASE: Gradual Load Increase")
    print("="*60)
    print("\nMake sure your FastAPI server is running: python app.py\n")
    
    # Round 1: Balanced start
    print("\n[ROUND 1] Initial balanced state")
    print("-" * 60)
    houses_r1 = [
        {"house_id": "B1", "power_kw": 0.50, "voltage": 230.0, "phase": "L1"},
        {"house_id": "H1", "power_kw": 0.50, "voltage": 230.0, "phase": "L2"},
        {"house_id": "B2", "power_kw": 0.50, "voltage": 230.0, "phase": "L3"},
    ]
    
    for house in houses_r1:
        power_kw = house["power_kw"]
        voltage = house["voltage"]
        current = power_kw / (voltage / 1000)
        send_telemetry(house["house_id"], voltage, current, power_kw, house["phase"])
    
    print("\nPhase loads: L1=0.50, L2=0.50, L3=0.50 kW (Balanced)")
    time.sleep(7)  # Wait for cooldown
    
    # Round 2: One house increases load slightly
    print("\n[ROUND 2] H1 increases to 0.80 kW")
    print("-" * 60)
    houses_r2 = [
        {"house_id": "B1", "power_kw": 0.50, "voltage": 230.0, "phase": "L1"},
        {"house_id": "H1", "power_kw": 0.80, "voltage": 230.0, "phase": "L2"},  # Increased
        {"house_id": "B2", "power_kw": 0.50, "voltage": 230.0, "phase": "L3"},
    ]
    
    for house in houses_r2:
        power_kw = house["power_kw"]
        voltage = house["voltage"]
        current = power_kw / (voltage / 1000)
        send_telemetry(house["house_id"], voltage, current, power_kw, house["phase"])
    
    print("\nPhase loads: L1=0.50, L2=0.80, L3=0.50 kW (Imbalance: 0.30 kW)")
    time.sleep(7)
    
    # Round 3: Add another heavy consumer on L2
    print("\n[ROUND 3] Add H2 with 1.20 kW on L2")
    print("-" * 60)
    houses_r3 = [
        {"house_id": "B1", "power_kw": 0.50, "voltage": 230.0, "phase": "L1"},
        {"house_id": "H1", "power_kw": 0.80, "voltage": 230.0, "phase": "L2"},
        {"house_id": "H2", "power_kw": 1.20, "voltage": 230.0, "phase": "L2"},  # New heavy load
        {"house_id": "B2", "power_kw": 0.50, "voltage": 230.0, "phase": "L3"},
    ]
    
    for house in houses_r3:
        power_kw = house["power_kw"]
        voltage = house["voltage"]
        current = power_kw / (voltage / 1000)
        send_telemetry(house["house_id"], voltage, current, power_kw, house["phase"])
    
    print("\nPhase loads: L1=0.50, L2=2.00, L3=0.50 kW (Imbalance: 1.50 kW - CRITICAL!)")
    time.sleep(7)
    
    # Round 4: Add more devices to other phases
    print("\n[ROUND 4] Add V1 and V2 to L1 and L3")
    print("-" * 60)
    houses_r4 = [
        {"house_id": "B1", "power_kw": 0.50, "voltage": 230.0, "phase": "L1"},
        {"house_id": "V1", "power_kw": 0.40, "voltage": 230.0, "phase": "L1"},  # New
        {"house_id": "H1", "power_kw": 0.80, "voltage": 230.0, "phase": "L2"},
        {"house_id": "H2", "power_kw": 1.20, "voltage": 230.0, "phase": "L2"},
        {"house_id": "B2", "power_kw": 0.50, "voltage": 230.0, "phase": "L3"},
        {"house_id": "V2", "power_kw": 0.35, "voltage": 230.0, "phase": "L3"},  # New
    ]
    
    for house in houses_r4:
        power_kw = house["power_kw"]
        voltage = house["voltage"]
        current = power_kw / (voltage / 1000)
        send_telemetry(house["house_id"], voltage, current, power_kw, house["phase"])
    
    print("\nPhase loads: L1=0.90, L2=2.00, L3=0.85 kW (Imbalance: 1.15 kW)")
    
    print("\n" + "="*60)
    print("✅ Gradual load increase test completed!")
    print("="*60)
    print("\nExpected behavior:")
    print("  - Round 1: No switching (balanced)")
    print("  - Round 2: Possible switch if above threshold")
    print("  - Round 3: Should trigger switching (critical imbalance)")
    print("  - Round 4: System should continue balancing")
    print("\nCheck dashboard: http://localhost:5500/dashboard.html")
    print("Review switch history to see system's response to gradual changes\n")
