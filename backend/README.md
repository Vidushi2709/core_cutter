# 🚀 Quick Start

### **Run the example**

```
python .\app.py
```

This will:

* Load some example readings
* Detect whether it is DAY or NIGHT mode
* Run that logic
* Print recommended switches (if any)

> ⚠ Later, `app.py` will be replaced with a FastAPI backend.

---

# 📁 Folder & File Guide (Simple Explanation)

Below is a clear explanation of **what each file does** and **why it exists**.

---

# 1️⃣ **`app.py` — The Demo Runner**

* Runs a sample scenario (morning or night)
* Prints out which house should move from which phase
* Helps you understand how the logic behaves

**Basically:** *Press a button → see results.*

---

# 2️⃣ **`configerations.py` — All Tunable Settings**

Contains simple constants that control how the system behaves, such as:

* List of phases: `["L1", "L2", "L3"]`
* How long a house must wait before switching again
* Minimum improvement needed before switching a house
* Voltage thresholds
* Export threshold to detect DAY mode

**Basically:** *All “settings” in one place.*

---

# 3️⃣ **`utility.py` — The Heart of the System**

This file contains **all core data models + core calculations** used everywhere.

## 📦 Dataclasses (simple data containers)

These are like small structured boxes holding information:

### **`ReadingOfEachHouse`**

* voltage
* power in kW
* timestamp

### **`HouseState`**

* which phase the house is on
* when it last switched
* its latest reading

### **`PhaseStats`**

* total load/export on a phase
* average voltage
* number of houses contributing

### **`RecommendedSwitch`**

* which house to move
* from → to which phase
* improvement amount
* why it was recommended

---

## 🏠 `HouseRegistry` — Stores all houses & their states

Keeps track of:

* which house is on which phase
* when it last switched
* latest voltage/power reading

### Important functions:

* **`add_house`** → register a new house
* **`update_reading`** → update voltage/power data
* **`apply_switch`** → move house to another phase

**Basically:** *Database of houses (in memory).*

---

## 📊 `PhaseRegistry` — Understands the Grid Condition

Calculates the **current health of each phase**:

* total power
* average voltage
* count of houses

Also has functions to:

* detect DAY vs NIGHT mode
* detect over/under voltage
* calculate imbalance

**Basically:** *Reads data from HouseRegistry and tells us what’s happening on the grid.*

---

# 4️⃣ **`morning_logic.py` — Daytime Balancing (Solar Export Mode)**

When solar panels cause high voltage, this logic tries to fix imbalance by moving **heavy exporters** to weaker phases.

### Functions:

* **`get_candidate_house`**

  * finds houses exporting > 0.1 kW
  * filters stale readings
  * filters recently switched houses
  * sorts exporters from largest → smallest

* **`find_best_switch`**

  * tries moving each house to each of the other phases
  * simulates the effect
  * picks the best improvement

**Basically:** *Move the biggest solar exporter away from overloaded phases.*

---

# 5️⃣ **`night_logic.py` — Night Balancing (Consumption Mode)**

At night, houses **consume** more than they export.
Voltage drops due to heavy loads.

This logic detects **large consumers** and tries to move them to reduce under-voltage issues.

### Functions:

* **`get_candidate_house`**

  * houses with negative power (load)
  * the most consuming houses first

* **`find_best_switch`**

  * similar to morning logic
  * but for consumers instead of exporters

**Basically:** *Fix night-time low voltage by spreading out the heavy loads.*

---

# 🔄 How All Files Work Together (Simple Overview)

1. IoT device sends voltage + power reading
2. `HouseRegistry` saves it
3. `PhaseRegistry` analyzes all readings
4. It figures out:

   * DAY or NIGHT
   * if voltage is too high or low
   * which phase is overloaded
5. Based on mode:

   * `MorningLogic` runs (export balancing)
   * or `NightLogic` runs (load balancing)
6. A smart phase switch recommendation is returned
7. `HouseRegistry.apply_switch()` updates the house’s phase
---

### To run the fastapi server: 

python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000