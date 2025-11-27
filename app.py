from datetime import datetime
from typing import Dict

from utility import HouseRegistry, PhaseRegistry
from morning_logic import MorningLogic
from night_logic import NightLogic


class PhaseBalancingController:
    """Main controller orchestrating all logic"""

    def __init__(self):
        self.registry = HouseRegistry()
        self.analyzer = PhaseRegistry(self.registry)
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
        voltage_issues = self.analyzer.detect_voltage_issues(phase_stats)
        
        # Choose appropriate balancer
        if mode == "DAY":
            recommendation = self.morning_balancer.find_best_switch(verbose=True)
        else:
            recommendation = self.night_balancer.find_best_switch(verbose=True)
        
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
            "voltage_issues": voltage_issues,
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
            self.registry.apply_switch(recommendation.house_id, recommendation.to_phase)
        
        return status


if __name__ == "__main__":
    # Create controller
    controller = PhaseBalancingController()
    
    # Register houses
    controller.registry.add_house("h1", "L1")
    controller.registry.add_house("h2", "L1")
    controller.registry.add_house("h3", "L2")
    controller.registry.add_house("h4", "L3")
    
    print("=" * 80)
    print("MORNING SCENARIO (Solar Export)")
    print("=" * 80)
    
    # Morning readings - houses exporting solar
    controller.registry.update_reading("h1", voltage=248, power_kw=2.5)  # Heavy export
    controller.registry.update_reading("h2", voltage=246, power_kw=1.8)  # Medium export
    controller.registry.update_reading("h3", voltage=233, power_kw=-0.5) # Small import
    controller.registry.update_reading("h4", voltage=231, power_kw=-0.3) # Small import
    
    status = controller.run_cycle()
    print(f"\nMode: {status['mode']}")
    print(f"Imbalance: {status['imbalance_kw']} kW")
    print("\nPhase Stats:")
    for ps in status["phase_stats"]:
        print(f"  {ps['phase']}: {ps['power_kw']:+.2f} kW, {ps['voltage']}V, {ps['house_count']} houses")
    
    if status["recommendation"]:
        rec = status["recommendation"]
        print(f"\n Recommendation:")
        print(f"   {rec['reason']}")
        print(f"   House: {rec['house_id']}")
        print(f"   Move: {rec['from_phase']} → {rec['to_phase']}")
        print(f"   Improvement: {rec['improvement_kw']} kW")
    else:
        print("\n No switch needed - system balanced")
    
    print("\n" + "=" * 80)
    print("NIGHT SCENARIO (Grid Import)")
    print("=" * 80)
    
    # Night readings - houses importing from grid
    controller.registry.update_reading("h1", voltage=233, power_kw=-3.2)  # Heavy load
    controller.registry.update_reading("h2", voltage=232, power_kw=-2.5)  # Medium load
    controller.registry.update_reading("h3", voltage=239, power_kw=-0.8)  # Light load
    controller.registry.update_reading("h4", voltage=238, power_kw=-0.6)  # Light load
    
    status = controller.run_cycle()
    print(f"\nMode: {status['mode']}")
    print(f"Imbalance: {status['imbalance_kw']} kW")
    print("\nPhase Stats:")
    for ps in status["phase_stats"]:
        print(f"  {ps['phase']}: {ps['power_kw']:+.2f} kW, {ps['voltage']}V, {ps['house_count']} houses")
    
    if status["recommendation"]:
        rec = status["recommendation"]
        print(f"\n Recommendation:")
        print(f"   {rec['reason']}")
        print(f"   House: {rec['house_id']}")
        print(f"   Move: {rec['from_phase']} → {rec['to_phase']}")
        print(f"   Improvement: {rec['improvement_kw']} kW")
    else:
        print("\n No switch needed - system balanced")