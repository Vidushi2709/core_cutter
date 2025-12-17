import requests
import random
import time

API_BASE = "http://localhost:8000"

def generate_100_houses_telemetry():
    """
    Generate telemetry for 12 houses with intentional imbalance
    to demonstrate the map's red/green logic
    """
    houses = []
    
    # Create imbalanced distribution:
    # Phase L1: 5 houses (high load) - IMBALANCED
    # Phase L2: 4 houses (medium load) - BALANCED
    # Phase L3: 3 houses (low load) - IMBALANCED
    
    house_id = 1
    
    # Phase L1 - 5 houses with higher consumption (RED - imbalanced)
    for i in range(5):
        houses.append({
            "house_id": f"House_{house_id:03d}",
            "phase": "L1",
            "voltage": round(random.uniform(235, 245), 2),
            "current": round(random.uniform(15, 25), 2),  # Higher current
            "power_kw": round(random.uniform(3.5, 6.0), 2),  # Higher power
        })
        house_id += 1
    
    # Phase L2 - 4 houses with medium consumption (GREEN - balanced)
    for i in range(4):
        houses.append({
            "house_id": f"House_{house_id:03d}",
            "phase": "L2",
            "voltage": round(random.uniform(235, 245), 2),
            "current": round(random.uniform(8, 15), 2),  # Medium current
            "power_kw": round(random.uniform(2.0, 3.5), 2),  # Medium power
        })
        house_id += 1
    
    # Phase L3 - 3 houses with lower consumption (RED - imbalanced)
    for i in range(3):
        houses.append({
            "house_id": f"House_{house_id:03d}",
            "phase": "L3",
            "voltage": round(random.uniform(235, 245), 2),
            "current": round(random.uniform(4, 10), 2),  # Lower current
            "power_kw": round(random.uniform(1.0, 2.5), 2),  # Lower power
        })
        house_id += 1
    
    return houses

def send_telemetry(houses):
    """Send telemetry data to the API (one house at a time)"""
    
    print(f"📡 Sending telemetry for {len(houses)} houses...")
    success_count = 0
    
    try:
        for house in houses:
            try:
                response = requests.post(f"{API_BASE}/telemetry", json=house)
                if response.status_code == 200:
                    success_count += 1
                    if success_count % 20 == 0:  # Progress update every 20 houses
                        print(f"   ✓ Sent {success_count}/{len(houses)} houses...")
                else:
                    print(f"   ✗ Failed {house['house_id']}: {response.status_code}")
            except Exception as e:
                print(f"   ✗ Error {house['house_id']}: {e}")
            
            time.sleep(0.05)  # Small delay to avoid overwhelming the server
        
        if success_count == len(houses):
            print(f"✅ Successfully sent telemetry for {len(houses)} houses")
            
            # Calculate phase totals
            phase_totals = {"L1": 0, "L2": 0, "L3": 0}
            phase_counts = {"L1": 0, "L2": 0, "L3": 0}
            
            for house in houses:
                phase_totals[house["phase"]] += house["power_kw"]
                phase_counts[house["phase"]] += 1
            
            print("\n📊 Phase Distribution:")
            for phase in ["L1", "L2", "L3"]:
                print(f"   Phase {phase}: {phase_counts[phase]} houses, {phase_totals[phase]:.2f} kW total")
            
            # Calculate imbalance
            max_power = max(phase_totals.values())
            min_power = min(phase_totals.values())
            imbalance = max_power - min_power
            
            print(f"\n⚖️  Imbalance: {imbalance:.2f} kW")
            
            if imbalance > 0.5:
                print("   🔴 Phases are IMBALANCED - Map should show RED markers on overloaded phases")
            else:
                print("   🟢 Phases are BALANCED - Map should show GREEN markers")
            
            print(f"\n💡 Expected Map Colors:")
            avg_power = sum(phase_totals.values()) / len(phase_totals)
            for phase in ["L1", "L2", "L3"]:
                if abs(phase_totals[phase] - avg_power) > 0.5:
                    color = "🔴 RED (Imbalanced)"
                else:
                    color = "🟢 GREEN (Balanced)"
                print(f"   Phase {phase}: {color}")
            
            return True
        else:
            print(f"❌ Failed to send telemetry: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("🏠  GENERATING 12 HOUSE TELEMETRY FOR MAP TEST")
    print("=" * 60)
    print()
    
    # Generate houses
    print("🔧 Generating telemetry for 12 houses...")
    houses = generate_100_houses_telemetry()
    print(f"✅ Generated data for {len(houses)} houses\n")
    
    # Send telemetry
    print("📡 Sending telemetry to API...")
    success = send_telemetry(houses)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ DONE! Open your dashboard to see the map with markers")
        print("=" * 60)
        print("\n📍 Check the map at the bottom of the dashboard:")
        print("   - Phase L1 houses should show RED (overloaded)")
        print("   - Phase L2 houses should show GREEN (balanced)")
        print("   - Phase L3 houses should show RED (underloaded)")
        print("\n🔄 The system will automatically try to balance the phases")
    else:
        print("\n❌ Failed to send telemetry. Please check if app.py is running.")

if __name__ == "__main__":
    main()
