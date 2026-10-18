#!/usr/bin/env python3
"""Bootstrap the TritonECU-Main floor plan: the 104-pin EEC-V connector, the
power board V3, the VR board V1 and the F767 MCU module placed on a 158 x 174
carrier.

Writes:
  TritonECU-Main.pretty/   footprints  (EECV_104, PowerBoard_V3_Mate, VRBoard_V1_Mate, MCUModule_F767_Mate)
  TritonECU-Main.kicad_sym symbols     (same four)
  fp-lib-table, sym-lib-table
  Interconnect.kicad_sch   sheet carrying the three symbols, power-board pins labelled
  TritonECU-Main.kicad_sch root sheet gets the Interconnect sheet added
  TritonECU-Main.kicad_pcb outline, the three footprints, reserved areas, notes

It is a BOOTSTRAP. On a board that already has footprints it only ADDS parts
whose reference is missing (symbol, labels and footprint), leaving everything
already placed or wired alone. Library files are always regenerated.
Close the project in KiCad first: it would overwrite the files on its next save.

Geometry sources
  EEC-V 104:  rusEFI rusefi_lib:eecv (physically fit-tested against the
              salvaged connector) for pad positions and post/centre holes;
              TE 770750-1 for the Ø1.40 pin drill and the 5.20 mm post-to-edge.
              See docs/1999-Ford-F150-4wd-5.42v/connector-sourcing.md.
  Power V3:   read from ../TritonECU/TritonECU.kicad_pcb (J2, J3, H1-H4, outline).
  VR V1:      read from the EasyEDA gerbers, docs/Schematics/TritonECU_VR_V_1_Greber.zip.
  MCU module: ../TritonECU-MCU/mcu_pinout.py (the module's own pinout definition).

Usage:  python3 gen_floorplan.py   (from this directory; needs kicad-cli via flatpak)
"""
import json, math, os, re, subprocess, sys, uuid, zipfile, io

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'TritonECU-MCU'))
import mcu_pinout
PROJ = 'TritonECU-Main'
LIB = PROJ
POWER_PCB = os.path.join(HERE, '..', 'TritonECU', 'TritonECU.kicad_pcb')
VR_ZIP = os.path.join(HERE, '..', '..', 'TritonECU_VR_V_1_Greber.zip')
PINOUT_MD = os.path.join(HERE, '..', '..', '..', '1999-Ford-F150-4wd-5.42v', 'eec-v-pinout.md')

# ---------------------------------------------------------------- parameters
O = (25.0, 25.0)            # board top-left on the page
BOARD_W, BOARD_L = 158.0, 174.0   # donor PCB (carrier-envelope.md); outline shape ** ESTIMATED: plain rectangle **
EDGE_BAND = 12.0            # edge-cooling band (carrier-envelope.md)

# EEC-V connector along the top (158 mm) edge, pin-1 row nearest the edge.
EEC_X = BOARD_W / 2         # ** ESTIMATED ** centred, as on rusEFI's own board
EEC_POST_TO_EDGE = 5.20     # TE 770750-1: board edge 5.20 from the post centreline

# Daughterboard placements: centre of each board outline, rotation in degrees
# (KiCad sense). Power and VR as the user arranged them in KiCad on 2026-10-16.
POWER_AT = (115.55, 133.35, -90)
VR_AT = (102.3675, 47.9158, 90)   # VR board V1: no longer placed - the VR front end is on the carrier (Vr.kicad_sch)
MCU_AT = (45.0, 60.0, 0)    # the 46 x 46 MCU module; 5 mm below the connector courtyard to leave the injector row

def U(): return str(uuid.uuid4())

# ---------------------------------------------------------------- geometry: EEC-V
def eec_pads():
    """(number, x, y) relative to the post centreline midpoint; y grows away
    from the board edge. Rows 3.0 apart, 3.4 pitch, 1.7 stagger, split in two
    blocks of 13 either side of the centre hole; numbers fall as x rises."""
    pads = []
    for r in range(4):
        y = -3.0 + 3.0 * r
        if r % 2 == 0:
            right, left = 49.0, -9.9
        else:
            right, left = 50.7, -8.2
        xs = [right - 3.4 * k for k in range(13)] + [left - 3.4 * k for k in range(13)]
        for k, x in enumerate(xs):
            pads.append((str(r * 26 + k + 1), round(x, 3), round(y, 3)))
    return pads

EEC_POSTS = [(-55.0, 0.0), (55.0, 0.0)]
EEC_CENTRE = (0.0, 14.45)

# ---------------------------------------------------------------- geometry: power V3
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

def rot(x, y, deg):
    t = math.radians(deg)
    return (x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t))

