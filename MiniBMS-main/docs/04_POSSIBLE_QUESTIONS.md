# MiniBMS — Possible Viva & Review Questions

**Project:** VisionAstraa | KLE Institute of Technology
**Coverage:** Fundamentals, project-specific, hardware, software, and advanced questions

---

## SECTION A — BMS Fundamentals

**Q1. What is a Battery Management System (BMS)?**
A BMS is an electronic system that monitors, protects, balances, and manages a rechargeable battery pack. It continuously reads cell voltages, current, and temperature, and takes protective actions (like opening MOSFETs) when unsafe conditions are detected.

---

**Q2. Why is a BMS essential for lithium-ion batteries?**
Lithium-ion cells are chemically unstable outside safe operating limits. Overcharging causes dendrite growth and fire risk. Over-discharging causes permanent copper dissolution inside the cell. Over-temperature accelerates aging and can cause thermal runaway. The BMS prevents all these failure modes.

---

**Q3. What is State of Charge (SOC)?**
SOC is the ratio of current charge to maximum possible charge, expressed as a percentage. SOC = 100% means fully charged; SOC = 0% means fully discharged. It is analogous to a fuel gauge.

---

**Q4. What is State of Health (SoH)?**
SoH represents the current capacity of the battery as a percentage of its original rated capacity.
`SoH = (Current Max Capacity / Original Capacity) × 100%`
A battery at 80% SoH is considered end-of-life for most EV applications.

---

**Q5. What is Open Circuit Voltage (OCV)?**
OCV is the voltage measured across a battery cell when no current is flowing (at rest). It has a predictable relationship with SOC, captured in an OCV–SoC lookup table. MiniBMS uses this table to initialize SOC at startup.

---

**Q6. What is Coulomb Counting and how does it work?**
Coulomb counting (also called current integration) tracks SOC by integrating the current over time:
`ΔSOC = (I × Δt / Capacity_Ah) × 100%`
Every second, the measured current is multiplied by the time step and divided by the rated capacity. This gives the change in charge, which is added or subtracted from the SOC.

---

**Q7. What are the limitations of Coulomb counting?**
- It accumulates error over time (sensor noise, drift)
- Needs accurate initial SOC (from OCV measurement at startup)
- Accuracy degrades if current sensor has offset error
- For this reason, many systems combine Coulomb counting with OCV correction (Kalman filtering in advanced BMS)

---

**Q8. What is Internal Resistance (IR) of a battery?**
IR is the opposition to current flow inside the cell itself, caused by electrolyte resistance and electrode interfaces. It causes a voltage drop under load: `V_terminal = OCV − I × IR`. High IR means less voltage reaches the load — cold or aged batteries have higher IR, reducing available power.

---

**Q9. What is thermal runaway?**
Thermal runaway is a self-accelerating process in lithium cells where heat causes chemical reactions that produce more heat, leading to catastrophic failure (venting, fire, explosion). It is triggered by overcharging, short circuits, crushing, or overheating. The BMS prevents it by enforcing temperature and voltage limits.

---

**Q10. What is cell balancing and why is it needed?**
In a series string, cells naturally develop different SOCs over time due to manufacturing variation and uneven aging. Balancing ensures all cells reach full charge (or empty) together, maximizing usable capacity. Without balancing, the weakest cell determines when charging stops, wasting the remaining capacity of stronger cells.

---

**Q11. Explain passive vs active cell balancing.**
- **Passive:** Energy from the highest cell is dissipated as heat through a resistor. Simple and cheap but wastes energy.
- **Active:** Energy is transferred from high cells to low cells using inductors, capacitors, or DC-DC converters. More efficient but more complex and expensive. Used in premium EV packs.

---

**Q12. What is the CC-CV charging protocol?**
CC-CV (Constant Current – Constant Voltage) is the standard method for charging Li-Ion cells:
1. **CC phase:** Charger supplies a fixed current (e.g., 1C rate) until the cell reaches its maximum voltage (4.2 V)
2. **CV phase:** Charger holds voltage at 4.2 V and current tapers down naturally as the cell fills
3. Charging ends when current drops below a cutoff threshold (typically C/20 or C/10)

