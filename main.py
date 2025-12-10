from datetime import datetime, timezone
from typing import Dict, Optional

from configerations import CRITICAL_IMBALANCE_KW, HIGH_EXPORT_THRESHOLD, HIGH_IMPORT_THRESHOLD, MIN_IMBALANCE_KW, MIN_SWITCH_GAP_MIN
from utility import HouseRegistry, PhaseRegistry, DataStorage
from export import export_logic
from consumption import consumption_logic


# Helper to compute minutes since a timestamp
def minutes_since(ts: datetime) -> float:
    # Use UTC-aware now to avoid naive/aware subtraction errors
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
        self.MODE_STABLE_SECONDS = 15

    def _stable_mode(self, detected_mode: str) -> str:
        now = datetime.now(timezone.utc)
        if self._last_mode is None:
            # First observation initializes the stable and pending modes.
            self._last_mode = detected_mode
            self._mode_since = now
            self._pending_mode = detected_mode
            self._pending_since = now
            return detected_mode

        if detected_mode == self._last_mode:
            # Reset pending change if detection agrees with stable mode.
            self._pending_mode = detected_mode
            self._pending_since = now
            self._mode_since = self._mode_since or now
            return self._last_mode

        # Detected mode differs from stable mode — require persistence.
        if self._pending_mode != detected_mode:
            # Start a new pending window for this different detection.
            self._pending_mode = detected_mode
            self._pending_since = now
            return self._last_mode

        # Same pending mode continues; check if it has persisted long enough.
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
        
        # Early health check
        if (not phase_issues) and (not power_issues) and (imbalance < MIN_IMBALANCE_KW):
            # System healthy — avoid recommending anything
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
        
        # Single-switch-per-run enforcement: get ONE best switch only
        recommendation = None
        
        # Choose appropriate balancer
        if mode == "EXPORT":
            recommendation = self.morning_balancer.find_best_switch()
        else:
            recommendation = self.night_balancer.find_best_switch()
        
        # Validate recommendation (only if one was returned from balancer)
        if recommendation:
            house = self.registry.houses.get(recommendation.house_id)
            if house is None:
                # House doesn't exist in registry (shouldn't happen, but safety check)
                recommendation = None
            else:
                # Check 1: has house been recently switched? (MIN_SWITCH_GAP_MIN enforcement)
                try:
                    if minutes_since(house.last_changed) < MIN_SWITCH_GAP_MIN:
                        recommendation = None  # Skip: recently switched
                except (AttributeError, TypeError):
                    recommendation = None  # Skip: missing last_changed attribute
                
                # Check: is improvement significant enough?
                if recommendation and recommendation.improved_kw <= 0:
                    recommendation = None
                
                # Check: is the house a strong exporter/importer or is imbalance critical?
                if recommendation:
                    try:
                        last_read = house.last_reading
                        p = last_read.power_kw if last_read else 0.0
                        strong_threshold = abs(p) >= max(HIGH_EXPORT_THRESHOLD, HIGH_IMPORT_THRESHOLD)
                        critical_imbalance = imbalance >= CRITICAL_IMBALANCE_KW
                        if not strong_threshold and not critical_imbalance:
                            recommendation = None  # skip small exporters/importers unless critical
                    except Exception:
                        recommendation = None  # missing reading data
        
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
        
        # Apply the single switch if recommendation survived all validations
        if recommendation:
            status["recommendation"] = {
                "house_id": recommendation.house_id,
                "from_phase": recommendation.from_phase,
                "to_phase": recommendation.to_phase,
                "improvement_kw": round(recommendation.improved_kw, 2),
                "new_imbalance_kw": round(recommendation.new_imbalance_kw, 2),
                "reason": recommendation.reason,
            }

            # Apply the switch to the registry
            try:
                self.registry.apply_switch(recommendation.house_id, recommendation.to_phase, recommendation.reason)
            except Exception as e:
                # If apply fails, keep the status for diagnostics
                status["apply_error"] = str(e)
        
        return status