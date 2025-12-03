from pathlib import Path

# Timing / gating
MIN_SWITCH_GAP_MIN = 20  # Minimum minutes between switches for same house
AUTO_BALANCE_INTERVAL = 60  # Run auto-balancing every 60 seconds
READING_EXPIRY_SECONDS = 3600  # Discard readings older than this

# Phases
PHASES = ["L1", "L2", "L3"]

# Switch / balancing tuning
SWITCH_IMPROVEMENT_KW = 0.3  # Minimum improvement needed to trigger switch
EXPORT_MODE_THRESHOLD = 0.5

# Voltage thresholds
OVERVOLTAGE_THRESHOLD = 245.0
UNDERVOLTAGE_THRESHOLD = 215.0
NORMAL_VOLTAGE_MIN = 220.0
NORMAL_VOLTAGE_MAX = 240.0

# Power thresholds
MIN_EXPORT_FOR_SWITCH = 0.5  # kW - minimum export to consider moving
MIN_IMPORT_FOR_SWITCH = 0.5  # kW - minimum import to consider moving
HIGH_EXPORT_THRESHOLD = 3.0  # kW - high solar export
HIGH_IMPORT_THRESHOLD = 3.0  # kW - high consumption
PHASE_OVERLOAD_THRESHOLD = 5.0

# Imbalance thresholds
HIGH_IMBALANCE_KW = 2.0
CRITICAL_IMBALANCE_KW = 3.5

# Data storage (Paths)
DATA_DIR = Path("./data")
HOUSES_DB = DATA_DIR / "houses.json"
TELEMETRY_DB = DATA_DIR / "telemetry.json"
HISTORY_DB = DATA_DIR / "switch_history.json"