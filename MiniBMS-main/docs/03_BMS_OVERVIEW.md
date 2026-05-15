# Battery Management System (BMS) — Complete Overview

**Project:** VisionAstraa | KLE Institute of Technology

---

## 1. What is a BMS?

A **Battery Management System (BMS)** is an electronic system that monitors, protects, and manages a rechargeable battery pack. It acts as the **brain** of the battery — it watches every cell's voltage, the pack's current and temperature, and makes real-time decisions to keep the battery safe, efficient, and long-lasting.

Without a BMS, a lithium battery can:
- **Catch fire** (overcharging → thermal runaway)
- **Permanently fail** (over-discharge → copper dissolution inside cell)
- **Deliver wrong information** (you think 50% charge is left but the pack is actually empty)

A BMS prevents all of this by acting as a **guardian** between the battery and the rest of the system.

---

## 2. Where is a BMS Used?

BMS technology is found in virtually every device powered by a lithium battery:

### Electric Vehicles (EVs)
- Cars: Tesla Model 3, Tata Nexon EV, Ola S1 scooter
- Buses: Olectra, Switch Mobility
- Two-wheelers and three-wheelers
- **The BMS here is critical** — packs can be 400–800 V with hundreds of cells in series/parallel

### Consumer Electronics
- Smartphones (the "battery health" percentage your phone shows = BMS data)
- Laptops (the smart battery chip inside every laptop battery pack)
- Power banks, wireless earbuds

### Energy Storage Systems (ESS)
- Home solar battery storage (e.g., Tata Power EZ Home, Luminous NXG)
- Grid-scale storage (100 MW installations for renewable energy smoothing)

### Industrial and Specialty
- Forklifts and warehouse AGVs
- Medical devices (portable ventilators, defibrillators)
- Drones and UAVs
- Aerospace (satellite power systems, Mars rovers)
- Telecom towers (backup power)

---

## 3. How Does a BMS Work?

A BMS performs several key functions simultaneously, every second the system is on:

### 3.1 Monitoring (Sensing)

The BMS continuously reads:

| Parameter | Sensor | Why |
|---|---|---|
| **Cell voltage** | Resistor divider + ADC | Detect OV / UV per cell |
| **Pack current** | Shunt resistor or Hall effect | Detect OC; needed for SOC |
| **Temperature** | NTC thermistor | Detect OT; correct IR estimation |
| **State of Charge** | Calculated (see 3.2) | Know how much energy remains |

### 3.2 State of Charge (SOC) Estimation

SOC is the "fuel gauge" of the battery — what % of charge remains.

**Method used in MiniBMS: Coulomb Counting**

```
SOC(t) = SOC(t-1) - [I × Δt / Capacity_Ah] × 100%
```

Every second, the BMS subtracts (discharge) or adds (charge) the electrons that flowed, keeping a running total. The OCV–SoC lookup table is used at startup to initialize the SOC from the resting voltage.

**Analogy:** Like a fuel meter in a car, but instead of measuring tank depth it counts every drop that flows in and out.

### 3.3 Protection

When a dangerous condition is detected, the BMS **opens the protection MOSFET switches**, disconnecting the battery from the load or charger:

| Fault | What Happens |
|---|---|
| **Over-Voltage** | Cell charged above max (4.2 V) → stops charging immediately |
| **Under-Voltage** | Cell discharged below min (2.5 V) → stops discharge immediately |
| **Over-Temperature** | Cells too hot → stops all current flow |
| **Over-Current** | Short circuit or excessive load → breaks the current path |

This protection response happens in **microseconds to milliseconds** on real hardware.

### 3.4 Cell Balancing

In a multi-cell series pack, cells naturally drift apart over time. Balancing ensures all cells are at the same voltage so the full capacity of the pack is usable.

- **Passive balancing:** Drain energy from full cells (as heat) until they match the lowest cell
- **Active balancing:** Transfer energy from high cells to low cells (more efficient)

### 3.5 State of Health (SoH) Estimation

SoH tells you how aged the battery is:

```
SoH = (Current Max Capacity / Original Capacity) × 100%
```

A new battery = 100% SoH. A battery at 80% SoH has lost 20% of its original capacity — in the EV world, 80% SoH is the threshold for battery replacement.

### 3.6 Communication

The BMS reports its data to other systems:
- **CAN bus** → Motor controller, dashboard display, charger
- **UART/Serial** → Debug output, data logging
- **SMBus** → Used in portable electronics (laptops use this)

