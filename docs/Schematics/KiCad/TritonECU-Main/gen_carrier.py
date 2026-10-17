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
      'DPAK5': 'Package_TO_SOT_SMD:TO-252-5_TabPin3',
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

    def symbol(self, lib_id, ref, value, x, y, footprint=None, rot=0, fields=None, hide_ref=False, bom=True):
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
             f'\t\t(exclude_from_sim no) (in_bom {"yes" if bom and not ref.startswith("#") else "no"}) (on_board yes) (dnp no)\n'
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
    power board (DB1), VPWR from the connector. PWR_FLAGs say so to ERC."""
    sh.text('Rails: +5V, +3.3V (always-on) and GND come from the power board, VPWR from EEC-V 71/97.', 20, 20)
    for k, net in enumerate(['+5V', '+3.3V', 'GND', 'VPWR']):
        f = sh.symbol('power:PWR_FLAG', f'#FLG{k + 1:02d}', 'PWR_FLAG', 40.64 + 25.4 * k, 50.8)
        sh.net(net, f['1'])
    sh.text('Bulk where the rails arrive from the power board connector.', 20, 120)
    sh.two('Device:C', 'C001', '10u', 'Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder', 50, 140, '+5V', 'GND')
    sh.two('Device:C', 'C002', '10u', 'Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder', 75, 140, '+3.3V', 'GND')
    sh.text('VBAT: the module RTC/backup domain, from the always-on 3.3 V. R001 can become a coin cell.', 20, 80)
    sh.two('Device:R', 'R001', '0', FP['R'], 50, 100, '+3.3V', 'VBAT')

SHEETS = [('Rails', 'Rails.kicad_sch', rails),
          ('Ignition', 'Ignition.kicad_sch', ignition),
          ('Injection', 'Injection.kicad_sch', injection)]

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
    if any(f.startswith('~') and f.endswith('.lck') for f in os.listdir('.')):
        sys.exit('project is open in KiCad - close it first')
    GLOBAL.update(net for net, *_ in cp.SIGNALS)
    GLOBAL.update(net for net, *_ in ep.PINS.values())
    GLOBAL.update({'WD_OE', 'NRST', 'VBAT', 'BOOT0'})      # + the module's non-port pins
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
