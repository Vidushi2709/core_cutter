from datetime import datetime
from typing import Dict

from utility import HouseRegistry, PhaseRegistry, DataStorage
from morning_logic import MorningLogic
from night_logic import NightLogic


class PhaseBalancingController:
    """Main controller orchestrating all logic"""

    def __init__(self, storage=None):
        self.storage = storage if storage else DataStorage()
        self.registry = HouseRegistry(self.storage)
        self.analyzer = PhaseRegistry(self.registry, self.storage)
        self.morning_balancer = MorningLogic(self.registry, self.analyzer)
        self.night_balancer = NightLogic(self.registry, self.analyzer)
    
    def run_cycle(self) -> Dict:
        """
        Run one balancing cycle
        Returns status and recommendation
        """
        phase_stats = self.analyzer.get_phase_stats()
        mode = self.analyzer.detect_mode(phase_stats)
        imbalance = self.analyzer.get_imbalance(phase_stats)
        phase_issues = self.analyzer.detect_voltage_issues(phase_stats)
        power_issues = self.analyzer.detect_power_issues(phase_stats)
        
        # Choose appropriate balancer
        if mode == "DAY":
            recommendation = self.morning_balancer.find_best_switch()
        else:
            recommendation = self.night_balancer.find_best_switch()
        
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
            self.registry.apply_switch(recommendation.house_id, recommendation.to_phase, recommendation.reason)
        
        return status