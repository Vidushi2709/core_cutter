"""
Test Case: Small Houses (Low Power)
Tests handling of very low power consumption (bulbs, small appliances)
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
    print("TEST CASE: Small Houses (Low Power Devices)")
    print("="*60)
    print("\nMake sure your FastAPI server is running: python app.py\n")
    
    # Small power devices - LED bulbs, chargers, etc.
    houses = [
        # Phase L1 - Light load
        {"house_id": "B1", "power_kw": 0.06, "voltage": 230.0, "phase": "L1"},  # 60W bulb
        {"house_id": "V1", "power_kw": 0.05, "voltage": 230.0, "phase": "L1"},  # 50W charger
        
        # Phase L2 - Imbalanced with small devices
        {"house_id": "H1", "power_kw": 0.17, "voltage": 230.0, "phase": "L2"},  # 170W appliance
        {"house_id": "H2", "power_kw": 0.15, "voltage": 230.0, "phase": "L2"},  # 150W appliance
        {"house_id": "H3", "power_kw": 0.12, "voltage": 230.0, "phase": "L2"},  # 120W appliance
        
        # Phase L3 - Light load
        {"house_id": "B2", "power_kw": 0.08, "voltage": 230.0, "phase": "L3"},  # 80W bulb
        {"house_id": "V2", "power_kw": 0.07, "voltage": 230.0, "phase": "L3"},  # 70W fan
    ]
    
    print("📤 Sending small house consumption data...\n")
    
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
    print("\nPhase loads (small devices):")
    print("  L1: 0.06 + 0.05 = 0.11 kW (110W)")
    print("  L2: 0.17 + 0.15 + 0.12 = 0.44 kW (440W)")
    print("  L3: 0.08 + 0.07 = 0.15 kW (150W)")
    print("\nImbalance: 0.44 - 0.11 = 0.33 kW (above 0.15 kW threshold)")
    print("\nExpected: System should switch 100W+ devices to balance")
    print("Note: Very small devices (<100W) might be skipped")
    print("Check dashboard: http://localhost:5500/dashboard.html\n")
