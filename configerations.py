MIN_SWITCH_GAP_MIN = 20  # Minimum minutes between switches for same house
PHASES = ["L1", "L2", "L3"]
SWITCH_IMPROVEMENT_KW = 0.3  # Minimum improvement needed to trigger switch
READING_EXPIRY_SECONDS = 90  # Discard readings older than this

# Voltage thresholds
OVERVOLTAGE_THRESHOLD = 245.0
UNDERVOLTAGE_THRESHOLD = 215.0
NORMAL_VOLTAGE_MIN = 220.0
NORMAL_VOLTAGE_MAX = 240.0
EXPORT_MODE_THRESHOLD = 0.5

# Imbalance thresholds
HIGH_IMBALANCE_KW = 2.0
CRITICAL_IMBALANCE_KW = 3.5