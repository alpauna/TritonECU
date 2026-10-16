#!/usr/bin/env python3
"""Generate the TritonECU-MCU module schematic: STM32F767ZIT6 + crystals,
decoupling, SWD and the four 2x18 headers defined in mcu_pinout.py.

Connections are made with net labels and power symbols placed on the pin
end points, so the sheet is generated rather than hand-wired. It is a
BOOTSTRAP: it refuses to overwrite a schematic that is not its own output
(no "gen_module.py" marker), so edits made in KiCad are never clobbered.

Values follow DS11532 (STM32F765xx/767xx) section 6.1.6 and AN4661:
  100 nF per VDD pin (10 x VDD, VDDUSB, VDDSDMMC) + 4.7 uF bulk
  VDDA: ferrite from VDD, 1 uF + 100 nF; VREF+ tied to VDDA
  VCAP_1 / VCAP_2: 2.2 uF each, ESR < 2 ohm
  HSE 8 MHz, CL 8 pF; LSE 32.768 kHz, CL 7 pF; load caps 10 pF
    (2 x (CL - ~3 pF stray), confirm against the chosen crystal)
  PDR_ON to VDD, BOOT0 10 k to GND, NRST 100 nF

Usage:  python3 gen_module.py   (needs kicad-cli via flatpak for the library copy)
"""
import json, os, re, subprocess, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mcu_pinout as mp

PROJ = 'TritonECU-MCU'
LIBDIR = '/app/extensions/Library/symbols'
MARK = 'gen_module.py'

def U(): return str(uuid.uuid4())

# ---------------------------------------------------------------- library access
_lib_cache = {}
def lib_text(lib):
    if lib not in _lib_cache:
        _lib_cache[lib] = subprocess.run(
            ['flatpak', 'run', '--command=cat', 'org.kicad.KiCad', f'{LIBDIR}/{lib}.kicad_sym'],
            check=True, capture_output=True, text=True).stdout
    return _lib_cache[lib]

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

def lib_symbol(lib_id):
    """(embedded text, {pin number: (x, y, angle)}) for 'Lib:Name'."""
    lib, name = lib_id.split(':')
    s = lib_text(lib)
    a = s.index(f'\n\t(symbol "{name}"\n') + 2
    blk = s[a:span(s, a)]
    assert '(extends' not in blk, lib_id
    pins = {}
    for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\).*?\(number "([^"]*)"', blk, re.S):
        pins.setdefault(m.group(4), []).append((float(m.group(1)), float(m.group(2)), int(m.group(3))))
    emb = blk.replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)
    return emb, pins

