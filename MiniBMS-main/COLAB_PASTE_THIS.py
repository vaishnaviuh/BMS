# ╔══════════════════════════════════════════════════════════════════════╗
# ║  MiniBMS — Google Colab Server                                       ║
# ║  PASTE THIS ENTIRE FILE into ONE Colab code cell, then press Run     ║
# ║  A public URL will appear. Copy it into your dashboard.              ║
# ╚══════════════════════════════════════════════════════════════════════╝

# ── Install ──────────────────────────────────────────────────────────────
import subprocess, sys
subprocess.run([sys.executable,"-m","pip","install","flask","flask-cors","pyngrok","-q"])

# ── Imports ───────────────────────────────────────────────────────────────
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import time, random, threading
from collections import deque

app = Flask(__name__)
CORS(app)

# ── MiniBMS Parameters (MiniBMSVariables.m) ───────────────────────────────
CAP_AH=4.3; NOMINAL_V=11.1
V_MIN=2.5; V_MAX=4.2
FAULT_OV=4.25; FAULT_UV=2.45; FAULT_OT=45.0; FAULT_OC=5.0
DT=1.0; HIST=300

OCV_SOC=[(0,2.50),(10,3.30),(20,3.56),(30,3.65),(40,3.72),
         (50,3.78),(60,3.84),(70,3.90),(80,3.96),(90,4.05),(100,4.20)]
IR_TEMP=[(5,130),(15,110),(25,95),(35,82),(45,75),(55,72),(65,70)]

def interp(tbl,x):
    if x<=tbl[0][0]: return tbl[0][1]
    if x>=tbl[-1][0]: return tbl[-1][1]
    for i in range(1,len(tbl)):
        if x<=tbl[i][0]:
            f=(x-tbl[i-1][0])/(tbl[i][0]-tbl[i-1][0])
            return tbl[i-1][1]+(tbl[i][1]-tbl[i-1][1])*f
    return tbl[-1][1]

ocv=lambda s:interp(OCV_SOC,s)
ir =lambda t:interp(IR_TEMP,t)/1000.0

