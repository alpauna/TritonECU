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

    def symbol(self, lib_id, ref, value, x, y, footprint='', rot=0, fields=None, hide_ref=False):
        pins = self.lib(lib_id)
        f = fields or {}
        props = [('Reference', ref, x, y - 3.81, hide_ref), ('Value', value, x, y + 3.81, False),
                 ('Footprint', footprint, x, y, True), ('Datasheet', '', x, y, True)]
        props += [(k, v, x, y, True) for k, v in f.items()]
        t = (f'\t(symbol (lib_id "{lib_id}") (at {x:.2f} {y:.2f} {rot}) (unit 1)\n'
             f'\t\t(exclude_from_sim no) (in_bom {"no" if ref.startswith("#") else "yes"}) (on_board yes) (dnp no)\n'
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

FP = {'0402': 'Capacitor_SMD:C_0402_1005Metric', '0603': 'Capacitor_SMD:C_0603_1608Metric',
      '0805': 'Capacitor_SMD:C_0805_2012Metric', 'R0402': 'Resistor_SMD:R_0402_1005Metric',
      'FB0603': 'Inductor_SMD:L_0603_1608Metric'}

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
                         'Connector_PinHeader_1.27mm:PinHeader_2x18_P1.27mm_Vertical',
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
    e = sh.symbol('Device:Crystal_GND24', 'Y1', '8MHz', 106 * G, y, 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',
                  fields={'Spec': '8 MHz, CL 8 pF, ESR <= 80 ohm, 3225 - part TBD'})
    sh.net('OSC_IN', *e['1'][0]); sh.net('OSC_OUT', *e['3'][0]); sh.net('GND', *e['2'][0])
    n += 1; two(f'C{n}', '10p', FP['0402'], 100 * G, y + 6 * G, 'OSC_IN', 'GND', fields={'Note': 'C0G'})
    n += 1; two(f'C{n}', '10p', FP['0402'], 112 * G, y + 6 * G, 'OSC_OUT', 'GND', fields={'Note': 'C0G'})
    e = sh.symbol('Device:Crystal', 'Y2', '32.768kHz', 130 * G, y, 'Crystal:Crystal_SMD_2012-2Pin_2.0x1.2mm',
                  fields={'Spec': '32.768 kHz, CL 7 pF, ESR <= 70 kohm, 2012 - part TBD'})
    sh.net('OSC32_IN', *e['1'][0]); sh.net('OSC32_OUT', *e['2'][0])
    n += 1; two(f'C{n}', '10p', FP['0402'], 124 * G, y + 6 * G, 'OSC32_IN', 'GND', fields={'Note': 'C0G'})
    n += 1; two(f'C{n}', '10p', FP['0402'], 136 * G, y + 6 * G, 'OSC32_OUT', 'GND', fields={'Note': 'C0G'})

    # SWD: Tag-Connect TC2030 on the module (PA13 SWDIO, PA14 SWCLK, PB3 SWO)
    e = sh.symbol('Connector:Conn_ARM_SWD_TagConnect_TC2030', 'J5', 'SWD TC2030', 152 * G, y,
                  'Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical')
    for num, net in {'1': '+3.3V', '2': 'PA13', '3': 'NRST', '4': 'PA14', '5': 'GND', '6': 'PB3'}.items():
        sh.net(net, *e[num][0])

    # mounting holes on GND, as the carrier footprint expects
    for i in range(4):
        e = sh.symbol('Mechanical:MountingHole_Pad', f'H{i + 1}', 'M3 standoff', (170 + 6 * i) * G, y,
                      'MountingHole:MountingHole_3.2mm_M3_Pad_Via')
        sh.net('GND', *e['1'][0])

    # power flags: +3.3V, GND and VBAT arrive through passive header pins; VDDA comes through the ferrite
    for i, net in enumerate(['+3.3V', 'GND', 'VDDA', 'VBAT']):
        e = sh.symbol('power:PWR_FLAG', f'#FLG{i + 1:02d}', 'PWR_FLAG', (100 + 8 * i) * G, 130 * G, hide_ref=True)
        (x, yy, o), = e['1']
        sh.net(net, x, yy, 'D')

    sh.text('6-layer board planned (user, 2026-10-16). +3.3V from the carrier (power board TLV62085); no regulator here.',
            100 * G, 140 * G)
    return sh

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
    pro_path = f'{PROJ}.kicad_pro'
    if not os.path.exists(pro_path):
        pro = json.load(open(os.path.join(HERE, '..', 'TritonECU-Main', 'TritonECU-Main.kicad_pro')))
        pro['meta']['filename'] = pro_path
    else:
        pro = json.load(open(pro_path))
    pro['sheets'] = [[sh.root, 'Root']]
    json.dump(pro, open(pro_path, 'w'), indent=2)
    print('schematic written')

if __name__ == '__main__':
    main()
