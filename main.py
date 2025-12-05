from datetime import datetime
from typing import Dict, Optional

from configerations import CRITICAL_IMBALANCE_KW, HIGH_EXPORT_THRESHOLD, HIGH_IMPORT_THRESHOLD, MIN_IMBALANCE_KW, MIN_SWITCH_GAP_MIN
from utility import HouseRegistry, PhaseRegistry, DataStorage
from morning_logic import MorningLogic
from night_logic import NightLogic


# Helper to compute minutes since a timestamp
def minutes_since(ts: datetime) -> float:
    return (datetime.now() - ts).total_seconds() / 60.0

class PhaseBalancingController:
    """Main controller orchestrating all logic"""

    def __init__(self, storage=None):
        self.storage = storage if storage else DataStorage()
        self.registry = HouseRegistry(self.storage)
        self.analyzer = PhaseRegistry(self.registry, self.storage)
        self.morning_balancer = MorningLogic(self.registry, self.analyzer)
        self.night_balancer = NightLogic(self.registry, self.analyzer)

        self._last_mode: Optional[str] = None
        self._mode_since: Optional[datetime] = None
        self.MODE_STABLE_SECONDS = 15
    def _stable_mode(self, detected_mode: str) -> str:
        now = datetime.now()
        if self._last_mode is None:
            self._last_mode = detected_mode
            self._mode_since = now
            return detected_mode


        if detected_mode != self._last_mode:
        # mode changed — require it to persist for MODE_STABLE_SECONDS
            if self._mode_since and (now - self._mode_since).total_seconds() >= self.MODE_STABLE_SECONDS:
                self._last_mode = detected_mode
                self._mode_since = now
                return detected_mode
            else:
            # keep previous mode until it persists
                return self._last_mode
        else:
            # mode unchanged; update since time
            self._mode_since = self._mode_since or now
            return self._last_mode
        
    def run_cycle(self) -> Dict:
        """
        Run one balancing cycle
        Returns status and recommendation
        """
        phase_stats = self.analyzer.get_phase_stats()
        r_mode = self.analyzer.detect_mode(phase_stats)
        mode= self._stable_mode(r_mode)
        imbalance = self.analyzer.get_imbalance(phase_stats)
        phase_issues = self.analyzer.detect_voltage_issues(phase_stats)
        power_issues = self.analyzer.detect_power_issues(phase_stats)
        
        # Early health check
        if (not phase_issues) and (not power_issues) and (imbalance < MIN_IMBALANCE_KW):
        # System healthy — avoid recommending anything
            return {
            "timestamp": datetime.now().isoformat(),
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
        
        # Choose appropriate balancer
        if mode == "DAY":
            recommendation = self.morning_balancer.find_best_switch()
        else:
            recommendation = self.night_balancer.find_best_switch()
        
        if recommendation:
            house = self.registry.houses.get(recommendation.house_id)
            if house is None:
                recommendation = None  # invalid house
            else:
                try:
                    if minutes_since(house.last_changed) < MIN_SWITCH_GAP_MIN:
                        recommendation = None  # recently switched  
                except Exception:
                    recommendation = None  # missing last_changed

        # ignore small/-ve improvements
                if recommendation and recommendation.improved_kw <=0:
                    recommendation = None 
                
                try:
                    last_read = house.last_reading
                    p = last_read.power_kw if last_read else 0.0
                    if recommendation and p is not None:
                        strong_threshold = abs(p)>=max(HIGH_EXPORT_THRESHOLD, HIGH_IMPORT_THRESHOLD)
                        critical_imbalance = imbalance >= CRITICAL_IMBALANCE_KW
                        if not strong_threshold and not critical_imbalance:
                            recommendation = None  # skip small exporters/importers when imbalance isn't critical
                except Exception:
                    recommendation = None  # missing reading
        
            
        # Build status report
        status = {
            "timestamp": datetime.now().isoformat(),
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

            # Apply the switch
            try:
                self.registry.apply_switch(recommendation.house_id, recommendation.to_phase, recommendation.reason)
            except Exception as e:
                # If apply fails, clear recommendation but keep the status for diagnostics
                status["apply_error"] = str(e)        
        return status