def power_geometry():
    s = open(POWER_PCB).read()
    out = {}
    for m in re.finditer(r'\n\t\(footprint ', s):
        b = s[m.start() + 2:span(s, m.start() + 2)]
        ref = re.search(r'"Reference" "([^"]+)"', b).group(1)
        if ref not in ('J2', 'J3', 'H1', 'H2', 'H3', 'H4'): continue
        fx, fy, *fr = map(float, re.search(r'\n\t\t\(at ([^)]*)\)', b).group(1).split())
        fr = fr[0] if fr else 0.0
        for p in re.finditer(r'\(pad "([^"]*)" \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+)', b):
            px, py = rot(float(p.group(2)), float(p.group(3)), fr)
            net = re.search(r'\(net "([^"]*)"\)', b[p.start():span(b, p.start())])
            out[(ref, p.group(1))] = (fx + px, fy + py, net.group(1).split('/')[-1] if net else '')
    e = re.search(r'\(gr_rect\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)(?:(?!\(gr_).)*?\(layer "Edge.Cuts"\)', s, re.S)
    x0, y0, x1, y1 = map(float, e.groups())
    return out, (x0, y0, x1, y1)

# ---------------------------------------------------------------- geometry: VR V1
def vr_geometry():
    z = zipfile.ZipFile(VR_ZIP)
    drl = z.read('Drill_PTH_Through.DRL').decode()
    gko = z.read('Gerber_BoardOutlineLayer.GKO').decode()
    holes = []; cur = None
    for line in drl.splitlines():
        m = re.match(r'T(\d+)$', line)
        if m: cur = m.group(1); continue
        m = re.match(r'X([-\d.]+)Y([-\d.]+)', line)
        if m: holes.append((cur, float(m.group(1)), float(m.group(2))))
    pts = [(int(a) / 1e5, int(b) / 1e5) for a, b in re.findall(r'X(-?\d+)Y(-?\d+)', gko)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    box = (min(xs), min(ys), max(xs), max(ys))
    u2 = sorted([(x, y) for t, x, y in holes if t == '02' and abs(x - 33.655) < 0.05], key=lambda p: p[1])
    u3 = sorted([(x, y) for t, x, y in holes if t == '02' and abs(x - 5.461) < 0.05], key=lambda p: p[1])
    mh = sorted([(x, y) for t, x, y in holes if t == '03'], key=lambda p: p[1])
    assert len(u2) == 9 and len(u3) == 10 and len(mh) == 2, (len(u2), len(u3), len(mh))
    return u2, u3, mh, box   # gerber coords, Y up; pin 1 (square pad) is the lowest Y

# ---------------------------------------------------------------- pin names
def eec_names():
    names = {}
    for line in open(PINOUT_MD):
        c = [x.strip().strip('*').strip('`').strip() for x in line.strip().strip('|').split('|')]
        if len(c) < 4 or not re.fullmatch(r'\d+', c[0]): continue
        n = int(c[0])
        if not 1 <= n <= 104: continue
        ms, f150 = c[1], c[3]
        name = ms if f150 in ('Same', '') else f150
        name = '' if name in ('--', '-') else name
        name = re.sub(r'[^A-Za-z0-9 +\-_/().#]', '', name).strip()[:30]
        names[n] = name
    return names

# ---------------------------------------------------------------- s-expr helpers
def fnt(size=1.27, thick=None):
    t = f' (thickness {thick})' if thick else ''
    return f'(effects (font (size {size} {size}){t}))'

def fp_text_prop(name, val, x, y, layer, hide=False, size=1.0):
    h = ' (hide yes)' if hide else ''
    return (f'\t\t(property "{name}" "{val}" (at {x} {y} 0) (layer "{layer}"){h} (uuid "{U()}")\n'
            f'\t\t\t{fnt(size, round(size * 0.15, 3))})\n')

def fp_rect(x0, y0, x1, y1, layer, w=0.1):
    return (f'\t\t(fp_rect (start {x0:.3f} {y0:.3f}) (end {x1:.3f} {y1:.3f}) '
            f'(stroke (width {w}) (type solid)) (fill no) (layer "{layer}") (uuid "{U()}"))\n')

def fp_txt(t, x, y, layer, size=1.0):
    return (f'\t\t(fp_text user "{t}" (at {x:.3f} {y:.3f} 0) (layer "{layer}") (uuid "{U()}")\n'
            f'\t\t\t{fnt(size, round(size * 0.15, 3))})\n')

def pad(num, x, y, size, drill, shape='circle', net=None, rot_=0, mech=False):
    n = f' (net "{net}")' if net else ''
    pt = '' if mech else ' (pintype "passive")'
    return (f'\t\t(pad "{num}" thru_hole {shape} (at {x:.4f} {y:.4f} {rot_}) (size {size} {size}) '
            f'(drill {drill}) (layers "*.Cu" "*.Mask") (remove_unused_layers no){n}{pt} (uuid "{U()}"))\n')

# ---------------------------------------------------------------- footprints (local)
def build_footprints():
    """Return {name: (descr, body-lines-with-pads-as-callable)}."""
    fps = {}

    # EECV_104
    def eec(nets, r=0):
        b = ''
        for num, x, y in eec_pads():
            b += pad(num, x, y, 2.0, 1.40, 'rect' if num == '1' else 'circle', nets.get(num), r)
        for x, y in EEC_POSTS + [EEC_CENTRE]:
            b += pad('', x, y, 4.5, 3.7, net=None, rot_=r, mech=True)
        b += fp_rect(-57.5, -EEC_POST_TO_EDGE, 57.5, 17.5, 'F.CrtYd', 0.05)
        b += fp_rect(-52.5, -4.5, 52.5, 7.5, 'F.Fab')
        b += fp_txt('EEC-V 104  pin 1 ->', 40, -4.3, 'F.Fab', 0.8)
        b += fp_txt('board edge (TE 5.20 from posts)', 0, -EEC_POST_TO_EDGE + 0.6, 'Dwgs.User', 0.8)
        b += fp_txt('[MEASURE] case flange keepout', 0, 16.5, 'Dwgs.User', 1.0)
        return b
    fps['EECV_104'] = ('Ford EEC-V 104-pin board header, 4x26 staggered. Pads: rusEFI rusefi_lib:eecv '
                       '(fit-tested). Pin drill 1.40 per TE 770750-1. Posts and centre hole 3.7 plated.', eec)

    # PowerBoard_V3_Mate
    pg, (x0, y0, x1, y1) = power_geometry()
    pcx, pcy = (x0 + x1) / 2, (y0 + y1) / 2
    def power(nets, r=0):
        b = ''
        for (ref, num), (x, y, _) in sorted(pg.items()):
            lx, ly = x - pcx, y - pcy
            if ref == 'J2': b += pad('A' + num, lx, ly, 1.7, 1.02, 'rect' if num == '1' else 'circle', nets.get('A' + num), r)
            elif ref == 'J3': b += pad('B' + num, lx, ly, 1.7, 1.02, 'rect' if num == '1' else 'circle', nets.get('B' + num), r)
            else: b += pad('MH' + ref[1], lx, ly, 6.0, 3.2, net=nets.get('MH' + ref[1]), rot_=r)
        w, h = (x1 - x0) / 2, (y1 - y0) / 2
        b += fp_rect(-w, -h, w, h, 'F.Fab', 0.15)
        b += fp_rect(-w - 0.5, -h - 0.5, w + 0.5, h + 0.5, 'F.CrtYd', 0.05)
        b += fp_txt('POWER V3 (75.3 x 58.9, on 10 mm standoffs)', 0, 0, 'F.Fab', 1.5)
        jx, jy = 19.55 - pcx, 63.05 - pcy
        b += fp_txt('J1 BATT in', jx + 2, jy - 3, 'F.Fab', 1.0)
        return b
    fps['PowerBoard_V3_Mate'] = ('Carrier side of TritonECU power board V3: J2 2x7 (A1-A14) and J3 2x3 (B1-B6) '
                                 'pin positions and the four M3 standoff screws (MH1-MH4), read from the V3 PCB.', power)

    # VRBoard_V1_Mate
    u2, u3, mh, (gx0, gy0, gx1, gy1) = vr_geometry()
    vcx, vcy = (gx0 + gx1) / 2, (gy0 + gy1) / 2
    L = lambda x, y: (x - vcx, -(y - vcy))
    def vr(nets, r=0):
        b = ''
        for i, (x, y) in enumerate(u2, 1):
            lx, ly = L(x, y); b += pad(f'A{i}', lx, ly, 1.7, 1.02, 'rect' if i == 1 else 'circle', nets.get(f'A{i}'), r)
        for i, (x, y) in enumerate(u3, 1):
            lx, ly = L(x, y); b += pad(f'B{i}', lx, ly, 1.7, 1.02, 'rect' if i == 1 else 'circle', nets.get(f'B{i}'), r)
        for i, (x, y) in enumerate(mh, 1):
            lx, ly = L(x, y); b += pad(f'MH{i}', lx, ly, 6.0, 3.2, net=nets.get(f'MH{i}'), rot_=r)
        w, h = (gx1 - gx0) / 2, (gy1 - gy0) / 2
        b += fp_rect(-w, -h, w, h, 'F.Fab', 0.15)
        b += fp_rect(-w - 0.5, -h - 0.5, w + 0.5, h + 0.5, 'F.CrtYd', 0.05)
        b += fp_txt('VR V1 (39.9 x 33.9)', 0, 0, 'F.Fab', 1.5)
        return b
    fps['VRBoard_V1_Mate'] = ('Carrier side of TritonECU VR board V1: U2 1x9 (A1-A9), U3 1x10 (B1-B10) and two '
                              'M3 standoff screws (MH1-MH2), read from the V1 gerbers.', vr)
    # MCUModule_F767_Mate
    def mcu(nets, r=0):
        m = mcu_pinout
        b = ''
        # Samtec FLE-118-01 sockets, SMT: vendor pad geometry (mcu_pinout.FLE), positions from mcu_pinout
        for num, x, y, sx, sy, _ in m.smt_pads(m.FLE):
            n = f' (net "{nets[num]}")' if nets.get(num) else ''
            b += (f'\t\t(pad "{num}" smd rect (at {x:.4f} {y:.4f} {r}) (size {sx} {sy}) '
                  f'(layers "F.Cu" "F.Paste" "F.Mask"){n} (pintype "passive") (uuid "{U()}"))\n')
        for x, y, d in m.align_holes(m.FLE):
            b += (f'\t\t(pad "" np_thru_hole circle (at {x:.4f} {y:.4f} {r}) (size {d} {d}) (drill {d}) '
                  f'(layers "*.Cu" "*.Mask") (uuid "{U()}"))\n')
        bx, by = m.FLE['body']
        for s in m.SIDES:
            (cx, cy), (ax, ay), _ = m.header_frame(s)
            hx, hy = (bx, by) if ax else (by, bx)
            b += fp_rect(cx - hx, cy - hy, cx + hx, cy + hy, 'F.Fab', 0.1)
        for i, (x, y) in enumerate(m.HOLES, 1):
            b += pad(f'MH{i}', x, y, m.HOLE_PAD, m.HOLE_DRILL, net=nets.get(f'MH{i}'), rot_=r)
        h = m.BOARD / 2
        b += fp_rect(-h, -h, h, h, 'F.Fab', 0.15)
        b += fp_rect(-h - 0.5, -h - 0.5, h + 0.5, h + 0.5, 'F.CrtYd', 0.05)
        b += fp_rect(-11, -11, 11, 11, 'F.Fab', 0.1)
        b += fp_txt(f'MCU F767 ({m.BOARD:g} x {m.BOARD:g}, {m.STANDOFF:g} mm standoffs)', 0, 0, 'F.Fab', 1.2)
        b += fp_txt('QFP pin 1', -8, -9, 'F.Fab', 0.8)
        return b
    fps['MCUModule_F767_Mate'] = (f'Carrier side of the TritonECU STM32F767ZIT6 module: four Samtec {mcu_pinout.SOCKET_MPN} 2x18 1.27 mm '
                                  f'SMT sockets (A-D, one per QFP side), and four PEM {mcu_pinout.STANDOFF_MPN} SMT M3 standoffs (MH1-MH4), {mcu_pinout.STANDOFF:g} mm stack. '
                                  f'Module {mcu_pinout.BOARD:g} x {mcu_pinout.BOARD:g} mm, MH1 (keying) at {mcu_pinout.HOLES[0]}. '
                                  'From TritonECU-MCU/mcu_pinout.py.', mcu)
    return fps, pg

def kicad_mod(name, descr, body):
    return (f'(footprint "{name}"\n\t(version 20260206)\n\t(generator "gen_floorplan.py")\n\t(layer "F.Cu")\n'
            f'\t(descr "{descr}")\n'
            + fp_text_prop('Reference', 'REF**', 0, -2, 'F.SilkS')
            + fp_text_prop('Value', name, 0, 2, 'F.Fab')
            + '\t(attr through_hole)\n' + body.replace('\n\t\t', '\n\t').replace('\t\t(', '\t(') + ')\n')

# ---------------------------------------------------------------- symbols
def sym_pin(num, name, x, y, ang):
    return (f'\t\t\t\t(pin passive line (at {x} {y} {ang}) (length 2.54)\n'
            f'\t\t\t\t\t(name "{name}" {fnt()}) (number "{num}" {fnt()}))\n')

def symbol_def(name, ref, pins_left, pins_right, width, descr, fp):
    n = max(len(pins_left), len(pins_right))
    top = (n - 1) * 2.54 / 2
    top = round(math.ceil(top / 2.54 - 1e-9) * 2.54, 3)
    hw = width / 2
    body = f'\t\t\t\t(rectangle (start {-hw} {round(top + 2.54, 3)}) (end {hw} {round(top - n * 2.54, 3)}) (stroke (width 0.254) (type default)) (fill (type background)))\n'
    for i, (num, nm) in enumerate(pins_left):
        body += sym_pin(num, nm, -hw - 2.54, round(top - i * 2.54, 3), 0)
    for i, (num, nm) in enumerate(pins_right):
        body += sym_pin(num, nm, hw + 2.54, round(top - i * 2.54, 3), 180)
    s = (f'\t\t(symbol "{name}"\n\t\t\t(exclude_from_sim no) (in_bom yes) (on_board yes)\n'
         f'\t\t\t(property "Reference" "{ref}" (at {-hw} {round(top + 3.81, 3)} 0) {fnt()})\n'
         f'\t\t\t(property "Value" "{name}" (at {-hw} {round(top - n * 2.54 - 1.27, 3)} 0) {fnt()})\n'
         f'\t\t\t(property "Footprint" "{fp}" (at 0 0 0) (hide yes) {fnt()})\n'
         f'\t\t\t(property "Datasheet" "" (at 0 0 0) (hide yes) {fnt()})\n'
         f'\t\t\t(property "Description" "{descr}" (at 0 0 0) (hide yes) {fnt()})\n'
         f'\t\t\t(symbol "{name}_1_1"\n{body}\t\t\t)\n\t\t)\n')
    pins = {}
    for i, (num, nm) in enumerate(pins_left): pins[num] = (-hw - 2.54, round(top - i * 2.54, 3), 'L')
    for i, (num, nm) in enumerate(pins_right): pins[num] = (hw + 2.54, round(top - i * 2.54, 3), 'R')
    return s, pins

def build_symbols(pg):
    names = eec_names()
    eec_l = [(str(n), names.get(n, '')) for n in range(1, 53)]
    eec_r = [(str(n), names.get(n, '')) for n in range(53, 105)]
    p_l = [('A' + str(n), pg[('J2', str(n))][2]) for n in range(1, 15)]
    p_r = [('B' + str(n), pg[('J3', str(n))][2]) for n in range(1, 7)] + [(f'MH{i}', 'STANDOFF') for i in range(1, 5)]
    v_l = [(f'A{n}', f'U2_{n}') for n in range(1, 10)]
    v_r = [(f'B{n}', f'U3_{n}') for n in range(1, 11)] + [('MH1', 'STANDOFF'), ('MH2', 'STANDOFF')]
    syms = {}
    syms['EECV_104'] = symbol_def('EECV_104', 'J', eec_l, eec_r, 66.04,
        'Ford EEC-V 104-pin PCM header. Pin names from docs/1999-Ford-F150-4wd-5.42v/eec-v-pinout.md', f'{LIB}:EECV_104')
    syms['PowerBoard_V3_Mate'] = symbol_def('PowerBoard_V3_Mate', 'DB', p_l, p_r, 20.32,
        'Power board V3 daughterboard interface (J2 = A, J3 = B). Pin names are the power board net names.', f'{LIB}:PowerBoard_V3_Mate')
    syms['VRBoard_V1_Mate'] = symbol_def('VRBoard_V1_Mate', 'DB', v_l, v_r, 15.24,
        'VR board V1 daughterboard interface (U2 = A, U3 = B).', f'{LIB}:VRBoard_V1_Mate')
    mp = mcu_pinout.module_pins()
    m_l = [(n, net) for n, _, _, net in mp if n[0] in 'AB']
    m_r = [(n, net) for n, _, _, net in mp if n[0] in 'CD'] + [(f'MH{i}', 'STANDOFF') for i in range(1, 5)]
    syms['MCUModule_F767_Mate'] = symbol_def('MCUModule_F767_Mate', 'DB', m_l, m_r, 20.32,
        'STM32F767ZIT6 module interface (headers A-D). Pin names are the MCU port pins.', f'{LIB}:MCUModule_F767_Mate')
    return syms

# ---------------------------------------------------------------- schematic
def placed_symbol(lib_name, ref, value, x, y, pins, root, sheet_uuid, su):
    pin_lines = ''.join(f'\t\t(pin "{p}" (uuid "{U()}"))\n' for p in pins)
    return (f'\t(symbol (lib_id "{LIB}:{lib_name}") (at {x} {y} 0) (unit 1)\n'
            f'\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{su}")\n'
            f'\t\t(property "Reference" "{ref}" (at {x} {y - 2} 0) {fnt()})\n'
            f'\t\t(property "Value" "{value}" (at {x} {y + 2} 0) (hide yes) {fnt()})\n'
            f'\t\t(property "Footprint" "{LIB}:{lib_name}" (at {x} {y} 0) (hide yes) {fnt()})\n'
            f'\t\t(property "Datasheet" "" (at {x} {y} 0) (hide yes) {fnt()})\n'
            f'{pin_lines}'
            f'\t\t(instances (project "{PROJ}" (path "/{root}/{sheet_uuid}" (reference "{ref}") (unit 1))))\n\t)\n')

def glabel(name, x, y, side):
    ang, just = (180, 'right') if side == 'L' else (0, 'left')
    return (f'\t(global_label "{name}" (shape passive) (at {x} {y} {ang}) '
            f'(effects (font (size 1.27 1.27)) (justify {just})) (uuid "{U()}"))\n')

# ---------------------------------------------------------------- main
POWER_BOARD_NET = {'SDA': 'I2C_SDA', 'SCL': 'I2C_SCL', '3.3_ENOUT': 'ENOUT',
                   '+VIN': 'VPROT',    # J3 +VIN is the LTC4364 OUTPUT (IC1 pin 1, after R2), not its input
                   '3_GOOD': None}     # 3_GOOD is not wired: carrier_pinmap.py

def interconnect_nets(pg):
    """{ref: {pin: net}} for the Interconnect sheet's global labels."""
    import carrier_pinmap, eecv_pins
    out = {'J1': {str(p): net for p, (net, *_) in eecv_pins.PINS.items()}}
    db1 = {}
    for (conn, num), v in pg.items():
        pin = ('A' if conn == 'J2' else 'B') + num
        name = v[2]
        db1[pin] = POWER_BOARD_NET.get(name, name)
    db1.update({f'MH{i}': 'GND' for i in range(1, 5)})      # the V3 standoffs are on its GND net
    out['DB1'] = db1
    port_net = {pin: net for net, pin, *_ in carrier_pinmap.SIGNALS}
    db3 = {}
    for pad, _, _, net in mcu_pinout.module_pins():
        if re.fullmatch(r'P[A-K]\d+', net):
            db3[pad] = port_net.get(net)          # spare and reserved port pins stay unlabelled
        else:
            db3[pad] = net                        # GND, +3.3V, NRST, VBAT, BOOT0
    db3.update({f'MH{i}': 'GND' for i in range(1, 5)})
    out['DB3'] = db3
    return out

def has_ref(text, ref):
    return re.search(r'\(property\s+"Reference"\s+"%s"' % re.escape(ref), text) is not None

def drop_blocks(text, keyword, pred):
    """Remove top-level (keyword ...) blocks for which pred(block) is true."""
    out, k = [], 0
    for m in re.finditer(r'\n\t\(%s[\s(]' % keyword, text):
        a = m.start() + 2
        if a < k: continue
        e = span(text, a)
        if pred(text[a:e]):
            out.append(text[k:m.start()]); k = e
    return ''.join(out) + text[k:]

def main():
    os.chdir(HERE)
    fps, pg = build_footprints()
    syms = build_symbols(pg)

    # libraries
    os.makedirs(f'{LIB}.pretty', exist_ok=True)
    for name, (descr, fn) in fps.items():
        open(f'{LIB}.pretty/{name}.kicad_mod', 'w').write(kicad_mod(name, descr, fn({})))
    open(f'{LIB}.kicad_sym', 'w').write('(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "gen_floorplan.py")\n\t(generator_version "10.0")\n'
                                       + ''.join(s.replace('\n\t\t', '\n\t').replace('\t\t(symbol', '\t(symbol', 1)
                                                 for s, _ in syms.values()) + ')\n')
    open('fp-lib-table', 'w').write(f'(fp_lib_table\n\t(version 7)\n\t(lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.pretty")(options "")(descr "TritonECU carrier parts"))\n)\n')
    open('sym-lib-table', 'w').write(f'(sym_lib_table\n\t(version 7)\n\t(lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.kicad_sym")(options "")(descr "TritonECU carrier parts"))\n'
                                     f'\t(lib (name "TritonECU-Carrier")(type "KiCad")(uri "${{KIPRJMOD}}/TritonECU-Carrier.kicad_sym")(options "")(descr "carrier symbols drawn by gen_carrier.py"))\n)\n')

    lock = [f for f in os.listdir('.') if f.startswith('~') and f.endswith(('.kicad_sch.lck', '.kicad_pcb.lck'))]
    if lock:
        print('libraries regenerated; project is open in KiCad (%s) - close it, then re-run' % ', '.join(lock))
        return

    # root sheet: add the Interconnect sheet
    root_s = open(f'{PROJ}.kicad_sch').read()
    root = re.search(r'\(uuid "([^"]+)"\)', root_s).group(1)
    if 'Interconnect.kicad_sch' not in root_s:
        sh = U()
        block = (f'\t(sheet (at 26.67 30.48) (size 30.48 27.94) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)\n'
                 f'\t\t(stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0)) (uuid "{sh}")\n'
                 f'\t\t(property "Sheetname" "Interconnect" (at 26.67 29.77 0) {fnt()})\n'
                 f'\t\t(property "Sheetfile" "Interconnect.kicad_sch" (at 26.67 59.0 0) {fnt()})\n'
                 f'\t\t(instances (project "{PROJ}" (path "/{root}" (page "3"))))\n\t)\n')
        root_s = root_s.replace('\t(sheet_instances', block + '\t(sheet_instances', 1)
        open(f'{PROJ}.kicad_sch', 'w').write(root_s)
        pro = json.load(open(f'{PROJ}.kicad_pro'))
        pro['sheets'].append([sh, 'Interconnect'])
        json.dump(pro, open(f'{PROJ}.kicad_pro', 'w'), indent=2)
    sheet_uuid = re.search(r'\(uuid "([^"]+)"\)\s*\(property "Sheetname" "Interconnect"', root_s).group(1)

    # Interconnect sheet: rebuilt on every run, so its labels always follow
    # carrier_pinmap.py and eecv_pins.py. Each symbol keeps the UUID it already
    # has, which is what keeps the PCB footprints linked to it.
    place = {'EECV_104': ('J1', 'EEC-V 104', 80.01, 110.49),
             'PowerBoard_V3_Mate': ('DB1', 'Power board V3', 200.66, 74.93),
             'MCUModule_F767_Mate': ('DB3', 'MCU module F767', 320.04, 149.86)}
    old = open('Interconnect.kicad_sch').read() if os.path.exists('Interconnect.kicad_sch') else ''
    def old_uuid(ref):
        m = re.search(r'\(uuid "([^"]+)"\)\n\t\t\(property "Reference" "%s"' % re.escape(ref), old)
        return m.group(1) if m else U()
    file_uuid = re.search(r'\(uuid "([^"]+)"\)', old).group(1) if old else U()
    nets = interconnect_nets(pg)
    libs, body = '', ''
    for n, (ref, val, x, y) in place.items():
        libs += syms[n][0].replace(f'(symbol "{n}"', f'(symbol "{LIB}:{n}"', 1)
        body += placed_symbol(n, ref, val, x, y, syms[n][1].keys(), root, sheet_uuid, old_uuid(ref))
        for num, (lx, ly, side) in syms[n][1].items():
            name = nets[ref].get(num)
            if name:
                body += glabel(name, round(x + lx, 3), round(y - ly, 3), side)
            elif ref in ('J1', 'DB3') or (ref == 'DB1' and num in nets['DB1']):
                # deliberately unused: free connector pins, spare and reserved
                # module pins (SWD/VCP are on the module's STDC14)
                body += f'\t(no_connect (at {round(x + lx, 3)} {round(y - ly, 3)}) (uuid "{U()}"))\n'
    sch = (f'(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n'
           f'\t(uuid "{file_uuid}")\n\t(paper "A3")\n\t(lib_symbols\n{libs}\t)\n{body}\t(embedded_fonts no)\n)\n')
    open('Interconnect.kicad_sch', 'w').write(sch)
    added = {}

    # netlist -> pad nets
    tmp = os.path.join(HERE, '.gen-netlist.net')
    subprocess.run(['flatpak', 'run', '--command=kicad-cli', f'--filesystem={HERE}', 'org.kicad.KiCad',
                    'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', tmp, f'{PROJ}.kicad_sch'],
                   check=True, capture_output=True)
    nl = open(tmp).read(); os.remove(tmp)
    nets = {}; uuids = {}
    tok = re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', nl); st = [[]]
    for t in tok:
        if t == '(': st.append([])
        elif t == ')': x = st.pop(); st[-1].append(x)
        else: st[-1].append(t[1:-1] if t.startswith('"') else t)
    for n in [x for x in st[0][0] if x[0] == 'nets'][0][1:]:
        name = [x[1] for x in n if x[0] == 'name'][0]
        for node in [x for x in n if x[0] == 'node']:
            d = {x[0]: x[1] for x in node[1:]}
            nets.setdefault(d['ref'], {})[d['pin']] = name
    for c in [x for x in st[0][0] if x[0] == 'components'][0][1:]:
        d = {x[0]: x for x in c[1:]}
        uuids[d['ref'][1]] = d['tstamps'][1]

    # board
    pcb_path = f'{PROJ}.kicad_pcb'
    pcb = open(pcb_path).read()
    fresh = '(footprint ' not in pcb
    ox, oy = O
    fp_place = {'J1': ('EECV_104', ox + EEC_X, oy + EEC_POST_TO_EDGE, 0),
                'DB1': ('PowerBoard_V3_Mate', ox + POWER_AT[0], oy + POWER_AT[1], POWER_AT[2]),
                'DB3': ('MCUModule_F767_Mate', ox + MCU_AT[0], oy + MCU_AT[1], MCU_AT[2])}
    value = {v[0]: v[1] for v in place.values()}
    # a placed mate footprint whose library version changed (e.g. a new connector)
    # is swapped for the new one, at the position and rotation it has on the board
    for ref, (n, x, y, r) in list(fp_place.items()):
        descr = fps[n][0]
        def stale(blk, ref=ref, descr=descr):
            return has_ref(blk, ref) and f'(descr "{descr}")' not in blk
        old = [pcb[a:span(pcb, a)] for a in (m.start() + 2 for m in re.finditer(r'\n\t\(footprint[\s(]', pcb))
               if stale(pcb[a:span(pcb, a)])]
        if old:
            at = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', old[0])
            fp_place[ref] = (n, float(at.group(1)), float(at.group(2)), float(at.group(3) or 0))
            pcb = drop_blocks(pcb, 'footprint', stale)
            print('refreshing', ref)
    add = ''; new_refs = []
    for ref, (n, x, y, r) in fp_place.items():
        if has_ref(pcb, ref): continue
        new_refs.append(ref)
        descr, fn = fps[n]
        add += (f'\t(footprint "{LIB}:{n}"\n\t\t(layer "F.Cu")\n\t\t(uuid "{U()}")\n\t\t(at {x:.3f} {y:.3f} {r})\n'
                f'\t\t(descr "{descr}")\n'
                + fp_text_prop('Reference', ref, 0, 0, 'F.SilkS', size=1.5)
                + fp_text_prop('Value', value[ref], 0, 2, 'F.Fab', hide=True)
                + fp_text_prop('Footprint', f'{LIB}:{n}', 0, 0, 'F.Fab', hide=True)
                + f'\t\t(path "/{sheet_uuid}/{uuids[ref]}")\n\t\t(sheetname "/Interconnect/")\n\t\t(sheetfile "Interconnect.kicad_sch")\n'
                f'\t\t(attr through_hole)\n' + fn(nets.get(ref, {}), r) + '\t)\n')
    gr = lambda x0, y0, x1, y1, layer, w=0.15: (f'\t(gr_rect (start {ox + x0:.3f} {oy + y0:.3f}) (end {ox + x1:.3f} {oy + y1:.3f}) '
                                                f'(stroke (width {w}) (type solid)) (fill no) (layer "{layer}") (uuid "{U()}"))\n')
    gt = lambda t, x, y, size=1.5, layer='Dwgs.User': (f'\t(gr_text "{t}" (at {ox + x:.3f} {oy + y:.3f} 0) (layer "{layer}") (uuid "{U()}")\n'
                                                     f'\t\t(effects (font (size {size} {size}) (thickness {size * 0.15:.3f})) (justify left)))\n')
    # the Nucleo-144 reservation is gone: the MCU module replaces it
    pcb = drop_blocks(pcb, 'gr_text', lambda b: 'NUCLEO-144 reserved' in b or 'morpho CN11/CN12' in b)
    pcb = drop_blocks(pcb, 'gr_rect', lambda b: re.search(r'\(start 39(\.0+)? 55(\.0+)?\)\s*\(end 109(\.0+)? 188(\.0+)?\)', b) is not None)
    if fresh:
        add += gr(0, 0, BOARD_W, BOARD_L, 'Edge.Cuts', 0.1)
        add += gr(0, 22, EDGE_BAND, BOARD_L, 'Dwgs.User') + gr(BOARD_W - EDGE_BAND, 22, BOARD_W, BOARD_L, 'Dwgs.User')
        add += gr(EDGE_BAND, BOARD_L - EDGE_BAND, BOARD_W - EDGE_BAND, BOARD_L, 'Dwgs.User')
        add += gt('EDGE COOLING BAND 12 mm', 1, BOARD_L - 5, 1.2)
        notes = ['FLOOR PLAN v0 - gen_floorplan.py',
                 'ESTIMATED: outline is a plain 158 x 174 rectangle',
                 'ESTIMATED: connector centred on the width',
                 'MISSING: case mounting holes [MEASURE] with carrier-template',
                 'MISSING: flange keepout around the connector [MEASURE]']
        for i, t in enumerate(notes):
            add += gt(t, 0, BOARD_L + 6 + i * 3.0, 1.5, 'Cmts.User')
    pcb = pcb.rstrip()
    assert pcb.endswith(')')
    open(pcb_path, 'w').write(pcb[:-1] + add + ')\n')
    print('added:', ', '.join(new_refs) or 'nothing')

if __name__ == '__main__':
    main()
