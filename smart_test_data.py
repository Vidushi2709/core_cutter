"""
Smart Test Data Sender - Sends initial imbalanced data, waits for system to balance,
then sends updated telemetry based on actual phase assignments.
"""
import requests
import time
from datetime import datetime

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
        return result.get("new_phase", phase)
    except Exception as e:
        print(f"❌ Error sending data for {house_id}: {e}")
        return phase

def get_current_status():
    """Get current system status."""
    try:
        response = requests.get(f"{API_BASE}/analytics/status")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching status: {e}")
        return None

def print_status(status):
    """Print current system status."""
    if not status:
        return
    
    print(f"\n{'='*60}")
    print(f"System Status: {status['mode']} | Imbalance: {status['imbalance_kw']:.2f} kW")
    print(f"{'='*60}")
    for phase in status['phases']:
        print(f"  {phase['phase']}: {phase['total_power_kw']:+.2f} kW | {phase['house_count']} houses | {phase['avg_voltage']:.1f}V")
        for house in phase['houses']:
            badge = "🔌 CONSUME" if house['power_kw'] > 0 else "☀️ EXPORT"
            print(f"    - {house['house_id']}: {house['power_kw']:+.2f} kW {badge}")
    print(f"{'='*60}\n")

def scenario_internal_conflict_with_balancing():
    """Scenario: Internal conflict that gets balanced over time."""
    print("\n" + "="*60)
    print("SMART TEST: Internal Conflict with Auto-Balancing")
    print("="*60)
    
    # Define house power profiles (fixed values)
    houses = {
        "H1": {"power_kw": -1.40, "voltage": 235.0, "initial_phase": "L1"},  # Export
        "H2": {"power_kw": -0.70, "voltage": 235.0, "initial_phase": "L3"},  # Export
        "B1": {"power_kw": 1.20, "voltage": 230.0, "initial_phase": "L1"},   # Consume
        "B2": {"power_kw": 0.20, "voltage": 230.0, "initial_phase": "L3"},   # Consume
        "H3": {"power_kw": 1.40, "voltage": 230.0, "initial_phase": "L2"},   # Consume
        "V1": {"power_kw": 0.40, "voltage": 230.0, "initial_phase": "L1"},   # Consume
        "V2": {"power_kw": 0.20, "voltage": 230.0, "initial_phase": "L2"},   # Consume
    }
    
    # Track current phase assignments
    current_phases = {hid: data["initial_phase"] for hid, data in houses.items()}
    
    print("\n📤 Step 1: Sending INITIAL imbalanced data...")
    print("-" * 60)
    
    # Send initial data
    for house_id, data in houses.items():
        power_kw = data["power_kw"]
        voltage = data["voltage"]
        current = power_kw / (voltage / 1000)  # I = P / V
        phase = current_phases[house_id]
        
        badge = "EXPORT" if power_kw < 0 else "CONSUME"
        print(f"✓ {house_id:4s} | Phase: {phase} | {power_kw:+.2f} kW | {voltage:.0f}V | {badge}")
        
        new_phase = send_telemetry(house_id, voltage, current, power_kw, phase)
        current_phases[house_id] = new_phase
    
    # Show initial status
    print("\n📊 Initial System Status:")
    status = get_current_status()
    print_status(status)
    
    # Wait for system to process and balance
    print("⏳ Waiting 3 seconds for system to balance...")
    time.sleep(3)
    
    # Now send continuous updates based on CURRENT phase assignments
    print("\n🔄 Step 2: Sending CONTINUOUS telemetry with updated phase assignments...")
    print("-" * 60)
    print("(Press Ctrl+C to stop)\n")
    
    cycle = 0
    try:
        while True:
            cycle += 1
            print(f"\n📡 Cycle {cycle} - {datetime.now().strftime('%H:%M:%S')}")
            
            # Send telemetry for each house using CURRENT phase assignment
            for house_id, data in houses.items():
                power_kw = data["power_kw"]
                voltage = data["voltage"]
                current = power_kw / (voltage / 1000)
                phase = current_phases[house_id]
                
                new_phase = send_telemetry(house_id, voltage, current, power_kw, phase)
                
                if new_phase != phase:
                    print(f"  ⚡ {house_id} switched: {phase} → {new_phase}")
                    current_phases[house_id] = new_phase
            
            # Show current status every 5 cycles
            if cycle % 5 == 0:
                status = get_current_status()
                print_status(status)
            
            time.sleep(2)  # Wait 2 seconds between cycles
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
        print("\n📊 Final System Status:")
        status = get_current_status()
        print_status(status)

def scenario_simple_imbalance():
    """Simple imbalance scenario with periodic updates."""
    print("\n" + "="*60)
    print("SMART TEST: Simple Imbalance with Auto-Balancing")
    print("="*60)
    
    houses = {
        "B1": {"power_kw": 1.20, "voltage": 230.0, "initial_phase": "L1"},
        "B2": {"power_kw": 0.20, "voltage": 230.0, "initial_phase": "L3"},
        "H1": {"power_kw": -1.40, "voltage": 235.0, "initial_phase": "L1"},
        "H2": {"power_kw": -0.70, "voltage": 235.0, "initial_phase": "L3"},
        "H3": {"power_kw": 1.40, "voltage": 230.0, "initial_phase": "L2"},
        "V1": {"power_kw": 0.40, "voltage": 230.0, "initial_phase": "L1"},
        "V2": {"power_kw": 0.20, "voltage": 230.0, "initial_phase": "L2"},
    }
    
    current_phases = {hid: data["initial_phase"] for hid, data in houses.items()}
    
    print("\n📤 Sending initial data...")
    for house_id, data in houses.items():
        power_kw = data["power_kw"]
        voltage = data["voltage"]
        current = power_kw / (voltage / 1000)
        phase = current_phases[house_id]
        
        new_phase = send_telemetry(house_id, voltage, current, power_kw, phase)
        current_phases[house_id] = new_phase
        print(f"✓ {house_id}: {power_kw:+.2f} kW on {new_phase}")
    
    status = get_current_status()
    print_status(status)
    
    print("⏳ Waiting for system to balance...")
    time.sleep(3)
    
    print("\n🔄 Sending continuous updates (Press Ctrl+C to stop)...")
    cycle = 0
    try:
        while True:
            cycle += 1
            for house_id, data in houses.items():
                power_kw = data["power_kw"]
                voltage = data["voltage"]
                current = power_kw / (voltage / 1000)
                phase = current_phases[house_id]
                
                new_phase = send_telemetry(house_id, voltage, current, power_kw, phase)
                if new_phase != phase:
                    print(f"⚡ {house_id} switched: {phase} → {new_phase}")
                    current_phases[house_id] = new_phase
            
            if cycle % 5 == 0:
                status = get_current_status()
                print(f"\n📊 Status after {cycle} cycles:")
                print_status(status)
            
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped")
        status = get_current_status()
        print_status(status)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SMART PHASE BALANCING TEST")
    print("="*60)
    print("\nMake sure your FastAPI server is running: python app.py")
    print("\nAvailable scenarios:")
    print("  1. Internal Conflict (mixed export/import on same phase)")
    print("  2. Simple Imbalance (all consuming, uneven distribution)")
    
    choice = input("\nSelect scenario (1-2): ").strip()
    
    if choice == "1":
        scenario_internal_conflict_with_balancing()
    elif choice == "2":
        scenario_simple_imbalance()
    else:
        print("Invalid choice")
