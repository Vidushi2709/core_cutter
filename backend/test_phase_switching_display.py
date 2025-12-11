#!/usr/bin/env python3
"""
Test script to verify phase switching is correctly reflected in the frontend dashboard.
This script:
1. Sends telemetry data that creates an imbalance
2. Checks if phase switching occurs in the backend
3. Verifies the frontend API returns correct data
4. Validates that house phases are updated properly
"""

import requests
import json
import time
from datetime import datetime

API_URL = "http://localhost:8000"

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def send_telemetry(house_id, voltage, current, power_kw, phase):
    """Send telemetry data to the backend"""
    data = {
        "house_id": house_id,
        "voltage": voltage,
        "current": current,
        "power_kw": power_kw,
        "phase": phase
    }
    response = requests.post(f"{API_URL}/telemetry", json=data)
    return response.json()

def get_system_status():
    """Get current system status"""
    response = requests.get(f"{API_URL}/analytics/status")
    return response.json()

def get_switch_history(limit=5):
    """Get switch history"""
    response = requests.get(f"{API_URL}/analytics/switches", params={"limit": limit})
    return response.json()

def print_phase_distribution(status):
    """Print current phase distribution"""
    print("Current Phase Distribution:")
    print("-" * 70)
    for phase in status["phases"]:
        print(f"  Phase {phase['phase']}: {phase['total_power_kw']:.2f} kW "
              f"({phase['house_count']} houses, Avg Voltage: {phase['avg_voltage']:.1f}V)")
    print(f"\n  System Mode: {status['mode']}")
    print(f"  Imbalance: {status['imbalance_kw']:.2f} kW")
    print("-" * 70)

def print_house_locations(status):
    """Print which houses are on which phases"""
    print("\nHouse Locations:")
    print("-" * 70)
    for phase in status["phases"]:
        houses = [h["house_id"] for h in phase["houses"]]
        if houses:
            print(f"  {phase['phase']}: {', '.join(houses)}")
    print("-" * 70)

def print_recent_switches(switches):
    """Print recent switch events"""
    print("\nRecent Phase Switches:")
    print("-" * 70)
    if switches["count"] == 0:
        print("  No switches recorded yet")
    else:
        for switch in switches["switches"][:5]:
            timestamp = datetime.fromisoformat(switch["timestamp"]).strftime("%H:%M:%S")
            print(f"  [{timestamp}] {switch['house_id']}: {switch['from_phase']} → {switch['to_phase']}")
            print(f"             Reason: {switch['reason']}")
    print("-" * 70)

