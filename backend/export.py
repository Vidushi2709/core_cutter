'''
Export-mode logic -> handles phase balancing when system is exporting.
'''
from datetime import datetime, timezone 
from typing import Optional, Dict, List
from utility import (
    RecommendedSwitch, 
    HouseRegistry,
    PhaseRegistry
)
from configerations import (
    CRITICAL_IMBALANCE_KW,
    HIGH_EXPORT_THRESHOLD,
    HIGH_IMBALANCE_KW,
    MIN_IMBALANCE_KW,
    PHASES,
    SWITCH_IMPROVEMENT_KW,
    READING_EXPIRY_SECONDS,
)

class export_logic:
    def __init__(self, registry: HouseRegistry, analyzer: PhaseRegistry):
        self.registry = registry
        self.analyzer = analyzer
    
    def get_candidate_house(self)-> List[Dict]:
        '''
        Get houses that can be switched.
        Priority to largest exporters first.
        
        NOTE: MIN_SWITCH_GAP_MIN validation is done in main.py run_cycle(),
        not here, to enforce single-switch-per-run logic consistently.
        '''
        now = datetime.now(timezone.utc)
        candidates = []
        for house in self.registry.houses.values():
            if not hasattr(house, "last_changed") or not hasattr(house, "last_reading"):
                continue

            r = house.last_reading
            if not r:
                continue
            if (now - r.timestamp).total_seconds() > READING_EXPIRY_SECONDS:
                continue

            if r.power_kw < -0.05:
                candidates.append({
                    "house_id": house.house_id,
                    "current_phase": house.phase,
                    "power_kw": r.power_kw,
                    "voltage": r.voltage,
                })
        candidates.sort(key=lambda x: abs(x["power_kw"]), reverse=True)
        return candidates

    def find_best_switch(self) -> Optional[RecommendedSwitch]:
        """
        Find the best house to switch to reduce imbalance.
        
        Priority 1: Resolve internal phase conflicts (exporters + importers on same phase)
        Priority 2: Balance across phases (global imbalance reduction)

        When all houses are on one phase with mixed export/import, moving the smaller
        load is better than moving the large exporter (to avoid creating new imbalance).
        """
        phase_stats = self.analyzer.get_phase_stats()
        current_imbalance_kw = self.analyzer.get_imbalance(phase_stats)

        # Remove redundant check - MIN_IMBALANCE_KW already checked in run_cycle()
        if current_imbalance_kw < MIN_IMBALANCE_KW:
            return None  # No significant imbalance to address
        
        # Phase power mapping
        phase_power = {ps.phase: ps.total_power_kw for ps in phase_stats}
        
        # Priority 1: Resolve internal conflicts
        conflicted_phases = self.analyzer.detect_conflicted_phases()
        if conflicted_phases:
            source_phase = conflicted_phases[0]
            
            all_houses_on_source = all(
                h.phase == source_phase for h in self.registry.houses.values()
                if h.last_reading
            )
            
            if all_houses_on_source:
                exporters_on_source = [
                    h for h in self.registry.houses.values()
                    if h.phase == source_phase and h.last_reading and h.last_reading.power_kw < -0.05
                ]
                
                if exporters_on_source:
                    exporter = max(exporters_on_source, key=lambda h: abs(h.last_reading.power_kw) if h.last_reading else 0)
                    if exporter.last_reading:
                        house_id = exporter.house_id
                        power = exporter.last_reading.power_kw
                    
                    empty_phases = [p for p in PHASES if p != source_phase and phase_power[p] == 0]
                    
                    if empty_phases:
                        to_phase = empty_phases[0]
                        new_power = phase_power.copy()
                        new_power[source_phase] -= power
                        new_power[to_phase] += power
                        
                        new_imbalance_kw = max(new_power.values()) - min(new_power.values())
                        improvement_kw = current_imbalance_kw - new_imbalance_kw
                        
                        return RecommendedSwitch(
                            house_id=house_id,
                            from_phase=source_phase,
                            to_phase=to_phase,
                            improved_kw=improvement_kw,  # May be negative
                            new_imbalance_kw=new_imbalance_kw,
                            reason=f"CONFLICT RESOLUTION: Separating mixed export/import on {source_phase} by moving {power:.2f}kW exporter to {to_phase}",
                        )
            else:
                exporters_on_source = [
                    h for h in self.registry.houses.values()
                    if h.phase == source_phase and h.last_reading and h.last_reading.power_kw < -0.1
                ]
                
                if exporters_on_source:
                    exporter = max(exporters_on_source, key=lambda h: abs(h.last_reading.power_kw) if h.last_reading else 0)
                    if exporter.last_reading:
                        house_id = exporter.house_id
                        power = exporter.last_reading.power_kw
                    
                    importer_phases = [
                        phase for phase in PHASES 
                        if phase != source_phase and phase_power[phase] > 0.1
                    ]
                    
                    best_switch = None
                    
                    for to_phase in importer_phases:
                        new_power = phase_power.copy()
                        new_power[source_phase] -= power
                        new_power[to_phase] += power
                        
                        new_imbalance_kw = max(new_power.values()) - min(new_power.values())
                        improvement_kw = current_imbalance_kw - new_imbalance_kw
                        
                        if improvement_kw > 0:
                            if best_switch is None or improvement_kw > best_switch.improved_kw:
                                best_switch = RecommendedSwitch(
                                    house_id=house_id,
                                    from_phase=source_phase,
                                    to_phase=to_phase,
                                    improved_kw=improvement_kw,
                                    new_imbalance_kw=new_imbalance_kw,
                                    reason=f"Resolving internal conflict on {source_phase}: Moving {power:.2f}kW exporter to {to_phase}",
                                )
                    
                    if best_switch:
                        return best_switch
        
        voltage_issues = self.analyzer.detect_voltage_issues(phase_stats)
        over_voltage_phases = set(voltage_issues.get("OVER_VOLTAGE", []))

        candidates = self.get_candidate_house()
        best_house: Optional[RecommendedSwitch] = None
        for c in candidates:
            house_id = c["house_id"]
            from_phase = c["current_phase"]
            power = c["power_kw"]

            # Allow houses with >= 100W export power (lowered from 400W)
            if abs(power) < 0.1 and current_imbalance_kw < CRITICAL_IMBALANCE_KW:
                continue
            
            for to_phase in PHASES:
                if to_phase == from_phase:
                    continue

                new_power = phase_power.copy()
                new_power[from_phase] -= power
                new_power[to_phase] += power

                new_imbalance_kw = max(new_power.values()) - min(new_power.values())

                if new_imbalance_kw >= current_imbalance_kw:
                    continue
                
                improvement_kw = current_imbalance_kw - new_imbalance_kw

                if improvement_kw <= 0:
                    continue

                if current_imbalance_kw >= CRITICAL_IMBALANCE_KW:
                    hysteresis_threshold = 0.05
                else:
                    hysteresis_threshold = max(SWITCH_IMPROVEMENT_KW, 0.05 * current_imbalance_kw)
                if improvement_kw < hysteresis_threshold:
                    continue

                if (best_house is None) or (improvement_kw > best_house.improved_kw):
                    best_house = RecommendedSwitch(
                        house_id=house_id,
                        from_phase=from_phase,
                        to_phase=to_phase,
                        improved_kw=improvement_kw,
                        new_imbalance_kw=new_imbalance_kw,
                        reason=f"Export mode: Moving {power:.2f}kW from {from_phase} to {to_phase}",
                    )

        return best_house
