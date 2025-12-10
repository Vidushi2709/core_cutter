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
CURRENT_MODE_THRESHOLD = 0.5  # Amps; exports above this imply export mode
EWMA_ALPHA = 0.2  # Smoothing factor for EWMA of house power

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

# Startup behavior
RESET_STATE_ON_START = True          # If True, clear last readings/smoothed power on startup
RESET_TELEMETRY_ON_START = True      # If True, truncate telemetry log on startup
RESET_HOUSES_ON_START = False        # If True, clear all registered houses/phases on startup (keep house registrations to preserve phase assignments)
RESET_SWITCH_HISTORY_ON_START = False # If True, clear switch history on startup

# Data storage
DATA_DIR = Path("./data")
HOUSES_DB = DATA_DIR / "houses.json"
TELEMETRY_DB = DATA_DIR / "telemetry.json"
HISTORY_DB = DATA_DIR / "switch_history.json"