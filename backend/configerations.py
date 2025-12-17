from pathlib import Path

# Timing / gating
MIN_SWITCH_GAP_MIN = 0.1  # 6 seconds - fast enough for critical imbalances, slow enough to prevent oscillation
AUTO_BALANCE_INTERVAL = 60
READING_EXPIRY_SECONDS = 3600

MIN_IMBALANCE_KW = 0.15  # Lowered to 150W for small loads like 170W bulbs
# Phases
PHASES = ["L1", "L2", "L3"]

# Switch / balancing tuning
SWITCH_IMPROVEMENT_KW = 0.05  # Lowered to 50W to allow smaller improvements
EXPORT_MODE_THRESHOLD = 0.2  # Lower threshold for light systems
CURRENT_MODE_THRESHOLD = 0.5  # Amps; exports above this imply export mode

# Voltage thresholds for 100–200V system
OVERVOLTAGE_THRESHOLD = 250.0
UNDERVOLTAGE_THRESHOLD = 200.0
NORMAL_VOLTAGE_MIN = 200.0
NORMAL_VOLTAGE_MAX = 240

# Power thresholds for light loads
MIN_EXPORT_FOR_SWITCH = 0.05     # 50W
MIN_IMPORT_FOR_SWITCH = 0.05     # 50W
HIGH_EXPORT_THRESHOLD = 0.1      # Lowered to 100W for small loads
HIGH_IMPORT_THRESHOLD = 0.1      # Lowered to 100W for small loads
PHASE_OVERLOAD_THRESHOLD = 1.0   # 1kW safe limit

# Imbalance thresholds
HIGH_IMBALANCE_KW = 0.15         # 150W
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
PHASE_TELEMETRY_DB = DATA_DIR / "phase_telemetry.json"  # Phase-level totals from edge node
HISTORY_DB = DATA_DIR / "switch_history.json"

# Phase telemetry settings
PHASE_TELEMETRY_EXPIRY_SECONDS = 10  # Phase totals expire after 10 seconds (fall back to house summation)
USE_PHASE_NODE_PRIORITY = False      # If True, prefer phase node telemetry over house summation (DISABLED - using house summation only)