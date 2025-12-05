from pathlib import Path

# Timing / gating
MIN_SWITCH_GAP_MIN = 0.1
AUTO_BALANCE_INTERVAL = 60
READING_EXPIRY_SECONDS = 3600

MIN_IMBALANCE_KW = 0.8 
# Phases
PHASES = ["L1", "L2", "L3"]

# Switch / balancing tuning
SWITCH_IMPROVEMENT_KW = 0.1  # Smaller improvement needed because loads are tiny
EXPORT_MODE_THRESHOLD = 0.2  # Lower threshold for light systems

# Voltage thresholds for 100–200V system
OVERVOLTAGE_THRESHOLD = 250.0
UNDERVOLTAGE_THRESHOLD = 200.0
NORMAL_VOLTAGE_MIN = 200.0
NORMAL_VOLTAGE_MAX = 240

# Power thresholds for light loads
MIN_EXPORT_FOR_SWITCH = 0.05     # 50W
MIN_IMPORT_FOR_SWITCH = 0.05     # 50W
HIGH_EXPORT_THRESHOLD = 0.4      # 400W
HIGH_IMPORT_THRESHOLD = 0.4      # 400W
PHASE_OVERLOAD_THRESHOLD = 1.0   # 1kW safe limit

# Imbalance thresholds
HIGH_IMBALANCE_KW = 0.3         # 300W
CRITICAL_IMBALANCE_KW = 0.6     # 600W

# Data storage
DATA_DIR = Path("./data")
HOUSES_DB = DATA_DIR / "houses.json"
TELEMETRY_DB = DATA_DIR / "telemetry.json"
HISTORY_DB = DATA_DIR / "switch_history.json"