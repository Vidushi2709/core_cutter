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
    HISTORY_DB,
    HIGH_EXPORT_THRESHOLD,
    HIGH_IMPORT_THRESHOLD,
    PHASE_OVERLOAD_THRESHOLD
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
        } # to serialize reading data and store it in json format
    
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
        ) # to deserialize reading data from json format back to ReadingOfEachHouse object

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
        # ensure directory exists
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
        path = Path(TELEMETRY_DB)
        data = self._load_json(path, default=[])

        # Replace any existing entry for this house to keep only the latest reading per house.
        data = [entry for entry in data if entry.get("house_id") != house_id]

        data.append({
            "house_id": house_id,
            "phase": phase,
            "timestamp": reading.timestamp.isoformat(),
            "voltage": reading.voltage,
            "current": reading.current,
            "power_kw": reading.power_kw
        })

        self._write_json(path, data)
        
    def append_switch_history(self, switch_record: Dict):
        path = Path(HISTORY_DB)
        data = self._load_json(path, default=[])
        # Append new record
        data.append(switch_record)
        # Save back as properly formatted JSON array
        self._write_json(path, data)
    
    def get_recent_telemetry(self, house_id: str, hours: int = 24) -> List[ReadingOfEachHouse]:
        path = Path(TELEMETRY_DB)
        data = self._load_json(path, default=[])

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = []

        for entry in data:
            if entry["house_id"] != house_id:
                continue

            ts = datetime.fromisoformat(entry["timestamp"])
            # Ensure UTC-aware datetime; if naive, assume UTC
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                result.append(
                    ReadingOfEachHouse(
                        timestamp=ts,
                        voltage=entry["voltage"],
                        current = entry.get("current", 0.0),
                        power_kw=entry["power_kw"]
                    )
                )

        return result

    def get_switch_history(self, limit: int = 24) -> List[Dict]:
        path = Path(HISTORY_DB)
        records = self._load_json(path, default=[])
        if not isinstance(records, list):
            return []
        # Return most recent `limit` entries (last N items in the array)
        return records[-limit:] if len(records) > limit else records

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
    def __init__(self, storage: DataStorage):
        """
        Registry of all houses and their current state.

        On startup we load any previously-saved houses from disk so that
        registrations and last readings survive a process restart.
        """
        self.storage = storage
        # Load from persistent storage if available, otherwise start empty.
        self.houses: Dict[str, HouseState] = (
            self.storage.load_houses() if self.storage else {}
        )
        
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
    
    # Note: `power_kw` sign convention used across the codebase:
    #  - positive => consumption/import
    #  - negative => generation/export
    def update_reading(self, house_id: str, voltage: float, current: float, power_kw: float):
        if house_id not in self.houses:
            raise ValueError(f"Unknown house: {house_id}")
        
        reading = ReadingOfEachHouse(
            timestamp=datetime.now(timezone.utc),
            voltage=voltage,
            current=current,
            power_kw=power_kw
        )
        
        # Update in-memory state
        self.houses[house_id].last_reading = reading
        
        # Persist both to the telemetry log and to the houses DB so that the
        # latest reading is reloaded after a restart.
        if self.storage:
            self.storage.append_telemetry(house_id, reading, self.houses[house_id].phase)
            self.storage.save_houses(self.houses)

    def apply_switch(self, house_id: str, new_phase: str, reason: Optional[str] = None):
        if house_id not in self.houses:
            raise ValueError("House not registered")

        old_phase = self.houses[house_id].phase
        self.houses[house_id].phase = new_phase
        self.houses[house_id].last_changed = datetime.now(timezone.utc)

        # Persist the updated house state and log the switch, if storage
        # is configured. Any logging error is swallowed so it doesn't
        # break the main flow.
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
                # Best-effort logging only, but surface a warning for diagnostics.
                print(f"Warning: failed to append switch history for {house_id}: {exc}")

''' Analytics on phases and houses 
1) what is the current state of each phase
2) recommend switches to balance phases'''
class PhaseRegistry:
    def __init__(self, registry: HouseRegistry, storage: DataStorage):
        self.registry = registry
        self.storage = storage

    def get_phase_stats(self) -> List[PhaseStats]:
        """Current stats for all phases."""
        stats = {p: {"power": 0.0, "voltages": [], "count": 0} for p in PHASES}
        now = datetime.now(timezone.utc)

        for house in self.registry.houses.values():
            r = house.last_reading
            if r is None:
                continue
            # Skip very old readings only if an expiry window is configured.
            # If READING_EXPIRY_SECONDS <= 0, we treat readings as non-expiring.
            if READING_EXPIRY_SECONDS > 0:
                if (now - r.timestamp).total_seconds() > READING_EXPIRY_SECONDS:
                    # we do the above to make sure we only take into account recent readings
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
        # Mode is derived from the sign of current instead of power to be
        # resilient to noisy power calculations. Negative current means export.
        now = datetime.now(timezone.utc)
        export_current = 0.0
        import_current = 0.0

        for house in self.registry.houses.values():
            reading = house.last_reading
            if reading is None:
                continue
            if READING_EXPIRY_SECONDS > 0:
                if (now - reading.timestamp).total_seconds() > READING_EXPIRY_SECONDS:
                    continue

            if reading.current < 0:
                export_current += -reading.current  # accumulate magnitude of exports
            else:
                import_current += reading.current

        if export_current > CURRENT_MODE_THRESHOLD and export_current >= import_current:
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
            # Only check voltage if phase has houses (avg_voltage > 0 means houses present)
            if ps.avg_voltage > 0:
                # Voltage-based issues
                if ps.avg_voltage > OVERVOLTAGE_THRESHOLD:
                    issues["OVER_VOLTAGE"].append(ps.phase)
                elif ps.avg_voltage < UNDERVOLTAGE_THRESHOLD:
                    issues["UNDER_VOLTAGE"].append(ps.phase)
            
            # Power-based issues
            # Positive power = consumption/import (overload)
            if ps.total_power_kw > PHASE_OVERLOAD_THRESHOLD:
                issues["OVERLOAD"].append(ps.phase)
            
            # Negative power = export/generation (excessive export)
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