#!/usr/bin/env python3
"""
Test script to verify phase switching logic works correctly.
"""

from datetime import datetime, timezone
from main import PhaseBalancingController
from utility import DataStorage

def test_phase_switching():
    """Test that phase switching works with your actual house data."""
    
    print("=" * 60)
    print("PHASE SWITCHING TEST")
    print("=" * 60)
    
    # Initialize controller
    controller = PhaseBalancingController(DataStorage())
    
    # Simulate fresh telemetry for all houses
    # Test: Make B2 heavy (2.4kW) on L3 which should trigger a switch
    houses_data = {
        "H1": {"phase": "L1", "voltage": 230.0, "current": 5.0, "power_kw": 1.0},
        "H2": {"phase": "L1", "voltage": 230.0, "current": -3.0, "power_kw": 0.2},
        "B1": {"phase": "L2", "voltage": 230.0, "current": 12.0, "power_kw": 2.4},
        # "B2": {"phase": "L3", "voltage": 230.0, "current": 12.0, "power_kw": 2.4},  # Heavy house
        # "B3": {"phase": "L1", "voltage": 230.0, "current": 2.0, "power_kw": 0.4},
        # "H3": {"phase": "L2", "voltage": 230.0, "current": 1.0, "power_kw": 0.2},
        # "H4": {"phase": "L2", "voltage": 230.0, "current": 1.0, "power_kw": 0.2},
        # "V1": {"phase": "L2", "voltage": 255.0, "current": 3.0, "power_kw": 0.3},
        # "V2": {"phase": "L2", "voltage": 190.0, "current": 1.0, "power_kw": 0.5},
    }
    
    print("\n1. Updating all house readings with fresh data...")
    print(f"   {'House':<6} {'Current Phase':<15} {'Power (kW)':<12}")
    print(f"   {'-'*6} {'-'*15} {'-'*12}")
    
    for house_id, data in houses_data.items():
        # Set the phase first if specified
        if "phase" in data:
            house = controller.registry.houses.get(house_id)
            if house:
                house.phase = data["phase"]
        
        controller.registry.update_reading(
            house_id, 
            data["voltage"], 
            data["current"], 
            data["power_kw"]
        )
        house = controller.registry.houses[house_id]
        print(f"   {house_id:<6} {house.phase:<15} {data['power_kw']:<12.2f}")
    
    print("\n2. Running balancing cycle...")
    result = controller.run_cycle()
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    print(f"\nMode: {result['mode']}")
    print(f"Imbalance: {result['imbalance_kw']:.2f} kW")
    
    print("\nPhase Stats:")
    for ps in result['phase_stats']:
        print(f"  {ps['phase']}: {ps['power_kw']:.2f} kW ({ps['house_count']} houses)")
    
    if result['recommendation']:
        rec = result['recommendation']
        print("\n✅ RECOMMENDATION APPROVED:")
        print(f"  House: {rec['house_id']}")
        print(f"  Current Phase: {rec['from_phase']}")
        print(f"  New Phase: {rec['to_phase']}")
        print(f"  House Power: {houses_data[rec['house_id']]['power_kw']:.2f} kW")
        print(f"  Improvement: {rec['improvement_kw']:.2f} kW")
        print(f"  Current Imbalance: {result['imbalance_kw']:.2f} kW")
        print(f"  New Imbalance: {rec['new_imbalance_kw']:.2f} kW")
        print(f"  Reason: {rec['reason']}")
    else:
        print("\n❌ NO RECOMMENDATION")
        if result['imbalance_kw'] < 0.5:
            print("   (System is balanced)")
        else:
            print("   (Check validation logs above)")
    
    print("\n" + "=" * 60)
    
    return result

if __name__ == "__main__":
    test_phase_switching()
