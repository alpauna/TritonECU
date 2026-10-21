#!/usr/bin/env python3
"""TritonECU carrier schematic: one hierarchical sheet per subsystem, joined to
the Interconnect sheet (connector J1 and the daughterboards) by global labels.

Net names come from carrier_pinmap.py (MCU side) and eecv_pins.py (connector
side); the circuits from the design documents cited on each sheet.

BOOTSTRAP: a sheet is regenerated only while it is still this script's output.
Once saved in KiCad (its generator field changes) it is left alone. Symbol
UUIDs are derived from sheet and reference, so a regenerated sheet keeps the PCB
footprints linked.

Usage:  python3 gen_carrier.py            (KiCad closed)
"""
import json, os, re, subprocess, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import carrier_pinmap as cp
import eecv_pins as ep

PROJ = 'TritonECU-Main'
MARK = 'gen_carrier.py'
STOCK = '/app/extensions/Library/symbols'
USER = '/home/apauna/Documents/KiCad/Libraries'      # ${KICAD_3RD_PARTY}
CLIB = 'TritonECU-Carrier'                            # this project's own symbols
NS = uuid.UUID('6b1f3c2e-8f8d-4f0a-9a57-7c1e2d9b4e10')

def UID(*key): return str(uuid.uuid5(NS, '/'.join(key)))
def U(): return str(uuid.uuid4())

# ---------------------------------------------------------------- footprints
FP = {'R': 'Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder',
      'C': 'Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder',
      'SOIC20': 'Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm',
      'SOT23': 'Package_TO_SOT_SMD:SOT-23',
      'SOT23-5': 'Package_TO_SOT_SMD:SOT-23-5',
      'SOT223': 'Package_TO_SOT_SMD:SOT-223-3_TabPin2',
      'R0805': 'Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder',
      'C0805': 'Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder',
      'QSOP16': 'Package_SO:QSOP-16_3.9x4.9mm_P0.635mm',
      'HDR4': 'Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',
      'DPAK': 'Package_TO_SOT_SMD:TO-252-2',
      'SMB': 'Diode_SMD:D_SMB',
      'TSSOP16': 'Package_SO:TSSOP-16_4.4x5mm_P0.65mm',
      'DPAK5': 'Package_TO_SOT_SMD:TO-252-5_TabPin3',
      'SMA': 'Diode_SMD:D_SMA',
      'SOD323': 'Diode_SMD:D_SOD-323F',
      'SOIC8': 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
      'TSSOP14': 'Package_SO:TSSOP-14_4.4x5mm_P0.65mm',
      'JP': 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm'}

# ---------------------------------------------------------------- own symbols
def own_symbol(name, ref, pins, descr, w=10.16):
    """Plain box; pins = [(num, name, side 'L'/'R', type)]."""
    left = [p for p in pins if p[2] == 'L']; right = [p for p in pins if p[2] == 'R']
    n = max(len(left), len(right)); top = (n - 1) * 1.27
    body = (f'\t\t\t(rectangle (start {-w/2} {top + 2.54}) (end {w/2} {top - n * 2.54}) '
            f'(stroke (width 0.254) (type default)) (fill (type background)))\n')
    for side, lst in (('L', left), ('R', right)):
        for i, (num, nm, _, typ) in enumerate(lst):
            x = -w / 2 - 2.54 if side == 'L' else w / 2 + 2.54
            body += (f'\t\t\t(pin {typ} line (at {x} {round(top - i * 2.54, 2)} {0 if side == "L" else 180}) (length 2.54)'
                     f' (name "{nm}" (effects (font (size 1.27 1.27)))) (number "{num}" (effects (font (size 1.27 1.27)))))\n')
    return (f'\t(symbol "{name}"\n\t\t(exclude_from_sim no) (in_bom yes) (on_board yes)\n'
            f'\t\t(property "Reference" "{ref}" (at {-w/2} {top + 3.81} 0) (effects (font (size 1.27 1.27)) (justify left)))\n'
            f'\t\t(property "Value" "{name}" (at {-w/2} {top - n * 2.54 - 1.27} 0) (effects (font (size 1.27 1.27)) (justify left)))\n'
            f'\t\t(property "Footprint" "" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
            f'\t\t(property "Datasheet" "" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
            f'\t\t(property "Description" "{descr}" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
            f'\t\t(symbol "{name}_1_1"\n{body}\t\t)\n\t)\n')

OWN = {
    # Diodes ZXMS6005DGQ IntelliFET, SOT-223: 1 IN, 2 D (tab), 3 S. The Samacsys
    # import has unnumbered pins and a 3-pad footprint, so it is not used.
    'IntelliFET': own_symbol('IntelliFET', 'Q', [('1', 'IN', 'L', 'input'), ('2', 'D', 'R', 'passive'),
                                                 ('3', 'S', 'R', 'passive')],
                             'Self-protected low-side switch, logic input (ZXMS6005DGQ)'),
    # Analog Devices MAX9926UAEE+T, QSOP-16, dual VR interface (datasheet pin table).
    # Pins 15/16: the datasheet's descriptions look swapped against the names; the
    # names are used (vr-conditioning.md).
    'MAX9926': own_symbol('MAX9926', 'U', [('16', 'IN1+', 'L', 'input'), ('15', 'IN1-', 'L', 'input'),
                                           ('9', 'IN2+', 'L', 'input'), ('10', 'IN2-', 'L', 'input'),
                                           ('1', 'INT_THRS1', 'L', 'input'), ('8', 'INT_THRS2', 'L', 'input'),
                                           ('13', 'ZERO_EN', 'L', 'input'), ('11', 'GND', 'L', 'power_in'),
                                           ('14', 'VCC', 'R', 'power_in'), ('4', 'COUT1', 'R', 'open_collector'),
                                           ('5', 'COUT2', 'R', 'open_collector'), ('12', 'DIRN', 'R', 'open_collector'),
                                           ('3', 'BIAS1', 'R', 'passive'), ('6', 'BIAS2', 'R', 'passive'),
                                           ('2', 'EXT1', 'R', 'input'), ('7', 'EXT2', 'R', 'input')],
                          'Dual VR sensor interface, differential input, adaptive threshold', w=15.24),
    # onsemi NCV8772C, DPAK-5 centre lead crop (case 175AA): 1 Vin, 2 RO, 3 GND (tab), 4 EN, 5 Vout
    'NCV8772': own_symbol('NCV8772', 'U', [('1', 'VIN', 'L', 'power_in'), ('4', 'EN', 'L', 'input'),
                                           ('3', 'GND', 'L', 'power_in'), ('5', 'VOUT', 'R', 'power_out'),
                                           ('2', 'RO', 'R', 'output')],
                          '350 mA LDO with reset, NCV8772C', w=12.7),
    # Standard dual / quad op-amp pinouts, one unit each so every pin is placed:
    # OPA2376AQDRQ1 SOIC-8 and TLV9064-Q1 SOIC/TSSOP-14 (both datasheets' pin tables).
    'OPAMP2': own_symbol('OPAMP2', 'U', [('3', '+INA', 'L', 'input'), ('2', '-INA', 'L', 'input'),
                                         ('5', '+INB', 'L', 'input'), ('6', '-INB', 'L', 'input'),
                                         ('4', 'V-', 'L', 'power_in'), ('8', 'V+', 'R', 'power_in'),
                                         ('1', 'OUTA', 'R', 'output'), ('7', 'OUTB', 'R', 'output')],
                         'Dual op-amp, standard SOIC-8 pinout (OPA2376)'),
    'OPAMP4': own_symbol('OPAMP4', 'U', [('3', '+IN1', 'L', 'input'), ('2', '-IN1', 'L', 'input'),
                                         ('5', '+IN2', 'L', 'input'), ('6', '-IN2', 'L', 'input'),
                                         ('10', '+IN3', 'L', 'input'), ('9', '-IN3', 'L', 'input'),
                                         ('12', '+IN4', 'L', 'input'), ('13', '-IN4', 'L', 'input'),
                                         ('11', 'V-', 'L', 'power_in'), ('4', 'V+', 'R', 'power_in'),
                                         ('1', 'OUT1', 'R', 'output'), ('7', 'OUT2', 'R', 'output'),
                                         ('8', 'OUT3', 'R', 'output'), ('14', 'OUT4', 'R', 'output')],
                         'Quad op-amp, standard 14-pin pinout (TLV9064)'),
}

def write_own_lib():
    open(os.path.join(HERE, f'{CLIB}.kicad_sym'), 'w').write(
        f'(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "{MARK}")\n\t(generator_version "10.0")\n'
        + ''.join(OWN.values()) + ')\n')

# ---------------------------------------------------------------- library access
_cache = {}
def lib_text(lib):
    if lib not in _cache:
        if lib == 'Samacsys':
            _cache[lib] = open(f'{USER}/Samacsys.kicad_sym').read()
        elif lib == CLIB:
            _cache[lib] = '(kicad_symbol_lib\n' + ''.join(OWN.values()) + ')\n'
        else:
            _cache[lib] = subprocess.run(['flatpak', 'run', '--command=cat', 'org.kicad.KiCad',
                                          f'{STOCK}/{lib}.kicad_sym'], check=True, capture_output=True, text=True).stdout
    return _cache[lib]

def span(s, a):
    d = 0; k = a; q = False
    while True:
        c = s[k]
        if q:
            if c == '\\': k += 1
            elif c == '"': q = False
        elif c == '"': q = True
        elif c == '(': d += 1
        elif c == ')': d -= 1
        k += 1
        if d == 0: return k

def find_symbol(s, name):
    m = re.search(r'\n\t\(symbol "%s"\s*\n' % re.escape(name), s)
    a = m.start() + 2
    return s[a:span(s, a)]

def lib_symbol(lib_id):
    """(embedded text, {pin: [(x, y, angle)]}, default footprint) for 'Lib:Name'.
    A derived symbol (extends) is flattened onto its parent's body."""
    lib, name = lib_id.split(':')
    s = lib_text(lib)
    blk = find_symbol(s, name)
    ext = re.search(r'\(extends "([^"]+)"\)', blk)
    fp = re.search(r'\(property "Footprint" "([^"]*)"', blk)
    fp = fp.group(1) if fp else ''
    if ext:
        pname = ext.group(1)
        parent = find_symbol(s, pname)
        # parent body: everything that is not a property, from the first (pin_*) /
        # (exclude_*) / unit sub-symbol on; the child's own header and properties stay
        units = re.search(r'\n\t\t\(symbol "%s_' % re.escape(pname), parent)
        settings = ''.join(m.group(0) for m in re.finditer(r'\n\t\t\((?:pin_numbers|pin_names)\b.*?(?=\n\t\t\()', parent, re.S)
                           if 'pin_' in m.group(0)[:16])
        body = parent[units.start():parent.rstrip().rindex(')')].replace(f'(symbol "{pname}_', f'(symbol "{name}_')
        head = blk[:blk.rstrip().rindex(')')]
        head = re.sub(r'\n\t\t\(extends "[^"]+"\)', settings, head, 1)
        blk = head + body + '\n\t)'
    pins = {}
    for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\).*?\(number "([^"]*)"', blk, re.S):
        pins.setdefault(m.group(4), []).append((float(m.group(1)), float(m.group(2)), int(m.group(3))))
    emb = blk.replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)
    return emb, pins, fp

