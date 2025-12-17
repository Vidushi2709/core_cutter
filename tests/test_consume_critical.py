"""
Test Case: Critical Imbalance
Tests system response to severe overload on one phase
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
    print("TEST CASE: Critical Imbalance - Severe Overload")
    print("="*60)
    print("\nMake sure your FastAPI server is running: python app.py\n")
    
    # Critical imbalance - one phase heavily overloaded
    houses = [
        # Phase L1 - Very light load
        {"house_id": "B1", "power_kw": 0.20, "voltage": 230.0, "phase": "L1"},
        
        # Phase L2 - CRITICAL OVERLOAD
        {"house_id": "H1", "power_kw": 1.80, "voltage": 230.0, "phase": "L2"},
        {"house_id": "H2", "power_kw": 1.50, "voltage": 230.0, "phase": "L2"},
        {"house_id": "H3", "power_kw": 1.20, "voltage": 230.0, "phase": "L2"},
        {"house_id": "V1", "power_kw": 0.90, "voltage": 230.0, "phase": "L2"},
        
        # Phase L3 - Light load
        {"house_id": "B2", "power_kw": 0.30, "voltage": 230.0, "phase": "L3"},
        {"house_id": "V2", "power_kw": 0.25, "voltage": 230.0, "phase": "L3"},
    ]
    
    print("📤 Sending critical imbalance data...\n")
    
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
    print("\nPhase loads:")
    print("  L1: 0.20 kW")
    print("  L2: 1.80 + 1.50 + 1.20 + 0.90 = 5.40 kW ⚠️⚠️⚠️ CRITICAL!")
    print("  L3: 0.30 + 0.25 = 0.55 kW")
    print("\nImbalance: 5.40 - 0.20 = 5.20 kW (CRITICAL - well above 0.6 kW!)")
    print("\nExpected: System should aggressively switch multiple houses from L2")
    print("Check dashboard: http://localhost:5500/dashboard.html\n")
