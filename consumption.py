'''
Consume-mode logic -> handles phase balancing when system is consuming.
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
    HIGH_IMBALANCE_KW,
    HIGH_IMPORT_THRESHOLD,
    MIN_IMBALANCE_KW,
    PHASES,
    SWITCH_IMPROVEMENT_KW,
    READING_EXPIRY_SECONDS,
)
class consumption_logic:
    def __init__(self, registry: HouseRegistry, analyzer: PhaseRegistry):
        self.registry = registry
        self.analyzer = analyzer
    
    def find_best_switch(self) -> Optional[RecommendedSwitch]:
        """Find the best house to switch to reduce consumption imbalance.
        
        Strategy: candidates are heavy consumers; simulate moving each to other phases;
        pick the move that maximizes net imbalance reduction.
        """
        now = datetime.now(timezone.utc)
        phase_stats = self.analyzer.get_phase_stats()
        current_imbalance_kw = self.analyzer.get_imbalance(phase_stats)

        if current_imbalance_kw < max(MIN_IMBALANCE_KW, HIGH_IMBALANCE_KW):
            return None  # No significant imbalance to fix

        # Collect houses with valid readings
        house_powers: List[Dict] = []
        for house in self.registry.houses.values():
            r = house.last_reading
            if not r:
                continue
            if (now - r.timestamp).total_seconds() > READING_EXPIRY_SECONDS:
                continue

            power_kw = house.smoothed_power_kw if house.smoothed_power_kw is not None else r.power_kw
            house_powers.append({
                "house_id": house.house_id,
                "phase": house.phase,
                "power_kw": power_kw,
            })

        # Filter candidates: significant consumers (positive power_kw > 0.1)
        candidates = [hp for hp in house_powers if hp["power_kw"] > 0.1]
        candidates.sort(key=lambda x: abs(x["power_kw"]), reverse=True)

        if not candidates:
            return None

        # Compute baseline net power per phase
        baseline_net = {p: 0.0 for p in PHASES}
        for hp in house_powers:
            baseline_net[hp["phase"]] += hp["power_kw"]

        # Hysteresis threshold
        hysteresis_threshold = max(SWITCH_IMPROVEMENT_KW, 0.05 * current_imbalance_kw)

        best: Optional[RecommendedSwitch] = None
        best_improvement = 0.0

        # Try each candidate move to each target phase
        for candidate in candidates:
            house_id = candidate["house_id"]
            source_phase = candidate["phase"]
            power_kw = candidate["power_kw"]

            if power_kw < HIGH_IMPORT_THRESHOLD and current_imbalance_kw < CRITICAL_IMBALANCE_KW:
                continue

            for target_phase in PHASES:
                if target_phase == source_phase:
                    continue

                # Simulate move
                new_net = baseline_net.copy()
                new_net[source_phase] -= power_kw
                new_net[target_phase] += power_kw

                new_imbalance = max(new_net.values()) - min(new_net.values())
                improvement = current_imbalance_kw - new_imbalance

                if improvement <= 0:
                    continue
                if improvement < hysteresis_threshold:
                    continue

                if improvement > best_improvement:
                    best_improvement = improvement
                    best = RecommendedSwitch(
                        house_id=house_id,
                        from_phase=source_phase,
                        to_phase=target_phase,
                        improved_kw=improvement,
                        new_imbalance_kw=new_imbalance,
                        reason=f"Consume: move {power_kw:.2f}kW from {source_phase} to {target_phase} (Δ={improvement:.2f}kW)",
                    )

        return best