# ---------------------------------------------------------------- sheet builder
class Sheet:
    def __init__(self):
        self.root = U()
        self.libs = {}
        self.items = []
        self.npwr = 0

    def lib(self, lib_id):
        if lib_id not in self.libs:
            self.libs[lib_id] = lib_symbol(lib_id)
        return self.libs[lib_id][1]

    def symbol(self, lib_id, ref, value, x, y, footprint='', rot=0, fields=None, hide_ref=False, bom=True):
        pins = self.lib(lib_id)
        f = fields or {}
        props = [('Reference', ref, x, y - 3.81, hide_ref), ('Value', value, x, y + 3.81, False),
                 ('Footprint', footprint, x, y, True), ('Datasheet', '', x, y, True)]
        props += [(k, v, x, y, True) for k, v in f.items()]
        t = (f'\t(symbol (lib_id "{lib_id}") (at {x:.2f} {y:.2f} {rot}) (unit 1)\n'
             f'\t\t(exclude_from_sim no) (in_bom {"yes" if bom and not ref.startswith("#") else "no"}) (on_board yes) (dnp no)\n'
             f'\t\t(uuid "{U()}")\n')
        for k, v, px, py, hide in props:
            h = ' (hide yes)' if hide else ''
            t += f'\t\t(property "{k}" "{v}" (at {px:.2f} {py:.2f} 0){h} (effects (font (size 1.27 1.27))))\n'
        for num in pins:
            t += f'\t\t(pin "{num}" (uuid "{U()}"))\n'
        t += f'\t\t(instances (project "{PROJ}" (path "/{self.root}" (reference "{ref}") (unit 1))))\n\t)\n'
        self.items.append(t)
        # pin end points on the sheet (y down), with the outward direction
        out = {}
        for num, lst in pins.items():
            res = []
            for px, py, a in lst:
                if rot:   # only 0/90/180/270, CCW on the sheet
                    for _ in range(rot // 90):
                        px, py, a = -py, px, (a + 90) % 360
                outward = {0: 'L', 180: 'R', 90: 'D', 270: 'U'}[a]
                res.append((round(x + px, 2), round(y - py, 2), outward))
            out[num] = res
        return out

    def label(self, name, x, y, outward):
        ang, just = {'L': (180, 'right'), 'R': (0, 'left'), 'U': (90, 'left'), 'D': (270, 'right')}[outward]
        self.items.append(f'\t(label "{name}" (at {x:.2f} {y:.2f} {ang}) '
                          f'(effects (font (size 1.27 1.27)) (justify {just} bottom)) (uuid "{U()}"))\n')

    def power(self, net, x, y, outward):
        self.npwr += 1
        if net == 'GND':
            rot = {'D': 0, 'U': 180, 'L': 270, 'R': 90}[outward]; lib_id = 'power:GND'
        elif net == 'PWR_FLAG':
            rot = {'U': 0, 'D': 180, 'L': 90, 'R': 270}[outward]; lib_id = 'power:PWR_FLAG'
        else:
            rot = {'U': 0, 'D': 180, 'L': 90, 'R': 270}[outward]; lib_id = f'power:{net}'
        self.symbol(lib_id, f'#PWR{self.npwr:03d}', net, x, y, rot=rot, hide_ref=True)

    def net(self, name, x, y, outward):
        if name in ('GND', '+3.3V'): self.power(name, x, y, outward)
        else: self.label(name, x, y, outward)

    def text(self, t, x, y, size=1.7):
        self.items.append(f'\t(text "{t}" (exclude_from_sim no) (at {x:.2f} {y:.2f} 0) '
                          f'(effects (font (size {size} {size})) (justify left bottom)) (uuid "{U()}"))\n')

    def write(self, path):
        libs = ''.join('\t\t' + e.replace('\n\t', '\n\t\t') + '\n' for e, _ in self.libs.values())
        s = (f'(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n'
             f'\t(uuid "{self.root}")\n\t(paper "A2")\n'
             f'\t(title_block (title "TritonECU MCU module - STM32F767ZIT6") (rev "1") '
             f'(comment 1 "Generated by {MARK} - see docs/mcu-module.md"))\n'
             f'\t(lib_symbols\n{libs}\t)\n' + ''.join(self.items) +
             f'\t(sheet_instances (path "/" (page "1")))\n\t(embedded_fonts no)\n)\n')
        open(path, 'w').write(s)

# ---------------------------------------------------------------- the circuit
MCU_NET = {'VSS': 'GND', 'VSSA': 'GND', 'VDD': '+3.3V', 'VDDUSB': '+3.3V', 'VDDSDMMC': '+3.3V',
           'PDR_ON': '+3.3V', 'VDDA': 'VDDA', 'VREF+': 'VDDA', 'VCAP_1': 'VCAP1', 'VCAP_2': 'VCAP2',
           'PH0': 'OSC_IN', 'PH1': 'OSC_OUT', 'PC14': 'OSC32_IN', 'PC15': 'OSC32_OUT'}

# hand-solder pad variants, as on the power board
FP = {'0402': 'Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder',
      '0603': 'Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder',
      '0805': 'Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder',
      'R0402': 'Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder',
      'FB0603': 'Inductor_SMD:L_0603_1608Metric_Pad1.05x0.95mm_HandSolder'}

def build():
    sh = Sheet()
    G = 2.54

    # U1
    u1 = sh.symbol('MCU_ST_STM32F7:STM32F767ZITx', 'U1', 'STM32F767ZIT6', 50 * G, 60 * G,
                   'Package_QFP:LQFP-144_20x20mm_P0.5mm',
                   fields={'MPN': 'STM32F767ZIT6', 'Manufacturer': 'STMicroelectronics'})
    for num, ends in u1.items():
        name = mp.LQFP144[int(num) - 1]
        net = MCU_NET.get(name, name)
        for x, y, o in ends:
            sh.net(net, x, y, o)

    # headers J1-J4 = A-D
    pins = mp.module_pins()
    for i, side in enumerate(mp.SIDES):
        hx, hy = (100 + 32 * i) * G, 30 * G
        ends = sh.symbol('Connector_Generic:Conn_02x18_Odd_Even', f'J{i + 1}', f'Header {side}', hx, hy,
                         f'{PROJ}:{HDR_FP}',
                         fields={'MPN': mp.HEADER_MPN, 'Manufacturer': 'Samtec', 'Mate': mp.SOCKET_MPN + ' on the carrier, ' + mp.STACK_NOTE,
                                 'Side': f'{side} - see mcu_pinout.py'})
        for pad, _, _, net in pins:
            if pad[0] != side: continue
            for x, y, o in ends[pad[1:]]:
                sh.net(net, x, y, o)

    def two(ref, val, fp, x, y, top, bot, lib='Device:C', fields=None):
        e = sh.symbol(lib, ref, val, x, y, fp, fields=fields)
        (x1, y1, o1), = e['1']; (x2, y2, o2), = e['2']
        sh.net(top, x1, y1, o1); sh.net(bot, x2, y2, o2)

    # row 1: decoupling
    y = 70 * G
    sh.text('Decoupling: one 100 nF at each VDD / VDDUSB / VDDSDMMC pin, bulk at the headers', 100 * G, y - 10 * G)
    n = 0
    for k in range(12):
        n += 1; two(f'C{n}', '100n', FP['0402'], (100 + 6 * k) * G, y, '+3.3V', 'GND')
    n += 1; two(f'C{n}', '4.7u', FP['0603'], (100 + 6 * 12) * G, y, '+3.3V', 'GND')
    n += 1; two(f'C{n}', '10u', FP['0805'], (100 + 6 * 13) * G, y, '+3.3V', 'GND',
                fields={'Note': 'X7R, rated >= 10 V'})

    # row 2: analog supply, regulator caps, VBAT, NRST, BOOT0
    y = 90 * G
    sh.text('VDDA / VREF+ (ferrite filtered), VCAP, VBAT, NRST, BOOT0', 100 * G, y - 10 * G)
    two('FB1', '220R@100MHz', FP['FB0603'], 100 * G, y, '+3.3V', 'VDDA', lib='Device:FerriteBead_Small')
    n += 1; two(f'C{n}', '1u', FP['0402'], 106 * G, y, 'VDDA', 'GND')
    n += 1; two(f'C{n}', '100n', FP['0402'], 112 * G, y, 'VDDA', 'GND')
    n += 1; two(f'C{n}', '2.2u', FP['0603'], 120 * G, y, 'VCAP1', 'GND', fields={'Note': 'ESR < 2 ohm (DS11532)'})
    n += 1; two(f'C{n}', '2.2u', FP['0603'], 126 * G, y, 'VCAP2', 'GND', fields={'Note': 'ESR < 2 ohm (DS11532)'})
    n += 1; two(f'C{n}', '100n', FP['0402'], 134 * G, y, 'VBAT', 'GND')
    n += 1; two(f'C{n}', '100n', FP['0402'], 140 * G, y, 'NRST', 'GND')
    two('R1', '10k', FP['R0402'], 148 * G, y, 'BOOT0', 'GND', lib='Device:R')

    # row 3: crystals
    y = 110 * G
    sh.text('HSE 8 MHz (CL 8 pF) and LSE 32.768 kHz (CL 7 pF). Load caps = 2 x (CL - stray); confirm with the chosen part', 100 * G, y - 10 * G)
    e = sh.symbol('Device:Crystal_GND24', 'Y1', '8MHz', 106 * G, y, 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm_HandSoldering',
                  fields={'Spec': '8 MHz, CL 8 pF, ESR <= 80 ohm, 3225 - part TBD'})
    sh.net('OSC_IN', *e['1'][0]); sh.net('OSC_OUT', *e['3'][0]); sh.net('GND', *e['2'][0])
    n += 1; two(f'C{n}', '10p', FP['0402'], 100 * G, y + 6 * G, 'OSC_IN', 'GND', fields={'Note': 'C0G'})
    n += 1; two(f'C{n}', '10p', FP['0402'], 112 * G, y + 6 * G, 'OSC_OUT', 'GND', fields={'Note': 'C0G'})
    e = sh.symbol('Device:Crystal', 'Y2', '32.768kHz', 130 * G, y, 'Crystal:Crystal_SMD_2012-2Pin_2.0x1.2mm_HandSoldering',
                  fields={'Spec': '32.768 kHz, CL 7 pF, ESR <= 70 kohm, 2012 - part TBD'})
    sh.net('OSC32_IN', *e['1'][0]); sh.net('OSC32_OUT', *e['2'][0])
    n += 1; two(f'C{n}', '10p', FP['0402'], 124 * G, y + 6 * G, 'OSC32_IN', 'GND', fields={'Note': 'C0G'})
    n += 1; two(f'C{n}', '10p', FP['0402'], 136 * G, y + 6 * G, 'OSC32_OUT', 'GND', fields={'Note': 'C0G'})

    # Programming: ST STDC14 (STLINK-V3 native, Samtec FTSH-107) on the module TOP, SMT so it
    # needs no holes through to the bottom headers. SWD + SWO + NRST, plus the ST-Link VCP on
    # USART3 PD8 (TX) / PD9 (RX), the same console the Nucleo uses. Pin 13 is the target's RX,
    # pin 14 the target's TX (UM2448). The same SWD pins also reach the carrier through the headers.
    e = sh.symbol('Connector:Conn_ST_STDC14', 'J5', 'STDC14 SWD+VCP', 152 * G, y,
                  'Connector_PinHeader_1.27mm:PinHeader_2x07_P1.27mm_Vertical_SMD',
                  fields={'MPN': 'FTSH-107-01-L-DV-K', 'Manufacturer': 'Samtec',
                          'Note': 'ST-Link V3 STDC14; footprint generic 2x07 1.27 SMD - check vs Samtec'})
    for num, net in {'3': '+3.3V', '4': 'PA13', '5': 'GND', '6': 'PA14', '7': 'GND', '8': 'PB3',
                     '11': 'GND', '12': 'NRST', '13': 'PD9', '14': 'PD8'}.items():
        sh.net(net, *e[num][0])
    for num in ('1', '2', '9', '10'):
        x, yy, _ = e[num][0]
        sh.items.append(f'\t(no_connect (at {x:.2f} {yy:.2f}) (uuid "{U()}"))\n')

    # mounting holes on GND, as the carrier footprint expects
    for i in range(4):
        e = sh.symbol('Mechanical:MountingHole_Pad', f'H{i + 1}', 'M3 standoff', (170 + 6 * i) * G, y,
                      'MountingHole:MountingHole_3.2mm_M3_Pad_Via', bom=False)
        sh.net('GND', *e['1'][0])

    # power flags: +3.3V, GND and VBAT arrive through passive header pins; VDDA comes through the ferrite
    for i, net in enumerate(['+3.3V', 'GND', 'VDDA', 'VBAT']):
        e = sh.symbol('power:PWR_FLAG', f'#FLG{i + 1:02d}', 'PWR_FLAG', (100 + 8 * i) * G, 130 * G, hide_ref=True)
        (x, yy, o), = e['1']
        sh.net(net, x, yy, 'D')

    sh.text('6-layer board planned (user, 2026-10-16). +3.3V from the carrier (power board TLV62085); no regulator here.',
            100 * G, 140 * G)
    return sh

# ---------------------------------------------------------------- header footprint
HDR_FP = 'Samtec_TFM-118-22-L-D-A'

def header_footprint():
    """Samtec TFM-118-22-L-D-A, SMT, for BOTTOM mounting. Pad size, pad offset and
    the -A alignment holes come from the vendor footprint (mcu_pinout.TFM). Odd
    pins sit on the y < 0 row, and pins 1/2 are at the RIGHT end of this library
    view. Flipping the part to the bottom mirrors it, so the numbering then follows
    mcu_pinout.py, which the carrier footprint also uses. Pin numbers are this
    project's, by position, not Samtec's: the pins mate by position."""
    T = mp.TFM
    w, l = T['pad']
    t = (f'(footprint "{HDR_FP}"\n\t(version 20260206)\n\t(generator "{MARK}")\n\t(layer "F.Cu")\n'
         f'\t(descr "Samtec TFM-118-22-L-D-A 2x18 1.27 mm SMT header, 9.91 mm stack with SFM-118-02. '
         f'Geometry from the Samacsys TFM-118-ZZ-XXX-D-A footprint; numbered for bottom mounting per mcu_pinout.py")\n'
         f'\t(property "Reference" "REF**" (at 0 -6 0) (layer "F.SilkS") (uuid "{U()}") (effects (font (size 1 1) (thickness 0.15))))\n'
         f'\t(property "Value" "{HDR_FP}" (at 0 6 0) (layer "F.Fab") (uuid "{U()}") (effects (font (size 1 1) (thickness 0.15))))\n'
         f'\t(attr smd)\n')
    for k in range(36):
        x = -(k // 2 - 8.5) * mp.PITCH
        y = -T['off'] if k % 2 == 0 else T['off']
        t += (f'\t(pad "{k + 1}" smd rect (at {x:.3f} {y:.3f}) (size {w} {l}) '
              f'(layers "F.Cu" "F.Paste" "F.Mask") (uuid "{U()}"))\n')
    for x in (-T['align_x'], T['align_x']):
        t += (f'\t(pad "" np_thru_hole circle (at {x} 0) (size {T["align"]} {T["align"]}) (drill {T["align"]}) '
              f'(layers "*.Cu" "*.Mask") (uuid "{U()}"))\n')
    bx, by = T['body']
    cy = max(by, T['off'] + l / 2) + 0.25
    for layer, (cw, ch), wd in (('F.CrtYd', (bx + 0.25, cy), 0.05), ('F.Fab', (bx, by), 0.1)):
        t += (f'\t(fp_rect (start {-cw} {-ch}) (end {cw} {ch}) (stroke (width {wd}) (type solid)) (fill no) '
              f'(layer "{layer}") (uuid "{U()}"))\n')
    t += (f'\t(fp_line (start 10.4 -3.6) (end 11.2 -3.6) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{U()}"))\n'
          f'\t(fp_text user "pin 1" (at 10.8 -4.4 0) (layer "F.Fab") (uuid "{U()}") (effects (font (size 0.6 0.6) (thickness 0.1))))\n)\n')
    return t

# ---------------------------------------------------------------- project
def main():
    os.chdir(HERE)
    sch = f'{PROJ}.kicad_sch'
    if os.path.exists(sch) and MARK not in open(sch).read():
        sys.exit(f'{sch} was edited outside {MARK}; refusing to overwrite')
    if any(f.startswith('~') and f.endswith('.lck') for f in os.listdir('.')):
        sys.exit('project is open in KiCad - close it first')
    sh = build()
    sh.write(sch)
    os.makedirs(f'{PROJ}.pretty', exist_ok=True)
    open(f'{PROJ}.pretty/{HDR_FP}.kicad_mod', 'w').write(header_footprint())
    open('fp-lib-table', 'w').write(f'(fp_lib_table\n\t(version 7)\n\t(lib (name "{PROJ}")(type "KiCad")'
                                    f'(uri "${{KIPRJMOD}}/{PROJ}.pretty")(options "")(descr "TritonECU MCU module parts"))\n)\n')
    pro_path = f'{PROJ}.kicad_pro'
    if not os.path.exists(pro_path):
        pro = json.load(open(os.path.join(HERE, '..', 'TritonECU-Main', 'TritonECU-Main.kicad_pro')))
        pro['meta']['filename'] = pro_path
    else:
        pro = json.load(open(pro_path))
    pro['sheets'] = [[sh.root, 'Root']]
    # 0.5 mm-pitch QFP fan-out: 0.15 mm signals; rails 0.3 mm
    ns = pro['net_settings']
    d = next(c for c in ns['classes'] if c['name'] == 'Default')
    d.update(track_width=0.15, clearance=0.15, via_diameter=0.5, via_drill=0.25)
    pw = dict(d, name='Power', priority=0, track_width=0.3, via_diameter=0.6, via_drill=0.3)
    ns['classes'] = [d, pw]
    # 1.27 mm header pads between plane-connected neighbours only fit one thermal spoke
    pro['board']['design_settings']['rules']['min_resolved_spokes'] = 1
    ns['netclass_patterns'] = [{'netclass': 'Power', 'pattern': n} for n in ('+3.3V', 'GND', '/VDDA', '/VCAP1', '/VCAP2')]
    json.dump(pro, open(pro_path, 'w'), indent=2)
    print('schematic written')

if __name__ == '__main__':
    main()