# ── BMS Simulator ─────────────────────────────────────────────────────────
class BMS:
    def __init__(self):
        self.soc=72.0;self.state="IDLE";self.tick=0
        self.ign=False;self.chg=False
        self.finj=False;self.nrst=False
        self.icmd=0.0;self.tcmd=28.0;self.cyc=0
        self.ev=deque(maxlen=100);self.hist=deque(maxlen=HIST)
        self._l=threading.Lock()
        self._e("MiniBMS started — IDLE")
        self._e(f"3S Li-Ion · {CAP_AH}Ah · OCV lookup active")

    def _e(self,msg,lv="info"):
        self.ev.appendleft({"tick":self.tick,"time":round(self.tick*DT,1),"msg":msg,"level":lv})

    def step(self):
        with self._l:
            self.tick+=1
            i=self.icmd;tc=self.tcmd
            r=ir(tc);oc=ocv(self.soc)
            cells=[round(max(V_MIN-.1,min(V_MAX+.1,oc+d+(random.random()-.5)*.012-i*r)),4)
                   for d in [0,.008,-.006]]
            pv=round(sum(cells),4)
            vf=any(v>FAULT_OV or v<FAULT_UV for v in cells) or self.finj
            tf=tc>=FAULT_OT or self.finj
            cf=abs(i)>FAULT_OC
            af=vf or tf or cf
            if af and self.state in("DISCHARGE","CHARGE"):
                r2=[]
                if vf:r2.append("voltage")
                if tf:r2.append(f"temp {round(tc)}°C")
                if cf:r2.append(f"OC {abs(i):.1f}A")
                self._e(f"FAULT: {', '.join(r2)}","error")
                self.state="FAULT";self.nrst=True
            if self.state=="IDLE" and not self.nrst:
                if self.chg:
                    if self.state!="CHARGE":self.state="CHARGE";self._e("→ CHARGE","ok")
                elif self.ign and not af:
                    if self.state!="DISCHARGE":self.state="DISCHARGE";self._e("→ DISCHARGE","ok")
            if self.state=="DISCHARGE" and not self.ign:self.state="IDLE"
            if self.state=="CHARGE" and not self.chg:self.state="IDLE"
            ai=0.0 if self.state in("IDLE","FAULT") else i
            ps=self.soc
            if self.state=="DISCHARGE":self.soc=max(0,self.soc-(ai/CAP_AH)*100*(DT/3600))
            elif self.state=="CHARGE":self.soc=min(100,self.soc+(abs(ai)/CAP_AH)*100*(DT/3600))
            if ps>20 and self.soc<=20:self._e("SOC warning: below 20%","warning")
            if ps<100 and self.soc>=99.9 and self.state=="CHARGE":
                self.cyc+=1;self._e(f"Cycle #{self.cyc} complete","ok")
            ah=round(self.soc*CAP_AH/100,4)
            snap={
                "tick":self.tick,"timestamp":round(self.tick*DT,2),
                "bms_state":self.state,"contactor":self.state in("DISCHARGE","CHARGE"),
                "ignition":self.ign,"charger":self.chg,
                "pack_voltage":pv,"current_A":round(ai,3),
                "power_W":round(abs(pv*ai),3),
                "soc_pct":round(self.soc,3),"ah_remaining":ah,
                "wh_remaining":round(ah*NOMINAL_V,3),
                "wh_total":round(CAP_AH*NOMINAL_V,2),
                "soh_pct":round(max(80,96-self.tick*.0005),2),
                "cycles":self.cyc,"cell_voltages":cells,
                "cell_dv_mv":round((max(cells)-min(cells))*1000,2),
                "ocv_per_cell":round(oc,4),"ir_mohm":round(r*1000,2),
                "temperature_C":round(tc,2),
                "fault_voltage":vf,"fault_temp":tf,
                "fault_overcurrent":cf,"fault_contactor":self.state=="FAULT",
                "any_fault":af,
                "tte_min":round(ah/ai*60,1) if self.state=="DISCHARGE" and ai>0
                    else round((CAP_AH-ah)/abs(ai)*60,1) if self.state=="CHARGE" and ai<0 else None
            }
            self.hist.append(snap);return snap

    def latest(self):
        with self._l:return dict(self.hist[-1]) if self.hist else {}
    def history(self,n=60):
        with self._l:return list(self.hist)[-n:]
    def events(self,n=20):
        with self._l:return list(self.ev)[:n]
    def ctrl(self,**kw):
        with self._l:
            if "current"     in kw:self.icmd=float(kw["current"])
            if "temperature" in kw:self.tcmd=float(kw["temperature"])
            if "ignition"    in kw:self.ign=bool(kw["ignition"])
            if "charger"     in kw:self.chg=bool(kw["charger"])
            if "fault_inject" in kw:
                self.finj=bool(kw["fault_inject"])
                if self.finj:self._e("Fault injected","error")
            if kw.get("reset"):
                self.finj=False;self.nrst=False
                self.ign=False;self.chg=False;self.state="IDLE"
                self._e("BMS reset — IDLE","ok")

bms=BMS()
def loop():
    while True:bms.step();time.sleep(DT)
threading.Thread(target=loop,daemon=True).start()

# ── Routes ────────────────────────────────────────────────────────────────
@app.route("/")
def idx():
    return jsonify({"service":"MiniBMS API","status":"live",
        "endpoints":["/api/live","/api/history","/api/cells","/api/soc",
                     "/api/faults","/api/state","/api/events",
                     "POST /api/control","/api/export/csv",
                     "/api/ocv_table","/api/ir_table"]})

@app.route("/api/live")
def live():return jsonify(bms.latest())

