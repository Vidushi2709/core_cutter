"""
Complete System Test - Phase Node + House Telemetry + Algorithm
Tests the full workflow with both phase node data and individual house readings.
"""
import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_separator(title=""):
    print("\n" + "="*60)
    if title:
        print(f"{title:^60}")
        print("="*60)

def send_phase_node_telemetry(L1, L2, L3):
    """Send aggregated phase totals from master node."""
    url = f"{BASE_URL}/telemetry/phases"
    data = {"L1_kw": L1, "L2_kw": L2, "L3_kw": L3}
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        print(f"✓ Phase Node Telemetry Sent:")
        print(f"  L1: {L1:.2f} kW | L2: {L2:.2f} kW | L3: {L3:.2f} kW")
        print(f"  Imbalance: {result.get('imbalance_kw', 0):.2f} kW | Source: {result.get('source', 'unknown')}")
        return result
    except Exception as e:
        print(f"✗ Error sending phase telemetry: {e}")
        return None

def send_house_telemetry(house_id, voltage, current, power_kw, phase):
    """Send individual house telemetry."""
    url = f"{BASE_URL}/telemetry"
    data = {
        "house_id": house_id,
        "voltage": voltage,
        "current": current,
        "power_kw": power_kw,
        "phase": phase
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        print(f"✓ {house_id} [{phase}]: {power_kw:.3f} kW")
        return result
    except Exception as e:
        print(f"✗ Error sending {house_id}: {e}")
        return None

def get_system_status():
    """Get current system status with phase stats."""
    url = f"{BASE_URL}/analytics/status"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"✗ Error getting status: {e}")
        return None

def get_switch_history(limit=5):
    """Get recent phase switches."""
    url = f"{BASE_URL}/analytics/switches?limit={limit}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"✗ Error getting switches: {e}")
        return None

def display_status(status):
    """Display current system status."""
    if not status:
        return
    
    print("\n📊 SYSTEM STATUS:")
    print(f"Mode: {status.get('mode', 'unknown').upper()}")
    
    phases_list = status.get('phases', [])
    phase_dict = {p['phase']: p for p in phases_list}
    
    total_houses = sum(p.get('house_count', 0) for p in phases_list)
    print(f"Total Houses: {total_houses}")
    
    print(f"\nPhase Distribution:")
    for phase_name in ['L1', 'L2', 'L3']:
        p = phase_dict.get(phase_name, {})
        total_kw = p.get('total_power_kw', 0)
        house_count = p.get('house_count', 0)
        print(f"  {phase_name}: {total_kw:6.2f} kW ({house_count} houses)")
    
    print(f"\nImbalance: {status.get('imbalance_kw', 0):.2f} kW")

def display_switches(switches):
    """Display recent phase switches."""
    if not switches or not isinstance(switches, list) or len(switches) == 0:
        print("\n🔄 No phase switches yet")
        return
    
    print(f"\n🔄 RECENT SWITCHES ({len(switches)}):")
    for sw in switches[:5]:
        timestamp = sw.get('timestamp', 'unknown')
        house_id = sw.get('house_id', 'unknown')
        from_phase = sw.get('from_phase', '?')
        to_phase = sw.get('to_phase', '?')
        reason = sw.get('reason', '')
        print(f"  [{timestamp}] {house_id}: {from_phase} → {to_phase}")
        if reason:
            print(f"    Reason: {reason}")

