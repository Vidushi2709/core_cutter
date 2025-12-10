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

        print(f"  [CONSUME] Current imbalance: {current_imbalance_kw:.2f} kW")
        
        # Removed overly restrictive check - allow balancing even for smaller imbalances
        if current_imbalance_kw < MIN_IMBALANCE_KW:
            print(f"  [CONSUME] Imbalance too low ({current_imbalance_kw:.2f} < {MIN_IMBALANCE_KW})")
            return None  # Only skip if imbalance is truly insignificant

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

        print(f"  [CONSUME] Found {len(house_powers)} houses with valid readings")
        
        # Filter candidates: consumers with power > 0.05 kW (lowered threshold)
        # Include ALL consuming houses, not just heavy ones
        candidates = [hp for hp in house_powers if hp["power_kw"] > 0.05]
        candidates.sort(key=lambda x: abs(x["power_kw"]), reverse=True)

        print(f"  [CONSUME] Found {len(candidates)} candidate houses for switching")
        for c in candidates[:5]:  # Show top 5
            print(f"    - {c['house_id']}: {c['power_kw']:.2f} kW on {c['phase']}")
        
        if not candidates:
            print(f"  [CONSUME] No candidates found")
            return None

        # Compute baseline net power per phase
        baseline_net = {p: 0.0 for p in PHASES}
        for hp in house_powers:
            baseline_net[hp["phase"]] += hp["power_kw"]

        print(f"  [CONSUME] Baseline phase loads: L1={baseline_net['L1']:.2f}, L2={baseline_net['L2']:.2f}, L3={baseline_net['L3']:.2f}")
        
        # More lenient hysteresis threshold
        hysteresis_threshold = max(SWITCH_IMPROVEMENT_KW, 0.02 * current_imbalance_kw)
        print(f"  [CONSUME] Hysteresis threshold: {hysteresis_threshold:.3f} kW")

        best: Optional[RecommendedSwitch] = None
        best_improvement = 0.0

        # Try each candidate move to each target phase
        for candidate in candidates:
            house_id = candidate["house_id"]
            source_phase = candidate["phase"]
            power_kw = candidate["power_kw"]

            # Relax power threshold - allow smaller houses to move if imbalance is moderate
            skip_small_house = (
                power_kw < HIGH_IMPORT_THRESHOLD and 
                current_imbalance_kw < HIGH_IMBALANCE_KW  # Use HIGH not CRITICAL
            )
            if skip_small_house:
                print(f"    [CONSUME] Skipping {house_id} ({power_kw:.2f}kW < {HIGH_IMPORT_THRESHOLD} AND {current_imbalance_kw:.2f}kW < {HIGH_IMBALANCE_KW})")
                continue

            print(f"    [CONSUME] Evaluating {house_id} ({power_kw:.2f}kW from {source_phase})")
            
            for target_phase in PHASES:
                if target_phase == source_phase:
                    continue

                # Simulate move
                new_net = baseline_net.copy()
                new_net[source_phase] -= power_kw
                new_net[target_phase] += power_kw

                new_imbalance = max(new_net.values()) - min(new_net.values())
                improvement = current_imbalance_kw - new_imbalance

                print(f"      {source_phase}→{target_phase}: new_loads=[L1:{new_net['L1']:.2f}, L2:{new_net['L2']:.2f}, L3:{new_net['L3']:.2f}], new_imbalance={new_imbalance:.2f}, improvement={improvement:.3f}")
                
                if improvement <= 0:
                    print(f"        SKIP: No improvement")
                    continue
                if improvement < hysteresis_threshold:
                    print(f"        SKIP: Below threshold ({improvement:.3f} < {hysteresis_threshold:.3f})")
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
                    print(f"        ✓ NEW BEST: improvement={improvement:.3f} kW")

        if best:
            print(f"  [CONSUME] Returning recommendation: {best.house_id} {best.from_phase}→{best.to_phase}")
        else:
            print(f"  [CONSUME] No valid recommendation found")
        
        return best