---

## SECTION B — MiniBMS Project-Specific Questions

**Q13. What does 3S mean in your project?**
3S means 3 cells connected in **series**. This triples the voltage while keeping the capacity the same.
- Nominal voltage: 3 × 3.7 V = 11.1 V
- Max voltage: 3 × 4.2 V = 12.6 V
- Capacity: 4.3 Ah (same as a single cell)
- Energy: 11.1 V × 4.3 Ah = 47.7 Wh

---

**Q14. What faults does MiniBMS protect against?**
MiniBMS monitors four fault conditions:

| Fault | Threshold |
|---|---|
| Over-Voltage (OV) | > 4.25 V per cell |
| Under-Voltage (UV) | < 2.45 V per cell |
| Over-Temperature (OT) | ≥ 45°C |
| Over-Current (OC) | |current| > 5.0 A |

---

**Q15. What happens when a fault is detected?**
1. The BMS state machine transitions to the **FAULT** state
2. The contactor MOSFET switches open → current drops to 0 A immediately
3. A fault latch is set (nrst = True) — blocks auto-recovery
4. The fault type and value are logged in the event log
5. The dashboard displays the fault, the alarm sounds, and a banner appears
6. The system remains in FAULT until a manual reset command is sent

---

**Q16. Why does the fault require a manual reset?**
This is a safety design principle called a **latching fault**. If the system automatically recovered after a fault, it could cycle into unsafe states repeatedly (e.g., repeatedly trying to discharge into a short circuit). The latch forces a human to acknowledge the fault before resuming operation, preventing potential damage or fire.

---

**Q17. How does MiniBMS calculate SOC?**
Using **Coulomb counting** updated every 1 second:
- In DISCHARGE: `SOC = SOC − (I / 4.3 Ah) × 100 × (1s / 3600s)`
- In CHARGE: `SOC = SOC + (I / 4.3 Ah) × 100 × (1s / 3600s)`
Initial SOC is set at 72% for demo purposes. On real hardware, it would be read from the OCV at startup.

---

**Q18. Why is the UI current slider limited to 3 A?**
The slider range is set to ±3 A as a safe operating range for the demo and college review build. The actual overcurrent fault threshold is 5 A. The 3 A limit is a conservative design choice to demonstrate normal operation without accidentally triggering faults during a presentation.

---

**Q19. What is the BMS state machine? Explain each state.**
The BMS uses a 4-state machine:
- **IDLE:** Pack connected, no load or charger active. Safe standby state.
- **DISCHARGE:** Ignition ON, contactor closed, current flows from pack to motor.
- **CHARGE:** Charger connected, current flows into cells. SOC increases.
- **FAULT:** A protection limit was exceeded. Contactor open, zero current, locked until reset.

Transitions:
- IDLE → DISCHARGE: when ignition is turned ON and no faults exist
- IDLE → CHARGE: when charger is connected
- DISCHARGE/CHARGE → FAULT: when any fault threshold is crossed
- FAULT → IDLE: only after explicit reset command

---

**Q20. What is the role of the Flask server in MiniBMS?**
The Flask server (`app.py`) acts as the **BMS backend**. It:
- Runs the BMS simulation (state machine, Coulomb counting, fault detection) in a background thread
- Exposes REST API endpoints (e.g., `/api/live`, `/api/faults`, `/api/control`)
- The HTML dashboard fetches data from these endpoints every second
- In real hardware, this would be replaced by the embedded MCU firmware

---

**Q21. What does ngrok do in the Colab setup?**
ngrok creates a **secure public tunnel** from the internet to the Flask server running inside Google Colab (which has no public IP). The ngrok URL (e.g., `https://abcd-1234.ngrok-free.app`) can be entered into the dashboard so it can reach the backend from any browser anywhere.

