from datetime import datetime, timezone
from typing import Dict

from configerations import MIN_IMBALANCE_KW, MIN_SWITCH_GAP_MIN
from main import minutes_since


def run_cycle(self) -> Dict:
        """
        Run one balancing cycle - implements single-switch-per-run logic.
        Returns status and recommendation.
        
        MODIFIED FOR DEMO: Thresholds relaxed to allow 170W bulb switching.
        """
        phase_stats = self.analyzer.get_phase_stats()
        r_mode = self.analyzer.detect_mode(phase_stats)
        mode = self._stable_mode(r_mode)
        imbalance = self.analyzer.get_imbalance(phase_stats)
        phase_issues = self.analyzer.detect_voltage_issues(phase_stats)
        power_issues = self.analyzer.detect_power_issues(phase_stats)
        
        # Debug: Print current phase loads
        print(f"\n=== PHASE BALANCING CYCLE ===")
        print(f"Mode: {mode}, Imbalance: {imbalance:.2f} kW")
        for ps in phase_stats:
            print(f"  {ps.phase}: {ps.total_power_kw:.2f} kW ({ps.house_count} houses)")
        
        # Early health check - Using lowered threshold (0.1kW) from configerations
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
        
        # Single-switch-per-run enforcement: get ONE best switch only
        recommendation = None
        
        # Choose appropriate balancer
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
        
        # Validate recommendation (only if one was returned from balancer)
        if recommendation:
            house = self.registry.houses.get(recommendation.house_id)
            if house is None:
                print(f"REJECTED: House {recommendation.house_id} not found in registry")
                recommendation = None
            else:
                # Check 1: has house been recently switched?
                try:
                    mins_since_switch = minutes_since(house.last_changed)
                    if mins_since_switch < MIN_SWITCH_GAP_MIN:
                        print(f"REJECTED: House {recommendation.house_id} switched {mins_since_switch:.2f} min ago (cooldown: {MIN_SWITCH_GAP_MIN} min)")
                        recommendation = None
                except (AttributeError, TypeError):
                    print(f"House {recommendation.house_id} has no switch history - allowing")
                    pass
                
                # Check 2: Validate improvement (ADJUSTED FOR DEMO BULBS)
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
                                
                                # --- DEMO LOGIC START ---
                                # 1. House Power: Allow anything >= 0.1 kW (100W) to catch your 170W bulbs
                                strong_house = abs(p) >= 0.1 
                                
                                # 2. Imbalance: Act if imbalance is >= 0.15 kW (150W)
                                high_imbalance = imbalance >= 0.15
                                
                                # 3. Improvement: Allow switch if it improves things by just 0.05 kW (50W)
                                good_improvement = recommendation.improved_kw >= 0.05
                                # --- DEMO LOGIC END ---
                                
                                print(f"Validation: power={abs(p):.2f}kW, imbalance={imbalance:.2f}kW, improvement={recommendation.improved_kw:.2f}kW")
                                print(f"  strong_house={strong_house}, high_imbalance={high_imbalance}, good_improvement={good_improvement}")
                                
                                if not (strong_house or high_imbalance or good_improvement):
                                    print(f"REJECTED: House too small and improvement insufficient")
                                    recommendation = None
                                else:
                                    print(f"APPROVED: Validation passed")
                            except Exception as e:
                                # Fallback if reading missing
                                if recommendation.improved_kw < 0.05:
                                    print(f"REJECTED: Missing reading and improvement < 0.05 kW")
                                    recommendation = None
                                else:
                                    print(f"APPROVED: Good improvement despite missing reading")
                    else:
                        print(f"APPROVED: Conflict resolution move")
        
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

            try:
                self.registry.apply_switch(recommendation.house_id, recommendation.to_phase, recommendation.reason)
            except Exception as e:
                status["apply_error"] = str(e)
        
        return status