def main():
    print_header("Phase Switching Frontend Display Test")
    
    # Step 1: Get initial state
    print_header("Step 1: Initial State")
    initial_status = get_system_status()
    print_phase_distribution(initial_status)
    print_house_locations(initial_status)
    
    initial_switches = get_switch_history(10)
    print_recent_switches(initial_switches)
    
    # Step 2: Create intentional imbalance
    print_header("Step 2: Creating Imbalance (Loading L1 heavily)")
    
    print("Sending telemetry for 5 houses on L1 with high consumption...")
    for i in range(1, 6):
        result = send_telemetry(
            house_id=f"TestHouse_{i}",
            voltage=240.0,
            current=20.0,  # High current
            power_kw=4.5,  # High consumption
            phase="L1"
        )
        print(f"  ✓ TestHouse_{i} registered on phase: {result['new_phase']}")
        time.sleep(0.3)
    
    print("\nSending telemetry for 2 houses on L2 with low consumption...")
    for i in range(6, 8):
        result = send_telemetry(
            house_id=f"TestHouse_{i}",
            voltage=238.0,
            current=5.0,  # Low current
            power_kw=1.0,  # Low consumption
            phase="L2"
        )
        print(f"  ✓ TestHouse_{i} registered on phase: {result['new_phase']}")
        time.sleep(0.3)
    
    print("\nSending telemetry for 1 house on L3 with low consumption...")
    result = send_telemetry(
        house_id="TestHouse_8",
        voltage=239.0,
        current=4.0,
        power_kw=0.8,
        phase="L3"
    )
    print(f"  ✓ TestHouse_8 registered on phase: {result['new_phase']}")
    
    # Step 3: Check if balancing occurred
    print_header("Step 3: Checking System After Imbalance")
    time.sleep(1)  # Give system time to process
    
    after_status = get_system_status()
    print_phase_distribution(after_status)
    print_house_locations(after_status)
    
    # Step 4: Check switch history
    print_header("Step 4: Verifying Switch History")
    after_switches = get_switch_history(15)
    print_recent_switches(after_switches)
    
    # Step 5: Verify specific houses moved
    print_header("Step 5: Verification Summary")
    
    # Check if any TestHouse moved from L1
    moved_houses = []
    for switch in after_switches["switches"]:
        if switch["house_id"].startswith("TestHouse_") and switch["from_phase"] == "L1":
            moved_houses.append(switch["house_id"])
    
    if moved_houses:
        print(f"✅ SUCCESS: Phase switching occurred!")
        print(f"   Houses moved from L1: {', '.join(moved_houses)}")
    else:
        print(f"⚠️  WARNING: No TestHouse switches detected from L1")
        print(f"   This might indicate the imbalance wasn't severe enough")
    
    # Verify frontend data integrity
    print("\n" + "="*70)
    print("Frontend Data Integrity Check:")
    print("="*70)
    
    all_houses_in_status = []
    for phase in after_status["phases"]:
        for house in phase["houses"]:
            all_houses_in_status.append((house["house_id"], house["phase"]))
    
    # Check if all TestHouses are tracked correctly
    test_houses = [h for h in all_houses_in_status if h[0].startswith("TestHouse_")]
    print(f"  Total TestHouses tracked: {len(test_houses)}")
    
    phase_counts = {"L1": 0, "L2": 0, "L3": 0}
    for house_id, phase in test_houses:
        phase_counts[phase] += 1
        print(f"    {house_id}: Phase {phase}")
    
    print(f"\n  Phase distribution of TestHouses:")
    print(f"    L1: {phase_counts['L1']} houses ({phase_counts['L1']/len(test_houses)*100:.1f}%)")
    print(f"    L2: {phase_counts['L2']} houses ({phase_counts['L2']/len(test_houses)*100:.1f}%)")
    print(f"    L3: {phase_counts['L3']} houses ({phase_counts['L3']/len(test_houses)*100:.1f}%)")
    
    if phase_counts["L1"] < 5:
        print(f"\n✅ SUCCESS: Houses were moved away from L1 (originally had 5, now has {phase_counts['L1']})")
    else:
        print(f"\n⚠️  WARNING: All houses still on L1 (system may not have triggered balancing)")
    
    print("\n" + "="*70)
    print("CONCLUSION:")
    print("="*70)
    
    print("""
The test has completed. To verify on the frontend dashboard:

1. Open the dashboard in your browser (likely http://localhost:5173)
2. Check the "Phase Distribution" cards - they should show:
   - Different power levels across phases
   - Updated house counts per phase
   
3. Check the "Switch Activity" section - it should show:
   - Recent TestHouse_X switches
   - Timestamp of when switches occurred
   - Reason for each switch
   
4. Check individual house cards - they should show:
   - Current phase assignment (should match backend data above)
   - Power consumption values
   - Updated in real-time (refreshes every 3 seconds)

If you see the switches in this output but NOT on the frontend dashboard,
there may be an issue with:
- Frontend API polling (check browser console)
- Data rendering in React components
- WebSocket/refresh timing

Current system status shows:
  - Mode: {mode}
  - Imbalance: {imbalance:.2f} kW
  - Recent switches: {switch_count}
    """.format(
        mode=after_status["mode"],
        imbalance=after_status["imbalance_kw"],
        switch_count=after_switches["count"]
    ))

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend at http://localhost:8000")
        print("   Make sure the backend is running with: cd backend && ./venv/bin/python3 app.py")
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
