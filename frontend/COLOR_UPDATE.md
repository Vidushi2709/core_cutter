# Phase Y Color Update

## Change Summary

### Phase Y Color Changed from Yellow to Light Blue

**Previous Color:** `#eab308` (Amber/Yellow)  
**New Color:** `#38bdf8` (Light Blue/Sky)

This makes Phase Y more distinguishable and easier to differentiate from warning/alert colors.

## Updated Phase Colors:

- **Phase R (L1)**: `#f43f5e` - Rose/Pink 🌸
- **Phase Y (L2)**: `#38bdf8` - Light Blue/Sky 🌊 ⚡ (Changed)
- **Phase B (L3)**: `#3b82f6` - Dark Blue 💙

## Data Status

### Backend Data: ✅ LIVE

The **0.0 kW values** you were seeing were **from the backend**, not hardcoded values. 

- The backend was running but had no house data initially
- After running `send_test_data.sh`, the backend now has:
  - **8 houses** with real telemetry data
  - Power consumption ranging from **-1.2 kW (export) to 3.5 kW (consume)**
  - Voltage readings around **236-242V**
  - Phase assignments across L1, L2, and L3

### Current System Status:
- **Mode**: CONSUME
- **Imbalance**: 5.6 kW
- **Total Houses**: 8 active
- **Phase L1**: 5 houses, 8.7 kW total
- **Real-time telemetry** is being served from backend

## How the Data Flows:

1. **Backend** (`app.py`) serves data via REST API on port 8000
2. **Frontend** fetches data from `http://localhost:8000/analytics/status`
3. **Update interval**: Frontend polls every 3 seconds (for status) and 5 seconds (for history)
4. **Test data script**: `backend/send_test_data.sh` sends sample telemetry to populate the system

## To Add More Test Data:

```bash
cd /home/ayush/Desktop/core_cutter/backend
./send_test_data.sh
```

This will add 8 houses with realistic power consumption, voltage, and phase assignments.
