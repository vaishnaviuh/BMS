# MiniBMS Dashboard — Block-by-Block Guide

**Project:** VisionAstraa | KLE Institute of Technology
**Version:** MiniBMS v2.0 · 3S Li-Ion · Model-Based Design

---

## Overview

The MiniBMS dashboard is a single-page web application that monitors and controls a 3-cell Li-Ion battery pack in real time. It connects to a Flask backend (or runs in built-in Demo Mode) and refreshes every second. Below is every panel explained.

---

## 1. Top Navigation Bar (Topbar)

**Location:** Sticky bar at the very top of the screen.

| Element | What it does |
|---|---|
| **MiniBMS EV** brand logo | Identifies the system; clicking does nothing — it is a label |
| **CAN / UART badges** | Show simulated communication bus status (green = active) |
| **MOTOR / CHARGER badges** | Indicate whether motor controller or charger bus is live |
| **Clock** | Real-time HH:MM:SS system clock |
| **ALARM ON / MUTED button** | Toggles audio fault alarms on or off. When a fault occurs the alarm sounds and speaks the fault name aloud |
| **Demo / Connected badge** | Green = connected to real backend, Blue = running internal simulation |
| **State Pill** | Shows the BMS state machine state: IDLE / DISCHARGE / CHARGE / FAULT |

---

## 2. Identity Bar

**Location:** Below the topbar, dark navy strip.

| Position | Content |
|---|---|
| Left | **VisionAstraa** — project/team name |
| Center | **KLE Institute of Technology** — college name, with sub-line showing platform description |
| Right | Build version and department name |

---

## 3. Boot Screen

**Shown once on page load.** Displays a startup sequence with animated log lines and a progress bar, simulating an embedded system power-on self-test. Fades out automatically after ~3 seconds and starts the dashboard.

---

## 4. API Server / URL Bar

**Location:** Top of main content area.

- **Input field:** Enter your ngrok or local server URL (e.g., `https://xxxx.ngrok-free.app`). Leave blank to run Demo Mode.
- **Connect button:** Switches from Demo to live server.
- **Demo button:** Returns to internal simulation.
- **↓ CSV button:** Downloads the last 300 seconds of data as a CSV file.

> In Demo Mode, all data is generated in the browser itself — no server is needed.

---

## 5. Vehicle System Overview — Car Side-Profile SVG

**Location:** Left half of the wide card at the top.

An animated SVG of the EV vehicle showing:

| Element | Meaning |
|---|---|
| **Battery pack rectangle** | Highlights green (normal), amber (low SOC), red (fault) |
| **BMS label** | Shows current BMS state and whether any fault is armed |
| **Motor** | Pulses when contactor is closed and discharging |
| **Charger icon** | Glows when charge mode is active |
| **Regen arrow** | Animates when current is negative (regenerative braking) |
| **Current flow arrows** | Animated dashes showing direction of current flow |

This diagram gives an instant visual of the EV's electrical state without reading numbers.

---

## 6. Battery Pack — Top Section View (3S)

**Location:** Right half of the top card.

SVG showing all 3 cells in the pack:

| Element | Meaning |
|---|---|
| **Cell circles (C1, C2, C3)** | Each cell's voltage shown numerically inside |
| **Color of circle** | Green = healthy, Blue = slightly low, Amber = caution, Red = over/under voltage |
| **dV label** | Cell imbalance — difference between max and min cell voltage in millivolts |
| **Pack Voltage** | Sum of all 3 cell voltages |
| **Current arrows** | Direction of current through pack |
| **Balancing indicators** | BAL tags light up when cell balancing is active |
| **Regen row** | Shows regenerative braking state |
| **Contactor row** | CLOSED = pack connected to load, OPEN = pack disconnected |

---

## 7. SOC HUD (State of Charge)

**Location:** Center strip below the top card.

The most important readout on the dashboard:

| Readout | Meaning |
|---|---|
| **Large % number** | Current State of Charge (0–100%), calculated via Coulomb counting |
| **SOC color** | Green (>60%), Blue (30–60%), Amber (<30%), Red (<10%) |
| **Ah remaining** | Actual amp-hours left in the pack |
| **Wh remaining** | Watt-hours left (energy remaining) |
| **SoH %** | State of Health — how much capacity remains vs. original design |
| **Cycles** | Number of full charge-discharge cycles completed |
| **TTE / TTC** | Time to Empty (discharging) or Time to Charge (charging) in minutes |

---

## 8. Cell Voltages Panel

**Location:** Left column, first card.

Displays individual cell voltages with vertical bar indicators:

| Element | Meaning |
|---|---|
| **V1 / V2 / V3 bars** | Height = voltage relative to 4.2V max |
| **Numeric voltage** | Exact voltage in volts (4 decimal places) |
| **dV (cell spread)** | Imbalance between cells in mV — should stay below 30 mV |
| **OCV per cell** | Open Circuit Voltage at current SOC from the lookup table |
| **IR mΩ** | Internal resistance in milliohms (increases with temperature extremes and aging) |

---

## 9. State Machine Panel

**Location:** Below cell voltages.

Shows the BMS operating state as a node diagram:

