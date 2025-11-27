'''
handles phase balancing during night time.
'''
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List
from utility import (
    RecommendedSwitch, 
    HouseRegistry,
    PhaseRegistry
)
from configerations import (
    PHASES,
    MIN_SWITCH_GAP_MIN,
    SWITCH_IMPROVEMENT_KW,
    READING_EXPIRY_SECONDS,
)
class NightLogic:
    def __init__(self, registry: HouseRegistry, analyzer: PhaseRegistry):
        self.registry = registry
        self.analyzer = analyzer
    
    def get_candidate_house(self) -> List[Dict]:
        '''
        Get houses that can be switched at night.
        Priority to largest consumers (most negative power_kw).
        '''
        now=datetime.now()
        candidates = []
        for house in self.registry.houses.values():
            time_since_switch= (now-house.last_changed).total_seconds()/60
            if time_since_switch < MIN_SWITCH_GAP_MIN:
                continue

            r=house.last_reading
            if not r:
                continue
            if (now-r.timestamp).total_seconds() > READING_EXPIRY_SECONDS:
                continue

            # At night we care about heavy consumers (negative power_kw).
            if r.power_kw < -0.1:
                candidates.append({
                    "house_id": house.house_id,
                    "current_phase": house.phase,
                    "power_kw": r.power_kw,
                    "voltage": r.voltage,
                })

        # sort by magnitude of consumption (largest loads first)
        candidates.sort(key=lambda x: abs(x["power_kw"]), reverse=True)
        return candidates
    def find_best_switch(self)-> Optional[RecommendedSwitch]:
        '''     
        Find the best house to switch to reduce the imbalance
        '''
        phase_stats = self.analyzer.get_phase_stats()
        current_imbalance_kw = self.analyzer.get_imbalance(phase_stats)

        phase_power = {ps.phase: ps.total_power_kw for ps in phase_stats}
        candidates = self.get_candidate_house()
        best_house: Optional[RecommendedSwitch] = None
        for c in candidates:
            house_id = c["house_id"]
            current_phase = c["current_phase"]
            power_kw = c["power_kw"]

            for target_phase in PHASES:
                if target_phase == current_phase:
                    continue

                new_phase_power = phase_power.copy()
                new_phase_power[current_phase] -= power_kw
                new_phase_power[target_phase] += power_kw

                new_imbalance_kw = max(new_phase_power.values()) - min(new_phase_power.values())
                improvement_kw = current_imbalance_kw - new_imbalance_kw

                if improvement_kw >= SWITCH_IMPROVEMENT_KW:
                    if (best_house is None) or (improvement_kw > best_house.improved_kw):
                        best_house = RecommendedSwitch(
                            house_id=house_id,
                            from_phase=current_phase,
                            to_phase=target_phase,
                            improved_kw=improvement_kw,
                            new_imbalance_kw=new_imbalance_kw,
                            reason=f"Night: Moving {power_kw:.2f}kW from {current_phase} to {target_phase}",
                        )

        return best_house