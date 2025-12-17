import requests
import time
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

def send_telemetry(house_id, phase, voltage, current, power_kw):
    """Send telemetry data for a house"""
    data = {
        "house_id": house_id,
        "phase": phase,
        "voltage": voltage,
        "current": current,
        "power_kw": power_kw,
        "timestamp": datetime.now().isoformat()
    }
    response = requests.post(f"{API_BASE}/telemetry", json=data)
    return response.json()

def get_status():
    """Get current system status"""
    response = requests.get(f"{API_BASE}/analytics/status")
    return response.json()

def print_status(status, scenario_name):
    """Print formatted status"""
    print(f"\n{'='*60}")
    print(f"SCENARIO: {scenario_name}")
    print(f"{'='*60}")
    print(f"System Mode: {status['mode']}")
    print(f"Imbalance: {status['imbalance_kw']:.3f} kW")
    print(f"\nPhase Distribution:")
    for phase in status['phases']:
        print(f"  {phase['phase']}: {phase['total_power_kw']:.3f} kW ({phase['house_count']} houses)")
    print(f"{'='*60}\n")

def test_export_scenario_1():
    """All houses exporting - balanced"""
    print("\n[TEST 1] All Houses Exporting - Balanced Distribution")
    
    # L1: 3 houses exporting
    send_telemetry("HOUSE_001", "L1", 238.0, 0.8, -0.19)
    send_telemetry("HOUSE_002", "L1", 239.0, 0.9, 0.21)
    send_telemetry("HOUSE_003", "L1", 237.5, 0.7, -0.17)
    
    # L2: 3 houses exporting
    send_telemetry("HOUSE_004", "L2", 238.5, 0.8, 0.19)
    send_telemetry("HOUSE_005", "L2", 239.2, 0.9, -0.21)
    send_telemetry("HOUSE_006", "L2", 237.0, 0.7, -0.16)
    
    # L3: 3 houses exporting
    send_telemetry("HOUSE_007", "L3", 238.8, 0.9, -0.21)
    send_telemetry("HOUSE_008", "L3", 237.3, 0.8, 0.19)
    send_telemetry("HOUSE_009", "L3", 239.5, 0.7, -0.17)
    
    time.sleep(2)
    status = get_status()
    print_status(status, "All Export - Balanced")
    return status

def test_export_scenario_2():
    """Mixed export and import - should trigger phase switching"""
    print("\n[TEST 2] Mixed Export/Import - High Imbalance")
    
    # L1: Heavy export
    send_telemetry("HOUSE_001", "L1", 238.0, 1.1, -0.26)
    send_telemetry("HOUSE_002", "L1", 239.0, 1.0, -0.24)
    send_telemetry("HOUSE_003", "L1", 237.5, 1.2, -0.29)
    
    # L2: Heavy consumption
    send_telemetry("HOUSE_004", "L2", 238.5, 1.0, 0.24)
    send_telemetry("HOUSE_005", "L2", 239.2, 1.1, 0.26)
    send_telemetry("HOUSE_006", "L2", 237.0, 0.9, 0.21)
    
    # L3: Light export
    send_telemetry("HOUSE_007", "L3", 238.8, 0.6, -0.14)
    send_telemetry("HOUSE_008", "L3", 237.3, 0.7, -0.16)
    
    time.sleep(2)
    status = get_status()
    print_status(status, "Mixed Export/Import - High Imbalance")
    return status

def test_export_scenario_3():
    """One phase with heavy export, others balanced"""
    print("\n[TEST 3] One Phase Heavy Export")
    
    # L1: Very heavy export
    send_telemetry("HOUSE_001", "L1", 238.0, 1.5, -0.36)
    send_telemetry("HOUSE_002", "L1", 239.0, 1.4, -0.34)
    send_telemetry("HOUSE_003", "L1", 237.5, 1.3, -0.31)
    send_telemetry("HOUSE_010", "L1", 238.2, 1.2, -0.29)
    
    # L2: Light export
    send_telemetry("HOUSE_004", "L2", 238.5, 0.6, -0.14)
    send_telemetry("HOUSE_005", "L2", 239.2, 0.7, -0.17)
    
    # L3: Light export
    send_telemetry("HOUSE_007", "L3", 238.8, 0.7, -0.17)
    send_telemetry("HOUSE_008", "L3", 237.3, 0.6, -0.14)
    
    time.sleep(2)
    status = get_status()
    print_status(status, "One Phase Heavy Export")
    return status

