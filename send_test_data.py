"""
Send manual telemetry data to test the dashboard.
Run this script while your FastAPI server (app.py) is running.
"""
import requests
import time

API_BASE = "http://localhost:8000"

# Test scenarios
def scenario_balanced():
    """Scenario 1: Balanced system - houses evenly distributed"""
    houses = [
        {"house_id": "H1", "voltage": 230, "current": 5, "power_kw": 1.2, "phase": "L1"},
        {"house_id": "H2", "voltage": 230, "current": 4, "power_kw": 0.9, "phase": "L2"},
        {"house_id": "H3", "voltage": 230, "current": 6, "power_kw": 1.4, "phase": "L3"},
        {"house_id": "B1", "voltage": 230, "current": 2, "power_kw": 0.5, "phase": "L1"},
        {"house_id": "B2", "voltage": 230, "current": 3, "power_kw": 0.7, "phase": "L2"},
        {"house_id": "B3", "voltage": 230, "current": 2, "power_kw": 0.4, "phase": "L3"},
    ]
    return houses

def scenario_imbalanced():
    """Scenario 2: All houses on L1 - critical imbalance"""
    houses = [
        {"house_id": "H1", "voltage": 230, "current": 8, "power_kw": 1.8, "phase": "L1"},
        {"house_id": "H2", "voltage": 230, "current": 5, "power_kw": 1.0, "phase": "L1"},
        {"house_id": "H3", "voltage": 230, "current": 6, "power_kw": 1.2, "phase": "L1"},
        {"house_id": "B1", "voltage": 230, "current": 2, "power_kw": 0.4, "phase": "L1"},
        {"house_id": "B2", "voltage": 230, "current": 12, "power_kw": 2.4, "phase": "L1"},
        {"house_id": "V1", "voltage": 230, "current": 3, "power_kw": 0.7, "phase": "L1"},
        {"house_id": "V2", "voltage": 230, "current": 1, "power_kw": 0.2, "phase": "L1"},
    ]
    return houses

def scenario_export_mode():
    """Scenario 3: Export mode - houses with solar panels exporting"""
    houses = [
        {"house_id": "H1", "voltage": 235, "current": -5, "power_kw": -1.2, "phase": "L1"},  # Exporting
        {"house_id": "H2", "voltage": 235, "current": -3, "power_kw": -0.7, "phase": "L2"},  # Exporting
        {"house_id": "B1", "voltage": 230, "current": 2, "power_kw": 0.5, "phase": "L1"},    # Consuming
        {"house_id": "B2", "voltage": 230, "current": 1, "power_kw": 0.2, "phase": "L3"},    # Consuming
        {"house_id": "V1", "voltage": 235, "current": -2, "power_kw": -0.5, "phase": "L1"},  # Exporting
    ]
    return houses

def scenario_voltage_issues():
    """Scenario 4: Voltage problems - over/under voltage"""
    houses = [
        {"house_id": "H1", "voltage": 260, "current": 8, "power_kw": 2.0, "phase": "L1"},   # Over voltage!
        {"house_id": "H2", "voltage": 190, "current": 5, "power_kw": 0.9, "phase": "L2"},   # Under voltage!
        {"house_id": "H3", "voltage": 230, "current": 6, "power_kw": 1.4, "phase": "L3"},   # Normal
        {"house_id": "B1", "voltage": 265, "current": 2, "power_kw": 0.5, "phase": "L1"},   # Over voltage!
    ]
    return houses

def scenario_internal_conflict():
    """Scenario 5: Internal conflict - export and import on same phase"""
    houses = [
        {"house_id": "H1", "voltage": 235, "current": -6, "power_kw": -1.4, "phase": "L1"},  # Exporting
        {"house_id": "B1", "voltage": 230, "current": 5, "power_kw": 1.2, "phase": "L1"},    # Importing - CONFLICT!
        {"house_id": "H2", "voltage": 235, "current": -3, "power_kw": -0.7, "phase": "L2"},  # Exporting
        {"house_id": "V1", "voltage": 230, "current": 2, "power_kw": 0.4, "phase": "L1"},    # Importing - CONFLICT!
    ]
    return houses

def send_telemetry(houses):
    """Send telemetry data for all houses"""
    print(f"\n{'='*60}")
    print(f"Sending telemetry for {len(houses)} houses...")
    print(f"{'='*60}")
    
    for house in houses:
        try:
            response = requests.post(f"{API_BASE}/telemetry", json=house)
            if response.status_code == 200:
                result = response.json()
                print(f"✓ {house['house_id']:4s} | Phase: {result['new_phase']} | {house['power_kw']:+6.2f} kW | {house['voltage']}V")
            else:
                print(f"✗ {house['house_id']:4s} | Error: {response.status_code}")
        except Exception as e:
            print(f"✗ {house['house_id']:4s} | Error: {e}")
        
        time.sleep(0.1)  # Small delay between requests
    
    print(f"\n✓ Data sent! Check dashboard at http://localhost:5500/dashboard.html")

def main():
    print("\n" + "="*60)
    print("PHASE BALANCING - MANUAL TEST DATA SENDER")
    print("="*60)
    print("\nMake sure your FastAPI server is running (python app.py)")
    print("\nAvailable scenarios:")
    print("  1. Balanced - Houses evenly distributed across phases")
    print("  2. Imbalanced - All houses on L1 (CRITICAL)")
    print("  3. Export Mode - Solar panels exporting to grid")
    print("  4. Voltage Issues - Over/under voltage alerts")
    print("  5. Internal Conflict - Mixed export/import on same phase")
    print("  6. All scenarios (run one by one)")
    
    choice = input("\nSelect scenario (1-6): ").strip()
    
    scenarios = {
        "1": ("Balanced System", scenario_balanced),
        "2": ("Critical Imbalance (All on L1)", scenario_imbalanced),
        "3": ("Export Mode (Solar)", scenario_export_mode),
        "4": ("Voltage Issues", scenario_voltage_issues),
        "5": ("Internal Conflict", scenario_internal_conflict),
    }
    
    if choice == "6":
        for num, (name, func) in scenarios.items():
            print(f"\n\n{'='*60}")
            print(f"SCENARIO {num}: {name}")
            send_telemetry(func())
            input("\nPress Enter to continue to next scenario...")
    elif choice in scenarios:
        name, func = scenarios[choice]
        print(f"\n\nSCENARIO {choice}: {name}")
        send_telemetry(func())
    else:
        print("Invalid choice!")
        return
    
    print("\n" + "="*60)
    print("Done! Open your dashboard to see the results.")
    print("Dashboard: http://localhost:5500/dashboard.html")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