---

## 4. Why is a BMS Required?

### 4.1 Safety — The Primary Reason

Lithium batteries are **energy-dense but chemically volatile**. Without protection:

- **Overcharging** causes lithium plating → dendrite growth → internal short circuit → fire
- **Over-discharging** causes copper dissolution → permanent capacity loss or internal short
- **Over-temperature** accelerates aging → can lead to venting, fire, or explosion
- **Short circuit** causes uncontrolled current surge → pack can explode in seconds

The BMS is the first and last line of defense against all these failure modes.

### 4.2 Longevity — Protecting Your Investment

A lithium pack for an EV costs ₹1–5 lakhs. The BMS extends pack life by:
- Preventing damage from extreme charge states
- Balancing cells so no single cell ages faster than others
- Keeping temperature in the optimal range (15–35°C for charging)

A well-managed pack can last **1,000–3,000 cycles** (8–15 years in daily use).
Without a BMS, the same pack may fail in **50–200 cycles**.

### 4.3 Accuracy — Knowing What You Have

Without SOC estimation, you have no reliable fuel gauge. The BMS gives:
- Real-time % charge
- Estimated range remaining
- Time to full charge
- Remaining energy in Wh

### 4.4 Regulatory Compliance

Many countries (including India under AIS-156 / AIS-038 standards for EVs) **legally require** a BMS in electric vehicles. It is not optional.

### 4.5 System Integration

The BMS is the interface between the battery and the rest of the vehicle:
- Tells the motor controller how much power is available
- Tells the charger when to stop, what current to use
- Reports data to the instrument cluster

---

## 5. BMS Classification

### By Number of Cells Supported
| Class | Cells | Application |
|---|---|---|
| Small | 1S–3S | Power banks, small tools |
| Medium | 4S–16S | E-bikes, scooters |
| Large | 16S–96S+ | Cars, buses, grid storage |

### By Architecture
| Type | Description |
|---|---|
| **Centralized** | One BMS board handles all cells. Simple but long wiring harness |
| **Distributed** | A small board on each cell/module. Modular, used in large packs |
| **Modular** | Groups of cells managed together, modules talk to a master BMS |

---

## 6. BMS in the Context of MiniBMS

MiniBMS is an academic, model-based design BMS that implements the core functions of a real BMS:

| Function | MiniBMS Implementation |
|---|---|
| Voltage monitoring | Per-cell voltage simulation with OCV lookup |
| Current monitoring | Commanded current with fault detection at 5A |
| Temperature monitoring | Commanded temperature with OT fault at 45°C |
| SOC estimation | Coulomb counting, updated every 1 second |
| SoH estimation | Degradation model based on cycle count and time |
| Protection | State machine locks to FAULT, zero current, contactor open |
| Balancing | Simulated via cell dV monitoring |
| Communication | REST API (HTTP) replacing CAN/UART in hardware |
| Display | HTML dashboard replacing instrument cluster |

The MATLAB Simulink model (`MiniBMS.slx`) generates the control algorithm, and the Python Flask server (`app.py`) implements the equivalent real-time processing for deployment.

---

## 7. Key Terms Glossary

| Term | Full Form | Meaning |
|---|---|---|
| BMS | Battery Management System | The overall protection and monitoring system |
| SOC | State of Charge | Current charge level (%) |
| SoH | State of Health | Remaining capacity vs. original (%) |
| OCV | Open Circuit Voltage | Cell voltage at rest (no current flowing) |
| IR | Internal Resistance | Resistance inside the cell |
| OV | Over-Voltage | Cell voltage above max safe limit |
| UV | Under-Voltage | Cell voltage below min safe limit |
| OT | Over-Temperature | Cell temperature above safe limit |
| OC | Over-Current | Current above safe limit |
| TTE | Time to Empty | Estimated minutes until pack is flat |
| TTC | Time to Charge | Estimated minutes until pack is full |
| dV | Delta Voltage | Voltage difference between cells |
| CC | Coulomb Counting | SOC tracking by integrating current over time |
| CC-CV | Constant Current – Constant Voltage | Standard Li-Ion charging protocol |
| NTC | Negative Temp. Coefficient | Type of thermistor (resistance drops with heat) |
| MOSFET | Metal-Oxide-Semiconductor FET | Electronic switch used as a contactor |
| CAN | Controller Area Network | Vehicle communication bus standard |

---

*Document: BMS Overview — MiniBMS v2.0*
*VisionAstraa | KLE Institute of Technology*
