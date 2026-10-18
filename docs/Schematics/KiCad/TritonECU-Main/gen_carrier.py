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
    sh.wire(u, {'1': 'COIL_ARM', '19': 'WD_OE', '10': 'GND', '20': '+5V'})
    for i in range(8):
        sh.wire(u, {str(2 + i): f'COIL{i + 1}', str(18 - i): f'GATE{i + 1}'})
    sh.two('Device:C', 'C101', '100n', FP['C'], 45, 125, '+5V', 'GND')
    sh.two('Device:R', 'R109', '10k', FP['R'], 30, 70, '+5V', 'COIL_ARM')
    sh.two('Device:R', 'R110', '10k', FP['R'], 40, 70, '+5V', 'WD_OE')
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
        sh.wire(u, {'1': 'GND', '8': 'GND', '13': 'GND', '11': 'GND', '14': '+5V', '2': None, '7': None, '12': None})
        for k, val in enumerate(('10n', '100n', '1u')):
            sh.two('Device:C', f'C{c}', val, FP['C'], x0 + 95 + 8 * k, 125, '+5V', 'GND'); c += 1
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
            sh.two('Device:R', f'R{r}', '10k', FP['R'], x0 + 100, y - 10, '+3.3V', out); r += 1
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
    sh.wire(u, {'1': oe_nets[0], '19': oe_nets[1], '10': 'GND', '20': '+5V'})
    sh.two('Device:C', f'C{base + 1}', '100n', FP['C'], 35, 135, '+5V', 'GND')
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
    sh.wire(m, {'3': 'MUX_OUT', '6': 'GND', '7': 'GND', '8': 'GND', '16': '+3.3V',
                '11': 'MUX_S0', '10': 'MUX_S1', '9': 'MUX_S2'})
    sh.two('Device:C', 'C402', '100n', FP['C'], 230, 150, '+3.3V', 'GND')
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
    sh.two('Device:R', 'R509', '10k', FP['R'], 30, 60, '+5V', 'PWM_OE')
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
    sh.two('Device:R', 'R704', '10k', FP['R'], 116, 165, '+3.3V', 'VREF_FAULT')
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

SHEETS = [('Rails', 'Rails.kicad_sch', rails),
          ('Ignition', 'Ignition.kicad_sch', ignition),
          ('Injection', 'Injection.kicad_sch', injection),
          ('VR', 'Vr.kicad_sch', vr),
          ('Solenoids', 'Solenoids.kicad_sch', solenoids),
          ('PWM', 'Pwm.kicad_sch', pwm_loads),
          ('Relays', 'Relays.kicad_sch', relays),
          ('VREF', 'Vref.kicad_sch', vref)]

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

def main():
    os.chdir(HERE)
    if any(f.startswith('~') and f.endswith(('.kicad_sch.lck', '.kicad_pcb.lck')) for f in os.listdir('.')):   # the project window alone holds nothing
        sys.exit('project is open in KiCad - close it first')
    GLOBAL.update(net for net, *_ in cp.SIGNALS)
    GLOBAL.update(net for net, *_ in ep.PINS.values())
    GLOBAL.update({'WD_OE', 'NRST', 'VBAT', 'BOOT0', 'VPROT', 'VREF_5V'})      # + the module's non-port pins
    GLOBAL.update(MUX)                                       # drain/supply senses cross to the mux
    write_own_lib()
    root_s = open(f'{PROJ}.kicad_sch').read()
    pro = json.load(open(f'{PROJ}.kicad_pro'))
    root_s, root = add_sheet_blocks(root_s, pro)
    for name, fname, fn in SHEETS:
        if os.path.exists(fname) and f'(generator "{MARK}")' not in open(fname).read():
            print(f'{fname}: edited in KiCad - left alone')
            continue
        sh = Sheet(name, name, root, UID(name, 'block'))
        fn(sh)
        sh.write(fname)
        print(f'{fname}: {len(sh.refs)} parts')
    open(f'{PROJ}.kicad_sch', 'w').write(root_s)
    json.dump(pro, open(f'{PROJ}.kicad_pro', 'w'), indent=2)

if __name__ == '__main__':
    main()