---

**Q22. What is OCV and how is it used in your project?**
OCV (Open Circuit Voltage) is the resting voltage of a cell. MiniBMS stores an OCV–SoC lookup table for the 3S Li-Ion cell. During simulation:
- `ocv_fn(soc)` interpolates the table to get the expected cell voltage at the current SOC
- Cell voltages are then computed as: `V_cell = OCV + small_offset − I × R_internal`
- The dashboard plots the OCV curve and shows a moving dot at the operating point

---

**Q23. How does the dashboard work without a server (Demo Mode)?**
In Demo Mode, the entire BMS simulation runs **inside the browser** in JavaScript. The same OCV table, IR table, Coulomb counting, and state machine logic implemented in Python is replicated in JS. When you click Demo, the JavaScript sim runs at 1 Hz, exactly like the Python backend, so the dashboard is fully functional without any server.

---

**Q24. What is the significance of the OCV–SoC curve shape?**
The Li-Ion OCV–SoC curve has a flat middle region (3.65–3.90 V across 20–80% SOC). This means voltage alone cannot reliably distinguish between 30% and 70% SOC — they look almost the same. This is why Coulomb counting is needed; voltage measurement alone is not sufficient for accurate SOC estimation in the mid-range.

---

**Q25. What does internal resistance tell you about battery health?**
IR increases as the battery ages. A new cell has low IR; an aged cell has high IR. High IR causes:
- Greater voltage drop under load → less effective capacity
- More heat generated during charge/discharge (P = I² × R)
Monitoring IR increase over cycles is one of the most reliable indicators of battery degradation.

---

## SECTION C — Hardware & Electronics Questions

**Q26. Why are two MOSFETs used in a BMS (charge and discharge)?**
One MOSFET alone can only block current in one direction because of the body diode. Using two back-to-back MOSFETs allows the BMS to block both charge and discharge current independently, giving full control over both current paths.

---

**Q27. What type of sensor is typically used for temperature in a BMS?**
An **NTC (Negative Temperature Coefficient) thermistor**. Its resistance decreases as temperature increases. Connected in a voltage divider, the ADC reading changes predictably with temperature, which is then converted to °C using the Steinhart-Hart equation or a lookup table.

---

**Q28. What is a shunt resistor and how is it used for current measurement?**
A shunt resistor is a very low resistance (e.g., 5–10 mΩ) placed in series with the battery pack. By Ohm's Law: `V = I × R`, measuring the tiny voltage across the shunt and dividing by its known resistance gives the current. A differential amplifier (e.g., INA219, INA226) amplifies this small voltage for the ADC.

---

**Q29. What is CAN bus and why is it used in EVs?**
Controller Area Network (CAN) is a robust serial communication protocol designed for vehicles. In an EV:
- BMS sends SOC, fault status, temperature to the VCU (Vehicle Control Unit)
- The VCU sends power limits back to the BMS
- CAN is used because it is fault-tolerant, supports multiple nodes, works reliably in high-noise environments, and is mandated by automotive standards

---

**Q30. What is the difference between 3S and 3P configurations?**
- **3S (series):** Cells connected in series. Voltage triples, capacity stays same.
  - 3 × 3.7 V = 11.1 V, same Ah
- **3P (parallel):** Cells connected in parallel. Voltage stays same, capacity triples.
  - 3.7 V, 3 × 4.3 Ah = 12.9 Ah
- **3S2P:** 3 cells in series, 2 strings in parallel. Doubles both current capability and energy.

---

## SECTION D — Advanced & Application Questions

**Q31. What is the Kalman Filter and why is it used in advanced BMS?**
The Kalman Filter is a mathematical algorithm that optimally combines noisy measurements (OCV, current sensor) with a model prediction to estimate the true state (SOC). It corrects for Coulomb counting drift by periodically anchoring the estimate to the OCV measurement. It is used in production-grade BMS in EVs like Tesla.

---

