#!/usr/bin/env python3
"""Place the TritonECU-MCU module PCB: 44 x 44 mm, 6 layers.

Runs inside KiCad's Python (pcbnew), via flatpak:
  flatpak run --command=python3 --filesystem=$PWD org.kicad.KiCad gen_module_pcb.py

It is a BOOTSTRAP for placement. It refuses to touch a board that already has
tracks, so routing work is never lost.

Stack-up (1.6 mm):
  F.Cu   signal: QFP and fan-out
  In1.Cu GND plane
  In2.Cu signal
  In3.Cu signal
  In4.Cu +3.3V plane
  B.Cu   signal: decoupling and crystals under the QFP; the four headers

Programming: an ST STDC14 (Samtec FTSH-107, SMT) on the TOP, beside the QFP,
reachable with the module mounted. It carries SWD, SWO, NRST and the ST-Link
VCP on USART3 (PD8/PD9). A Tag-Connect would not fit: its alignment holes would
land under the QFP or a header.

Every pad is checked against mcu_pinout.py, so the module still mates the
carrier footprint (TritonECU-Main:MCUModule_F767_Mate).
"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mcu_pinout as mp
import pcbnew

PROJ = 'TritonECU-MCU'
FPLIB = '/app/extensions/Library/Footprints/footprints'
ORIGIN = (100.0, 100.0)          # board centre on the page
MM = pcbnew.FromMM

def V(x, y): return pcbnew.VECTOR2I(MM(ORIGIN[0] + x), MM(ORIGIN[1] + y))

# ---------------------------------------------------------------- netlist
def netlist():
    tmp = os.path.join(HERE, '.gen-netlist.net')
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', tmp,
                    f'{PROJ}.kicad_sch'], check=True, capture_output=True)
    nl = open(tmp).read(); os.remove(tmp)
    comps = {}
    for blk in nl[:nl.index('\n\t(libparts')].split('\n\t\t(comp\n')[1:]:
        ref = re.search(r'\(ref "([^"]+)"\)', blk).group(1)
        comps[ref] = dict(value=re.search(r'\(value "([^"]*)"\)', blk).group(1),
                          fp=re.search(r'\(footprint "([^"]*)"\)', blk).group(1),
                          uuid=re.search(r'\(tstamps "([0-9a-f-]{36})"\)', blk).group(1),
                          fields=dict(re.findall(r'\(field\s*\(name "([^"]+)"\)\s*"([^"]*)"\)', blk)))
    pins = {}
    for blk in nl.split('\n\t\t(net\n')[1:]:
        name = re.search(r'\(name "([^"]+)"\)', blk).group(1)
        for r, p, typ in re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)(?:\s*\(pinfunction "[^"]*"\))?\s*\(pintype "([^"]+)"\)', blk):
            # NC pins and no-connect-flagged pins have no net in the schematic
            if typ != 'no_connect' and not name.startswith('unconnected-('):
                pins[(r, p)] = name
    return comps, pins

def symbol_fields():
    """{ref: {field: value}} straight from the schematic. The netlist leaves out
    empty fields, which DRC's schematic parity check then reports as missing."""
    sch = open(f'{PROJ}.kicad_sch').read()
    body = sch[sch.index('\n\t(lib_symbols'):]
    body = body[body.index('\n\t)\n'):]          # skip the embedded library
    out = {}
    for blk in body.split('\n\t(symbol\n')[1:]:
        props = dict(re.findall(r'\n\t\t\(property "([^"]+)" "([^"]*)"', blk))
        out[props['Reference']] = props
    return out

# ---------------------------------------------------------------- placement
QFP_PAD = {}   # filled once U1 is placed: pin -> (x, y) module coords

def inward(pin, r):
    """Point at distance r from the centre, on the line from the centre to the pin."""
    x, y = QFP_PAD[pin]
    if abs(x) > abs(y): return (r * (1 if x > 0 else -1), y)
    return (x, r * (1 if y > 0 else -1))

