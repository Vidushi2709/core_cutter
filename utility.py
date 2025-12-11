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
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any
from pathlib import Path
import json
from configerations import (
    PHASES,
    READING_EXPIRY_SECONDS,
    CURRENT_MODE_THRESHOLD,
    OVERVOLTAGE_THRESHOLD,
    UNDERVOLTAGE_THRESHOLD,
    DATA_DIR,
    HOUSES_DB,
    TELEMETRY_DB,
    PHASE_TELEMETRY_DB,
    PHASE_TELEMETRY_EXPIRY_SECONDS,
    USE_PHASE_NODE_PRIORITY,
    HISTORY_DB,
    HIGH_EXPORT_THRESHOLD,
    HIGH_IMPORT_THRESHOLD,
    PHASE_OVERLOAD_THRESHOLD,
    RESET_STATE_ON_START,
    RESET_TELEMETRY_ON_START,
    RESET_HOUSES_ON_START,
    RESET_SWITCH_HISTORY_ON_START,
)

@dataclass
class ReadingOfEachHouse:
    """Data from one house at a particular time."""
    timestamp: datetime
    voltage: float
    current : float
    power_kw: float
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "voltage": self.voltage,
            "current": self.current,
            "power_kw": self.power_kw,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ReadingOfEachHouse':
        """Recreate a ReadingOfEachHouse from a dict loaded from JSON."""
        ts = datetime.fromisoformat(data["timestamp"])
        # Ensure UTC-aware datetime; if naive, assume UTC
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return cls(
            timestamp=ts,
            voltage=data["voltage"],
            current=data.get("current", 0.0),
            power_kw=data["power_kw"],
        )

@dataclass
class HouseState:
    """Current phase of the house."""
    house_id: str
    phase: str
    last_changed: datetime
    last_reading: Optional[ReadingOfEachHouse]

    def to_dict(self) -> Dict:
        return {
            "house_id": self.house_id,
            "phase": self.phase,
            "last_changed": self.last_changed.isoformat(),
            "last_reading": self.last_reading.to_dict() if self.last_reading else None,
        }
    @classmethod
    def from_dict(cls, data: Dict) -> 'HouseState':
        lc = datetime.fromisoformat(data["last_changed"])
        # Ensure UTC-aware datetime; if naive, assume UTC
        if lc.tzinfo is None:
            lc = lc.replace(tzinfo=timezone.utc)
        return cls(
            house_id=data["house_id"],
            phase=data["phase"],
            last_changed=lc,
            last_reading=ReadingOfEachHouse.from_dict(data["last_reading"]) if data["last_reading"] else None,
        )
    
# Store data locally
class DataStorage:
    def __init__(self):
        if isinstance(DATA_DIR, str):
            Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
        else:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
    def _load_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def _write_json(self, path: Path, data: Any):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def save_houses(self, houses: Dict[str, HouseState]):
        data = {hid: house.to_dict() for hid, house in houses.items()}
        self._write_json(Path(HOUSES_DB), data)
    
    def load_houses(self) -> Dict[str, HouseState]:
        data = self._load_json(Path(HOUSES_DB), default={})
        if not isinstance(data, dict):
            return {}
        return {hid: HouseState.from_dict(hdata) for hid, hdata in data.items()}
    
    def append_telemetry(self, house_id: str, reading: ReadingOfEachHouse, phase: str):
        """Append telemetry reading to history (preserves all readings for dashboard analytics)."""
        path = Path(TELEMETRY_DB)
        data = self._load_json(path, default=[])

        data.append({
            "house_id": house_id,
            "phase": phase,
            "timestamp": reading.timestamp.isoformat(),
            "voltage": reading.voltage,
            "current": reading.current,
            "power_kw": reading.power_kw
        })

        self._write_json(path, data)

    def clear_telemetry(self):
        path = Path(TELEMETRY_DB)
        self._write_json(path, [])

    def clear_switch_history(self):
        path = Path(HISTORY_DB)
        self._write_json(path, [])
        
    def append_switch_history(self, switch_record: Dict):
        path = Path(HISTORY_DB)
        data = self._load_json(path, default=[])
        data.append(switch_record)
        self._write_json(path, data)

    def get_switch_history(self, limit: int = 24) -> List[Dict]:
        path = Path(HISTORY_DB)
        records = self._load_json(path, default=[])
        if not isinstance(records, list):
            return []
        recent = records[-limit:] if len(records) > limit else records
        return list(reversed(recent))
    
    def save_phase_telemetry(self, telemetry: 'PhaseTelemetry'):
        """Save latest phase telemetry from edge node."""
        path = Path(PHASE_TELEMETRY_DB)
        self._write_json(path, telemetry.to_dict())
    
    def load_phase_telemetry(self) -> Optional['PhaseTelemetry']:
        """Load latest phase telemetry if not expired."""
        path = Path(PHASE_TELEMETRY_DB)
        data = self._load_json(path, default=None)
        if not data:
            return None
        
        try:
            telemetry = PhaseTelemetry.from_dict(data)
            now = datetime.now(timezone.utc)
            age_seconds = (now - telemetry.timestamp).total_seconds()
            if age_seconds > PHASE_TELEMETRY_EXPIRY_SECONDS:
                return None  # Expired
            return telemetry
        except Exception as e:
            print(f"Warning: Failed to load phase telemetry: {e}")
            return None

