"""Utility types and analytics for phase balancing.

Conventions:
- `power_kw` and `total_power_kw` are signed:
    - Negative values mean generation/export (house exporting to grid).
    - Positive values mean consumption/import (house drawing from grid).

Main responsibilities:
- `HouseRegistry` stores per-house state and readings.
- `PhaseRegistry` aggregates per-phase stats and detects mode/imbalances.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List
from configerations import (
        PHASES,
        READING_EXPIRY_SECONDS,
        EXPORT_MODE_THRESHOLD,
        OVERVOLTAGE_THRESHOLD,
        UNDERVOLTAGE_THRESHOLD,
)


@dataclass
class ReadingOfEachHouse:
    """Data from one house at a particular time."""
    timestamp: datetime
    voltage: float
    power_kw: float


@dataclass
class HouseState:
    """Current phase of the house."""
    house_id: str
    phase: str
    last_changed: datetime
    last_reading: Optional[ReadingOfEachHouse]


@dataclass
class PhaseStats:
    """Aggregate of all houses in a phase."""
    phase: str
    total_power_kw: float
    house_count: int
    avg_voltage: float


@dataclass
class RecommendedSwitch:
    """Recommendation to switch a house to a different phase."""
    house_id: str
    from_phase: str
    to_phase: str
    improved_kw: float
    new_imbalance_kw: float
    reason: str

# all houses and their current phase
class HouseRegistry:
    def __init__(self):
        self.houses: Dict[str, HouseState] = {}

    def add_house(self, house_id: str, initial_phase: str):
        # initialize last_changed far in the past so newly-registered houses
        # are immediately eligible for switching unless explicitly set otherwise
        self.houses[house_id] = HouseState(
            house_id=house_id,
            phase=initial_phase,
            last_changed=datetime(1970, 1, 1),
            last_reading=None,
        )
    
    # Note: `power_kw` sign convention used across the codebase:
    #  - positive => consumption/import
    #  - negative => generation/export
    def update_reading(self, house_id: str, voltage: float, power_kw: float):
        if house_id not in self.houses:
            raise ValueError("House not registered")

        self.houses[house_id].last_reading = ReadingOfEachHouse(
            timestamp=datetime.now(),
            voltage=voltage,
            power_kw=power_kw,
        )

    def apply_switch(self, house_id: str, new_phase: str):
        if house_id not in self.houses:
            raise ValueError("House not registered")

        self.houses[house_id].phase = new_phase
        self.houses[house_id].last_changed = datetime.now()


''' Analytics on phases and houses 
1) what is the current state of each phase
2) recommend switches to balance phases'''
class PhaseRegistry:
    def __init__(self, registry: HouseRegistry):
        self.registry = registry

    def get_phase_stats(self) -> List[PhaseStats]:
        """Current stats for all phases."""
        stats = {p: {"power": 0.0, "voltages": [], "count": 0} for p in PHASES}
        now = datetime.now()

        for house in self.registry.houses.values():
            r = house.last_reading
            if r is None:
                continue
            if (now - r.timestamp).total_seconds() > READING_EXPIRY_SECONDS:
                continue

            phase = house.phase
            # accumulate signed power: negative reduces phase total (export),
            # positive increases it (consumption).
            stats[phase]["power"] += r.power_kw
            stats[phase]["voltages"].append(r.voltage)
            stats[phase]["count"] += 1

        return [
            PhaseStats(
                phase=p,
                total_power_kw=stats[p]["power"],
                house_count=stats[p]["count"],
                avg_voltage=(
                    sum(stats[p]["voltages"]) / len(stats[p]["voltages"])
                    if stats[p]["voltages"]
                    else 0.0
                ),
            )
            for p in PHASES
        ]

    def get_imbalance(self, phase_stat: List[PhaseStats]) -> float:
        # Imbalance is defined as difference between the most-consuming
        # phase and the most-generating phase.
        powers = [ps.total_power_kw for ps in phase_stat]
        return max(powers) - min(powers)

    def detect_mode(self, phase_stat: List[PhaseStats]) -> str:
        # Exports are negative totals. Compute total export power (kW)
        # by summing the absolute value of negative phase totals.
        total_export = sum(-ps.total_power_kw for ps in phase_stat if ps.total_power_kw < 0)
        # If exported power exceeds threshold, consider it daytime (solar exporting).
        if total_export > EXPORT_MODE_THRESHOLD:
            return "DAY"
        return "NIGHT"
    
    def detect_voltage_issues(self, phase_stat: List[PhaseStats]) -> Dict[str, List[str]]:
        issues = {"OVER_VOLTAGE": [], "UNDER_VOLTAGE": []}
        for ps in phase_stat:
            if ps.avg_voltage > OVERVOLTAGE_THRESHOLD:
                issues["OVER_VOLTAGE"].append(ps.phase)
            elif ps.avg_voltage < UNDERVOLTAGE_THRESHOLD:
                issues["UNDER_VOLTAGE"].append(ps.phase)
        return issues