def rot_for(pin):
    """0402 long axis pointing at the pin (radial)."""
    x, y = QFP_PAD[pin]
    return 0 if abs(x) > abs(y) else 90

VDD_PINS = [17, 30, 39, 52, 62, 72, 84, 95, 108, 121, 131, 144]   # C1..C12, in schematic order
RING = 8.4

def placements():
    """ref -> (x, y, rotation, side)  side 'F' or 'B'."""
    P = {'U1': (0, 0, 0, 'F')}
    for i, pin in enumerate(VDD_PINS, 1):
        x, y = inward(pin, RING); P[f'C{i}'] = (x, y, rot_for(pin), 'B')
    P['C13'] = (2.5, 4.0, 90, 'B')                # 4.7u bulk
    P['C14'] = (5.0, 4.0, 90, 'B')                # 10u bulk
    P['C16'] = (-8.4, 6.8, 0, 'B')                 # VDDA 100n by pins 32/33
    P['C15'] = (-4.4, 6.6, 90, 'B')                # VDDA 1u
    P['FB1'] = (-6.0, 6.6, 90, 'B')
    x, y = inward(6, RING); P['C19'] = (x, y, 0, 'B')             # VBAT
    x, y = inward(25, RING); P['C20'] = (x, y, 0, 'B')            # NRST
    x, y = inward(71, 6.4); P['C17'] = (x - 0.8, y, 90, 'B')      # VCAP1
    x, y = inward(106, 6.4); P['C18'] = (x, y + 0.8, 0, 'B')      # VCAP2
    x, y = inward(138, RING); P['R1'] = (x, y, 90, 'B')           # BOOT0
    P['Y1'] = (-4.5, 2.4, 0, 'B')                  # HSE by PH0/PH1 (pins 23/24)
    P['C21'] = (-0.6, 1.6, 0, 'B'); P['C22'] = (-0.6, 3.4, 0, 'B')
    P['Y2'] = (-5.2, -4.6, 90, 'B')                # LSE by PC14/PC15 (pins 8/9)
    P['C23'] = (-2.8, -5.4, 0, 'B'); P['C24'] = (-2.8, -3.8, 0, 'B')
    # STDC14 programming header on TOP, over header D, near PA13/PA14 (pins 105/109)
    P['J5'] = (4.0, -17.0, 90, 'F')
    for i, (x, y) in enumerate(mp.HOLES, 1):
        P[f'H{i}'] = (x, y, 0, 'B')      # Wurth SMT spacers, soldered to the bottom
    return P

HEADER_CENTRE = {'A': (-(mp.ROW_IN + mp.PITCH / 2), 0), 'B': (0, mp.ROW_IN + mp.PITCH / 2),
                 'C': (mp.ROW_IN + mp.PITCH / 2, 0), 'D': (0, -(mp.ROW_IN + mp.PITCH / 2))}

# ---------------------------------------------------------------- build
def load(fpid):
    lib, name = fpid.split(':')
    path = os.path.join(HERE, f'{PROJ}.pretty') if lib == PROJ else f'{FPLIB}/{lib}.pretty'
    fp = pcbnew.FootprintLoad(path, name)
    assert fp, fpid
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp

def pad_xy(p):
    q = p.GetPosition()
    return (round(pcbnew.ToMM(q.x) - ORIGIN[0], 3), round(pcbnew.ToMM(q.y) - ORIGIN[1], 3))

# ---------------------------------------------------------------- power fanout
VIA_D, VIA_HOLE, STUB_W = 0.5, 0.25, 0.25
CLR = 0.17            # copper clearance used here: rule 0.15 plus margin
HOLE_CLR = 0.3        # to NPTH alignment holes
VIA_PITCH = 0.75      # min centre distance between any two vias (hole-to-hole 0.25 + margin)
EDGE = mp.BOARD / 2 - 0.5 - VIA_D / 2

