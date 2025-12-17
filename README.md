```
(｡•̀ᴗ-)✧  ⚡  🌞  ⚙️
```

# Dynamic Phase Balancing in Distribution Feeders

```
╭──────────────────────────────╮
│  Dynamic • Smart • Balanced  │
│  Power Distribution System   │
╰──────────────────────────────╯
```

---

## Problem Statement

Rooftop solar panels are doing great… except they’ve made distribution feeders wildly unbalanced, especially with small single-phase systems causing voltage tantrums.

This project builds a smart IoT and edge-based controller that keeps the phases calm, balanced, and solar-friendly by dynamically shifting loads in real time.

---

## Solution Overview

```
( •̀ ω •́ )✧  Smart control at the edge
```
The system acts like a tiny but very serious traffic cop for electricity, sitting at distribution feeder nodes. It constantly watches real-time load and solar data on each phase, spots trouble (aka imbalance), and decides when it’s time to switch phases before things get messy.

The solution is built with:

- Simplicity – no overthinking

- Reliability – no random decisions

- Low-cost deployment – no budget panic

so it can actually survive in the real world.

Core Components

- Real-time telemetry (because guessing is bad)

- Rule-based logic with a little ML help (brains + experience)

- Automatic phase switching logs and alerts (no secrets)

- Simple dashboards (easy on the eyes)

The overall architecture is modular, edge-ready, and always paying attention... so the grid doesn’t have to.

---

## High-Level Architecture

```
   ☀️  Telemetry (IoT / Smart Meters)
                ↓
        📦 Edge Data Storage
                ↓
      ⚙️ Phase Analysis Engine
                ↓
        🤖 ML Assistance (Optional)
                ↓
     🔁 Phase Switching + Alerts
                ↓
        📊 Dashboard / Logs
```

---

## Project Structure Explained

```
├── alert_system/           # An alert gets sent to the person incharge abou the imbalance (why? no idea, lol)
│
├── backend/                # Core backend logic (aka entire reason of my eye bags)
│   ├── __init__.py
│   ├── app.py              # Application entry / API bootstrap
│   ├── main.py             # Main controller runner
│   ├── configurations.py  # System thresholds and constants
│   ├── consumption.py     # Load and PV consumption calculations
│   ├── export.py           # Data export utilities
│   ├── utility.py          # Common helper functions
│
├── data/                   # Edge-level persistent data (simulated) (ik you must be thinking json? ew! but eh idc)
│   ├── telemetry.json      # Phase-wise telemetry
│   ├── houses.json         # House-to-phase mappings
│   ├── alerts.json         # Generated alerts
│   ├── switch_history.json # Phase switching audit trail
│
├── frontend/               # Visualization layer (it is literally ai slop, don't come at me plz)
│   ├── dashboard.html      # Main dashboard
│
├── ml/                     # Machine Learning components (data is syntethic, not the best just a small model to show)
│   ├── __init__.py
│   ├── generate_datasets.py
│   ├── ml_predictor.py
│   ├── ml_integration.py
│   ├── train_and_save_model.py
│   ├── phase_balancing_model.pkl
│   ├── phase_balancing_training_data.csv
│   ├── phase_balancing_test_data.csv
│   └── model.ipynb
│
├── tests/                  # Validation and testing (my bestie files) 
│
└── README.md
```

---

## How the System Works (Simplified Flow)

```
(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧  Step by step
```

### 1. Telemetry Ingestion

Smart meters or IoT devices provide phase-wise data such as load, voltage, and solar injection. In this project, telemetry is **simulated** and stored locally in JSON files to represent edge-level data storage.

---

### 2. Phase Imbalance Detection

The controller continuously monitors:

* Load differences across phases
* Voltage limit violations
* Uneven solar power injection

When imbalance exceeds predefined safe limits, corrective action is triggered.

---

### 3. Dynamic Phase Balancing

Single-phase consumers are shifted between phases to balance the load.

All switching actions are:

* Safety-checked
* Logged for traceability
* Stored in `switch_history.json`

---

### 4. ML-Assisted Decision Support

```
🤖 but make it helpful, not risky
```

Machine learning is used as a **decision-support layer** to:

* Suggest optimal phase movements
* Reduce unnecessary switching
* Improve long-term balancing behavior

Rule-based logic remains the primary control mechanism. (currently not being used)

---

### 5. Alerts and Monitoring

Alerts are generated for:

* Severe phase imbalance
* Frequent switching events
* Voltage violations

SMS alert functionality is demonstrated using Twilio (testing only). (My sms box is filled with this now, help me)

---

### 6. Visualization

HTML dashboards provide a clear view of:

* Phase-wise loading conditions
* Switching actions taken
* Active alerts and system health
(it started flickering in front of the judges for some reason and i madeup some issue like this happens coz blehhh, and they bought it)
---

## Key Features

```
✨ What makes it cool
```

* Dynamic phase reconfiguration
* Improved voltage profile and power quality
* Increased rooftop solar hosting capacity
* Edge-compute friendly and low-cost
* Fully auditable switching history
* ML-ready modular design

---

## Technology Stack

* **Backend:** Python
* **Data Storage:** JSON (edge-simulated)
* **Frontend:** HTML / JavaScript
* **Machine Learning:** scikit-learn

---

## Future Enhancements

```
🚀 where this can go next
```

* Integration with real smart meters and RTUs
* Deployment on embedded edge devices
* Reinforcement learning–based optimization
* Three-phase inverter coordination
* SCADA / utility system integration

---

## Conclusion

```
(๑•̀ㅂ•́)و✧  Mission accomplished
```

This project shows a smart and practical way to keep power phases from fighting each other. Using edge intelligence, real-time monitoring, and a little ML magic, it improves power quality while letting more solar join the party.

okay, bye ༼ つ ◕_◕ ༽つ