def main():
    print_separator("COMPLETE SYSTEM TEST")
    print("Testing: Phase Node Telemetry + House Telemetry + Algorithm")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/analytics/status", timeout=2)
    except:
        print("\n❌ ERROR: Server not running!")
        print("Start the server first: python app.py")
        return
    
    # ========================================
    # STEP 1: Send Phase Node Telemetry
    # ========================================
    print_separator("STEP 1: Master Node Telemetry")
    print("Sending aggregated phase totals from master node...")
    send_phase_node_telemetry(L1=5.2, L2=1.8, L3=3.1)
    time.sleep(1)
    
    status = get_system_status()
    display_status(status)
    
    # ========================================
    # STEP 2: Send Individual House Telemetry
    # ========================================
    print_separator("STEP 2: House Telemetry")
    print("Sending individual house readings...")
    
    # Houses on L1 (heavily loaded)
    send_house_telemetry("HOUSE_001", 230, 8.7, 2.0, "L1")
    send_house_telemetry("HOUSE_002", 230, 6.5, 1.5, "L1")
    send_house_telemetry("HOUSE_003", 230, 4.3, 1.0, "L1")
    
    # Houses on L2 (lightly loaded)
    send_house_telemetry("HOUSE_004", 230, 2.2, 0.5, "L2")
    send_house_telemetry("HOUSE_005", 230, 2.6, 0.6, "L2")
    
    # Houses on L3 (medium loaded)
    send_house_telemetry("HOUSE_006", 230, 5.2, 1.2, "L3")
    send_house_telemetry("HOUSE_007", 230, 4.3, 1.0, "L3")
    
    time.sleep(1)
    
    # ========================================
    # STEP 3: Check Status (Should Use House Data Now)
    # ========================================
    print_separator("STEP 3: Status After House Data")
    print("Waiting for phase node data to expire (10 seconds)...")
    time.sleep(10)
    
    status = get_system_status()
    display_status(status)
    switches = get_switch_history()
    display_switches(switches)
    
    # ========================================
    # STEP 4: Send More House Data (Trigger Algorithm)
    # ========================================
    print_separator("STEP 4: Trigger Balancing Algorithm")
    print("Adding more houses to create imbalance...")
    
    # Add more heavy load to L1
    send_house_telemetry("HOUSE_008", 230, 8.7, 2.0, "L1")
    send_house_telemetry("HOUSE_009", 230, 7.8, 1.8, "L1")
    
    time.sleep(2)
    
    status = get_system_status()
    display_status(status)
    switches = get_switch_history()
    display_switches(switches)
    
    # ========================================
    # STEP 5: Send Fresh Phase Node Data
    # ========================================
    print_separator("STEP 5: Fresh Master Node Data")
    print("Sending new phase node telemetry (should override house summation)...")
    send_phase_node_telemetry(L1=3.5, L2=3.2, L3=3.0)
    
    time.sleep(1)
    
    status = get_system_status()
    display_status(status)
    
    # ========================================
    # STEP 6: Monitor for 30 seconds
    # ========================================
    print_separator("STEP 6: Real-time Monitoring")
    print("Monitoring system for 30 seconds...")
    print("Watch the dashboard: http://localhost:8000/dashboard.html")
    
    for i in range(6):
        time.sleep(5)
        status = get_system_status()
        if status:
            phases_list = status.get('phases', [])
            phase_dict = {p['phase']: p for p in phases_list}
            imbalance = status.get('imbalance_kw', 0)
            mode = status.get('mode', 'unknown')
            
            l1_kw = phase_dict.get('L1', {}).get('total_power_kw', 0)
            l2_kw = phase_dict.get('L2', {}).get('total_power_kw', 0)
            l3_kw = phase_dict.get('L3', {}).get('total_power_kw', 0)
            
            print(f"[{i*5+5}s] L1:{l1_kw:.1f} | "
                  f"L2:{l2_kw:.1f} | "
                  f"L3:{l3_kw:.1f} | "
                  f"Imb:{imbalance:.1f}kW | Mode:{mode}")
    
    # ========================================
    # FINAL SUMMARY
    # ========================================
    print_separator("TEST COMPLETE")
    switches = get_switch_history()
    display_switches(switches)
    
    print(f"\n✓ Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Check dashboard: http://localhost:8000/dashboard.html")
    print(f"View data files: data/houses.json, data/phase_telemetry.json")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