# ---------------------------------------------------------------- sheet builder
GLOBAL = set()       # every net named by the two maps crosses sheets

class Sheet:
    def __init__(self, name, title, root, block):
        self.name, self.title, self.root, self.block = name, title, root, block
        self.uuid = UID(name, 'file')
        self.libs, self.items, self.npwr = {}, [], 0
        self.refs = []

    def symbol(self, lib_id, ref, value, x, y, footprint=None, rot=0, fields=None, hide_ref=False, bom=True, dnp=False):
        if not ref.startswith('#'):       # power symbols sit exactly on a pin end
            x, y = round(x / 2.54) * 2.54, round(y / 2.54) * 2.54
        if lib_id not in self.libs:
            self.libs[lib_id] = lib_symbol(lib_id)
        _, pins, deffp = self.libs[lib_id]
        fp = deffp if footprint is None else footprint
        props = [('Reference', ref, x, y - 5.08, hide_ref), ('Value', value, x, y + 5.08, False),
                 ('Footprint', fp, x, y, True), ('Datasheet', '', x, y, True)]
        props += [(k, v, x, y, True) for k, v in (fields or {}).items()]
        su = UID(self.name, ref) if not ref.startswith('#') else U()
        t = (f'\t(symbol (lib_id "{lib_id}") (at {x:.2f} {y:.2f} {rot}) (unit 1)\n'
             f'\t\t(exclude_from_sim no) (in_bom {"yes" if bom and not ref.startswith("#") else "no"}) (on_board yes) (dnp {"yes" if dnp else "no"})\n'
             f'\t\t(uuid "{su}")\n')
        for k, v, px, py, hide in props:
            h = ' (hide yes)' if hide else ''
            t += f'\t\t(property "{k}" "{v}" (at {px:.2f} {py:.2f} 0){h} (effects (font (size 1.27 1.27))))\n'
        for num in pins:
            t += f'\t\t(pin "{num}" (uuid "{U()}"))\n'
        t += (f'\t\t(instances (project "{PROJ}" (path "/{self.root}/{self.block}" '
              f'(reference "{ref}") (unit 1))))\n\t)\n')
        self.items.append(t)
        if not ref.startswith('#'):
            self.refs.append(ref)
        out = {}
        for num, lst in pins.items():
            res = []
            for px, py, a in lst:
                for _ in range(rot // 90):
                    px, py, a = -py, px, (a + 90) % 360
                res.append((round(x + px, 2), round(y - py, 2), {0: 'L', 180: 'R', 90: 'D', 270: 'U'}[a]))
            out[num] = res
        return out

    def power(self, net, x, y, outward):
        self.npwr += 1
        if net == 'GND':
            rot = {'D': 0, 'U': 180, 'L': 270, 'R': 90}[outward]
        else:
            rot = {'U': 0, 'D': 180, 'L': 90, 'R': 270}[outward]
        if net == 'VPWR':      # no stock power symbol: a global label, like the connector side
            self.label(net, x, y, outward); return
        self.symbol(f'power:{net}', f'#PWR{self.npwr:03d}', net, x, y, rot=rot, hide_ref=True)

    def label(self, name, x, y, outward):
        ang, just = {'L': (180, 'right'), 'R': (0, 'left'), 'U': (90, 'left'), 'D': (270, 'right')}[outward]
        if name in GLOBAL:
            self.items.append(f'\t(global_label "{name}" (shape passive) (at {x:.2f} {y:.2f} {ang}) '
                              f'(effects (font (size 1.27 1.27)) (justify {just})) (uuid "{U()}"))\n')
        else:
            self.items.append(f'\t(label "{name}" (at {x:.2f} {y:.2f} {ang}) '
                              f'(effects (font (size 1.27 1.27)) (justify {just} bottom)) (uuid "{U()}"))\n')

    def net(self, name, pin_ends):
        for x, y, o in pin_ends:
            if name in ('GND', '+3.3V', '+5V', 'VPWR'):
                self.power(name, x, y, o)
            elif name is None:
                self.items.append(f'\t(no_connect (at {x:.2f} {y:.2f}) (uuid "{U()}"))\n')
            else:
                self.label(name, x, y, o)

    def wire(self, sym, nets):
        """nets: {pin number: net name or None for no-connect}."""
        for num, name in nets.items():
            self.net(name, sym[num])

    def text(self, t, x, y, size=1.7):
        t = t.replace('"', "'")
        self.items.append(f'\t(text "{t}" (exclude_from_sim no) (at {x:.2f} {y:.2f} 0) '
                          f'(effects (font (size {size} {size})) (justify left bottom)) (uuid "{U()}"))\n')

    def two(self, lib_id, ref, value, fp, x, y, a, b, fields=None):
        """Two-pin part, vertical: pin 1 up to net a, pin 2 down to net b."""
        s = self.symbol(lib_id, ref, value, x, y, fp, fields=fields)
        self.net(a, s['1']); self.net(b, s['2'])

    def write(self, path):
        libs = ''.join('\t\t' + e.replace('\n\t', '\n\t\t') + '\n' for e, _, _ in self.libs.values())
        s = (f'(kicad_sch\n\t(version 20260306)\n\t(generator "{MARK}")\n\t(generator_version "10.0")\n'
             f'\t(uuid "{self.uuid}")\n\t(paper "A3")\n'
             f'\t(title_block (title "TritonECU carrier - {self.title}") (rev "1") '
             f'(comment 1 "Generated by {MARK}"))\n'
             f'\t(lib_symbols\n{libs}\t)\n' + ''.join(self.items) + '\t(embedded_fonts no)\n)\n')
        open(path, 'w').write(s)

# ---------------------------------------------------------------- sheets
def ignition(sh):
    """output-drivers.md: 74HCT541 #1 at 5 V -> 470R -> ISL9V3040 x8; OE1 armed by
    firmware, OE2 by the TPS3823A-33 watchdog through a BSS138; RESET also to NRST."""
    sh.text('Ignition: 8 x COP. 74HCT541 at 5 V (the IGBT plateau is 3.0 V), 470R gates (datasheet RG),', 20, 20)
    sh.text('no gate capacitor, no C-E snubber. OE1 = firmware armed, OE2 = watchdog alive. output-drivers.md', 20, 24)
    u = sh.symbol('74xx:74HCT541', 'U101', '74HCT541', 60, 90, FP['SOIC20'])
    sh.wire(u, {'1': 'COIL_ARM', '19': 'WD_OE', '10': 'GND', '20': '+5V_SW'})
    for i in range(8):
        sh.wire(u, {str(2 + i): f'COIL{i + 1}', str(18 - i): f'GATE{i + 1}'})
    sh.two('Device:C', 'C101', '100n', FP['C'], 45, 125, '+5V_SW', 'GND')
    sh.two('Device:R', 'R109', '10k', FP['R'], 30, 70, '+5V_SW', 'COIL_ARM')
    sh.two('Device:R', 'R110', '10k', FP['R'], 40, 70, '+5V_SW', 'WD_OE')
    for i in range(8):
        y = 45 + i * 22
        r = sh.symbol('Device:R', f'R{101 + i}', '470', 120, y, FP['R'], rot=90)
        sh.wire(r, {'1': f'GATE{i + 1}', '2': f'G{i + 1}'})
        q = sh.symbol('Samacsys:ISL9V3040S3ST', f'Q{101 + i}', 'ISL9V3040S3ST', 160, y)
        sh.wire(q, {'1': f'G{i + 1}', '3': f'COIL{i + 1}_OUT', '2': 'GND'})
    # watchdog: TPS3823A-33DBVR on the always-on 3.3 V
    w = sh.symbol('Power_Supervisor:TPS3823-xxDBV', 'U102', 'TPS3823A-33DBVR', 60, 170)
    sh.wire(w, {'5': '+3.3V', '2': 'GND', '4': 'WDI', '3': None, '1': 'NRST'})
    sh.two('Device:C', 'C102', '100n', FP['C'], 35, 170, '+3.3V', 'GND')
    sh.two('Device:R', 'R111', '1M', FP['R'], 85, 185, 'NRST', 'GND')
    f = sh.symbol('Transistor_FET:BSS138', 'Q109', 'BSS138', 100, 170)
    sh.wire(f, {'1': 'NRST', '2': 'GND', '3': 'WD_OE'})
    j = sh.symbol('Jumper:SolderJumper_2_Open', 'JP101', 'OE2 strap', 100, 195, FP['JP'], bom=False)
    sh.wire(j, {'1': 'WD_OE', '2': 'GND'})
    sh.text('WDI: NO pull resistor - a floating WDI is how the TPS3823 disables itself in Standby.', 20, 210)
    sh.text('JP101 closed = v1 strap, OE2 always low (watchdog not fitted).', 20, 214)

def injection(sh):
    """output-drivers.md: ZXMS6005DGQ x8 straight from 3.3 V GPIO; the 60-70 V active
    clamp is the injector turn-off, so no diode. 10k input pulldown, custom-board.md."""
    sh.text('Injection: 8 x ZXMS6005DGQ IntelliFET, direct from GPIO. Active clamp 60-70 V = fast close:', 20, 20)
    sh.text('NO freewheel diode. 10k input pulldown holds every injector off through reset. output-drivers.md', 20, 24)
    for i in range(8):
        y = 45 + i * 22
        r = sh.symbol('Device:R', f'R{201 + i}', '10k', 80, y + 8, FP['R'])
        sh.wire(r, {'1': f'INJ{i + 1}', '2': 'GND'})
        q = sh.symbol(f'{CLIB}:IntelliFET', f'Q{201 + i}', 'ZXMS6005DGQTA', 120, y, FP['SOT223'])
        sh.wire(q, {'1': f'INJ{i + 1}', '2': f'INJ{i + 1}_OUT', '3': 'GND'})

def rails(sh):
    """The carrier makes no rails of its own: +5V, +3.3V and GND arrive from the
    power board (DB1), VPWR from the connector. VPROT is the power board's LTC4364
    output (its J3 +VIN), the source for VREF. PWR_FLAGs say so to ERC."""
    sh.text('Rails: +5V, +3.3V (always-on) and GND come from the power board, VPWR from EEC-V 71/97.', 20, 20)
    for k, net in enumerate(['+5V', '+3.3V', 'GND', 'VPWR', 'VPROT']):
        f = sh.symbol('power:PWR_FLAG', f'#FLG{k + 1:02d}', 'PWR_FLAG', 40.64 + 25.4 * k, 50.8)
        sh.net(net, f['1'])
    sh.text('Bulk where the rails arrive from the power board connector.', 20, 120)
    sh.two('Device:C', 'C001', '10u', 'Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder', 50, 140, '+5V', 'GND')
    sh.two('Device:C', 'C002', '10u', 'Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder', 75, 140, '+3.3V', 'GND')
    sh.text('Switched rails: +5V and +3.3V stay up parked (3.3 V is made from 5 V), so everything that only matters while', 20, 170)
    sh.text('running hangs off +5V_SW / +3.3V_SW: driver buffers, MAX9926, ADC, op-amps, mux, TFT and VR pull-ups. Always on:', 20, 174)
    sh.text('MCU, watchdog, CAN transceiver (wake), SCP receiver, input clamps, SD switch. TPS22917: slew-limited, no inrush dip on the MCU rail.', 20, 178)
    sh.text('SW_RAIL_EN 100k down: rails off until firmware runs, and every driver input is then held off by its own pull-down.', 20, 182)
    for k, (src, dst) in enumerate((('+5V', '+5V_SW'), ('+3.3V', '+3.3V_SW'))):
        x = 60 + 110 * k
        w = sh.symbol('Power_Management:TPS22917DBV', f'U00{1 + k}', 'TPS22917DBVR', x, 210)
        sh.wire(w, {'1': src, '2': 'GND', '3': 'SW_RAIL_EN', '4': f'SW{k + 1}_CT', '5': f'SW{k + 1}_QOD', '6': dst})
        sh.two('Device:C', f'C00{3 + 3 * k}', '1u', FP['C0805'], x - 25, 210, src, 'GND')
        sh.two('Device:C', f'C00{4 + 3 * k}', '1n', FP['C'], x - 5, 235, f'SW{k + 1}_CT', 'GND',
               fields={'Note': 'slew: ~40 uF of decoupling downstream'})
        sh.two('Device:C', f'C00{5 + 3 * k}', '10u', FP['C0805'], x + 30, 220, dst, 'GND')
        sh.two('Device:R', f'R00{2 + k}', '100', FP['R'], x + 20, 235, f'SW{k + 1}_QOD', dst,
               fields={'Note': 'quick output discharge, rate-limited'})
    sh.two('Device:R', 'R004', '100k', FP['R'], 40, 240, 'SW_RAIL_EN', 'GND')
    sh.text('VBAT: the module RTC/backup domain, from the always-on 3.3 V. R001 can become a coin cell.', 20, 80)
    sh.two('Device:R', 'R001', '0', FP['R'], 50, 100, '+3.3V', 'VBAT')

def vr(sh):
    """3 x MAX9926, Mode A2, on the carrier (VR board V1 stays a bench board).
    vr-conditioning.md, review-vr-v1.md, review-vr-chain.md, review-vr-channel-count.md."""
    sh.text('VR inputs: 3 x MAX9926, Mode A2 (INT_THRS = ZERO_EN = GND, EXT open). 2 x 5k 0805 per leg = 300 V headroom', 20, 20)
    sh.text('(V1 had one; add-on per vr-conditioning.md). 470 pF C0G 200 V across the inputs: 2x10k -> 17 kHz, 0.34 deg at 6000 rpm.', 20, 24)
    sh.text('BIAS: 100 nF to GND (review-vr-v1 #3). VCC: 10 nF closest + 100 nF + 1 uF. COUT open drain, 10k to 3.3 V.', 20, 28)
    sh.text('Single-ended sensors (CMP, OSS, TSS, transfer case) return their - leg on SIGRTN, pin 91.', 20, 32)
    chans = [  # (chip, channel, P net, N net, output net)
        (1, 1, 'CKP_P', 'CKP_N', 'CKP'), (1, 2, 'VR_SPARE_P', 'VR_SPARE_N', 'VR_SPARE'),
        (2, 1, 'CMP_IN', 'SIGRTN', 'CMP'), (2, 2, 'OSS_IN', 'SIGRTN', 'OSS'),
        (3, 1, 'TSS_IN', 'SIGRTN', 'TSS'), (3, 2, 'TC_SPEED_IN', 'SIGRTN', 'TC_SPEED')]
    pin = {1: ('16', '15', '4', '3'), 2: ('9', '10', '5', '6')}     # IN+, IN-, COUT, BIAS
    r = 301; c = 301
    for chip in (1, 2, 3):
        x0 = 30 + (chip - 1) * 125
        u = sh.symbol(f'{CLIB}:MAX9926', f'U30{chip}', 'MAX9926UAEE+T', x0 + 70, 90, FP['QSOP16'])
        sh.wire(u, {'1': 'GND', '8': 'GND', '13': 'GND', '11': 'GND', '14': '+5V_SW', '2': None, '7': None, '12': None})
        for k, val in enumerate(('10n', '100n', '1u')):
            sh.two('Device:C', f'C{c}', val, FP['C'], x0 + 95 + 8 * k, 125, '+5V_SW', 'GND'); c += 1
        for (cc, ch, pnet, nnet, out) in [q for q in chans if q[0] == chip]:
            ip, im, co, bi = pin[ch]
            tag = f'U30{chip}_{ch}'
            y = 55 if ch == 1 else 115
            for leg, src, dst in (('P', pnet, f'{tag}_INP'), ('N', nnet, f'{tag}_INM')):
                mid = f'{tag}_{leg}M'
                yy = y + (0 if leg == 'P' else 10)
                a1 = sh.symbol('Device:R', f'R{r}', '5k', x0 + 10, yy, FP['R0805'], rot=90,
                               fields={'Note': 'VR input leg, 0805 for 150 V each'}); r += 1
                sh.wire(a1, {'1': src, '2': mid})
                a2 = sh.symbol('Device:R', f'R{r}', '5k', x0 + 25, yy, FP['R0805'], rot=90); r += 1
                sh.wire(a2, {'1': mid, '2': dst})
            sh.two('Device:C', f'C{c}', '470p', FP['C0805'], x0 + 40, y + 5, f'{tag}_INP', f'{tag}_INM',
                   fields={'Note': 'C0G, 200 V'}); c += 1
            sh.net(f'{tag}_INP', u[ip]); sh.net(f'{tag}_INM', u[im])
            sh.net(out, u[co])
            sh.two('Device:R', f'R{r}', '10k', FP['R'], x0 + 100, y - 10, '+3.3V_SW', out); r += 1
            sh.net(f'{tag}_BIAS', u[bi])
            sh.two('Device:C', f'C{c}', '100n', FP['C'], x0 + 110, y - 10, f'{tag}_BIAS', 'GND'); c += 1
    j = sh.symbol('Connector_Generic:Conn_01x04', 'J301', 'VR spare', 60, 175, FP['HDR4'])
    sh.wire(j, {'1': 'VR_SPARE_P', '2': 'VR_SPARE_N', '3': 'GND', '4': 'VR_SPARE'})
    sh.text('J301: the sixth channel, brought out. No MCU pin: all EXTI lines are taken (carrier-pinmap.md).', 20, 190)
    sh.text('CMP shield (EEC-V 25, 567 LB/YE): single-point to the star through R399. Not SIGRTN. review-vr-chain.md sec.3', 20, 200)
    sh.two('Device:R', 'R399', '0', FP['R'], 200, 200, 'CMP_SHIELD', 'GND')

# Solenoid / heater channels (74HCT541 #3) and PWM channels (74HCT541 #2).
# (MCU net, connector net, freewheel return or None, drain-sense mux net or None)
SOL = [('HTR11', 'HTR11_OUT', None, 'DS_HTR11'), ('HTR21', 'HTR21_OUT', None, 'DS_HTR21'),
       ('HTR12', 'HTR12_OUT', None, 'DS_HTR12'), ('HTR22', 'HTR22_OUT', None, 'DS_HTR22'),
       ('VENT', 'VENT_OUT', None, 'DS_VENT'), ('IMCC', 'IMCC_OUT', None, None),
       ('SSA', 'SSA_OUT', None, None), ('SSB', 'SSB_OUT', None, None)]
PWM = [('EVAP', 'EVAP_OUT', 'FW_391', 'DS_EVAP'), ('EGR', 'EGR_OUT', 'FW_391', None),
       ('TCC', 'TCC_OUT', 'FW_1138', None), ('EPC', 'EPC_OUT', 'FW_1138', None),
       ('IAC', 'IAC_OUT', 'VPWR', None), ('VSS_OUT', 'VSS_OUT_PIN', None, None),
       ('CCS', 'CCS_OUT', None, None)]
MUX = ['DS_HTR11', 'DS_HTR21', 'DS_HTR12', 'DS_HTR22', 'DS_EVAP', 'DS_VENT', 'SUP_1138', 'SUP_391']
# Relay channels (TBD62083AFNG): (MCU net, connector net)
RELAY = [('FPUMP', 'FPUMP_OUT'), ('FAN1', 'FAN1_OUT'), ('FAN2', 'FAN2_OUT'), ('ACC', 'ACC_OUT')]
PTC = dict(value='MF-MSMF030/60-2', fp='Fuse:Fuse_1812_4532Metric',
           fields={'Note': 'PTC 0.30 A hold / 0.60 A trip, 60 V, 1812 [CONFIRM vs coil current]'})
FW_DIODE = dict(value='STPS3H100UY', fields={'Note': 'Schottky >= 60 V 3 A AEC-Q101 [CONFIRM part]'})

def low_side_bank(sh, base, buf_ref, chans, oe_nets, title):
    """74HCT541 at 5 V -> 2.2k -> NCV8405A (or NCV8408B for EPC). Each 541 output
    has a 100k pulldown so a high-Z buffer leaves the gate off."""
    u = sh.symbol('74xx:74HCT541', buf_ref, '74HCT541', 50, 100, FP['SOIC20'])
    sh.wire(u, {'1': oe_nets[0], '19': oe_nets[1], '10': 'GND', '20': '+5V_SW'})
    sh.two('Device:C', f'C{base + 1}', '100n', FP['C'], 35, 135, '+5V_SW', 'GND')
    for k in range(8):
        if k < len(chans):
            mcu, out, fw, ds = chans[k]
            n = k + 1
            sh.wire(u, {str(2 + k): mcu, str(18 - k): f'{mcu}_BUF'})
            y = 40 + k * 21
            sh.two('Device:R', f'R{base + 20 + n}', '100k', FP['R'], 95, y + 6, f'{mcu}_BUF', 'GND')
            g = sh.symbol('Device:R', f'R{base + 10 + n}', '2.2k', 110, y, FP['R'], rot=90)
            sh.wire(g, {'1': f'{mcu}_BUF', '2': f'{mcu}_G'})
            if mcu == 'EPC':
                q = sh.symbol('Transistor_FET:Q_NMOS_GDS', f'Q{base + n}', 'NCV8408BDTRKG', 135, y, FP['DPAK'],
                              fields={'Note': 'self-protected, DPAK; latch reads as gate current'})
                sh.wire(q, {'1': f'{mcu}_G', '2': out, '3': 'GND'})
            else:
                q = sh.symbol('Samacsys:NCV8405ASTT1G', f'Q{base + n}', 'NCV8405ASTT1G', 135, y)
                sh.wire(q, {'1': f'{mcu}_G', '2': out, '4': out, '3': 'GND'})
            if fw:
                d = sh.symbol('Device:D_Schottky', f'D{base + n}', FW_DIODE['value'], 165, y, FP['SMB'],
                              rot=90, fields=FW_DIODE['fields'])
                sh.wire(d, {'1': fw, '2': out})          # cathode to the solenoid feed
            if ds:
                sh.two('Device:R', f'R{base + 30 + n}', '100k', FP['R'], 185, y, out, ds)
                sh.two('Device:R', f'R{base + 40 + n}', '10.5k', FP['R'], 185, y + 10, ds, 'GND')
        else:
            sh.wire(u, {str(2 + k): 'GND', str(18 - k): None})
    sh.text(title, 20, 20)

def solenoids(sh):
    """output-drivers.md: 74HCT541 #3 at 5 V (OE on the watchdog net) -> NCV8405A x8.
    Heaters store nothing; SSA/SSB/IMCC/vent are on/off and use the 42 V clamp.
    Drain sense 100k/10.5k on the heaters and the vent, into the 74HC4051."""
    low_side_bank(sh, 400, 'U401', SOL, ('WD_OE', 'WD_OE'),
                  'Solenoids and heaters: 74HCT541 #3 at 5 V, both OE on WD_OE (watchdog) -> 2.2k -> NCV8405A x8. '
                  'No diodes: on/off loads use the 42 V clamp.')
    sh.text('Drain sense 100k/10.5k: a load dump lands at full scale; open load / short to battery read in software.', 20, 26)
    # the mux: 8 slow diagnostics -> MUX_OUT
    m = sh.symbol('74xx:74HC4051', 'U402', '74HC4051', 250, 120, FP['TSSOP16'])
    ins = {'13': MUX[0], '14': MUX[1], '15': MUX[2], '12': MUX[3], '1': MUX[4], '5': MUX[5], '2': MUX[6], '4': MUX[7]}
    sh.wire(m, ins)
    sh.wire(m, {'3': 'MUX_OUT', '6': 'GND', '7': 'GND', '8': 'GND', '16': '+3.3V_SW',
                '11': 'MUX_S0', '10': 'MUX_S1', '9': 'MUX_S2'})
    sh.two('Device:C', 'C402', '100n', FP['C'], 230, 150, '+3.3V_SW', 'GND')
    for k, net in enumerate(MUX):           # 100 nF on the input side: settling in ns, analog-mux-scan.md
        sh.two('Device:C', f'C{411 + k}', '100n', FP['C'], 280 + 8 * (k % 4), 80 + 30 * (k // 4), net, 'GND')
    sh.text('74HC4051 at 3.3 V: 100 nF on each INPUT, not one after the mux - switching then settles in ns.', 20, 200)

def pwm_loads(sh):
    """output-drivers.md: 74HCT541 #2 at 5 V, OE = PWM_OE (software-releasable) ->
    NCV8405A, EPC on NCV8408B. PWM loads freewheel to their own feed: TCC, EPC to
    1138 (pin 82), EVAP, EGR to 391 (pin 48), IAC to VPWR at the connector side."""
    low_side_bank(sh, 500, 'U501', PWM, ('PWM_OE', 'PWM_OE'),
                  'PWM loads: 74HCT541 #2 at 5 V, OE = PWM_OE (10k up: off at power-on) -> 2.2k -> NCV8405A, EPC NCV8408B. '
                  'Freewheel Schottky to the load feed.')
    sh.two('Device:R', 'R509', '10k', FP['R'], 30, 60, '+5V_SW', 'PWM_OE')
    sh.text('Supply sense on the freewheel pins: 100k/10.5k each, into the mux. A blown fuse 24 is one DTC.', 20, 205)
    for k, (pinnet, sup) in enumerate((('FW_1138', 'SUP_1138'), ('FW_391', 'SUP_391'))):
        sh.two('Device:R', f'R{561 + 2 * k}', '100k', FP['R'], 230 + 20 * k, 215, pinnet, sup)
        sh.two('Device:R', f'R{562 + 2 * k}', '10.5k', FP['R'], 230 + 20 * k, 228, sup, 'GND')
    r = sh.symbol('Device:R', 'R565', '10k', 185, 150, FP['R'], fields={'Note': 'VSS pull-up, NOT POPULATED until circuit 679 level is known'},
                  dnp=True)
    sh.wire(r, {'1': '+5V', '2': 'VSS_OUT_PIN'})

def relays(sh):
    """output-drivers.md, cooling-fans.md sec.5.2: TBD62083AFNG straight from 3.3 V GPIO
    (VIN(ON) 2.5 V at 0.1 mA). Clamp diodes are built in, all to COMMON, which goes to
    permanent B+ so the run-on fan coils (on B+) are clamped above their own feed.
    No current limit in the part: the PTC is the only over-current protection
    (harness-protection.md, review-protection-sweep.md B1)."""
    sh.text('Relays: TBD62083AFNG, direct from GPIO. 100k pulldown holds every relay off through reset.', 20, 20)
    sh.text('COMMON = permanent B+ (EEC-V 55, 729 RD/WH, CJB 5 A): every coil feed is at or below it, so no channel', 20, 24)
    sh.text('back-feeds. [CONFIRM] sharing pin 55 with the battery-sense divider: clamp current is only the coil decay.', 20, 28)
    sh.text('PTC in series: the array has no current limit, so a shorted coil is stopped by F60x. Coil currents [CONFIRM] on the truck.', 20, 32)
    u = sh.symbol('Samacsys:TBD62083AFNG', 'U601', 'TBD62083AFNG', 110, 90)
    sh.wire(u, {'9': 'GND', '10': 'VBAT_SENSE'})
    for k in range(8):
        if k < len(RELAY):
            mcu, out = RELAY[k]
            n = k + 1
            sh.net(mcu, u[str(1 + k)])
            sh.net(f'{mcu}_SINK', u[str(18 - k)])
            sh.two('Device:R', f'R{600 + n}', '100k', FP['R'], 70 + 8 * k, 130, mcu, 'GND')
            f = sh.symbol('Device:Polyfuse', f'F{600 + n}', PTC['value'], 170, 60 + 15 * k, PTC['fp'], rot=90,
                          fields=PTC['fields'])
            sh.wire(f, {'1': f'{mcu}_SINK', '2': out})
        else:
            sh.wire(u, {str(1 + k): 'GND', str(18 - k): None})
    sh.two('Device:C', 'C601', '100n', FP['C0805'], 140, 130, 'VBAT_SENSE', 'GND', fields={'Note': '100 V X7R'})
    sh.text('Channels 5-8 spare: inputs to GND, outputs open. No MCU pins left for them (carrier-pinmap.md).', 20, 160)

def vref(sh):
    """vref-supply.md, review-vref-chain.md: NCV8772C 5.00 V LDO on the protected rail
    (VPROT, LTC4364 out), EN from the MCU -> TPS2H160B-Q1 dual high-side switch, 248 mA
    limit per feed -> LM74700-Q1 + DMN6040 ideal diode -> feed, SMAJ24CA to GND.
    One VREF pin on this truck (90): channel 2's chain is drawn and not fitted."""
    sh.text('VREF: NCV8772C 5.00 V on VPROT (the LTC4364 output, not the 5 V buck-boost), EN under MCU control.', 20, 20)
    sh.text('TPS2H160B-Q1: RCL 8.06k = 248 mA per feed; RCS 2.2k (2.5 V linear ceiling at VS = 5 V); THER high = latch.', 20, 24)
    sh.text('LM74700-Q1 + DMN6040 (VGS +-20 V) blocks a short to battery; SMAJ24CA stands off 24 V, transients only. No PPTC.', 20, 28)
    sh.text('Firmware sheds a faulted channel (t_CL deg 80-180 us), retries seconds apart. Hold IN1/IN2/SEL low while EN is low.', 20, 32)
    # regulator
    u = sh.symbol(f'{CLIB}:NCV8772', 'U701', 'NCV8772CDT504RKG', 60, 70, FP['DPAK5'])
    sh.wire(u, {'1': 'VPROT', '4': 'VREF_EN', '3': 'GND', '5': 'VREF_5V', '2': None})
    sh.two('Device:R', 'R701', '100k', FP['R'], 35, 90, 'VREF_EN', 'GND')
    sh.two('Device:C', 'C701', '1u', FP['C0805'], 30, 60, 'VPROT', 'GND', fields={'Note': '50 V X7R'})
    sh.two('Device:C', 'C702', '100n', FP['C'], 40, 60, 'VPROT', 'GND', fields={'Note': '50 V'})
    sh.two('Device:C', 'C703', '22u', 'Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder', 85, 60,
           'VREF_5V', 'GND', fields={'Note': 'X7R >= 16 V; sized for the 250 mA step'})
    sh.two('Device:C', 'C704', '100n', FP['C'], 95, 60, 'VREF_5V', 'GND')
    sh.text('VREF_5V is the ratiometric divisor: the ADS8588H senses it here, one channel for both feeds.', 20, 100)
    # switch
    w = sh.symbol('Samacsys:TPS2H160BQPWPRQ1', 'U702', 'TPS2H160BQPWPRQ1', 140, 120)
    sh.wire(w, {'13': 'VREF_5V', '14': 'VREF_5V', '8': 'GND', '17': 'GND', '10': None,
                '1': 'VREF_IN1', '2': 'VREF_IN2', '5': 'VREF_SEL', '4': 'VREF_FAULT',
                '3': 'VREF_DIAG', '9': 'VREF_THER', '6': 'VREF_CS_RAW', '7': 'VREF_CL',
                '15': 'VREF1_SW', '16': 'VREF1_SW', '11': 'VREF2_SW', '12': 'VREF2_SW'})
    sh.two('Device:C', 'C705', '100n', FP['C'], 120, 150, 'VREF_5V', 'GND')
    sh.two('Device:R', 'R702', '10k', FP['R'], 100, 130, 'VREF_5V', 'VREF_DIAG', fields={'Note': 'DIAG_EN high, from VS'})
    sh.two('Device:R', 'R703', '10k', FP['R'], 108, 130, 'VREF_5V', 'VREF_THER', fields={'Note': 'THER high = latch, from VS'})
    sh.two('Device:R', 'R704', '10k', FP['R'], 116, 165, '+3.3V_SW', 'VREF_FAULT')
    sh.two('Device:R', 'R705', '2.2k', FP['R'], 100, 175, 'VREF_CS_RAW', 'GND', fields={'Note': 'RCS, 1 %'})
    r = sh.symbol('Device:R', 'R706', '4.7k', 85, 165, FP['R'], rot=90)
    sh.wire(r, {'1': 'VREF_CS_RAW', '2': 'VREF_CS'})
    d = sh.symbol('Device:D_Schottky', 'D703', 'BAT54J', 70, 155, FP['SOD323'], rot=90,
                  fields={'Note': 'CS is driven to the rail in a fault'})
    sh.wire(d, {'1': '+3.3V', '2': 'VREF_CS'})
    sh.two('Device:R', 'R707', '8.06k', FP['R'], 92, 175, 'VREF_CL', 'GND', fields={'Note': 'RCL, 1 %: 248 mA'})
    # per feed: ideal diode, TVS
    for ch, feed in ((1, 'VREF'), (2, 'VREF2')):
        dnp = ch == 2
        y = 70 + (ch - 1) * 70
        sw, g, vc = f'VREF{ch}_SW', f'VREF{ch}_G', f'VREF{ch}_VCAP'
        c = sh.symbol('Power_Management:LM74700', f'U70{2 + ch}', 'LM74700QDBVRQ1', 220, y + 25, dnp=dnp)
        sh.wire(c, {'6': sw, '3': sw, '4': feed, '5': g, '1': vc, '2': 'GND'})
        f = sh.symbol('power:PWR_FLAG', f'#FLG7{ch:02d}', 'PWR_FLAG', 195.58, round((y + 22.86) / 2.54) * 2.54)     # OUTn is a supply
        sh.net(sw, f['1'])
        q = sh.symbol('Samacsys:DMN6040SVTQ-7', f'Q70{ch}', 'DMN6040SVTQ-7', 215, y, dnp=dnp)
        sh.wire(q, {'4': sw, '3': g, '1': feed, '2': feed, '5': feed, '6': feed})
        for ref, val, x, a, b in ((f'C{705 + ch}', '100n', 250, vc, sw), (f'C{707 + ch}', '22n', 258, sw, 'GND')):
            k = sh.symbol('Device:C', ref, val, x, y + 20, FP['C'], dnp=dnp)
            sh.net(a, k['1']); sh.net(b, k['2'])
        t = sh.symbol('Device:D_TVS', f'D70{ch}', 'SMAJ24CA', 275, y + 10, FP['SMA'], rot=90,
                      fields={'Note': 'bidirectional, 24 V standoff; buy AEC-Q101 [DECIDE] maker'}, dnp=dnp)
        sh.wire(t, {'1': feed, '2': 'GND'})
    tp = sh.symbol('Connector:TestPoint', 'TP701', 'VREF2', 290, 150, 'TestPoint:TestPoint_Pad_D1.5mm', dnp=True)
    sh.wire(tp, {'1': 'VREF2'})
    sh.text('Channel 2 (U704, Q702, D702, TP701) not fitted: this truck has one VREF pin, 90. Never enable IN2.', 180, 205)
    # short-to-battery sense, feed 1
    sh.text('Short to battery: 100k/12.4k from the feed. 5 V -> 0.55 V, 14 V -> 1.54 V, 27 V -> 2.98 V. Returns to the ADC ground.', 20, 205)
    sh.two('Device:R', 'R708', '100k', FP['R'], 300, 70, 'VREF', 'VREF_STB')
    sh.two('Device:R', 'R709', '12.4k', FP['R'], 300, 85, 'VREF_STB', 'GND', fields={'Note': '1 %'})
    sh.two('Device:C', 'C710', '10n', FP['C'], 310, 85, 'VREF_STB', 'GND')
    d = sh.symbol('Device:D_Schottky', 'D704', 'BAT54J', 320, 70, FP['SOD323'], rot=90)
    sh.wire(d, {'1': '+3.3V', '2': 'VREF_STB'})

def adc(sh):
    """adc-front-end.md (channels, straps, battery divider), always-on-domain.md
    (MAX6070 reference), o2-input-stage.md, knock-front-end-schematic.md, tft-sensor.md.
    ADS8588H, serial on DOUTA, +-10 V, external 2.5 V reference."""
    R = iter(range(801, 900)); C = iter(range(801, 900)); D = iter(range(801, 900))
    def r(val, x, y, a, b, fp=None, **kw):
        sh.two('Device:R', f'R{next(R)}', val, fp or FP['R'], x, y, a, b, **kw)
    def c(val, x, y, a, b, fp=None, **kw):
        sh.two('Device:C', f'C{next(C)}', val, fp or FP['C'], x, y, a, b, **kw)
    def clamp(x, y, node):                          # Schottky from node up to +3.3V
        d = sh.symbol('Device:D_Schottky', f'D{next(D)}', 'BAT54J', x, y, FP['SOD323'], rot=90)
        sh.wire(d, {'1': '+3.3V', '2': node})

    sh.text('ADC: ADS8588H, serial on DOUTA, RANGE high = +-10 V (forced: ch 8 is VREF at 5.00 V), OS0-2 low, external 2.5 V reference.', 20, 16)
    sh.text('Ch: 1 MAF diff (968 return on AIN1GND), 2 TPS, 3 HO2S 21, 4 HO2S 11 (buffered), 5 CHT, 6 IAT, 7 battery 180k/30k, 8 VREF_5V.', 20, 20)
    sh.text('AGND: the ADS8588H, its reference and its input conditioning. Meets GND and SIGRTN only at NT801, the star', 20, 24)
    sh.text('under EEC-V 91. TPS, CHT, IAT and VREF sense are measured against SIGRTN (VxGND), MAF against MAF_RTN.', 20, 28)
    # --- the converter
    u = sh.symbol('Samacsys:ADS8588HIPM', 'U801', 'ADS8588HIPM', 40, 60)
    nets = {'1': '+5V_SW', '37': '+5V_SW', '38': '+5V_SW', '48': '+5V_SW', '23': '+3.3V_SW',
            '2': 'AGND', '26': 'AGND', '35': 'AGND', '40': 'AGND', '41': 'AGND', '47': 'AGND', '43': 'AGND', '46': 'AGND',
            '3': 'AGND', '4': 'AGND', '5': 'AGND', '6': '+3.3V_SW', '7': '+3.3V_SW', '8': '+3.3V_SW', '34': 'AGND',
            '9': 'ADC_CONVST', '10': 'ADC_CONVSTB', '11': 'ADC_RESET', '12': 'ADC_SCK', '13': 'ADC_CS',
            '14': 'ADC_BUSY', '15': None, '24': 'ADC_MISO', '25': None,
            '36': 'ADC_REGCAP1', '39': 'ADC_REGCAP2', '42': 'ADC_REF', '44': 'ADC_REFCAP', '45': 'ADC_REFCAP',
            '16': 'ADC_DB0', '17': 'ADC_DB1', '18': 'ADC_DB2', '29': 'ADC_DB11', '32': 'ADC_DB14', '33': 'ADC_DB15'}
    for k in ('19', '20', '21', '22', '27', '28', '30', '31'):
        nets[k] = None
    ain = [('MAF_A', 'MAF_G'), ('TPS_A', 'TPS_G'), ('O2_21_A', 'AGND'), ('O2_11_A', 'AGND'),
           ('CHT_A', 'CHT_G'), ('IAT_A', 'IAT_G'), ('VBAT_A', 'AGND'), ('VREF_5V', 'SIGRTN')]
    for i, (pnet, gnet) in enumerate(ain):
        nets[str(49 + 2 * i)] = pnet; nets[str(50 + 2 * i)] = gnet
    sh.wire(u, nets)
    # REFCAPA/B are shorted by the datasheet's own instruction; the import types them
    # as outputs, so the embedded copy makes them passive (ERC pin_to_pin otherwise)
    emb, pins, fp0 = sh.libs['Samacsys:ADS8588HIPM']
    emb = re.sub(r'\(pin output(\s+line\s+\(at [^)]*\)\s+\(length [^)]*\)\s+\(name "REFCAP[AB]")', r'(pin passive\1', emb)
    sh.libs['Samacsys:ADS8588HIPM'] = (emb, pins, fp0)
    r('0', 30, 140, 'ADC_CONVST', 'ADC_CONVSTB', fields={'Note': 'CONVSTA-B link: a 0R, not a trace (AD7606C WR)'})
    for k, n in enumerate(('ADC_DB0', 'ADC_DB1', 'ADC_DB2', 'ADC_DB11', 'ADC_DB14', 'ADC_DB15')):
        r('10k', 40 + 7 * k, 140, n, 'AGND')
    sh.text('10k pull-downs: DB0-2 per the AD7606C serial rule, DB15/BYTE SEL low = serial not byte mode, DB11/DB14 parked.', 20, 152)
    for k in range(4):
        c('100n', 90 + 7 * k, 140, '+5V_SW', 'AGND')
    c('10u', 118, 140, '+5V_SW', 'AGND', FP['C0805'])
    c('100n', 125, 140, '+3.3V_SW', 'AGND')
    c('1u', 90, 160, 'ADC_REGCAP1', 'AGND'); c('1u', 97, 160, 'ADC_REGCAP2', 'AGND')
    c('10u', 104, 160, 'ADC_REFCAP', 'AGND', FP['C0805'], fields={'Note': 'REFCAPA+B shorted, low ESR'})
    # --- the star: the only copper joining AGND, GND and SIGRTN
    nt = sh.symbol('Device:NetTie_3', 'NT801', 'NetTie_3', 55, 165, 'NetTie:NetTie-3_SMD_Pad0.5mm',
                   fields={'Note': 'star point: place under EEC-V 91, beside R399'})
    sh.wire(nt, {'1': 'GND', '2': 'AGND', '3': 'SIGRTN'})
    f = sh.symbol('power:PWR_FLAG', '#FLG802', 'PWR_FLAG', 68.58, 162.56)
    sh.net('AGND', f['1'])
    # --- the 2.5 V reference, gated, on 3.3 V (EN is 0.7 x VIN)
    sh.text('Reference: MAX6070AAUT25 on 3.3 V (EN threshold is 0.7 x VIN). 220R + 10u in, 0.1u FILTER, 4.7u + 100n at REFIN.', 150, 40)
    sh.text('EN gated by ADC_REF_EN, 10k pull-down holds it off in Standby. 25 ms wait after enable. REFSEL low = external.', 150, 44)
    rf = sh.symbol('Reference_Voltage:MAX6070AAUT25+T', 'U802', 'MAX6070AAUT25+T', 190, 70)
    sh.wire(rf, {'4': 'ADC_REF_IN', '3': 'ADC_REF_EN', '2': 'AGND', '1': 'ADC_REF_FLT', '5': 'ADC_REF', '6': 'ADC_REF'})
    a = sh.symbol('Device:R', f'R{next(R)}', '220', 160, 60, FP['R'], rot=90)
    sh.wire(a, {'1': '+3.3V', '2': 'ADC_REF_IN'})
    f = sh.symbol('power:PWR_FLAG', '#FLG801', 'PWR_FLAG', 152.4, 66.04)    # the RC-filtered 3.3 V
    sh.net('ADC_REF_IN', f['1'])
    c('10u', 160, 75, 'ADC_REF_IN', 'AGND', FP['C0805']); c('100n', 168, 75, 'ADC_REF_IN', 'AGND')
    r('10k', 175, 90, 'ADC_REF_EN', 'AGND')
    c('100n', 215, 90, 'ADC_REF_FLT', 'AGND', fields={'Note': 'CFILTER'})
    c('4.7u', 225, 70, 'ADC_REF', 'AGND', FP['C0805'], fields={'Note': 'X7R 16 V, at REFIN'})
    c('100n', 233, 70, 'ADC_REF', 'AGND')
    # --- unbuffered inputs: series footprint fitted as 0R until review-analog-chain #4 is decided
    sh.text('Unbuffered channels: series resistor footprints fitted 0R - review-analog-chain.md #4 is [DECIDE]. Thermistor', 150, 110)
    sh.text('pull-ups from VREF_5V (ratiometric with ch 8); value [CONFIRM] against Ford tables. Battery: no filter cap.', 150, 114)
    for k, (src, dst) in enumerate((('MAF_IN', 'MAF_A'), ('TPS_IN', 'TPS_A'), ('CHT_IN', 'CHT_A'), ('IAT_IN', 'IAT_A'))):
        a = sh.symbol('Device:R', f'R{next(R)}', '0', 165, 125 + 10 * k, FP['R'], rot=90,
                      fields={'Note': 'series R [DECIDE]'})
        sh.wire(a, {'1': src, '2': dst})
    r('2.49k', 190, 145, 'VREF_5V', 'CHT_IN', fields={'Note': 'CHT pull-up [CONFIRM]'})
    r('2.49k', 198, 145, 'VREF_5V', 'IAT_IN', fields={'Note': 'IAT pull-up [CONFIRM]'})
    t = sh.symbol('Device:D_TVS', f'D{next(D)}', 'SMBJ30A', 215, 130, FP['SMB'], rot=90,
                  fields={'Note': 'unidirectional; pin 55 transient, same as the lead TVS3'})
    sh.wire(t, {'1': 'VBAT_SENSE', '2': 'GND'})
    r('180k', 225, 125, 'VBAT_SENSE', 'VBAT_A', fields={'Note': '1 %, ratio 7.000'})
    r('30k', 225, 140, 'VBAT_A', 'AGND', fields={'Note': '1 %'})
    # --- O2: four buffered channels on +5V
    sh.text('HO2S x4: 10k + 1n + BAT54S to +5V, 22M to the 455 mV bias node, OPA2376 follower, 1k + 1u after it. JP = 0R not fitted.', 250, 40)
    sh.text('Guard each 22M node with a ring driven from the buffer output. Downstream pair: BAT54J to 3.3 V, the MCU ADC is 3.3 V.', 250, 44)
    o2 = [('O2_21_IN', 'O2_21_A'), ('O2_11_IN', 'O2_11_A'), ('O2_12_IN', 'O2_DN1'), ('O2_22_IN', 'O2_DN2')]
    for pk in range(2):
        op = sh.symbol(f'{CLIB}:OPAMP2', f'U{803 + pk}', 'OPA2376AQDRQ1', 330, 70 + 70 * pk, FP['SOIC8'])
        sh.wire(op, {'8': '+5V_SW', '4': 'GND'})
        c('100n', 345, 90 + 70 * pk, '+5V_SW', 'GND')
        for half in range(2):
            ch = 2 * pk + half
            src, dst = o2[ch]
            tag = f'O2_{ch + 1}'
            y = 55 + 35 * ch
            ip, im, out = (('3', '2', '1'), ('5', '6', '7'))[half]
            a = sh.symbol('Device:R', f'R{next(R)}', '10k', 262, y, FP['R0805'], rot=90, fields={'Note': '1 %, fault limit'})
            sh.wire(a, {'1': src, '2': f'{tag}_HZ'})
            c('1n', 275, y + 10, f'{tag}_HZ', 'GND', fields={'Note': 'C0G 50 V'})
            dd = sh.symbol('Diode:BAT54S', f'D{next(D)}', 'BAT54S', 285, y + 10)
            sh.wire(dd, {'1': 'GND', '2': '+5V_SW', '3': f'{tag}_HZ'})
            r('22M', 297, y + 10, f'{tag}_HZ', 'O2_BIASNODE', FP['R0805'], fields={'Note': '1 %, guard the node'})
            sh.net(f'{tag}_HZ', op[ip]); sh.net(f'{tag}_BUF', op[im]); sh.net(f'{tag}_BUF', op[out])
            a = sh.symbol('Device:R', f'R{next(R)}', '1k', 360, y, FP['R'], rot=90)
            sh.wire(a, {'1': f'{tag}_BUF', '2': dst})
            ret, note = ('GND', 'X7R 16 V') if dst.startswith('O2_DN') else ('AGND', 'X7R 16 V, at the converter')
            c('1u', 372, y + 10, dst, ret, fields={'Note': note})
            j = sh.symbol('Device:R', f'R{next(R)}', '0', 385, y + 10, FP['R'], dnp=True,
                          fields={'Note': 'JP: bypass the buffer for a 0-5 V wideband module'})
            sh.wire(j, {'1': f'{tag}_HZ', '2': dst})
            if dst.startswith('O2_DN'):
                clamp(395, y + 10, dst)
    r('91k', 300, 205, '+5V_SW', 'O2_BIASNODE', fields={'Note': '1 %'})
    r('9.1k', 300, 220, 'O2_BIASNODE', 'GND', fields={'Note': '1 %'})
    c('100n', 310, 220, 'O2_BIASNODE', 'GND')
    a = sh.symbol('Device:R', f'R{next(R)}', '1k', 285, 212, FP['R'], rot=90, fields={'Note': 'DAC excitation, o2-input-stage.md sec.7'})
    sh.wire(a, {'1': 'O2_BIAS', '2': 'O2_BIASNODE'})
    # --- knock: differential charge amp, on 3.3 V
    sh.text('Knock: TLV9064 differential charge amp. ON 3.3 V with VMID 1.8 V (MAX6070AAUT18), NOT 5 V / 2.5 V as drawn in', 20, 175)
    sh.text('knock-front-end-schematic.md: KNOCK lands on PC3, a 3.3 V ADC. Cf 220p C0G, Rf 1M, R5-R8 0.1 % matched. Guard KP/KN_IN.', 20, 179)
    k4 = sh.symbol(f'{CLIB}:OPAMP4', 'U805', 'TLV9064QPWRQ1', 120, 225, FP['TSSOP14'])
    sh.wire(k4, {'4': '+3.3V_SW', '11': 'GND', '2': 'KP_IN', '3': 'VMID', '1': 'KA_OUT', '6': 'KN_IN', '5': 'VMID', '7': 'KB_OUT',
                 '9': 'KC_N', '10': 'KC_P', '8': 'KNOCK_DIFF', '12': 'VMID_F', '13': 'VMID', '14': 'VMID'})
    c('100n', 140, 255, '+3.3V_SW', 'GND')
    for leg, (src, node, outn) in enumerate((('KNOCK_IN', 'KP_IN', 'KA_OUT'), ('KNOCK_RTN', 'KN_IN', 'KB_OUT'))):
        y = 200 + 30 * leg
        a = sh.symbol('Device:R', f'R{next(R)}', '1k', 40, y, FP['R'], rot=90, fields={'Note': '1 %'})
        sh.wire(a, {'1': src, '2': node})
        dd = sh.symbol('Diode:BAT54S', f'D{next(D)}', 'BAV199', 30, y + 12, fields={'Note': 'low-leakage, not BAV99'})
        sh.wire(dd, {'1': 'GND', '2': '+3.3V_SW', '3': src})
        c('220p', 60, y + 8, node, outn, fields={'Note': 'C0G 5 %: the knock calibration'})
        r('1M', 70, y + 8, node, outn, fields={'Note': '1 %'})
    a = sh.symbol('Device:R', f'R{next(R)}', '10k', 85, 260, FP['R'], rot=90, fields={'Note': '0.1 % matched'})
    sh.wire(a, {'1': 'KA_OUT', '2': 'KC_N'})
    a = sh.symbol('Device:R', f'R{next(R)}', '10k', 85, 270, FP['R'], rot=90, fields={'Note': '0.1 % matched'})
    sh.wire(a, {'1': 'KB_OUT', '2': 'KC_P'})
    r('10k', 100, 265, 'KC_N', 'KNOCK_DIFF', fields={'Note': '0.1 % matched'})
    r('10k', 108, 265, 'KC_P', 'VMID', fields={'Note': '0.1 % matched'})
    c('620p', 116, 265, 'KC_N', 'KNOCK_DIFF', fields={'Note': 'C0G'})
    c('620p', 124, 265, 'KC_P', 'VMID', fields={'Note': 'C0G'})
    a = sh.symbol('Device:R', f'R{next(R)}', '470', 160, 215, FP['R'], rot=90)
    sh.wire(a, {'1': 'KNOCK_DIFF', '2': 'KNOCK'})
    c('15n', 172, 225, 'KNOCK', 'GND')
    kr = sh.symbol('Reference_Voltage:MAX6070AAUT18+T', 'U806', 'MAX6070AAUT18+T', 190, 250)
    sh.wire(kr, {'4': '+3.3V_SW', '3': '+3.3V_SW', '2': 'GND', '1': 'KNK_FLT', '5': 'VREF_KNK', '6': 'VREF_KNK'})
    c('100n', 175, 265, '+3.3V_SW', 'GND'); c('100n', 210, 265, 'KNK_FLT', 'GND')
    c('1u', 218, 245, 'VREF_KNK', 'GND')
    a = sh.symbol('Device:R', f'R{next(R)}', '100', 230, 240, FP['R'], rot=90)
    sh.wire(a, {'1': 'VREF_KNK', '2': 'VMID_F'})
    c('1u', 240, 250, 'VMID_F', 'GND')
    # --- slow channels on the MCU's own ADC
    sh.text('MCU ADC (3.3 V): DPFE 0-5 V via 10k/18k, TFT 2.2k pull-up from 3.3 V (tft-sensor.md), FP monitor 100k/10.5k', 250, 245)
    sh.text('like the solenoid supply sense. 1k into each pin + BAT54J to 3.3 V where the harness can reach the pin.', 250, 249)
    r('10k', 260, 260, 'DPFE_IN', 'DPFE', fields={'Note': '1 %'}); r('18k', 260, 275, 'DPFE', 'GND', fields={'Note': '1 %'})
    c('10n', 268, 275, 'DPFE', 'GND'); clamp(276, 270, 'DPFE')
    r('2.2k', 295, 255, '+3.3V_SW', 'TFT_IN', fields={'Note': '1 %, TFT pull-up'})
    a = sh.symbol('Device:R', f'R{next(R)}', '1k', 305, 265, FP['R'], rot=90)
    sh.wire(a, {'1': 'TFT_IN', '2': 'TFT'})
    c('100n', 318, 275, 'TFT', 'GND'); clamp(326, 270, 'TFT')
    r('100k', 345, 260, 'FP_MON_IN', 'FP_MON'); r('10.5k', 345, 275, 'FP_MON', 'GND')
    c('100n', 353, 275, 'FP_MON', 'GND')
    # --- negative-input legs (ADS8588H SBAS843A 7.3.2: match AIN_nP's series R on AIN_nGND; 6.5: +-0.3 V)
    # Last in the sheet so the references above keep their numbers.
    for k, t in enumerate(('AIN_nGND legs (ADS8588H 7.3.2): series R matched to',
                           'the AIN_nP series R, fitted 0R alongside them.',
                           'MAF_RTN is the only remote one (+-0.3 V operating):',
                           'BAV199 to AGND/+5V_SW, 10k so an open 968 reads 0.')):
        sh.text(t, 195, 166 + 3 * k, 1.27)
    for k, (src, dst, sig) in enumerate((('MAF_RTN', 'MAF_G', 'MAF'), ('SIGRTN', 'TPS_G', 'TPS'),
                                         ('SIGRTN', 'CHT_G', 'CHT'), ('SIGRTN', 'IAT_G', 'IAT'))):
        a = sh.symbol('Device:R', f'R{next(R)}', '0', 200 + 12 * k, 185, FP['R'], rot=90,
                      fields={'Note': f'match the {sig}_IN series R'})
        sh.wire(a, {'1': src, '2': dst})
    r('10k', 205, 198, 'MAF_G', 'AGND', fields={'Note': 'defines AIN_1GND if 968 opens'})
    dd = sh.symbol('Diode:BAT54S', f'D{next(D)}', 'BAV199', 218, 198, fields={'Note': 'low-leakage, not BAV99'})
    sh.wire(dd, {'1': 'AGND', '2': '+5V_SW', '3': 'MAF_G'})

def comms(sh):
    """f150-1999-target.md sec.5.3 + review-scp-chain.md (SCP), can-bus.md (CAN),
    USB-C device port, microSD on SDMMC2 1-bit behind a load switch."""
    R = iter(range(901, 1000)); C = iter(range(901, 1000)); D = iter(range(901, 1000))
    def r(val, x, y, a, b, fp=None, **kw):
        sh.two('Device:R', f'R{next(R)}', val, fp or FP['R'], x, y, a, b, **kw)
    def c(val, x, y, a, b, fp=None, **kw):
        sh.two('Device:C', f'C{next(C)}', val, fp or FP['C'], x, y, a, b, **kw)
    def ser(val, x, y, a, b, **kw):
        k = sh.symbol('Device:R', f'R{next(R)}', val, x, y, FP['R'], rot=90, **kw)
        sh.wire(k, {'1': a, '2': b})
    # --- SCP / J1850 PWM
    sh.text('SCP (J1850 PWM, EEC-V 16 = SCP+, 15 = SCP-): DRV8837 drives, TLV7031 receives. Passive state is IN1 = IN2 = LOW (coast,', 20, 16)
    sh.text('Hi-Z) so another node can win arbitration; nSLEEP 10k low releases the whole bus at power-on. 100R per TX line.', 20, 20)
    sh.text('RX divider 100k:100k BOTH to GND (not 10k:100k, not to 3.3 V: the two OpenJ1850 traps), MM3Z3V3 clamps, 4.7M hysteresis.', 20, 24)
    u = sh.symbol('Driver_Motor:DRV8837', 'U901', 'DRV8837DSGR', 60, 60)
    sh.wire(u, {'1': '+5V', '8': '+3.3V', '4': 'GND', '9': 'GND', '6': 'J1850_TXP', '5': 'J1850_TXN',
                '7': 'J1850_NSLEEP', '2': 'SCP_TXP', '3': 'SCP_TXN'})
    r('10k', 35, 80, 'J1850_NSLEEP', 'GND', fields={'Note': 'bus released until firmware runs'})
    c('100n', 45, 80, '+5V', 'GND'); c('1u', 52, 80, '+5V', 'GND'); c('100n', 75, 80, '+3.3V', 'GND')
    ser('100', 95, 55, 'SCP_TXP', 'SCP_P', fields={'Note': 'harness fault limit, 83 mA into VM'})
    ser('100', 95, 65, 'SCP_TXN', 'SCP_N')
    t = sh.symbol('Power_Protection:NUP2105L', f'D{next(D)}', 'NUP2105L', 115, 60,
                  fields={'Note': '24 V standoff, ~30 pF: transients only [CONFIRM]'})
    sh.wire(t, {'1': 'SCP_P', '2': 'SCP_N', '3': 'GND'})
    for k, (bus, node) in enumerate((('SCP_P', 'SCP_RXP'), ('SCP_N', 'SCP_RXN'))):
        y = 100 + 20 * k
        ser('100k', 40, y, bus, node)
        r('100k', 55, y + 8, node, 'GND')
        z = sh.symbol('Diode:MM3Zxx', f'D{next(D)}', 'MM3Z3V3BW', 65, y + 8, rot=90)
        sh.wire(z, {'1': node, '2': 'GND'})
    cmp_ = sh.symbol('Comparator:TLV7031DBV', 'U902', 'TLV7031DBVR', 95, 110)
    sh.wire(cmp_, {'5': '+3.3V', '2': 'GND', '3': 'SCP_RXP', '4': 'SCP_RXN', '1': 'SCP_CMP'})
    c('100n', 110, 125, '+3.3V', 'GND')
    r('4.7M', 85, 135, 'SCP_CMP', 'SCP_RXP', fields={'Note': 'hysteresis, about +-35 mV'})
    ser('100', 120, 110, 'SCP_CMP', 'J1850_RX')
    z = sh.symbol('Device:D_Zener', f'D{next(D)}', 'SMF3.3A', 135, 120, 'Diode_SMD:D_SMF', rot=90,
                  fields={'Note': 'unidirectional TVS: OUT has the same VCC + 0.3 V limit as the inputs'})
    sh.wire(z, {'1': 'J1850_RX', '2': 'GND'})
    # --- CAN
    sh.text('CAN (private, to the dash display; EEC-V 42 = CAN_H, 43 = CAN_L, terminals added): TJA1042T/3, 10 uA standby.', 170, 16)
    sh.text('RXD goes to CAN1_RX (PD0) AND to PA0/WKUP1 through R9xx: Standby wakes only on a WKUP pin. STB has an internal pull-up.', 170, 20)
    x = sh.symbol('Interface_CAN_LIN:TJA1042T-3', 'U903', 'TJA1042T/3', 210, 60)
    sh.wire(x, {'1': 'CAN_TX', '4': 'CAN_RX', '8': 'CAN_STB', '3': '+5V', '5': '+3.3V', '2': 'GND',
                '7': 'CAN_H', '6': 'CAN_L'})
    r('0', 185, 80, 'CAN_RX', 'CAN_RX_WAKE', fields={'Note': 'RXD to WKUP1 too: one net on two pins'})
    c('100n', 230, 80, '+5V', 'GND'); c('4.7u', 237, 80, '+5V', 'GND', FP['C0805']); c('100n', 244, 80, '+3.3V', 'GND')
    sh.text('TERMINATION - this ECU is a bus END. Split, matched 1 %: 2 x 60.4R + 4.7n. A THIRD node must NOT terminate.', 170, 100)
    r('60.4', 260, 110, 'CAN_H', 'CAN_SPLIT', 'Resistor_SMD:R_1206_3216Metric_Pad1.30x1.75mm_HandSolder', fields={'Note': '1 %, matched'})
    r('60.4', 260, 125, 'CAN_SPLIT', 'CAN_L', 'Resistor_SMD:R_1206_3216Metric_Pad1.30x1.75mm_HandSolder', fields={'Note': '1 %, matched'})
    c('4.7n', 272, 125, 'CAN_SPLIT', 'GND')
    t = sh.symbol('Power_Protection:NUP2105L', f'D{next(D)}', 'NUP2105L', 290, 115,
                  fields={'Note': 'the CAN bus TVS, 24 V standoff'})
    sh.wire(t, {'1': 'CAN_H', '2': 'CAN_L', '3': 'GND'})
    # --- USB-C device
    sh.text('USB-C, device only (tuning, flashing): 5.1k on CC1/CC2, USBLC6-2SC6, VBUS sensed only (never powers the ECU).', 20, 165)
    j = sh.symbol('Connector:USB_C_Receptacle_USB2.0_16P', 'J901', 'USB4105-GF-A', 50, 210,
                  'Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal')
    vb = 'USB_VBUS_C'
    sh.wire(j, {'A4': vb, 'A9': vb, 'B4': vb, 'B9': vb, 'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND',
                'A6': 'USB_DP', 'B6': 'USB_DP', 'A7': 'USB_DM', 'B7': 'USB_DM', 'A5': 'USB_CC1', 'B5': 'USB_CC2',
                'A8': None, 'B8': None, 'SH': 'USB_SHIELD'})
    r('5.1k', 90, 230, 'USB_CC1', 'GND'); r('5.1k', 97, 230, 'USB_CC2', 'GND')
    e = sh.symbol('Power_Protection:USBLC6-2SC6', 'U904', 'USBLC6-2SC6', 120, 200)
    sh.wire(e, {'1': 'USB_DP', '6': 'USB_DP', '3': 'USB_DM', '4': 'USB_DM', '5': vb, '2': 'GND'})
    r('15k', 140, 195, vb, 'USB_VBUS', fields={'Note': '5 V -> 3.2 V at PA9'})
    r('27k', 140, 210, 'USB_VBUS', 'GND')
    c('1u', 150, 195, vb, 'GND')
    r('1M', 105, 245, 'USB_SHIELD', 'GND'); c('4.7n', 113, 245, 'USB_SHIELD', 'GND', fields={'Note': '50 V'})
    # --- microSD
    sh.text('microSD, SDMMC2 1-bit. Card power through TPS22917 on SD_PWR_EN (100k down): 3.3 V is always on and an idle', 170, 165)
    sh.text('card alone is ~100 uA against the 184 uA parked budget. Pull-ups go to the CARD rail so nothing back-powers it. No CD pin.', 170, 169)
    w = sh.symbol('Power_Management:TPS22917DBV', 'U905', 'TPS22917DBVR', 200, 200)
    sh.wire(w, {'1': '+3.3V', '2': 'GND', '3': 'SD_PWR_EN', '4': 'SD_CT', '5': 'SD_QOD', '6': 'SD_3V3'})
    r('100', 215, 210, 'SD_QOD', 'SD_3V3', fields={'Note': 'quick output discharge, rate-limited'})
    r('100k', 180, 220, 'SD_PWR_EN', 'GND')
    c('1u', 180, 190, '+3.3V', 'GND')
    c('1n', 205, 225, 'SD_CT', 'GND', fields={'Note': 'slew: no inrush dip on the MCU rail'})
    c('4.7u', 225, 225, 'SD_3V3', 'GND', FP['C0805']); c('100n', 232, 225, 'SD_3V3', 'GND')
    sd = sh.symbol('Connector:Micro_SD_Card_Det2', 'J902', '104031-0811', 300, 210,
                   'Connector_Card:microSD_HC_Molex_104031-0811')
    sh.wire(sd, {'4': 'SD_3V3', '6': 'GND', '5': 'SD_CLK', '3': 'SD_CMD', '7': 'SD_D0', '8': 'SD_D1',
                 '1': 'SD_D2', '2': 'SD_D3', '9': None, '10': None, 'SH': 'GND'})
    ser('22', 260, 190, 'SD_CK', 'SD_CLK', fields={'Note': 'clock edge damping'})
    for k, n in enumerate(('SD_CMD', 'SD_D0', 'SD_D1', 'SD_D2', 'SD_D3')):
        r('47k', 250 + 7 * k, 240, 'SD_3V3', n)
    sh.text('DAT3 pulled up keeps the card in SD mode (low at CMD0 selects SPI). DAT1/DAT2 unused in 1-bit, pulled up.', 170, 270)

# Switch inputs: (MCU net, connector net, ground-switched?) - harness-protection.md
SWITCHES = [('TR1', 'TR1_IN', True), ('TR2', 'TR2_IN', True), ('TR4', 'TR4_IN', True), ('4X4L', '4X4L_IN', True),
            ('TR3A', 'TR3A_IN', False), ('BRAKE', 'BRAKE_IN', False), ('ACP', 'ACP_IN', False), ('TCS', 'TCS_IN', False)]

def inputs(sh):
    """harness-protection.md: series resistor + TVS + pull-up. One network for all:
    pull-up to VPWR (fitted on ground-switched inputs only), SMF24A, 33k/15k, 10n,
    BAT54J to 3.3 V. Key-on sense is the same divider on VPWR, into PC13 / WKUP4."""
    sh.text('Switch inputs. One network: [4.7k pull-up to VPWR, ground-switched only] - SMF24A - 33k - node (15k, 10n, BAT54J to 3.3 V) - MCU.', 20, 16)
    sh.text('Pull-ups go to VPWR, not 5 V / 3.3 V: those stay up parked, and a TR bit closed in Park would draw mA all night.', 20, 20)
    sh.text('Levels: 14 V -> clamped; 9 V cranking -> 2.8 V (high-side) / 2.6 V (ground-switched) vs VIH 2.3 V. Open high-side reads 0.', 20, 24)
    sh.text('TR3A (64): on this 4R70W it is 12 V cranking in P/N, so the high-side network. A 4R100 (270R coded) needs a 2.2k', 20, 28)
    sh.text('pull-up to 3.3 V and 1k series instead - 4r100-deltas.md. Brake 92 is hot-at-all-times: 12 V when pressed.', 20, 32)
    R = iter(range(1001, 1100)); C = iter(range(1001, 1100)); D = iter(range(1001, 1100))
    for k, (mcu, pin, gsw) in enumerate(SWITCHES):
        x, y = 30 + (k % 4) * 95, 55 + (k // 4) * 70
        sh.text(f'{mcu} ({"ground-switched" if gsw else "12 V high-side"})', x, y - 8, 1.27)
        pu = sh.symbol('Device:R', f'R{next(R)}', '4.7k', x, y + 5, FP['R0805'], dnp=not gsw,
                       fields={'Note': 'wetting pull-up to VPWR' + ('' if gsw else ', not fitted: high-side input')})
        sh.wire(pu, {'1': 'VPWR', '2': pin})
        t = sh.symbol('Device:D_Zener', f'D{next(D)}', 'SMF24A', x + 12, y + 20, 'Diode_SMD:D_SMF', rot=90,
                      fields={'Note': 'unidirectional TVS, stands off above battery'})
        sh.wire(t, {'1': pin, '2': 'GND'})
        a = sh.symbol('Device:R', f'R{next(R)}', '33k', x + 30, y + 10, FP['R0805'], rot=90)
        sh.wire(a, {'1': pin, '2': mcu})
        sh.two('Device:R', f'R{next(R)}', '15k', FP['R'], x + 45, y + 20, mcu, 'GND')
        sh.two('Device:C', f'C{next(C)}', '10n', FP['C'], x + 53, y + 20, mcu, 'GND')
        d = sh.symbol('Device:D_Schottky', f'D{next(D)}', 'BAT54J', x + 62, y + 20, FP['SOD323'], rot=90)
        sh.wire(d, {'1': '+3.3V', '2': mcu})
    # key-on sense
    sh.text('Key-on: VPWR (EEC relay, 361 RD) through the same divider to PC13 / WKUP4 - Standby wakes only on a WKUP pin.', 20, 200)
    sh.text('100 nF, not 10 nF: a wake input should ignore ms-scale harness spikes. Also key-off detect while running.', 20, 204)
    a = sh.symbol('Device:R', f'R{next(R)}', '33k', 60, 220, FP['R0805'], rot=90)
    sh.wire(a, {'1': 'VPWR', '2': 'IGN_WAKE'})
    sh.two('Device:R', f'R{next(R)}', '15k', FP['R'], 75, 230, 'IGN_WAKE', 'GND')
    sh.two('Device:C', f'C{next(C)}', '100n', FP['C'], 83, 230, 'IGN_WAKE', 'GND')
    d = sh.symbol('Device:D_Schottky', f'D{next(D)}', 'BAT54J', 92, 230, FP['SOD323'], rot=90)
    sh.wire(d, {'1': '+3.3V', '2': 'IGN_WAKE'})
    # bench outputs and BOOT0
    sh.text('TACH / SPEED: software square waves for the bench (gauge testing), header only - 220R each.', 150, 200)
    j = sh.symbol('Connector_Generic:Conn_01x03', 'J1001', 'TACH/SPEED', 200, 225, 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical')
    sh.wire(j, {'1': 'TACH_H', '2': 'SPEED_H', '3': 'GND'})
    for n in ('TACH', 'SPEED'):
        a = sh.symbol('Device:R', f'R{next(R)}', '220', 170, 220 + (10 if n == 'SPEED' else 0), FP['R'], rot=90)
        sh.wire(a, {'1': n, '2': f'{n}_H'})
    sh.text('BOOT0: 10k down on the module. Close JP1001 at power-up for USB DFU (system bootloader on PA11/PA12).', 150, 250)
    jp = sh.symbol('Jumper:SolderJumper_2_Open', 'JP1001', 'BOOT0 DFU', 200, 265, FP['JP'], bom=False)
    sh.wire(jp, {'1': '+3.3V', '2': 'BOOT0'})

SHEETS = [('Rails', 'Rails.kicad_sch', rails),
          ('Ignition', 'Ignition.kicad_sch', ignition),
          ('Injection', 'Injection.kicad_sch', injection),
          ('VR', 'Vr.kicad_sch', vr),
          ('Solenoids', 'Solenoids.kicad_sch', solenoids),
          ('PWM', 'Pwm.kicad_sch', pwm_loads),
          ('Relays', 'Relays.kicad_sch', relays),
          ('VREF', 'Vref.kicad_sch', vref),
          ('ADC', 'ADC.kicad_sch', adc),
          ('Comms', 'Comms.kicad_sch', comms),
          ('Inputs', 'Inputs.kicad_sch', inputs)]

# ---------------------------------------------------------------- root sheet
def add_sheet_blocks(root_s, pro):
    root = re.search(r'\(uuid "([^"]+)"\)', root_s).group(1)
    for k, (name, fname, _) in enumerate(SHEETS):
        if f'"{fname}"' in root_s:
            continue
        bu = UID(name, 'block')
        x, y = 70 + (k % 4) * 40, 30.48 + (k // 4) * 40
        block = (f'\t(sheet (at {x} {y}) (size 30.48 27.94) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)\n'
                 f'\t\t(stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0)) (uuid "{bu}")\n'
                 f'\t\t(property "Sheetname" "{name}" (at {x} {y - 0.71} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))\n'
                 f'\t\t(property "Sheetfile" "{fname}" (at {x} {y + 28.5} 0) (effects (font (size 1.27 1.27)) (justify left top)))\n'
                 f'\t\t(instances (project "{PROJ}" (path "/{root}" (page "{4 + k}"))))\n\t)\n')
        root_s = root_s.replace('\t(sheet_instances', block + '\t(sheet_instances', 1)
        pro['sheets'].append([bu, name])
    return root_s, root

def block_uuid(root_s, fname):
    """The uuid of the root sheet block already pointing at fname (a placeholder
    drawn in KiCad keeps its own), or None."""
    for m in re.finditer(r'\n\t\(sheet\b', root_s):
        b = root_s[m.start() + 1:span(root_s, m.start() + 2)]
        if f'"Sheetfile" "{fname}"' in b:
            return re.search(r'\(uuid "([^"]+)"\)', b).group(1)
    return None

def main():
    os.chdir(HERE)
    if any(f.startswith('~') and f.endswith(('.kicad_sch.lck', '.kicad_pcb.lck')) for f in os.listdir('.')):   # the project window alone holds nothing
        sys.exit('project is open in KiCad - close it first')
    GLOBAL.update(net for net, *_ in cp.SIGNALS)
    GLOBAL.update(net for net, *_ in ep.PINS.values())
    GLOBAL.update({'WD_OE', 'NRST', 'VBAT', 'BOOT0', 'VPROT', 'VREF_5V', '+5V_SW', '+3.3V_SW', 'AGND'})      # + the module's non-port pins
    GLOBAL.update(MUX)                                       # drain/supply senses cross to the mux
    write_own_lib()
    root_s = open(f'{PROJ}.kicad_sch').read()
    pro = json.load(open(f'{PROJ}.kicad_pro'))
    root_s, root = add_sheet_blocks(root_s, pro)
    for name, fname, fn in SHEETS:
        if os.path.exists(fname):
            t = open(fname).read()
            if f'(generator "{MARK}")' not in t and '(symbol' in t:     # an empty placeholder is ours to fill
                print(f'{fname}: edited in KiCad - left alone')
                continue
        sh = Sheet(name, name, root, block_uuid(root_s, fname) or UID(name, 'block'))
        fn(sh)
        sh.write(fname)
        print(f'{fname}: {len(sh.refs)} parts')
    open(f'{PROJ}.kicad_sch', 'w').write(root_s)
    json.dump(pro, open(f'{PROJ}.kicad_pro', 'w'), indent=2)

if __name__ == '__main__':
    main()
