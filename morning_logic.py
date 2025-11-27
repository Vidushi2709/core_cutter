'''
Morning logic -> handles phase balancing during morning time.
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

class MorningLogic:
    def __init__(self, registry: HouseRegistry, analyzer: PhaseRegistry):
        self.registry = registry
        self.analyzer = analyzer
    
    def get_candidate_house(self)-> List[Dict]:
        '''
        Get houses that can be switched
        Prioirty to largest exporters first
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

            if r.power_kw>0.1:
                candidates.append({
                    "house_id": house.house_id,
                    "current_phase": house.phase,
                    "power_kw": r.power_kw,
                    "voltage": r.voltage,
                })
        candidates.sort(key=lambda x: x["power_kw"], reverse=True)
        return candidates

    def find_best_switch(self) -> Optional[RecommendedSwitch]:
        """
        Find the best house to switch to reduce the imbalance
        moving large exporters from overloaded to underloaded phases
        """
        phase_stats = self.analyzer.get_phase_stats()
        current_imbalance_kw = self.analyzer.get_imbalance(phase_stats)

        phase_power = {ps.phase: ps.total_power_kw for ps in phase_stats}
        candidates = self.get_candidate_house()
        best_house: Optional[RecommendedSwitch] = None
        for c in candidates:
            house_id = c["house_id"]
            from_phase = c["current_phase"]
            power = c["power_kw"]
            for to_phase in PHASES:
                if to_phase == from_phase:
                    continue

                new_power = phase_power.copy()
                new_power[from_phase] -= power
                new_power[to_phase] += power

                new_imbalance_kw = max(new_power.values()) - min(new_power.values())
                improvement_kw = current_imbalance_kw - new_imbalance_kw

                if improvement_kw >= SWITCH_IMPROVEMENT_KW:
                    if (best_house is None) or (improvement_kw > best_house.improved_kw):
                        best_house = RecommendedSwitch(
                            house_id=house_id,
                            from_phase=from_phase,
                            to_phase=to_phase,
                            improved_kw=improvement_kw,
                            new_imbalance_kw=new_imbalance_kw,
                            reason=f"Day Time: Moving {power:.2f}kW from {from_phase} to {to_phase}",
                        )

        return best_house

