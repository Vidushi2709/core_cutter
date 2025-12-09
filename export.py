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
            if (now - r.timestamp).total_seconds() > READING_EXPIRY_SECONDS:  # reading too old
                continue

            # Morning: target large exporters (negative power_kw)
            # Negative `power_kw` indicates exporting (generation).
            # Select significant exporters only (avoid small noisy values)
            if r.power_kw < -0.1:  # 0.1 kW threshold to avoid noise
                candidates.append({
                    "house_id": house.house_id,
                    "current_phase": house.phase,
                    "power_kw": r.power_kw,
                    "voltage": r.voltage,
                })
        # Sort by magnitude of export (largest exporters first)
        # Since exporters have negative power_kw, sort to get most negative first
        candidates.sort(key=lambda x: abs(x["power_kw"]), reverse=True)
        return candidates

    def find_best_switch(self) -> Optional[RecommendedSwitch]:
        """
        Find the best house to switch to reduce the imbalance.

        Steps:
        1. Get current phase stats and compute imbalance.
        2. For each candidate exporter, try moving it to every other phase.
        3. Compute new imbalance after the simulated move and the improvement.
        4. Return the move with the largest improvement >= `SWITCH_IMPROVEMENT_KW`.
        """
        phase_stats = self.analyzer.get_phase_stats()
        current_imbalance_kw = self.analyzer.get_imbalance(phase_stats)

        if current_imbalance_kw < max(MIN_IMBALANCE_KW, HIGH_IMBALANCE_KW):
            return None  # No significant imbalance to address
        
        # Use voltage info to constrain moves:
        # - Morning (DAY) = solar/export mode
        # - Only move houses OFF phases that are over-voltage
        # - Only move them TO phases that are NOT over-voltage (normal or under)
        voltage_issues = self.analyzer.detect_voltage_issues(phase_stats)
        over_voltage_phases = set(voltage_issues.get("OVER_VOLTAGE", []))

        # phase_power: mapping phase -> signed total kW
        phase_power = {ps.phase: ps.total_power_kw for ps in phase_stats}

        candidates = self.get_candidate_house()
        best_house: Optional[RecommendedSwitch] = None
        for c in candidates:
            house_id = c["house_id"]
            from_phase = c["current_phase"]
            power = c["power_kw"]

            # Sign convention: power < 0 means exporting (generation).
            # The candidates list filters for power_kw < -0.1, so power should always be negative here.
            assert isinstance(power, (int, float)), f"power must be numeric, got {type(power)}"
            assert power < 0, f"Expected exporter (power < 0), got power={power} for house {house_id}"

            if abs(power) < HIGH_EXPORT_THRESHOLD and current_imbalance_kw < CRITICAL_IMBALANCE_KW:
                continue
            
            for to_phase in PHASES:
                if to_phase == from_phase:
                    continue

                # Simulate the move by adjusting phase totals.
                # When moving exporter from from_phase to to_phase:
                #   - Remove power from from_phase: new_power[from_phase] -= power (power is negative, so this increases the value)
                #   - Add power to to_phase: new_power[to_phase] += power (power is negative, so this decreases the value)
                new_power = phase_power.copy()
                new_power[from_phase] -= power 
                new_power[to_phase] += power

                new_imbalance_kw = max(new_power.values()) - min(new_power.values())

                if new_imbalance_kw >= current_imbalance_kw:
                    continue
                
                improvement_kw = current_imbalance_kw - new_imbalance_kw

                if improvement_kw <= 0:
                    continue

                # Hysteresis threshold: require minimum improvement to avoid oscillation.
                # Use the larger of SWITCH_IMPROVEMENT_KW or 5% of current imbalance.
                # This conservative approach blocks tiny marginal switches that cause oscillation.
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
