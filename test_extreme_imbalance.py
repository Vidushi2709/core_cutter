"""
Extreme Imbalance Test - Stress Test for Phase Balancing Algorithm
Creates severe imbalance scenarios to thoroughly test the balancing logic.
"""
import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_separator(title=""):
    print("\n" + "="*70)
    if title:
        print(f"{title:^70}")
        print("="*70)

def send_phase_node_telemetry(L1, L2, L3):
    """Send aggregated phase totals from master node."""
    url = f"{BASE_URL}/telemetry/phases"
    data = {"L1_kw": L1, "L2_kw": L2, "L3_kw": L3}
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        print(f"📡 PHASE NODE: L1={L1:.1f}kW | L2={L2:.1f}kW | L3={L3:.1f}kW | Imb={result.get('imbalance_kw', 0):.1f}kW | Source={result.get('source', 'unknown')}")
        return result
    except Exception as e:
        print(f"✗ Error sending phase node telemetry: {e}")
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
        assigned_phase = result.get('new_phase', phase)
        marker = "🔄" if assigned_phase != phase else "  "
        print(f"{marker} {house_id:12} [{phase}→{assigned_phase}]: {power_kw:5.2f} kW")
        return result
    except Exception as e:
        print(f"✗ Error sending {house_id}: {e}")
        return None

def get_system_status():
    """Get current system status."""
    url = f"{BASE_URL}/analytics/status"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def display_status(status, title=""):
    """Display current system status."""
    if not status:
        return
    
    if title:
        print(f"\n{title}")
    
    phases_list = status.get('phases', [])
    phase_dict = {p['phase']: p for p in phases_list}
    
    print(f"Mode: {status.get('mode', 'unknown')}")
    print(f"Imbalance: {status.get('imbalance_kw', 0):.2f} kW")
    
    print("\nPhase Distribution:")
    for phase_name in ['L1', 'L2', 'L3']:
        p = phase_dict.get(phase_name, {})
        total_kw = p.get('total_power_kw', 0)
        house_count = p.get('house_count', 0)
        bar = "█" * int(total_kw)
        print(f"  {phase_name}: {total_kw:6.2f} kW ({house_count:2} houses) {bar}")

def get_switch_history():
    """Get recent switches."""
    url = f"{BASE_URL}/analytics/switches?limit=10"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return []

def display_switches(switches):
    """Display recent switches."""
    if not switches or not isinstance(switches, list) or len(switches) == 0:
        print("\n🔄 No switches made yet")
        return
    
    print(f"\n🔄 SWITCHES MADE ({len(switches)}):")
    for i, sw in enumerate(switches[:10], 1):
        house_id = sw.get('house_id', 'unknown')
        from_phase = sw.get('from_phase', '?')
        to_phase = sw.get('to_phase', '?')
        reason = sw.get('reason', 'Balance')
        print(f"  {i:2}. {house_id:12} {from_phase} → {to_phase:2} ({reason})")

