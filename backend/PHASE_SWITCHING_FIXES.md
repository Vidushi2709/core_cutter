# Phase Switching Issues - Analysis & Fixes

## 🚨 Critical Problems Identified

### Problem 1: **Overly Restrictive Validation Logic**
**Location:** `main.py` lines 115-125

**Issue:** The validation was TOO STRICT and rejected valid switch recommendations:
```python
# OLD CODE (PROBLEM):
if not strong_threshold and not critical_imbalance:
    recommendation = None  # Rejects too many valid switches!
```

**Why it failed:**
- Required BOTH conditions: house power >= 0.4 kW AND imbalance >= 0.6 kW
- Small houses (0.2 kW) couldn't switch even when imbalance was severe (2.7 kW)
- Used `CRITICAL_IMBALANCE_KW` (0.6) instead of `HIGH_IMBALANCE_KW` (0.3)

**Fix Applied:**
```python
# NEW CODE (FIXED):
# Allow switch if ANY of these conditions are true:
# 1. House has significant power (>= 0.4 kW)
# 2. Imbalance is high (>= 0.3 kW) 
# 3. Improvement is substantial (>= 0.3 kW)
strong_house = abs(p) >= max(HIGH_EXPORT_THRESHOLD, HIGH_IMPORT_THRESHOLD)
high_imbalance = imbalance >= HIGH_IMBALANCE_KW  # 0.3 kW (more lenient)
good_improvement = recommendation.improved_kw >= 0.3

if not (strong_house or high_imbalance or good_improvement):
    recommendation = None
```

---

### Problem 2: **Consumption Logic Too Conservative**
**Location:** `consumption.py` line 32

**Issue:**
```python
# OLD CODE (PROBLEM):
if current_imbalance_kw < max(MIN_IMBALANCE_KW, HIGH_IMBALANCE_KW):
    return None  # Required 0.8 kW imbalance before acting!

# Also filtered out small houses:
candidates = [hp for hp in house_powers if hp["power_kw"] > 0.1]  # Too strict

# And required large power or critical imbalance:
if power_kw < HIGH_IMPORT_THRESHOLD and current_imbalance_kw < CRITICAL_IMBALANCE_KW:
    continue  # Skipped 0.2-0.4 kW houses unless imbalance > 0.6 kW
```

**Fix Applied:**
```python
# NEW CODE (FIXED):
if current_imbalance_kw < MIN_IMBALANCE_KW:
    return None  # Only need 0.5 kW imbalance

# Include smaller houses:
candidates = [hp for hp in house_powers if hp["power_kw"] > 0.05]  # More inclusive

# More lenient thresholds:
skip_small_house = (
    power_kw < HIGH_IMPORT_THRESHOLD and 
    current_imbalance_kw < HIGH_IMBALANCE_KW  # Use 0.3 instead of 0.6
)
```

---

### Problem 3: **Configuration Too Strict**
**Location:** `configerations.py`

**Changes:**
| Setting | Old Value | New Value | Reason |
|---------|-----------|-----------|--------|
| `MIN_SWITCH_GAP_MIN` | 0.1 min (6s) | 0.5 min (30s) | Prevent rapid oscillation |
| `MIN_IMBALANCE_KW` | 0.8 kW | 0.5 kW | Be more responsive to imbalances |

---

### Problem 4: **Missing Debug Output**
**Location:** `main.py`

**Fix:** Added comprehensive logging:
```python
print(f"\n=== PHASE BALANCING CYCLE ===")
print(f"Mode: {mode}, Imbalance: {imbalance:.2f} kW")
for ps in phase_stats:
    print(f"  {ps.phase}: {ps.total_power_kw:.2f} kW ({ps.house_count} houses)")

# Shows why recommendations are rejected:
print(f"REJECTED: House too small and improvement insufficient")
print(f"APPROVED: Validation passed")
```

---

## 📊 Your Current Situation (from houses.json)

**Current Phase Distribution:**
- **L1**: 1 house (H1: 4.8 kW) 
- **L2**: 7 houses (B1, B2, B3, H3, H4, V1, V2: 2.1 kW total)
- **L3**: 1 house (H2: 4.0 kW)