**Q32. What is thermal runaway propagation and how is it prevented?**
In a large pack, one cell going into thermal runaway can trigger adjacent cells (the heat ignites the electrolyte in neighboring cells). Prevention:
- Fireproof barriers between cell groups
- Temperature-triggered cooling
- BMS shuts down the entire pack at early temperature rise
- Cell venting channels direct hot gases away from other cells

---

**Q33. What are the AIS standards relevant to EV BMS in India?**
- **AIS-156:** Safety requirements for Li-Ion traction batteries in EVs
- **AIS-038 Rev. 2:** Specific requirements for electric two-wheelers and three-wheelers
These standards mandate battery protection circuits (i.e., a BMS), thermal management, and state-of-charge reporting as requirements for EV certification in India.

---

**Q34. What is C-rate?**
C-rate describes charging/discharging current relative to capacity:
- **1C rate** for a 4.3 Ah cell = 4.3 A (full charge/discharge in 1 hour)
- **0.5C** = 2.15 A (2 hours)
- **2C** = 8.6 A (30 minutes, but stressful for the cell)
Fast charging uses 2C–4C; gentle overnight charging uses 0.2C–0.5C.

---

**Q35. Why does battery range decrease in winter?**
At low temperatures:
- IR increases dramatically (e.g., 95 mΩ at 25°C vs 130 mΩ at 5°C)
- The voltage drop under load (I × R) is larger → battery appears empty sooner
- Chemical reaction rates inside the cell slow down, reducing effective capacity
- Some EVs pre-heat the battery pack before driving in winter to restore range

---

**Q36. What is the difference between energy density and power density?**
- **Energy density** (Wh/kg): How much energy the battery stores per kg. Determines range.
- **Power density** (W/kg): How fast the battery can deliver energy per kg. Determines acceleration.
Li-Ion has high energy density; supercapacitors have high power density. Some EVs use both (hybrid energy storage).

---

**Q37. Can your MiniBMS be extended to real hardware? What would you change?**
Yes. To deploy on real hardware:
1. Replace the Python simulation with embedded C firmware (on STM32 or Arduino)
2. Connect real voltage dividers, NTC thermistors, and current shunt
3. Replace the Flask REST API with CAN bus messages
4. Add BQ76920 or similar analog front-end IC for accurate cell voltage measurement
5. Add a dedicated charger IC for CC-CV charging control
6. The MATLAB Simulink model (`MiniBMS.slx`) can generate embedded C code directly using Embedded Coder toolbox

---

**Q38. What is the role of Model-Based Design in this project?**
Model-Based Design (MBD) is a development methodology where the system is first designed and simulated as a mathematical model (in MATLAB/Simulink), and then the model is automatically converted to code for the target hardware. In MiniBMS:
- The Simulink model defines the BMS algorithm (state machine, SOC estimator, protection logic)
- The model is simulated and validated in MATLAB
- The Python code replicates the same logic for the web backend
- In production, MATLAB Embedded Coder would generate C code directly from the Simulink model

---

**Q39. What would you improve in MiniBMS if given more time?**
- Implement Extended Kalman Filter (EKF) for more accurate SOC estimation
- Add CC-CV charging algorithm with automatic charger cutoff
- Implement active cell balancing
- Add data logging to a database (SQLite/PostgreSQL)
- Deploy on real hardware (STM32 + BQ76920)
- Add CAN bus communication to interface with motor controller
- Add battery aging model for more accurate SoH estimation

---

**Q40. What is Second Life Battery usage?**
When an EV battery reaches ~80% SoH, it is no longer suitable for the performance demands of an EV. However, it still has 80% of its original capacity, which is perfectly usable for less demanding applications like home energy storage, UPS systems, or solar storage. This "second life" reduces waste and lowers the cost of stationary energy storage.

---

*Document: Possible Viva & Review Questions — MiniBMS v2.0*
*VisionAstraa | KLE Institute of Technology*
*40 questions covering fundamentals, project-specific topics, hardware, and advanced concepts*