def main():
    print_separator("EXTREME IMBALANCE TEST - STRESS TEST")
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
    
    # Check server
    try:
        requests.get(f"{BASE_URL}/analytics/status", timeout=2)
    except:
        print("\n❌ ERROR: Server not running!")
        print("Start server: python app.py")
        return
    
    # ========================================
    # SCENARIO 1: SEVERE OVERLOAD ON L1
    # ========================================
    print_separator("SCENARIO 1: Severe L1 Overload")
    print("Sending initial phase node data...")
    send_phase_node_telemetry(L1=15.5, L2=1.0, L3=1.0)
    time.sleep(1)
    
    print("\nLoading L1 with 8 heavy houses...")
    
    # Heavy houses on L1 (total ~15kW)
    send_house_telemetry("HEAVY_01", 230, 10.0, 2.3, "L1")
    send_house_telemetry("HEAVY_02", 230, 9.5, 2.2, "L1")
    send_house_telemetry("HEAVY_03", 230, 9.0, 2.1, "L1")
    send_house_telemetry("HEAVY_04", 230, 8.5, 2.0, "L1")
    send_house_telemetry("HEAVY_05", 230, 8.0, 1.9, "L1")
    send_house_telemetry("HEAVY_06", 230, 7.5, 1.8, "L1")
    send_house_telemetry("HEAVY_07", 230, 7.0, 1.7, "L1")
    send_house_telemetry("HEAVY_08", 230, 6.5, 1.5, "L1")
    
    # Light houses on L2 and L3 (total ~1kW each)
    send_house_telemetry("LIGHT_01", 230, 2.0, 0.5, "L2")
    send_house_telemetry("LIGHT_02", 230, 2.0, 0.5, "L2")
    send_house_telemetry("LIGHT_03", 230, 2.0, 0.5, "L3")
    send_house_telemetry("LIGHT_04", 230, 2.0, 0.5, "L3")
    
    time.sleep(2)
    status = get_system_status()
    display_status(status, "📊 STATUS AFTER INITIAL LOAD:")
    display_switches(get_switch_history())
    
    # ========================================
    # SCENARIO 2: ADD MEDIUM HOUSES TO TRIGGER MORE BALANCING
    # ========================================
    print_separator("SCENARIO 2: Adding Medium Houses")
    print("Adding medium-power houses to force rebalancing...")
    
    send_house_telemetry("MEDIUM_01", 230, 5.0, 1.2, "L1")
    send_house_telemetry("MEDIUM_02", 230, 5.0, 1.2, "L1")
    send_house_telemetry("MEDIUM_03", 230, 5.0, 1.2, "L1")
    send_house_telemetry("MEDIUM_04", 230, 4.5, 1.0, "L2")
    send_house_telemetry("MEDIUM_05", 230, 4.5, 1.0, "L3")
    
    time.sleep(2)
    status = get_system_status()
    display_status(status, "📊 STATUS AFTER ADDING MEDIUM HOUSES:")
    display_switches(get_switch_history())
    
    # ========================================
    # SCENARIO 3: GRADUAL LOAD INCREASE
    # ========================================
    print_separator("SCENARIO 3: Gradual Load Increase")
    print("Sending updated phase node data (gradual increase)...")
    send_phase_node_telemetry(L1=12.0, L2=8.0, L3=9.0)
    time.sleep(1)
    
    print("\nGradually increasing loads on all houses...")
    
    # Increase all heavy houses by 50%
    send_house_telemetry("HEAVY_01", 230, 15.0, 3.5, "L1")
    time.sleep(0.5)
    send_house_telemetry("HEAVY_02", 230, 14.0, 3.3, "L1")
    time.sleep(0.5)
    send_house_telemetry("HEAVY_03", 230, 13.0, 3.1, "L1")
    time.sleep(0.5)
    send_house_telemetry("HEAVY_04", 230, 12.0, 2.8, "L1")
    time.sleep(0.5)
    send_house_telemetry("HEAVY_05", 230, 11.0, 2.6, "L1")
    time.sleep(0.5)
    
    status = get_system_status()
    display_status(status, "📊 STATUS AFTER LOAD INCREASE:")
    display_switches(get_switch_history())
    
    # ========================================
    # SCENARIO 4: ADD VARIABLE LOADS
    # ========================================
    print_separator("SCENARIO 4: Variable Load Pattern")
    print("Adding houses with varying consumption patterns...")
    
    send_house_telemetry("VARIABLE_01", 230, 10.0, 2.5, "L1")
    send_house_telemetry("VARIABLE_02", 230, 3.0, 0.7, "L2")
    send_house_telemetry("VARIABLE_03", 230, 8.0, 1.9, "L1")
    send_house_telemetry("VARIABLE_04", 230, 4.0, 0.9, "L3")
    send_house_telemetry("VARIABLE_05", 230, 6.0, 1.4, "L2")
    send_house_telemetry("VARIABLE_06", 230, 9.0, 2.1, "L1")
    send_house_telemetry("VARIABLE_07", 230, 2.5, 0.6, "L3")
    send_house_telemetry("VARIABLE_08", 230, 7.0, 1.6, "L2")
    
    time.sleep(2)
    status = get_system_status()
    display_status(status, "📊 STATUS AFTER VARIABLE LOADS:")
    display_switches(get_switch_history())
    
    # ========================================
    # SCENARIO 5: MASSIVE SPIKE ON ONE PHASE
    # ========================================
    print_separator("SCENARIO 5: Massive Spike Test")
    print("Sending phase node data with massive L2 spike...")
    send_phase_node_telemetry(L1=13.0, L2=28.0, L3=13.0)
    time.sleep(1)
    
    print("\nCreating extreme spike on L2...")
    
    send_house_telemetry("SPIKE_01", 230, 18.0, 4.2, "L2")
    send_house_telemetry("SPIKE_02", 230, 17.0, 4.0, "L2")
    send_house_telemetry("SPIKE_03", 230, 16.0, 3.8, "L2")
    send_house_telemetry("SPIKE_04", 230, 15.0, 3.5, "L2")
    
    time.sleep(2)
    status = get_system_status()
    display_status(status, "📊 STATUS AFTER MASSIVE SPIKE:")
    display_switches(get_switch_history())
    
    # ========================================
    # SCENARIO 6: MIXED EXPORT/IMPORT
    # ========================================
    print_separator("SCENARIO 6: Mixed Export/Import")
    print("Sending phase node data with solar export...")
    send_phase_node_telemetry(L1=16.5, L2=15.5, L3=14.7)
    time.sleep(1)
    
    print("\nAdding solar export houses (negative power)...")
    
    send_house_telemetry("SOLAR_01", 230, -8.0, -1.8, "L1")
    send_house_telemetry("SOLAR_02", 230, -7.0, -1.6, "L2")
    send_house_telemetry("SOLAR_03", 230, -6.0, -1.4, "L3")
    
    time.sleep(2)
    status = get_system_status()
    display_status(status, "📊 STATUS WITH SOLAR EXPORT:")
    display_switches(get_switch_history())
    
    # ========================================
    # SCENARIO 7: MONITORING PERIOD
    # ========================================
    print_separator("SCENARIO 7: Continuous Monitoring")
    print("Monitoring system for 20 seconds...")
    
    for i in range(4):
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
            
            l1_cnt = phase_dict.get('L1', {}).get('house_count', 0)
            l2_cnt = phase_dict.get('L2', {}).get('house_count', 0)
            l3_cnt = phase_dict.get('L3', {}).get('house_count', 0)
            
            print(f"[{(i+1)*5:2}s] L1:{l1_kw:5.1f}kW({l1_cnt:2}h) | "
                  f"L2:{l2_kw:5.1f}kW({l2_cnt:2}h) | "
                  f"L3:{l3_kw:5.1f}kW({l3_cnt:2}h) | "
                  f"Imb:{imbalance:5.1f}kW | {mode}")
    
    # ========================================
    # FINAL SUMMARY
    # ========================================
    print_separator("FINAL SUMMARY")
    
    status = get_system_status()
    if status:
        phases_list = status.get('phases', [])
        phase_dict = {p['phase']: p for p in phases_list}
        total_houses = sum(p.get('house_count', 0) for p in phases_list)
        
        print(f"\n📊 FINAL STATE:")
        print(f"Total Houses: {total_houses}")
        print(f"Mode: {status.get('mode', 'unknown')}")
        print(f"Final Imbalance: {status.get('imbalance_kw', 0):.2f} kW")
        
        print(f"\nPhase Distribution:")
        for phase_name in ['L1', 'L2', 'L3']:
            p = phase_dict.get(phase_name, {})
            total_kw = p.get('total_power_kw', 0)
            house_count = p.get('house_count', 0)
            avg_per_house = total_kw / house_count if house_count > 0 else 0
            bar = "█" * int(total_kw)
            print(f"  {phase_name}: {total_kw:6.2f} kW | {house_count:2} houses | Avg: {avg_per_house:.2f} kW/house")
            print(f"      {bar}")
    
    switches = get_switch_history()
    display_switches(switches)
    
    if switches and isinstance(switches, list) and status:
        print(f"\n✅ Algorithm made {len(switches)} phase switches")
        
        # Calculate initial vs final imbalance improvement
        print(f"\n📈 PERFORMANCE METRICS:")
        print(f"Total Switches: {len(switches)}")
        print(f"Final Imbalance: {status.get('imbalance_kw', 0):.2f} kW")
        
        print(f"\nPhase Distribution:")
        for phase_name in ['L1', 'L2', 'L3']:
            p = phase_dict.get(phase_name, {})
            total_kw = p.get('total_power_kw', 0)
            house_count = p.get('house_count', 0)
            avg_per_house = total_kw / house_count if house_count > 0 else 0
            bar = "█" * int(total_kw)
            print(f"  {phase_name}: {total_kw:6.2f} kW | {house_count:2} houses | Avg: {avg_per_house:.2f} kW/house")
            print(f"      {bar}")
    
    switches = get_switch_history()
    display_switches(switches)
    
    if switches and isinstance(switches, list) and status:
        print(f"\n✅ Algorithm made {len(switches)} phase switches")
        
        # Calculate initial vs final imbalance improvement
        print(f"\n📈 PERFORMANCE METRICS:")
        print(f"Total Switches: {len(switches)}")
        print(f"Final Imbalance: {status.get('imbalance_kw', 0):.2f} kW")
        
        # Count switches per house
        house_switch_count = {}
        for sw in switches:
            house_id = sw.get('house_id', '')
            house_switch_count[house_id] = house_switch_count.get(house_id, 0) + 1
        
        most_switched = max(house_switch_count.items(), key=lambda x: x[1]) if house_switch_count else (None, 0)
        if most_switched[0]:
            print(f"Most Switched House: {most_switched[0]} ({most_switched[1]} times)")
    
    print(f"\n✓ Test completed at {datetime.now().strftime('%H:%M:%S')}")
    print(f"Dashboard: http://localhost:8000/dashboard.html")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
