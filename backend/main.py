from datetime import datetime, timezone
from typing import Dict, Optional

from configerations import CRITICAL_IMBALANCE_KW, HIGH_EXPORT_THRESHOLD, HIGH_IMPORT_THRESHOLD, HIGH_IMBALANCE_KW, MIN_IMBALANCE_KW, MIN_SWITCH_GAP_MIN
from utility import HouseRegistry, PhaseRegistry, DataStorage
from export import export_logic
from consumption import consumption_logic


def minutes_since(ts: datetime) -> float:
    return (datetime.now(timezone.utc) - ts).total_seconds() / 60.0

class PhaseBalancingController:
    """Main controller orchestrating all logic"""

    def __init__(self, storage=None):
        self.storage = storage if storage else DataStorage()
        self.registry = HouseRegistry(self.storage)
        self.analyzer = PhaseRegistry(self.registry, self.storage)
        self.morning_balancer = export_logic(self.registry, self.analyzer)
        self.night_balancer = consumption_logic(self.registry, self.analyzer)

        self._last_mode: Optional[str] = None
        self._mode_since: Optional[datetime] = None
        self._pending_mode: Optional[str] = None
        self._pending_since: Optional[datetime] = None
        self.MODE_STABLE_SECONDS = 10

    def _stable_mode(self, detected_mode: str) -> str:
        now = datetime.now(timezone.utc)
        if self._last_mode is None:
            self._last_mode = detected_mode
            self._mode_since = now
            self._pending_mode = detected_mode
            self._pending_since = now
            return detected_mode

        if detected_mode == self._last_mode:
            self._pending_mode = detected_mode
            self._pending_since = now
            self._mode_since = self._mode_since or now
            return self._last_mode

        if self._pending_mode != detected_mode:
            self._pending_mode = detected_mode
            self._pending_since = now
            return self._last_mode

        if self._pending_since and (now - self._pending_since).total_seconds() >= self.MODE_STABLE_SECONDS:
            self._last_mode = detected_mode
            self._mode_since = now
        return self._last_mode
        
    def run_cycle(self) -> Dict:
        """
        Run one balancing cycle - implements single-switch-per-run logic.
        Returns status and recommendation.
        
        IMPORTANT: Only ONE switch will be applied per cycle, even if multiple
        improvements are available. This enforces gradual, predictable changes.
        """
        phase_stats = self.analyzer.get_phase_stats()
        r_mode = self.analyzer.detect_mode(phase_stats)
        mode = self._stable_mode(r_mode)
        imbalance = self.analyzer.get_imbalance(phase_stats)
        phase_issues = self.analyzer.detect_voltage_issues(phase_stats)
        power_issues = self.analyzer.detect_power_issues(phase_stats)
        
        print(f"\n=== PHASE BALANCING CYCLE ===")
        print(f"Mode: {mode}, Imbalance: {imbalance:.2f} kW")
        for ps in phase_stats:
            print(f"  {ps.phase}: {ps.total_power_kw:.2f} kW ({ps.house_count} houses)")
        
        if (not phase_issues) and (not power_issues) and (imbalance < MIN_IMBALANCE_KW):
            print(f"System healthy - no action needed (imbalance {imbalance:.2f} < {MIN_IMBALANCE_KW})")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mode": mode,
                "imbalance_kw": round(imbalance, 3),
                "phase_stats": [
                    {"phase": ps.phase, "power_kw": round(ps.total_power_kw, 3), "voltage": round(ps.avg_voltage, 1) if ps.avg_voltage else None, "house_count": ps.house_count}
                    for ps in phase_stats
                ],
                "phase_issues": phase_issues,
                "power_issues": power_issues,
                "recommendation": None,
            }
        
        recommendation = None
        
        if mode == "EXPORT":
            print("Using EXPORT mode balancer")
            recommendation = self.morning_balancer.find_best_switch()
        else:
            print("Using CONSUME mode balancer")
            recommendation = self.night_balancer.find_best_switch()
        
        if recommendation:
            print(f"Balancer recommends: {recommendation.house_id} from {recommendation.from_phase} to {recommendation.to_phase} (improvement: {recommendation.improved_kw:.2f} kW)")
        else:
            print("Balancer returned no recommendation")
        
        if recommendation:
            house = self.registry.houses.get(recommendation.house_id)
            if house is None:
                print(f"REJECTED: House {recommendation.house_id} not found in registry")
                recommendation = None
            else:
                try:
                    mins_since_switch = minutes_since(house.last_changed)
                    if mins_since_switch < MIN_SWITCH_GAP_MIN:
                        print(f"REJECTED: House {recommendation.house_id} switched {mins_since_switch:.2f} min ago (cooldown: {MIN_SWITCH_GAP_MIN} min)")
                        recommendation = None
                except (AttributeError, TypeError):
                    print(f"House {recommendation.house_id} has no switch history - allowing")
                    pass
                
                if recommendation:
                    is_conflict_resolution = "CONFLICT" in recommendation.reason.upper()
                    
                    if not is_conflict_resolution:
                        if recommendation.improved_kw <= 0:
                            print(f"REJECTED: Non-positive improvement ({recommendation.improved_kw:.2f} kW)")
                            recommendation = None
                        elif recommendation.improved_kw > 0:
                            try:
                                last_read = house.last_reading
                                p = last_read.power_kw if last_read else 0.0
                                
                                # Aligned with idk.py working thresholds
                                strong_house = abs(p) >= 0.1  # 100W threshold for small loads
                                high_imbalance = imbalance >= 0.15  # 150W imbalance threshold
                                good_improvement = recommendation.improved_kw >= 0.05  # 50W improvement threshold
                                
                                print(f"Validation: power={abs(p):.2f}kW, imbalance={imbalance:.2f}kW, improvement={recommendation.improved_kw:.2f}kW")
                                print(f"  strong_house={strong_house}, high_imbalance={high_imbalance}, good_improvement={good_improvement}")
                                
                                if not (strong_house or high_imbalance or good_improvement):
                                    print(f"REJECTED: House too small and improvement insufficient")
                                    recommendation = None
                                else:
                                    print(f"APPROVED: Validation passed")
                            except Exception as e:
                                # Fallback: require only 50W improvement if reading missing
                                if recommendation.improved_kw < 0.05:
                                    print(f"REJECTED: Missing reading and improvement < 0.05 kW")
                                    recommendation = None
                                else:
                                    print(f"APPROVED: Good improvement despite missing reading")
                    else:
                        print(f"APPROVED: Conflict resolution move (bypasses normal checks)")
        
        # Build status report
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "imbalance_kw": round(imbalance, 2),
            "phase_stats": [
                {
                    "phase": ps.phase,
                    "power_kw": round(ps.total_power_kw, 2),
                    "voltage": round(ps.avg_voltage, 1) if ps.avg_voltage else None,
                    "house_count": ps.house_count
                }
                for ps in phase_stats
            ],
            "phase_issues": phase_issues,
            "power_issues": power_issues,
            "recommendation": None
        }
        
        if recommendation:
            status["recommendation"] = {
                "house_id": recommendation.house_id,
                "from_phase": recommendation.from_phase,
                "to_phase": recommendation.to_phase,
                "improvement_kw": round(recommendation.improved_kw, 2),
                "new_imbalance_kw": round(recommendation.new_imbalance_kw, 2),
                "reason": recommendation.reason,
            }

            try:
                self.registry.apply_switch(recommendation.house_id, recommendation.to_phase, recommendation.reason)
            except Exception as e:
                status["apply_error"] = str(e)
        
        return status