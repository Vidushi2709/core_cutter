"""
Test Case: Balanced Consumption
All phases equally loaded - system should NOT switch
"""
import requests

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
        print(f"✓ {house_id:4s} | Phase: {result['new_phase']} | {power_kw:+.2f} kW | {voltage:.0f}V | CONSUME")
        return result.get("new_phase", phase)
    except Exception as e:
        print(f"❌ Error sending data for {house_id}: {e}")
        return phase

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST CASE: Balanced Consumption")
    print("="*60)
    print("\nMake sure your FastAPI server is running: python app.py\n")
    
    # All phases equally loaded - should NOT trigger switching
    houses = [
        # Phase L1 - 1.0 kW total
        {"house_id": "B1", "power_kw": 0.60, "voltage": 230.0, "phase": "L1"},
        {"house_id": "V1", "power_kw": 0.40, "voltage": 230.0, "phase": "L1"},
        
        # Phase L2 - 1.0 kW total
        {"house_id": "H1", "power_kw": 0.50, "voltage": 230.0, "phase": "L2"},
        {"house_id": "H2", "power_kw": 0.50, "voltage": 230.0, "phase": "L2"},
        
        # Phase L3 - 1.0 kW total
        {"house_id": "B2", "power_kw": 0.70, "voltage": 230.0, "phase": "L3"},
        {"house_id": "V2", "power_kw": 0.30, "voltage": 230.0, "phase": "L3"},
    ]
    
    print("📤 Sending balanced consumption data...\n")
    
    for house in houses:
        power_kw = house["power_kw"]
        voltage = house["voltage"]
        current = power_kw / (voltage / 1000)
        
        send_telemetry(
            house["house_id"],
            voltage,
            current,
            power_kw,
            house["phase"]
        )
    
    print("\n" + "="*60)
    print("✅ Data sent successfully!")
    print("="*60)
    print("\nPhase loads (perfectly balanced):")
    print("  L1: 0.60 + 0.40 = 1.00 kW")
    print("  L2: 0.50 + 0.50 = 1.00 kW")
    print("  L3: 0.70 + 0.30 = 1.00 kW")
    print("\nImbalance: 1.00 - 1.00 = 0.00 kW ✅ BALANCED")
    print("\nExpected: NO switching should occur")
    print("Check dashboard: http://localhost:5500/dashboard.html\n")