def test_export_scenario_4():
    """Export with voltage variations"""
    print("\n[TEST 4] Export with Voltage Variations")
    
    # L1: Normal voltage, moderate export
    send_telemetry("HOUSE_001", "L1", 238.0, 0.9, -0.21)
    send_telemetry("HOUSE_002", "L1", 239.0, 0.8, -0.19)
    
    # L2: High voltage, light export
    send_telemetry("HOUSE_004", "L2", 245.0, 0.6, -0.14)
    send_telemetry("HOUSE_005", "L2", 246.5, 0.7, -0.17)
    
    # L3: Normal voltage, heavy export
    send_telemetry("HOUSE_007", "L3", 238.8, 1.2, -0.29)
    send_telemetry("HOUSE_008", "L3", 237.3, 1.1, -0.26)
    send_telemetry("HOUSE_009", "L3", 239.5, 1.0, -0.24)
    
    time.sleep(2)
    status = get_status()
    print_status(status, "Export with Voltage Variations")
    return status

def test_export_scenario_5():
    """Progressive export increase over time"""
    print("\n[TEST 5] Progressive Export Increase")
    
    stages = [
        ("Initial - Light Export", 0.10),
        ("Stage 2 - Moderate Export", 0.20),
        ("Stage 3 - Heavy Export", 0.30),
        ("Stage 4 - Very Heavy Export", 0.40)
    ]
    
    for stage_name, power_multiplier in stages:
        print(f"\n--- {stage_name} ---")
        
        # Distribute houses across phases with increasing export
        send_telemetry("HOUSE_001", "L1", 238.0, 0.6, -0.14 * power_multiplier / 0.10)
        send_telemetry("HOUSE_002", "L1", 239.0, 0.7, -0.17 * power_multiplier / 0.10)
        
        send_telemetry("HOUSE_004", "L2", 238.5, 0.8, -0.19 * power_multiplier / 0.10)
        send_telemetry("HOUSE_005", "L2", 239.2, 0.9, -0.21 * power_multiplier / 0.10)
        
        send_telemetry("HOUSE_007", "L3", 238.8, 0.7, -0.17 * power_multiplier / 0.10)
        send_telemetry("HOUSE_008", "L3", 237.3, 0.8, -0.19 * power_multiplier / 0.10)
        
        time.sleep(2)
        status = get_status()
        print(f"Mode: {status['mode']}, Imbalance: {status['imbalance_kw']:.3f} kW")

def test_export_scenario_6():
    """Internal conflict - same phase with both export and import"""
    print("\n[TEST 6] Internal Conflict - Mixed Power Flow")
    
    # L1: Both exporting and consuming houses
    send_telemetry("HOUSE_001", "L1", 238.0, 1.0, -0.24)  # Exporting
    send_telemetry("HOUSE_002", "L1", 239.0, 0.9, -0.21)  # Exporting
    send_telemetry("HOUSE_003", "L1", 237.5, 1.1, 0.26)   # Consuming
    
    # L2: All consuming
    send_telemetry("HOUSE_004", "L2", 238.5, 0.8, 0.19)
    send_telemetry("HOUSE_005", "L2", 239.2, 0.9, 0.21)
    
    # L3: All exporting
    send_telemetry("HOUSE_007", "L3", 238.8, 1.0, -0.24)
    send_telemetry("HOUSE_008", "L3", 237.3, 0.9, -0.21)
    
    time.sleep(2)
    status = get_status()
    print_status(status, "Internal Conflict - Mixed Power Flow")
    return status

def run_all_tests():
    """Run all export test scenarios"""
    print("\n" + "="*60)
    print("EXPORT LOGIC TEST SUITE")
    print("Testing various export scenarios for phase balancing")
    print("="*60)
    
    try:
        # Check server connectivity
        response = requests.get(f"{API_BASE}/analytics/status")
        if response.status_code != 200:
            print("ERROR: Cannot connect to backend server")
            return
        
        test_export_scenario_1()
        time.sleep(3)
        
        test_export_scenario_2()
        time.sleep(3)
        
        test_export_scenario_3()
        time.sleep(3)
        
        test_export_scenario_4()
        time.sleep(3)
        
        test_export_scenario_5()
        time.sleep(3)
        
        test_export_scenario_6()
        
        print("\n" + "="*60)
        print("ALL EXPORT TESTS COMPLETED")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\nERROR: Cannot connect to backend server at", API_BASE)
        print("Please ensure the server is running with: python run_server.py")
    except Exception as e:
        print(f"\nERROR: {str(e)}")

if __name__ == "__main__":
    run_all_tests()