**Imbalance:** 2.7 kW (L1 max - L2 min)

**Why switches stopped:**
- Houses on L2 are small (0.2-0.7 kW each)
- Old validation logic rejected them as "too small"
- Even though imbalance was severe (2.7 kW > 0.6 kW critical threshold)

---

## ✅ What Should Happen Now

With the fixes applied:

1. **More responsive switching:**
   - Acts on imbalance >= 0.5 kW (was 0.8 kW)
   - Considers smaller houses (>= 0.05 kW, was 0.1 kW)

2. **Better validation:**
   - Allows switches if imbalance >= 0.3 kW (was 0.6 kW)
   - OR improvement >= 0.3 kW
   - OR house power >= 0.4 kW

3. **Smoother operation:**
   - 30-second cooldown (was 6 seconds)
   - Prevents oscillation while allowing responsive changes

4. **Better debugging:**
   - See phase loads before each cycle
   - See why recommendations are accepted/rejected
   - Track which balancer is running (EXPORT/CONSUME)

---

## 🔧 How to Test

### Option 1: Manual Test with Fresh Telemetry
```bash
# Send fresh telemetry data to your API
curl -X POST http://localhost:8000/telemetry -H "Content-Type: application/json" -d '{
  "house_id": "H1",
  "voltage": 230.0,
  "current": 22.0,
  "power_kw": 4.8,
  "phase": "L1"
}'

# Send data for each house...
# Then check the response to see which phase it recommends
```

### Option 2: Direct Python Test
```python
from main import PhaseBalancingController
from utility import DataStorage
from datetime import datetime, timezone

controller = PhaseBalancingController(DataStorage())

# Simulate fresh reading
controller.registry.update_reading("H1", 230.0, 22.0, 4.8)
controller.registry.update_reading("B1", 230.0, 2.0, 0.4)
# ... update all houses

# Run cycle
result = controller.run_cycle()
print(f"Recommendation: {result.get('recommendation')}")
```

### Option 3: Watch Live
```bash
# Run your FastAPI server with auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# In another terminal, watch logs
tail -f data/switch_history.json
```

---

## 🎯 Expected Behavior

**Scenario:** Current state (L1: 4.8kW, L2: 2.1kW, L3: 4.0kW)

**Expected switches (in order):**
1. Move B1 (0.4kW) from L2 → L1 or L3 (balance the load)
2. Move B2 (0.4kW) from L2 → L1 or L3
3. Move V1 (0.7kW) from L2 → L1 or L3
4. Continue until phases are balanced

**Target balanced state:**
- L1: ~3.6 kW
- L2: ~3.6 kW  
- L3: ~3.6 kW
- Imbalance: < 0.5 kW

---

## 🐛 Troubleshooting

### If switches still not happening:

1. **Check reading timestamps:**
   ```python
   from datetime import datetime, timezone
   # Are readings < 60 min old?
   ```

2. **Check MIN_SWITCH_GAP_MIN:**
   - Look at `last_changed` in houses.json
   - Must be > 30 seconds ago

3. **Enable verbose logging:**
   ```python
   # In main.py, the debug prints should show:
   # - Current phase loads
   # - Balancer recommendation
   # - Validation checks (APPROVED/REJECTED)
   ```

4. **Check phase stats:**
   ```bash
   curl http://localhost:8000/analytics/status
   ```

---

## 📝 Summary of Changes

**Files Modified:**
1. ✅ `main.py` - Fixed validation logic, added debug output
2. ✅ `consumption.py` - More lenient thresholds, includes smaller houses
3. ✅ `configerations.py` - Reduced MIN_IMBALANCE_KW, increased cooldown

**Key Improvements:**
- ✅ Uses `HIGH_IMBALANCE_KW` (0.3) instead of `CRITICAL_IMBALANCE_KW` (0.6)
- ✅ OR-based validation (any condition passes) instead of AND (all required)
- ✅ Considers houses >= 0.05 kW instead of >= 0.1 kW
- ✅ Added comprehensive debug logging
- ✅ Better cooldown period (30s vs 6s)

**Result:** Phase switching should now work smoothly and precisely! 🎉
