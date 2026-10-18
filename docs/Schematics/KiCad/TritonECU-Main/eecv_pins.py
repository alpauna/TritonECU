#!/usr/bin/env python3
"""EEC-V 104-pin connector (J1): which carrier net lands on which pin, for the
1999 F-150 5.4L. The connector-side twin of carrier_pinmap.py.

Sources, in order of authority:
  1. Ford's diagrams, as read in 1999-Ford-F150-4wd-5.42v/schematic-findings.md.
     Their legend: `*` = 5.4L, `**` = 4.2L/4.6L. "SSA -> PCM 27 (*6)" therefore
     means pin 6 on THIS truck; 27 is the 4.6L pin, and on the 5.4L pin 27 is
     coil 5.
  2. eec-v-pinout.md, the '99 F150 column (MegaSquirt PNP sheet).
  3. Design documents for pins this ECU adds (freewheel returns, fan 2).

Checked: no pin carries two nets, every pin is 1-104, the grounds and VPWR are
the 5.4L's (pin 24 is the 4.6L ground, not used).

Usage:  python3 eecv_pins.py        check, and list the nets by connector position
"""
import re, os

# pin: (net, what, source)
PINS = {
    # --- power and returns
    71: ('VPWR', 'key-switched power, 361 RD', 'pinout + findings sec.17'),
    97: ('VPWR', 'key-switched power, 361 RD', 'pinout + findings sec.17'),
    3: ('GND', 'power ground, 570 BK/WH (the 5.4L fourth ground is *3)', 'findings'),
    51: ('GND', 'power ground', 'pinout'),
    77: ('GND', 'power ground', 'pinout'),
    103: ('GND', 'power ground', 'pinout'),
    55: ('VBAT_SENSE', 'battery voltage sense, 729 RD/WH, KAM feed', 'findings sec.19'),
    90: ('VREF', '5 V sensor reference', 'pinout'),
    91: ('SIGRTN', 'sensor return, 359', 'schematic-ecu-v1 sec.14a'),
    36: ('MAF_RTN', 'MAF return, Kelvin sense (not AGND at the connector)', 'schematic-ecu-v1 sec.14a'),
    48: ('FW_391', 'circuit 391 brought in as a freewheel return', 'schematic-ecu-v1 sec.12'),
    82: ('FW_1138', 'circuit 1138 brought in as a freewheel return (TCC, EPC, SSA, SSB)', 'findings sec.5'),
    25: ('CMP_SHIELD', 'CMP shield drain, 567 LB/YE', 'pinout + findings'),
    # --- ignition, COP. Coil n = cylinder n
    26: ('COIL1_OUT', 'coil 1', 'pinout'), 104: ('COIL2_OUT', 'coil 2', 'pinout'),
    52: ('COIL3_OUT', 'coil 3', 'pinout'), 53: ('COIL4_OUT', 'coil 4', 'pinout'),
    27: ('COIL5_OUT', 'coil 5', 'pinout'), 1: ('COIL6_OUT', 'coil 6', 'pinout'),
    78: ('COIL7_OUT', 'coil 7', 'pinout'), 79: ('COIL8_OUT', 'coil 8', 'pinout'),
    # --- injection
    75: ('INJ1_OUT', 'injector 1', 'pinout'), 101: ('INJ2_OUT', 'injector 2', 'pinout'),
    74: ('INJ3_OUT', 'injector 3', 'pinout'), 100: ('INJ4_OUT', 'injector 4', 'pinout'),
    73: ('INJ5_OUT', 'injector 5', 'pinout'), 99: ('INJ6_OUT', 'injector 6', 'pinout'),
    72: ('INJ7_OUT', 'injector 7', 'pinout'), 98: ('INJ8_OUT', 'injector 8', 'pinout'),
    # --- solenoids and heaters (74HCT541 #3 group)
    93: ('HTR11_OUT', 'HO2S 11 heater (RF/bank 1 upstream)', 'pinout'),
    94: ('HTR21_OUT', 'HO2S 21 heater (LF)', 'pinout'),
    95: ('HTR12_OUT', 'HO2S 12 heater (RR)', 'pinout'),
    96: ('HTR22_OUT', 'HO2S 22 heater (LR)', 'pinout'),
    67: ('VENT_OUT', 'canister vent', 'findings'),
    46: ('IMCC_OUT', 'intake manifold communication control', 'pinout'),
    6: ('SSA_OUT', 'shift solenoid A, 237 OG/YE (*6 = 5.4L)', 'findings sec.5'),
    11: ('SSB_OUT', 'shift solenoid B, 315 VT/OG (*11 = 5.4L)', 'findings sec.5'),
    # --- PWM loads (74HCT541 #2 group)
    56: ('EVAP_OUT', 'canister purge', 'pinout'),
    47: ('EGR_OUT', 'EGR vacuum regulator', 'pinout'),
    54: ('TCC_OUT', 'torque converter clutch', 'findings sec.5'),
    81: ('EPC_OUT', 'electronic pressure control', 'findings sec.5'),
    83: ('IAC_OUT', 'idle air control', 'pinout'),
    68: ('VSS_OUT_PIN', 'road speed out, 679 GY/BK, open drain', 'findings'),
    20: ('CCS_OUT', 'coast clutch, 4R100 only (free on the 4R70W)', 'pinout'),
    # --- relays
    80: ('FPUMP_OUT', 'fuel pump relay', 'pinout'),
    19: ('FAN1_OUT', 'cooling fan 1 relay', 'pinout, cooling-fans.md'),
    18: ('FAN2_OUT', 'cooling fan 2 relay', 'pinout, cooling-fans.md'),
    69: ('ACC_OUT', 'A/C WOT cut-out relay, 331 PK/YE', 'findings sec.8'),
    # --- position and speed (to the VR board)
    21: ('CKP_P', 'crank +', 'pinout'), 22: ('CKP_N', 'crank -', 'pinout'),
    85: ('CMP_IN', 'cam, VR single-ended', 'pinout'),
    84: ('OSS_IN', 'output shaft speed', 'findings sec.7'),
    59: ('TSS_IN', 'turbine shaft speed', 'pinout'),
    7: ('TC_SPEED_IN', 'transfer case speed, 1496 PK', 'findings sec.7'),
    # --- analog sensors (ADS8588H or the internal ADC)
    88: ('MAF_IN', 'MAF', 'pinout'), 89: ('TPS_IN', 'throttle position', 'pinout'),
    39: ('IAT_IN', 'intake air temperature', 'pinout'),
    66: ('CHT_IN', 'cylinder head temperature', 'pinout'),
    65: ('DPFE_IN', 'EGR delta-pressure', 'pinout'),
    37: ('TFT_IN', 'transmission fluid temperature', 'pinout'),
    40: ('FP_MON_IN', 'fuel pump monitor', 'pinout'),
    60: ('O2_11_IN', 'HO2S 11 (RF upstream)', 'pinout'),
    87: ('O2_21_IN', 'HO2S 21 (LF upstream)', 'pinout'),
    35: ('O2_12_IN', 'HO2S 12 (RR downstream)', 'pinout'),
    61: ('O2_22_IN', 'HO2S 22 (LR downstream)', 'pinout'),
    57: ('KNOCK_IN', 'knock sensor', 'pinout'),
    32: ('KNOCK_RTN', 'knock sensor, second wire (two-wire piezo)', 'pinout, knock-front-end.md'),
    # --- switches
    34: ('TR1_IN', 'trans range 1', 'pinout'), 49: ('TR2_IN', 'trans range 2', 'pinout'),
    64: ('TR3A_IN', 'trans range 3A / start in P or N, 199 LB/YE', 'findings sec.21'),
    50: ('TR4_IN', 'trans range 4', 'pinout'),
    92: ('BRAKE_IN', 'brake pedal position', 'pinout'),
    41: ('ACP_IN', 'A/C cycling pressure switch, 347 BK/YE', 'findings sec.8'),
    29: ('TCS_IN', 'O/D cancel switch', 'pinout'),
    14: ('4X4L_IN', '4x4 low indicator switch, 784 LB/BK (C189)', 'findings sec.14-15'),
    # --- bus
    15: ('SCP_N', 'SCP- 915 PNK/LT BLU', 'pinout'), 16: ('SCP_P', 'SCP+ 914 TAN/ORG', 'pinout'),
    # private CAN to the dash display: terminals ADDED in two empty cavities beside SCP
    42: ('CAN_H', 'CAN high, added terminal (unused cavity)', 'can-bus.md'),
    43: ('CAN_L', 'CAN low, added terminal (unused cavity)', 'can-bus.md'),
}

