%% MiniBMSExport.m
%  ─────────────────────────────────────────────────────────────────
%  Run this script AFTER running the MiniBMS.slx Simulink simulation.
%  It reads all Simulink output workspace variables and writes them
%  to JSON (for the Flask server) and CSV (for the dashboard).
%
%  Usage:
%    1. Open MiniBMS.slx and run MiniBMSVariables.m first
%    2. Run the simulation (press Play)
%    3. Run this script: >> MiniBMSExport
%    4. Files created:  minibms_export.json
%                       minibms_export.csv
%  ─────────────────────────────────────────────────────────────────

clear; clc;
fprintf('MiniBMS Export — reading Simulink output workspace...\n\n');

%% ── 1. Read signals from Simulink output workspace ──────────────
%  These match the logsout / To Workspace blocks in MiniBMS.slx

try
    % Get simulation output object if using Simulink.SimulationOutput
    if exist('simOut','var')
        t       = simOut.get('tout');
        soc     = simOut.get('SOC').Data;
        voltage = simOut.get('PackVoltage').Data;
        current = simOut.get('Current').Data;
        temp    = simOut.get('Temperature').Data;
        state   = simOut.get('BMSState').Data;    % 0=IDLE,1=DISC,2=CHG,3=FAULT
        faults  = simOut.get('FaultFlags').Data;  % [vFault, tFault, contFault]
    else
        % Fallback: read from base workspace To Workspace blocks
        t       = evalin('base','tout');
        soc     = evalin('base','SOC');
        voltage = evalin('base','PackVoltage');
        current = evalin('base','Current');
        temp    = evalin('base','Temperature');
        state   = evalin('base','BMSState');
        faults  = evalin('base','FaultFlags');
    end
    fprintf('  Signals loaded from Simulink workspace.\n');
catch
    fprintf('  [WARNING] Could not read Simulink outputs.\n');
    fprintf('  Generating synthetic data from MiniBMSVariables.m parameters.\n\n');
    % ── Synthetic fallback using real model parameters ──
    MiniBMSVariables;   % load model parameters
    t       = (0:1:600)';      % 600s simulation
    soc_0   = 80;              % initial SoC %
    I_load  = 2.0;             % constant discharge current A
    dt_h    = 1/3600;
    soc     = max(0, soc_0 - (I_load / BatteryCapacity_Ah) * 100 * dt_h * (0:length(t)-1)');
    current = I_load * ones(size(t));
    temp    = 28 + 2*sin(2*pi*t/300);
    % OCV lookup for voltage
    voltage = zeros(size(t));
    for k = 1:length(t)
        ocv = interp1(OCV_SOC(:,1), OCV_SOC(:,2), soc(k), 'linear','extrap');
        ir  = interp1(IR_Temp(:,1), IR_Temp(:,2), temp(k), 'linear','extrap') / 1000;
        voltage(k) = 3 * (ocv - current(k) * ir);
    end
    state  = ones(size(t));   % DISCHARGE
    faults = zeros(length(t), 3);
    fprintf('  Synthetic data generated (%d timesteps).\n', length(t));
end

N = length(t);
fprintf('  Timesteps: %d\n', N);

%% ── 2. Derived quantities ────────────────────────────────────────
% These mirror what the dashboard computes
try
    load('MiniBMSVariables.mat');
catch
    MiniBMSVariables;
end

BMS_STATE_LABELS = {'IDLE','DISCHARGE','CHARGE','FAULT'};
state_str = cell(N,1);
for k = 1:N
    idx = round(state(k)) + 1;
    if idx < 1 || idx > 4, idx = 1; end
    state_str{k} = BMS_STATE_LABELS{idx};
end

power_W      = voltage .* current;
ah_remaining = soc * BatteryCapacity_Ah / 100;
wh_remaining = ah_remaining * 11.1;   % nominal 3S pack voltage
fault_v      = faults(:,1);
fault_t      = faults(:,2);
fault_c      = faults(:,3);
any_fault    = fault_v | fault_t | fault_c;

%% ── 3. Export to CSV ─────────────────────────────────────────────
csv_file = 'minibms_export.csv';
fid = fopen(csv_file,'w');
fprintf(fid, 'tick,timestamp_s,bms_state,soc_pct,pack_voltage_V,current_A,power_W,temperature_C,ah_remaining,wh_remaining,fault_voltage,fault_temp,fault_contactor,any_fault\n');
for k = 1:N
    fprintf(fid, '%d,%.2f,%s,%.3f,%.4f,%.4f,%.4f,%.2f,%.4f,%.4f,%d,%d,%d,%d\n', ...
        k, t(k), state_str{k}, soc(k), voltage(k), current(k), power_W(k), ...
        temp(k), ah_remaining(k), wh_remaining(k), ...
        fault_v(k), fault_t(k), fault_c(k), any_fault(k));
end
fclose(fid);
fprintf('  CSV exported → %s\n', csv_file);

%% ── 4. Export to JSON (for Flask server) ────────────────────────
json_file = 'minibms_export.json';
data_struct = struct();
data_struct.meta = struct(...
    'model',    'MiniBMS.slx', ...
    'cells',    3, ...
    'chemistry','Li-Ion', ...
    'capacity_Ah', BatteryCapacity_Ah, ...
    'exported', datestr(now,'yyyy-mm-dd HH:MM:SS'));
data_struct.thresholds = struct(...
    'ov_V', 4.25, 'uv_V', 2.45, 'ot_C', 45.0, 'oc_A', 5.0);
data_struct.ocv_table = OCV_SOC;   % [soc%, ocv_V] matrix
data_struct.ir_table  = IR_Temp;   % [temp_C, ir_mOhm] matrix

% Build records array
records = cell(N,1);
for k = 1:N
    records{k} = struct(...
        'tick',         k, ...
        'timestamp',    t(k), ...
        'bms_state',    state_str{k}, ...
        'soc_pct',      round(soc(k),3), ...
        'pack_voltage', round(voltage(k),4), ...
        'current_A',    round(current(k),4), ...
        'power_W',      round(power_W(k),4), ...
        'temperature_C',round(temp(k),2), ...
        'ah_remaining', round(ah_remaining(k),4), ...
        'wh_remaining', round(wh_remaining(k),3), ...
        'fault_voltage',logical(fault_v(k)), ...
        'fault_temp',   logical(fault_t(k)), ...
        'fault_contactor', logical(fault_c(k)), ...
        'any_fault',    logical(any_fault(k)));
end
data_struct.records = records;

json_str = jsonencode(data_struct);
fid = fopen(json_file,'w');
fprintf(fid, '%s', json_str);
fclose(fid);
fprintf('  JSON exported → %s\n', json_file);

%% ── 5. Summary ───────────────────────────────────────────────────
fprintf('\n──────────────────────────────────────────\n');
fprintf('  MiniBMS Export Summary\n');
fprintf('──────────────────────────────────────────\n');
fprintf('  Duration       : %.1f s\n', t(end));
fprintf('  Final SoC      : %.1f %%\n', soc(end));
fprintf('  Min pack V     : %.3f V\n', min(voltage));
fprintf('  Max pack V     : %.3f V\n', max(voltage));
fprintf('  Max temp       : %.1f °C\n', max(temp));
fprintf('  Fault events   : %d\n', sum(diff(any_fault)==1));
fprintf('  Files created  : %s, %s\n', csv_file, json_file);
fprintf('──────────────────────────────────────────\n');
fprintf('\nNext: upload minibms_export.json to your Flask server\n');
fprintf('or load minibms_export.csv directly into the dashboard.\n');