def power_fanout(board, nets):
    """A via beside every GND / +3.3V SMD pad, straight into In1 (GND) / In4 (+3.3V),
    so the autorouter never has to carry power. Each via is placed at the first
    candidate spot whose via and stub clear every other-net pad, hole and via."""
    import math
    obst = []      # pad shapes: (SHAPE, layers, net)
    geo = []       # plain geometry, module coords: (x1, y1, x2, y2, half_width, layers or None, net, clearance)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                x, y = pad_xy(p)
                geo.append((x, y, x, y, p.GetDrillSize().x / 2e6, None, '', HOLE_CLR))
                continue
            for L in (pcbnew.F_Cu, pcbnew.B_Cu):
                if p.IsOnLayer(L):
                    obst.append((p.GetEffectiveShape(L), {L}, p.GetNetname()))
    vias = []

    def segdist(px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L2))
        return math.hypot(px - x1 - t * dx, py - y1 - t * dy)

    def seg2seg(a, b):
        (x1, y1, x2, y2), (x3, y3, x4, y4) = a, b
        return min(segdist(x1, y1, x3, y3, x4, y4), segdist(x2, y2, x3, y3, x4, y4),
                   segdist(x3, y3, x1, y1, x2, y2), segdist(x4, y4, x1, y1, x2, y2))

    def ok(pad, L, net, vx, vy):
        if abs(vx) > EDGE or abs(vy) > EDGE: return False
        if any(math.hypot(vx - a, vy - b) < VIA_PITCH for a, b in vias): return False
        c = V(vx, vy)
        circ = pcbnew.SHAPE_CIRCLE(c, MM(VIA_D / 2))
        seg = pcbnew.SHAPE_SEGMENT(pad.GetPosition(), c, MM(STUB_W))
        for sh, layers, n in obst:
            if n == net: continue
            if sh.Collide(circ, MM(CLR)): return False
            if L in layers and sh.Collide(seg, MM(CLR)): return False
        px, py = pad_xy(pad)
        for x1, y1, x2, y2, hw, layers, n, clr in geo:
            if n == net and n: continue
            if segdist(vx, vy, x1, y1, x2, y2) < VIA_D / 2 + hw + clr: return False
            if (layers is None or L in layers) and seg2seg((px, py, vx, vy), (x1, y1, x2, y2)) < STUB_W / 2 + hw + clr:
                return False
        return True

    def candidates(pad, fp):
        """Yield (x, y) module coords, best first."""
        px, py = pad_xy(pad)
        sz = pad.GetSize(); sx, sy = sz.x / 1e6, sz.y / 1e6
        ang = math.radians(pad.GetOrientation().AsDegrees())
        # pad's long axis in board coords (KiCad rotates clockwise on screen)
        lx, ly = (math.cos(ang), -math.sin(ang)) if sx >= sy else (math.sin(ang), math.cos(ang))
        half = max(sx, sy) / 2
        ref = fp.GetReference()
        if ref == 'U1' or ref in ('J1', 'J2', 'J3', 'J4'):
            # along the pad axis: U1 inward first (outward stays free for signal escape);
            # headers away from the header centreline (the two rows face each other)
            if ref == 'U1':
                inward = -1 if lx * px + ly * py > 0 else 1
                dirs = (inward, -inward)
            else:
                (hx, hy), _, _ = mp.header_frame(mp.SIDES[int(ref[1]) - 1])
                out = 1 if lx * (px - hx) + ly * (py - hy) > 0 else -1
                dirs = (out, -out)
            tx, ty = -ly, lx
            for sgn in dirs:
                for extra in (0.0, 0.3, 0.6, 1.0, 1.4, 1.8):
                    for t in (0.0, 0.5, -0.5, 0.9, -0.9, 1.3, -1.3):
                        d = half + CLR + VIA_D / 2 + 0.02 + extra
                        yield (px + sgn * lx * d + t * tx, py + sgn * ly * d + t * ty)
        else:
            for k in range(4):
                r = half + CLR + VIA_D / 2 + 0.05 + 0.25 * k
                for a in range(0, 360, 30):
                    yield (px + r * math.cos(math.radians(a)), py + r * math.sin(math.radians(a)))

    missed = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            net = pad.GetNetname()
            if net not in ('GND', '+3.3V') or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            L = pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
            for vx, vy in candidates(pad, fp):
                if ok(pad, L, net, vx, vy): break
            else:
                missed.append(f'{fp.GetReference()}.{pad.GetNumber()}'); continue
            c = V(vx, vy)
            v = pcbnew.PCB_VIA(board); v.SetPosition(c); v.SetDrill(MM(VIA_HOLE)); v.SetWidth(MM(VIA_D))
            v.SetNet(nets[net]); v.SetLocked(True); board.Add(v)
            t = pcbnew.PCB_TRACK(board); t.SetStart(pad.GetPosition()); t.SetEnd(c); t.SetWidth(MM(STUB_W))
            t.SetLayer(L); t.SetNet(nets[net]); t.SetLocked(True); board.Add(t)
            vias.append((vx, vy))
            px, py = pad_xy(pad)
            geo.append((vx, vy, vx, vy, VIA_D / 2, None, net, CLR))
            geo.append((px, py, vx, vy, STUB_W / 2, {L}, net, CLR))
    print(f'power fanout: {len(vias)} vias' + (f'; NO SPOT for {missed}' if missed else ''))