```
[IDLE] → [CHARGE]
       → [DISCHARGE]
       → [FAULT]
```

| State | Meaning |
|---|---|
| **IDLE** | Pack is connected but no load or charger active |
| **DISCHARGE** | Ignition ON, contactor closed, current flowing to motor |
| **CHARGE** | Charger connected, current flowing into cells |
| **FAULT** | A protection limit was exceeded — contactor opened, locked out until reset |

---

## 10. Fault Indicators Panel

**Location:** Right side, mid-section.

Four fault guards always watching:

| Fault | Trigger Condition | Threshold |
|---|---|---|
| **OV (Over-Voltage)** | Any cell voltage > 4.25 V | 4.25 V |
| **UV (Under-Voltage)** | Any cell voltage < 2.45 V | 2.45 V |
| **OT (Over-Temperature)** | Pack temperature ≥ 45 °C | 45 °C |
| **OC (Over-Current)** | Absolute current > 5.0 A | 5.0 A |

Each row shows the live reading vs. the threshold. Green = safe, Red = fault active.

When a fault fires:
1. The row turns red
2. The alarm beeps and speaks the fault name
3. A red banner appears at the top of the screen
4. The BMS state switches to FAULT and contactors open

---

## 11. Temperature / Thermal Panel

**Location:** Mid-right column.

| Element | Meaning |
|---|---|
| **Temperature bar** | Visual fill showing % of OT threshold used |
| **°C readout** | Current pack temperature |
| **HB bars (heartbeat)** | Animated health bars for voltage, current, temperature |
| **Thermal cells** | Color-coded cells showing temperature zones: Cool / Normal / Warm / Hot |

---

## 12. AI Health Monitor & Grade

**Location:** Right column, lower section.

| Element | Meaning |
|---|---|
| **Grade letter (A–F)** | Overall pack health grade based on SoH, cell spread, temperature, IR |
| **Anomaly flags** | Flags for: high cell spread, elevated temperature, high IR, degraded SoH |
| **Health bars** | Visual indicators for voltage health, thermal health, IR health |

**Grading logic:**
- **A:** SoH ≥ 95%, dV < 15 mV, temp < 35°C, IR < 100 mΩ
- **B:** SoH ≥ 90%, dV < 30 mV, temp < 40°C
- **C:** SoH ≥ 85%
- **D:** SoH ≥ 80%
- **F:** SoH < 80%

---

## 13. Range & TTE Card

**Location:** Below health panel.

| Readout | Meaning |
|---|---|
| **Est. km range** | Estimated driving range based on current SOC and power consumption |
| **Time to Empty** | How many minutes at current discharge rate until battery is flat |

---

## 14. Drive Parameters (Control Panel)

**Location:** Bottom-right control section.

| Control | Range | Meaning |
|---|---|---|
| **Current slider** | -3.0 A to +3.0 A | Positive = discharge (motor draw), Negative = regen/charge |
| **Temperature slider** | 5°C to 60°C | Simulates ambient/cell temperature |
| **Ignition toggle** | ON/OFF | Turns on drive mode (DISCHARGE state) |
| **Charger toggle** | ON/OFF | Connects charger (CHARGE state) |
| **Fault Inject** | Button | Immediately triggers all fault flags for testing |
| **Reset** | Button | Clears fault latch and returns BMS to IDLE |
| **Sport Mode** | Toggle | Visual accent; increases max current label display |

---

## 15. Event Log

**Location:** Bottom-left section.

Scrollable log of all BMS events in chronological order (newest first):

| Color | Event type |
|---|---|
| Green | OK events (charge complete, state transitions) |
| Amber | Warnings (SOC below 20%) |
| Red | Errors (fault triggered) |
| Grey | Info (startup messages) |

---

## 16. Charts Section

Four live-updating time-series graphs:

| Chart | Y-axis | What to watch for |
|---|---|---|
| **Pack Voltage** | Volts | Should stay between 7.5 V (empty) and 12.6 V (full) |
| **Current** | Amps | Positive = discharge, Negative = charge |
| **Temperature** | °C | Should stay below 45°C |
| **Cell Voltages** | Volts per cell | All 3 bars should be roughly equal |

---

## 17. OCV–SoC Curve

A reference chart showing the Open Circuit Voltage vs. State of Charge relationship for the Li-Ion cell. The moving dot shows where the pack currently sits on this curve. A flat region in the middle (3.65–3.90 V) means SOC is harder to estimate from voltage alone — this is why Coulomb counting is used.

---

## 18. IR–Temperature Curve

Shows how Internal Resistance changes with temperature. Resistance is highest at cold temperatures (130 mΩ at 5°C) and drops as the cell warms up (70 mΩ at 65°C). Cold batteries deliver less power for the same voltage because the IR drop is larger.

---

## 19. Footer

| Element | Meaning |
|---|---|
| **MiniBMS v2.0** | Version label |
| **Model-Based Design · EV Application · College Review Build** | Build tag |
| **Tick counter** | Number of simulation steps run since page load |

---

*Last updated: MiniBMS v2.0 — VisionAstraa / KLE Institute of Technology*