@app.route("/api/history")
def hist():return jsonify(bms.history(int(request.args.get("n",60))))

@app.route("/api/cells")
def cells():
    d=bms.latest()
    return jsonify({k:d.get(k) for k in["cell_voltages","ocv_per_cell","cell_dv_mv","ir_mohm","temperature_C","pack_voltage"]})

@app.route("/api/soc")
def soc_r():
    d=bms.latest()
    return jsonify({k:d.get(k) for k in["soc_pct","soh_pct","ah_remaining","wh_remaining","wh_total","cycles","tte_min"]})

@app.route("/api/faults")
def faults():
    d=bms.latest()
    return jsonify({k:d.get(k) for k in["fault_voltage","fault_temp","fault_overcurrent","fault_contactor","any_fault","temperature_C","current_A","cell_voltages"]})

@app.route("/api/state")
def state():
    d=bms.latest()
    return jsonify({k:d.get(k) for k in["bms_state","ignition","charger","contactor","tick","timestamp"]})

@app.route("/api/events")
def evts():return jsonify(bms.events(int(request.args.get("n",20))))

@app.route("/api/control",methods=["POST"])
def ctrl():
    bms.ctrl(**(request.get_json(force=True,silent=True) or {}))
    return jsonify({"ok":True,"state":bms.state,"tick":bms.tick})

@app.route("/api/export/csv")
def csv_dl():
    h=bms.history(HIST)
    cols=["tick","timestamp","bms_state","soc_pct","pack_voltage","current_A","power_W",
          "temperature_C","ah_remaining","wh_remaining","soh_pct","cycles","cell_dv_mv",
          "ir_mohm","fault_voltage","fault_temp","fault_overcurrent","any_fault",
          "cell_v1","cell_v2","cell_v3"]
    rows=[",".join(cols)]
    for d in h:
        cv=d.get("cell_voltages",[None,None,None])
        rows.append(",".join(str(v) for v in [d.get("tick"),d.get("timestamp"),d.get("bms_state"),
            d.get("soc_pct"),d.get("pack_voltage"),d.get("current_A"),d.get("power_W"),
            d.get("temperature_C"),d.get("ah_remaining"),d.get("wh_remaining"),d.get("soh_pct"),
            d.get("cycles"),d.get("cell_dv_mv"),d.get("ir_mohm"),
            int(d.get("fault_voltage",0)),int(d.get("fault_temp",0)),
            int(d.get("fault_overcurrent",0)),int(d.get("any_fault",0)),
            cv[0] if len(cv)>0 else "",cv[1] if len(cv)>1 else "",cv[2] if len(cv)>2 else ""]))
    return Response("\n".join(rows),mimetype="text/csv",
        headers={"Content-Disposition":"attachment; filename=minibms.csv"})

@app.route("/api/ocv_table")
def ocv_t():return jsonify([{"soc":s,"ocv":v} for s,v in OCV_SOC])

@app.route("/api/ir_table")
def ir_t():return jsonify([{"temp_c":t,"ir_mohm":r} for t,r in IR_TEMP])

# ── Launch with ngrok ─────────────────────────────────────────────────────
from pyngrok import ngrok

# Optional: set your ngrok authtoken for a stable URL
# Get free token at https://dashboard.ngrok.com/get-started/your-authtoken
# ngrok.set_auth_token("YOUR_TOKEN_HERE")

pub = ngrok.connect(5000)
print("\n" + "="*62)
print("  MiniBMS Backend is LIVE!")
print(f"\n  Public URL  →  {pub}")
print(f"  Live data   →  {pub}/api/live")
print(f"  History     →  {pub}/api/history?n=60")
print(f"  Control     →  POST {pub}/api/control")
print(f"  Export CSV  →  {pub}/api/export/csv")
print("\n  Copy the Public URL into your dashboard's API_BASE.")
print("="*62 + "\n")

app.run(port=5000)
