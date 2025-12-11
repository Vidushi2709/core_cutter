#!/usr/bin/env python3
"""
Test with EXACT original data from your houses.json
"""

from datetime import datetime, timezone
from main import PhaseBalancingController
from utility import DataStorage
import json

# Load the original house assignments
with open('data/houses.json', 'r') as f:
    houses_json = json.load(f)

print("=" * 70)
print("TESTING WITH ORIGINAL DATA FROM houses.json")
print("=" * 70)

controller = PhaseBalancingController(DataStorage())

# Use exact data from houses.json
houses_data = {
    "B1": {"voltage": 230.0, "current": 2.0, "power_kw": 0.4, "phase": "L2"},
    "B2": {"voltage": 230.0, "current": 2.0, "power_kw": 0.4, "phase": "L2"},
    "B3": {"voltage": 230.0, "current": 2.0, "power_kw": 0.4, "phase": "L2"},
    "H1": {"voltage": 230.0, "current": 22.0, "power_kw": 4.8, "phase": "L1"},
    "H2": {"voltage": 230.0, "current": 19.0, "power_kw": 4.0, "phase": "L3"},
    "H3": {"voltage": 230.0, "current": 1.0, "power_kw": 0.2, "phase": "L2"},
    "H4": {"voltage": 230.0, "current": 1.0, "power_kw": 0.2, "phase": "L2"},
    "V1": {"voltage": 255.0, "current": 3.0, "power_kw": 0.7, "phase": "L2"},
    "V2": {"voltage": 190.0, "current": 1.0, "power_kw": 0.2, "phase": "L2"},
}

print("\nCurrent state (from houses.json):")
for house_id, data in sorted(houses_data.items()):
    actual_phase = houses_json.get(house_id, {}).get('phase', '?')
    print(f"  {house_id}: {data['power_kw']:.1f} kW on {actual_phase}")

print("\nPhase loads:")
phase_totals = {'L1': 0, 'L2': 0, 'L3': 0}
for house_id, data in houses_data.items():
    phase = houses_json.get(house_id, {}).get('phase', 'L2')
    phase_totals[phase] += data['power_kw']

for phase in ['L1', 'L2', 'L3']:
    houses_on_phase = [h for h, d in houses_data.items() if houses_json.get(h, {}).get('phase') == phase]
    print(f"  {phase}: {phase_totals[phase]:.1f} kW ({len(houses_on_phase)} houses) {houses_on_phase}")

current_imbalance = max(phase_totals.values()) - min(phase_totals.values())
print(f"\nCurrent imbalance: {current_imbalance:.1f} kW")

print("\n" + "=" * 70)
print("Updating readings and running cycle...")
print("=" * 70 + "\n")

# Update all readings
for house_id, data in houses_data.items():
    controller.registry.update_reading(
        house_id, 
        data["voltage"], 
        data["current"], 
        data["power_kw"]
    )

# Run cycle
result = controller.run_cycle()

print("\n" + "=" * 70)
print("RESULT")
print("=" * 70)

if result['recommendation']:
    rec = result['recommendation']
    print(f"\n✅ SUCCESS - Recommendation Generated:")
    print(f"   House: {rec['house_id']}")
    print(f"   Move: {rec['from_phase']} → {rec['to_phase']}")
    print(f"   Current Power: {houses_data[rec['house_id']]['power_kw']:.2f} kW")
    print(f"   Improvement: {rec['improvement_kw']:.2f} kW")
    print(f"   New Imbalance: {rec['new_imbalance_kw']:.2f} kW (from {result['imbalance_kw']:.2f} kW)")
    print(f"   Reason: {rec['reason']}")
    
    # Show what phases will look like after switch
    print(f"\n   After switch:")
    new_totals = phase_totals.copy()
    house_power = houses_data[rec['house_id']]['power_kw']
    new_totals[rec['from_phase']] -= house_power
    new_totals[rec['to_phase']] += house_power
    for phase in ['L1', 'L2', 'L3']:
        print(f"     {phase}: {new_totals[phase]:.2f} kW")
    
else:
    print(f"\n❌ NO RECOMMENDATION")
    print(f"   Imbalance: {result['imbalance_kw']:.2f} kW")
    if result['imbalance_kw'] < 0.5:
        print(f"   Status: System balanced")
    else:
        print(f"   Status: Check logs above - something prevented recommendation")

print("\n" + "=" * 70)