# Deliberately unconnected, with the reason
NOT_CONNECTED = {
    24: '4.2L/4.6L ground pin; not wired on the 5.4L',
    13: 'FEPS / DLC 13: 18 V programming, leave open on a 3.3 V system',
    12: 'trans control indicator lamp: dash is on SCP',
    62: 'fuel tank pressure: not fitted',
    63: 'fuel pressure: future',
    38: 'MS sheet ECT jumper: this truck uses CHT on 66',
}

# signals carrier_pinmap.py has but the connector does not carry, and why
OFF_CONNECTOR = {'TACH': 'test header only', 'SPEED': 'test header only'}


def pad_positions():
    t = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'TritonECU-Main.pretty', 'EECV_104.kicad_mod')).read()
    return {int(n): (float(x), float(y)) for n, x, y in re.findall(r'\(pad "(\d+)" \w+ \w+ \(at ([-\d.]+) ([-\d.]+)', t)}


def check():
    errors = []
    for p in PINS:
        if not 1 <= p <= 104:
            errors.append(f'pin {p} out of range')
        if p in NOT_CONNECTED:
            errors.append(f'pin {p} is both used and not connected')
    if 24 in PINS:
        errors.append('pin 24 is the 4.6L ground')
    for coil, ss in ((27, 6), (1, 11)):
        if not PINS[coil][0].startswith('COIL') or not PINS[ss][0].startswith('SS'):
            errors.append(f'pins {coil}/{ss}: coil/shift-solenoid swap (4.6L numbering)')
    return errors


if __name__ == '__main__':
    errs = check()
    for e in errs:
        print('ERROR', e)
    pads = pad_positions()
    groups = {}
    for p, (net, *_ ) in PINS.items():
        g = re.sub(r'\d*_?(OUT|IN|P|N|RTN|PIN)?$', '', net) or net
        groups.setdefault(g, []).append(p)
    print(f'{len(PINS)} pins used, {len(NOT_CONNECTED)} deliberately open, {104 - len(PINS) - len(NOT_CONNECTED)} free')
    for g, ps in sorted(groups.items(), key=lambda kv: min(pads[p][0] for p in kv[1])):
        xs = [pads[p][0] for p in ps]
        print(f'  {g:10s} x {min(xs):6.1f} .. {max(xs):6.1f}   pins {sorted(ps)}')
    raise SystemExit(1 if errs else 0)