@dataclass
class PhaseTelemetry:
    """Direct phase-level power readings from edge node."""
    timestamp: datetime
    L1_kw: float
    L2_kw: float
    L3_kw: float
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "L1_kw": self.L1_kw,
            "L2_kw": self.L2_kw,
            "L3_kw": self.L3_kw,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PhaseTelemetry':
        ts = datetime.fromisoformat(data["timestamp"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return cls(
            timestamp=ts,
            L1_kw=data["L1_kw"],
            L2_kw=data["L2_kw"],
            L3_kw=data["L3_kw"],
        )

@dataclass
class PhaseStats:
    """Aggregate of all houses in a phase."""
    phase: str
    total_power_kw: float
    house_count: int
    avg_voltage: float
    source: str = "house_summation"  # 'house_summation' or 'phase_node'


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
    def __init__(self, storage: DataStorage):
        self.storage = storage
        self.houses: Dict[str, HouseState] = (
            self.storage.load_houses() if self.storage else {}
        )
        if self.storage and RESET_STATE_ON_START:
            self._reset_state_on_start()
        elif self.storage and RESET_HOUSES_ON_START:
            self._reset_houses_on_start()
        elif self.storage and not (RESET_STATE_ON_START or RESET_HOUSES_ON_START):
            self._recover_latest_readings_from_telemetry()

    def add_house(self, house_id: str, initial_phase: str):
        # initialize last_changed far in the past so newly-registered houses
        # are immediately eligible for switching unless explicitly set otherwise
        self.houses[house_id] = HouseState(
            house_id=house_id,
            phase=initial_phase,
            last_changed=datetime(1970, 1, 1, tzinfo=timezone.utc),
            last_reading=None,
        )
        if self.storage:
            # Persist the newly-registered house so it is available
            # after server restarts.
            self.storage.save_houses(self.houses)

    def _reset_state_on_start(self):
        """Clear cached readings and optionally telemetry when resetting on startup.
        
        This ensures a fresh start for balancing logic.
        """
        for house in self.houses.values():
            house.last_reading = None
        if self.storage:
            self.storage.save_houses(self.houses)
            if RESET_TELEMETRY_ON_START:
                try:
                    self.storage.clear_telemetry()
                except Exception as exc:
                    print(f"Warning: failed to clear telemetry on startup: {exc}")

    def _reset_houses_on_start(self):
        """Clear all house registrations and logs when configured to start fresh."""
        self.houses = {}
        if not self.storage:
            return
        try:
            self.storage.save_houses(self.houses)
            if RESET_TELEMETRY_ON_START:
                self.storage.clear_telemetry()
            if RESET_SWITCH_HISTORY_ON_START:
                self.storage.clear_switch_history()
        except Exception as exc:
            print(f"Warning: failed to fully reset houses on startup: {exc}")
    
    def _recover_latest_readings_from_telemetry(self):
        """Recover latest readings from telemetry.json on startup.
        
        This ensures in-memory state is restored after server restart,
        so analytics and balancing work even if telemetry arrived but
        server crashed before persisting to houses.json.
        """
        from pathlib import Path
        
        telemetry_path = Path(TELEMETRY_DB)
        if not telemetry_path.exists():
            return
        
        # Read telemetry.json as JSON array (not JSONL)
        latest_per_house = {}  # house_id -> (timestamp, reading)
        
        try:
            telemetry_data = self.storage._load_json(telemetry_path, default=[])
            if not isinstance(telemetry_data, list):
                print(f"Warning: Telemetry data is not a list, skipping recovery")
                return
            
            for entry in telemetry_data:
                try:
                    house_id = entry.get("house_id")
                    if not house_id:
                        continue
                    
                    ts = datetime.fromisoformat(entry["timestamp"])
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    
                    now = datetime.now(timezone.utc)
                    if READING_EXPIRY_SECONDS > 0:
                        if (now - ts).total_seconds() > READING_EXPIRY_SECONDS:
                            continue
                    
                    if house_id not in latest_per_house or ts > latest_per_house[house_id][0]:
                        reading = ReadingOfEachHouse(
                            timestamp=ts,
                            voltage=entry.get("voltage", 0.0),
                            current=entry.get("current", 0.0),
                            power_kw=entry.get("power_kw", 0.0)
                        )
                        latest_per_house[house_id] = (ts, reading)
                except (KeyError, ValueError, TypeError) as e:
                    continue
        except Exception as e:
            print(f"Warning: Failed to recover telemetry on startup: {e}")
            return
        
        for house_id, (_, reading) in latest_per_house.items():
            if house_id in self.houses:
                self.houses[house_id].last_reading = reading
    
    def update_reading(self, house_id: str, voltage: float, current: float, power_kw: float):
        if house_id not in self.houses:
            raise ValueError(f"Unknown house: {house_id}")
        
        reading = ReadingOfEachHouse(
            timestamp=datetime.now(timezone.utc),
            voltage=voltage,
            current=current,
            power_kw=power_kw
        )
        
        self.houses[house_id].last_reading = reading
        
        if self.storage:
            self.storage.append_telemetry(house_id, reading, self.houses[house_id].phase)
            self.storage.save_houses(self.houses)

    def apply_switch(self, house_id: str, new_phase: str, reason: Optional[str] = None):
        if house_id not in self.houses:
            raise ValueError("House not registered")

        old_phase = self.houses[house_id].phase
        self.houses[house_id].phase = new_phase
        self.houses[house_id].last_changed = datetime.now(timezone.utc)

        if self.storage:
            self.storage.save_houses(self.houses)

            switch_record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "house_id": house_id,
                "from_phase": old_phase,
                "to_phase": new_phase,
                "reason": reason if reason else "",
            }
            try:
                self.storage.append_switch_history(switch_record)
            except Exception as exc:
                print(f"Warning: failed to append switch history for {house_id}: {exc}")

class PhaseRegistry:
    def __init__(self, registry: HouseRegistry, storage: DataStorage):
        self.registry = registry
        self.storage = storage
        self.use_phase_node = USE_PHASE_NODE_PRIORITY

    def _effective_power_kw(self, house: HouseState, now: datetime) -> Optional[float]:
        """Return house power from last reading, respecting reading expiry."""
        reading = house.last_reading
        if reading is None:
            return None
        if READING_EXPIRY_SECONDS > 0:
            if (now - reading.timestamp).total_seconds() > READING_EXPIRY_SECONDS:
                return None
        return reading.power_kw
    def get_phase_stats(self) -> List[PhaseStats]:
        """Current stats for all phases.
        
        Priority:
        1. Use phase node telemetry if available and not expired
        2. Fall back to house summation if phase node unavailable
        """
        # Try to load phase node telemetry first
        if self.use_phase_node and self.storage:
            phase_telemetry = self.storage.load_phase_telemetry()
            if phase_telemetry:
                return self._get_stats_from_phase_node(phase_telemetry)
        
        # Fall back to house summation
        return self._get_stats_from_houses()
    
    def _get_stats_from_phase_node(self, telemetry: PhaseTelemetry) -> List[PhaseStats]:
        """Build phase stats directly from edge node telemetry."""
        # Still get house count and voltage from house data for dashboard
        house_stats = {p: {"voltages": [], "count": 0} for p in PHASES}
        now = datetime.now(timezone.utc)
        
        for house in self.registry.houses.values():
            r = house.last_reading
            if r is None:
                continue
            if READING_EXPIRY_SECONDS > 0:
                if (now - r.timestamp).total_seconds() > READING_EXPIRY_SECONDS:
                    continue
            
            phase = house.phase
            house_stats[phase]["voltages"].append(r.voltage)
            house_stats[phase]["count"] += 1
        
        # Use phase node power values
        phase_powers = {"L1": telemetry.L1_kw, "L2": telemetry.L2_kw, "L3": telemetry.L3_kw}
        
        return [
            PhaseStats(
                phase=p,
                total_power_kw=phase_powers[p],
                house_count=house_stats[p]["count"],
                avg_voltage=(
                    sum(house_stats[p]["voltages"]) / len(house_stats[p]["voltages"])
                    if house_stats[p]["voltages"]
                    else 0.0
                ),
                source="phase_node"
            )
            for p in PHASES
        ]
    
    def _get_stats_from_houses(self) -> List[PhaseStats]:
        """Build phase stats by summing individual house readings (fallback)."""
        stats = {p: {"power": 0.0, "voltages": [], "count": 0} for p in PHASES}
        now = datetime.now(timezone.utc)

        for house in self.registry.houses.values():
            effective_power = self._effective_power_kw(house, now)
            r = house.last_reading
            if effective_power is None or r is None:
                continue

            phase = house.phase
            stats[phase]["power"] += effective_power
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
                source="house_summation"
            )
            for p in PHASES
        ]

    def get_imbalance(self, phase_stat: List[PhaseStats]) -> float:
        powers = [ps.total_power_kw for ps in phase_stat]
        return max(powers) - min(powers)
    
    def get_phase_internal_imbalance(self, phase: str) -> Dict[str, float]:
        """Detect imbalance WITHIN a single phase (exporters vs importers conflicting).
        
        Returns:
            {
                'export_power': total export magnitude,
                'import_power': total import magnitude,
                'internal_imbalance': abs difference (conflict magnitude),
                'has_conflict': True if both exporters and importers exist
            }
        """
        now = datetime.now(timezone.utc)
        export_power = 0.0
        import_power = 0.0
        
        for house in self.registry.houses.values():
            if house.phase != phase:
                continue

            effective_power = self._effective_power_kw(house, now)
            if effective_power is None:
                continue

            if effective_power < 0:
                export_power += abs(effective_power)
            else:
                import_power += effective_power
        
        # Internal imbalance = how much conflict exists
        internal_imbalance = abs(export_power - import_power)
        has_conflict = export_power > 0.1 and import_power > 0.1  # Both exporters AND importers
        
        return {
            'export_power': export_power,
            'import_power': import_power,
            'internal_imbalance': internal_imbalance,
            'has_conflict': has_conflict
        }
    
    def detect_conflicted_phases(self) -> List[str]:
        """Find phases with internal exporter/importer conflicts.
        
        Returns list of phase names that have both exporters and importers,
        prioritized by internal imbalance magnitude.
        """
        conflicted = []
        for phase in PHASES:
            internal = self.get_phase_internal_imbalance(phase)
            if internal['has_conflict']:
                conflicted.append((phase, internal['internal_imbalance']))
        
        conflicted.sort(key=lambda x: x[1], reverse=True)
        return [phase for phase, _ in conflicted]
    
    def detect_phase_issues_detailed(self) -> Dict[str, Dict[str, Any]]:
        """Detailed per-phase analysis including internal conflicts.
        
        Returns:
            {
                'L1': {'net_power': -5.0, 'export_power': 5.0, 'import_power': 0.0, 'internal_imbalance': 5.0, 'has_conflict': False},
                'L2': {'net_power': 0.5, 'export_power': 0.0, 'import_power': 0.5, 'internal_imbalance': 0.5, 'has_conflict': False},
                ...
            }
        """
        phase_stats = self.get_phase_stats()
        issues = {}
        
        for phase in PHASES:
            phase_power = next((ps.total_power_kw for ps in phase_stats if ps.phase == phase), 0.0)
            internal = self.get_phase_internal_imbalance(phase)
            
            issues[phase] = {
                'net_power': phase_power,
                'export_power': internal['export_power'],
                'import_power': internal['import_power'],
                'internal_imbalance': internal['internal_imbalance'],
                'has_conflict': internal['has_conflict']
            }
        
        return issues

    def detect_mode(self, phase_stat: List[PhaseStats]) -> str:
        now = datetime.now(timezone.utc)
        export_power = 0.0
        import_power = 0.0

        for house in self.registry.houses.values():
            effective_power = self._effective_power_kw(house, now)
            if effective_power is None:
                continue

            if effective_power < 0:
                export_power += abs(effective_power)
            else:
                import_power += effective_power

        if export_power > CURRENT_MODE_THRESHOLD and export_power >= import_power:
            return "EXPORT"
        return "CONSUME"
    
    def detect_voltage_issues(self, phase_stat: List[PhaseStats]) -> Dict[str, List[str]]:
        issues = {
            "OVER_VOLTAGE": [],
            "UNDER_VOLTAGE": [],
            "OVERLOAD": [],
            "EXCESSIVE_EXPORT": []
        }
        
        for ps in phase_stat:
            if ps.avg_voltage > 0:
                if ps.avg_voltage > OVERVOLTAGE_THRESHOLD:
                    issues["OVER_VOLTAGE"].append(ps.phase)
                elif ps.avg_voltage < UNDERVOLTAGE_THRESHOLD:
                    issues["UNDER_VOLTAGE"].append(ps.phase)
            
            if ps.total_power_kw > PHASE_OVERLOAD_THRESHOLD:
                issues["OVERLOAD"].append(ps.phase)
            
            if ps.total_power_kw < -PHASE_OVERLOAD_THRESHOLD:
                issues["EXCESSIVE_EXPORT"].append(ps.phase)
        
        return issues
    
    def detect_power_issues(self, phase_stats: List[PhaseStats]) -> Dict[str, Any]:
        """Analyze power-based problems"""
        issues = {
            "overloaded_phases": [],
            "high_export_phases": [],
            "high_import_phases": [],
            "max_export_phase": None,
            "max_import_phase": None
        }
        
        max_export = 0
        max_import = 0
        
        for ps in phase_stats:
            # Detect phase overload (either direction)
            if abs(ps.total_power_kw) > PHASE_OVERLOAD_THRESHOLD:
                issues["overloaded_phases"].append({
                    "phase": ps.phase,
                    "power_kw": ps.total_power_kw,
                    "type": "import" if ps.total_power_kw > 0 else "export"
                })
            
            # Track high export phases (negative power = export)
            if ps.total_power_kw < -HIGH_EXPORT_THRESHOLD:
                issues["high_export_phases"].append(ps.phase)
                export_magnitude = abs(ps.total_power_kw)
                if export_magnitude > max_export:
                    max_export = export_magnitude
                    issues["max_export_phase"] = ps.phase
            
            # Track high import phases (positive power = import)
            if ps.total_power_kw > HIGH_IMPORT_THRESHOLD:
                issues["high_import_phases"].append(ps.phase)
                if ps.total_power_kw > max_import:
                    max_import = ps.total_power_kw
                    issues["max_import_phase"] = ps.phase
        
        return issues