def main():
    os.chdir(HERE)
    path = f'{PROJ}.kicad_pcb'
    if os.path.exists(path):
        old = pcbnew.LoadBoard(path)
        if any(t.GetClass() == 'PCB_TRACK' and t.GetWidth() != MM(STUB_W) for t in old.GetTracks()):
            sys.exit(f'{path} has routing - refusing to re-place')
    comps, pins = netlist()
    fields = symbol_fields()

    board = pcbnew.NewBoard(path)
    board.SetCopperLayerCount(6)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(MM(1.6))
    for layer, name, typ in [(pcbnew.In1_Cu, 'In1.GND', pcbnew.LT_POWER), (pcbnew.In2_Cu, 'In2.Sig', pcbnew.LT_SIGNAL),
                             (pcbnew.In3_Cu, 'In3.Sig', pcbnew.LT_SIGNAL), (pcbnew.In4_Cu, 'In4.3V3', pcbnew.LT_POWER)]:
        board.SetLayerName(layer, name); board.SetLayerType(layer, typ)

    nets = {}
    for n in sorted(set(pins.values())):
        nets[n] = pcbnew.NETINFO_ITEM(board, n); board.Add(nets[n])

    # outline
    h = mp.BOARD / 2
    r = pcbnew.PCB_SHAPE(board); r.SetShape(pcbnew.SHAPE_T_RECT)
    r.SetStart(V(-h, -h)); r.SetEnd(V(h, h)); r.SetLayer(pcbnew.Edge_Cuts); r.SetWidth(MM(0.1))
    board.Add(r)

    def add(ref, x, y, rot, side):
        c = comps[ref]
        fp = load(c['fp'])
        fp.SetReference(ref); fp.SetValue(c['value'])
        fp.SetPath(pcbnew.KIID_PATH(f"/{c['uuid']}"))
        fp.SetSheetname('/'); fp.SetSheetfile(f'{PROJ}.kicad_sch')
        for k, v in fields[ref].items():
            if k in ('Reference', 'Value', 'Footprint', 'Description'):
                continue
            if k == 'Datasheet':
                fp.GetField(k).SetText(v); continue
            fp.SetField(k, v); fp.GetField(k).SetVisible(False)
        board.Add(fp)
        fp.SetPosition(V(x, y))
        if side == 'B':
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetOrientationDegrees(rot)
        if side == 'B' and ref[0] in 'CRFY':
            # too dense under the QFP for silk references: keep them on B.Fab
            fp.Reference().SetLayer(pcbnew.B_Fab)
            fp.Reference().SetTextSize(pcbnew.VECTOR2I(MM(0.4), MM(0.4))); fp.Reference().SetTextThickness(MM(0.06))
            fp.Reference().SetPosition(fp.GetPosition())
        if ref[0] == 'H': fp.Reference().SetVisible(False)
        for p in fp.Pads():
            n = pins.get((ref, p.GetNumber()))
            if n: p.SetNet(nets[n])
        return fp

    # U1 first: the ring positions are derived from its pads
    u1 = add('U1', 0, 0, 0, 'F')
    for p in u1.Pads(): QFP_PAD[int(p.GetNumber())] = pad_xy(p)
    assert QFP_PAD[1][0] < -10 and QFP_PAD[1][1] < -8, 'QFP pin 1 must be top-left'

    for ref, (x, y, rot, side) in placements().items():
        if ref != 'U1': add(ref, x, y, rot, side)

    # headers: pick the bottom-side orientation whose pads land on mcu_pinout's positions
    want = {pad: (x, y) for pad, x, y, _, _, _ in mp.smt_pads(mp.FTSH)}
    holes = sorted((x, y) for x, y, _ in mp.align_holes(mp.FTSH))
    for i, s in enumerate(mp.SIDES):
        ref = f'J{i + 1}'
        cx, cy = HEADER_CENTRE[s]
        fp = add(ref, cx, cy, 0, 'B')
        for rot in (0, 90, 180, 270):
            fp.SetOrientationDegrees(rot)
            if all(max(abs(a - b) for a, b in zip(pad_xy(p), want[s + p.GetNumber()])) < 0.002
                   for p in fp.Pads() if p.GetNumber()):
                break
        else:
            sys.exit(f'{ref}: no orientation matches mcu_pinout side {s}')
    got = sorted(pad_xy(p) for fp in board.GetFootprints() if fp.GetReference() in ('J1', 'J2', 'J3', 'J4')
                 for p in fp.Pads() if not p.GetNumber())
    assert all(max(abs(a - b) for a, b in zip(g, w)) < 0.002 for g, w in zip(got, holes)), 'alignment holes'

    power_fanout(board, nets)

    # planes
    def plane(layer, net):
        z = pcbnew.ZONE(board); z.SetLayer(layer); z.SetNet(nets[net])
        ol = z.Outline(); ol.NewOutline()
        e = 0.5   # board-edge copper clearance
        for x, y in [(-h + e, -h + e), (h - e, -h + e), (h - e, h - e), (-h + e, h - e)]:
            ol.Append(MM(ORIGIN[0] + x), MM(ORIGIN[1] + y))
        z.SetLocalClearance(MM(0.3)); z.SetMinThickness(MM(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        board.Add(z)
    plane(pcbnew.In1_Cu, 'GND')
    plane(pcbnew.In4_Cu, '+3.3V')
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())

    # notes
    for k, t in enumerate(['MCU module V1 - placement by gen_module_pcb.py, not routed',
                           'Stack: F sig / In1 GND / In2 sig / In3 sig / In4 +3.3V / B sig',
                           f'Headers: Samtec {mp.HEADER_MPN} SMT on the bottom (vendor pad geometry)']):
        tx = pcbnew.PCB_TEXT(board); tx.SetText(t); tx.SetLayer(pcbnew.Cmts_User)
        tx.SetPosition(V(-h, h + 4 + 2.5 * k)); tx.SetTextSize(pcbnew.VECTOR2I(MM(1.2), MM(1.2)))
        tx.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
        board.Add(tx)

    pcbnew.SaveBoard(path, board)
    # the API fill misses the clearance round the flipped headers' NPTH alignment
    # holes; kicad-cli's refill gets it right
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--refill-zones', '--save-board', '-o', os.devnull, path],
                   check=True, capture_output=True)
    print('placed', len(board.GetFootprints()), 'footprints;', len(nets), 'nets')

if __name__ == '__main__':
    main()
