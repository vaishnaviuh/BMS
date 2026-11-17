# MiniBMS Backend — Setup Guide

> **Credit:** The Simulink BMS model is based on [MiniBMS by ks-santosh](https://github.com/ks-santosh/MiniBMS) (MIT License, see `MiniBMS-main/LICENSE`). My additions: the EV dashboard, the Flask/Colab backend, the MATLAB export script and the docs.

## Files in this package

| File | Purpose |
|---|---|
| `COLAB_PASTE_THIS.py` | **← Start here.** Paste into Google Colab, run, get URL |
| `app.py` | Full annotated Flask server (local or cloud deploy) |
| `MiniBMSExport.m` | MATLAB script to export Simulink workspace → JSON/CSV |
| `requirements.txt` | pip packages for local install |

---

## Option A — Google Colab (easiest, no setup)

1. Go to **https://colab.research.google.com**
2. Create a new notebook
3. Open `COLAB_PASTE_THIS.py`, select all, copy
4. Paste into a single code cell in Colab
5. Press **Shift+Enter** to run
6. Wait ~30 seconds — you will see output like:

```
==============================================================
  MiniBMS Backend is LIVE!

  Public URL  →  https://abcd-1234.ngrok-free.app
  Live data   →  https://abcd-1234.ngrok-free.app/api/live
  History     →  https://abcd-1234.ngrok-free.app/api/history?n=60
  Control     →  POST https://abcd-1234.ngrok-free.app/api/control
  Export CSV  →  https://abcd-1234.ngrok-free.app/api/export/csv

  Copy the Public URL into your dashboard's API_BASE.
==============================================================
```

7. Copy the `Public URL` into your dashboard

---

## Option B — Run locally

```bash
pip install -r requirements.txt
python app.py
# Server runs at http://localhost:5000
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/live` | Latest snapshot — all signals |
| GET | `/api/history?n=60` | Last N snapshots |
| GET | `/api/cells` | 3 cell voltages, OCV, IR |
| GET | `/api/soc` | SOC, SoH, Ah, Wh, TTE |
| GET | `/api/faults` | All 4 fault flags |
| GET | `/api/state` | BMS state machine status |
| GET | `/api/events?n=20` | Event log |
| POST | `/api/control` | Send commands (see below) |
| GET | `/api/export/csv` | Download history as CSV |
| GET | `/api/ocv_table` | OCV–SoC lookup table |
| GET | `/api/ir_table` | IR–Temperature table |

---

## POST /api/control — Command body

```json
{
  "current":      2.5,
  "temperature":  30,
  "ignition":     true,
  "charger":      false,
  "fault_inject": false,
  "reset":        false
}
```

- `current`: positive = discharge, negative = charge (Amps)
- `temperature`: cell temperature in °C
- `ignition`: true/false — turns on drive mode
- `charger`: true/false — connects charger
- `fault_inject`: true — triggers immediate fault
- `reset`: true — resets fault latch, returns to IDLE

---

## Connect the Dashboard

In the dashboard widget, set `API_BASE` to your ngrok URL:

```javascript
const API_BASE = "https://your-ngrok-url.ngrok-free.app";

// Fetch live data every second
setInterval(async () => {
  const res = await fetch(API_BASE + "/api/live");
  const data = await res.json();
  // data.soc_pct, data.pack_voltage, data.bms_state, etc.
}, 1000);
```

---

## MATLAB Export

After running MiniBMS.slx simulation in MATLAB:

```matlab
>> MiniBMSVariables    % load parameters first
>> sim('MiniBMS')      % run simulation
>> MiniBMSExport       % export to JSON + CSV
```

This creates `minibms_export.json` and `minibms_export.csv` with all
Simulink output workspace signals in the exact format the API serves.
