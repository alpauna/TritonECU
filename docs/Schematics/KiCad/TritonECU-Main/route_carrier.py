#!/usr/bin/env python3
"""Autoroute the carrier with Freerouting, headless (KiCad closed).

  python3 route_carrier.py classes      net classes into TritonECU-Main.kicad_pro (host python)
  flatpak run --command=python3 --filesystem=$PWD org.kicad.KiCad route_carrier.py export
                                        GND plane on In1.Cu, fill, write route/carrier.dsn
  java -jar freerouting-2.4.1.jar -de route/carrier.dsn -do route/carrier.ses -mp 100 --gui.enabled=false
  flatpak run --command=python3 --filesystem=$PWD org.kicad.KiCad route_carrier.py import
                                        read route/carrier.ses, refill zones, save
  kicad-cli pcb drc --format json -o route/drc.json TritonECU-Main.kicad_pcb
  flatpak run --command=python3 --filesystem=$PWD org.kicad.KiCad route_carrier.py repair route/drc.json
                                        delete shorting / clearance-violating / dangling tracks, then
                                        stitch every GND / AGND fragment the DRC lists as unconnected to
                                        its In1.Cu plane with a via (and a stub, for a pad). Repeat with a
                                        fresh DRC until it stops gaining.

Net classes - harness-protection.md, output-drivers.md:
  Coil    COIL*_OUT: the ISL9V3040 clamps at 400 V. 0.8 mm clearance is IPC-2221 B4
          (external, coated, 301-500 V): the board must be CONFORMAL COATED.
  Power   injector / solenoid / heater / relay outputs, freewheel returns, VPWR, VPROT.
          0.8 mm: the widest that still escapes between EEC-V pads (2.0 mm on
          3.4 mm pitch leaves 1.4 mm = 0.8 + 2 x 0.2).
  Supply  the logic and sensor rails, 0.4 mm.
  GND is a solid plane on In1.Cu, with an AGND island under the ADC column joined only
  at NT801 (the analog star); everything else is Default 0.2 mm.

Stackup, 6 layers, 1.6 mm: F.Cu signal / In1.Cu GND plane (power) / In2.Cu, In3.Cu, In4.Cu
signal / B.Cu signal. Four layers with In1 as the plane left about 340 unrouted at pass 4.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = 'TritonECU-Main'
ROUTE = os.path.join(HERE, 'route')

CLASSES = {   # name: (track, clearance, via dia, via drill, patterns)
    'Coil': (1.2, 0.8, 0.8, 0.4, ['COIL*_OUT']),
    'Power': (0.8, 0.2, 0.8, 0.4, ['INJ*_OUT', 'HTR*_OUT', 'SSA_OUT', 'SSB_OUT', 'VENT_OUT', 'IMCC_OUT',
                                   'EVAP_OUT', 'EGR_OUT', 'TCC_OUT', 'EPC_OUT', 'IAC_OUT', 'CCS_OUT',
                                   'FPUMP_OUT', 'FAN?_OUT', 'ACC_OUT', '*_SINK', 'FW_391', 'FW_1138',
                                   'VPWR', 'VPROT']),
    'Supply': (0.4, 0.2, 0.6, 0.3, ['+5V', '+5V_SW', '+3.3V', '+3.3V_SW', 'VREF_5V', 'VREF', 'VREF?_SW',
                                    '*SD_3V3', 'VBAT', 'GND', 'AGND']),
}

def classes():
    p = os.path.join(HERE, f'{PROJ}.kicad_pro')
    pro = json.load(open(p))
    ns = pro['net_settings']
    default = next(c for c in ns['classes'] if c['name'] == 'Default')
    ns['classes'] = [default]
    for name, (w, cl, vd, vdr, _) in CLASSES.items():
        c = dict(default); c.update(name=name, track_width=w, clearance=cl, via_diameter=vd, via_drill=vdr)
        ns['classes'].append(c)
    ns['netclass_patterns'] = [{'netclass': name, 'pattern': pat}
                               for name, (*_, pats) in CLASSES.items() for pat in pats]
    json.dump(pro, open(p, 'w'), indent=2)
    print('net classes:', ', '.join(CLASSES))

def agnd_island(board, margin=0.5):
    """Rectangle around every footprint with an AGND pad, the star NT801 excepted."""
    import pcbnew
    xs, ys = [], []
    for fp in board.GetFootprints():
        if fp.GetReference() == 'NT801' or not any(p.GetNetname() == 'AGND' for p in fp.Pads()):
            continue
        b = fp.GetBoundingBox(False)
        xs += [b.GetLeft(), b.GetRight()]; ys += [b.GetTop(), b.GetBottom()]
    m = pcbnew.FromMM(margin)
    l, t, r, b = min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m
    print('AGND island %.1f %.1f - %.1f %.1f' % tuple(pcbnew.ToMM(v) for v in (l, t, r, b)))
    return ((l, t), (r, t), (r, b), (l, b))

def _zone(board, name, net, priority, clearance, corners, hole=None):
    """Create or update an In1.Cu plane in place. Existing zones are reused rather than
    removed and re-added: Remove + a new ZONE corrupted the heap intermittently."""
    import pcbnew
    z = next((z for z in board.Zones() if z.GetZoneName() == name), None)
    if z is None:
        z = pcbnew.ZONE(board)
        z.SetZoneName(name)
        board.Add(z)
    z.SetLayer(pcbnew.In1_Cu)
    z.SetNet(board.FindNet(net))
    z.SetAssignedPriority(priority)
    z.SetMinThickness(pcbnew.FromMM(0.25))
    z.SetLocalClearance(pcbnew.FromMM(clearance))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    ol = z.Outline()
    ol.RemoveAllContours(); ol.NewOutline()
    for x, y in corners:
        ol.Append(int(x), int(y))
    if hole:                                  # so the DSN's GND plane does not claim the AGND island
        ol.NewHole()
        for x, y in hole:
            ol.Append(int(x), int(y), 0, 0)

def gnd_plane(board):
    import pcbnew
    bb = board.GetBoardEdgesBoundingBox()
    l, t, r, b = bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()
    # AGND island under the ADC column (gen_carrier_pcb PACK), cut out of GND by priority and
    # by a hole in GND's outline. It meets GND only through NT801, the star at its top edge.
    isl = agnd_island(board)
    _zone(board, 'GND_PLANE', 'GND', 0, 0.3, ((l, t), (r, t), (r, b), (l, b)), hole=isl)
    _zone(board, 'AGND_PLANE', 'AGND', 1, 0.5, isl)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())

def export():
    import pcbnew
    os.makedirs(ROUTE, exist_ok=True)
    board = pcbnew.LoadBoard(os.path.join(HERE, f'{PROJ}.kicad_pcb'))
    # In1.Cu is a plane: typed 'power', the DSN says so and Freerouting reaches it by vias only.
    # Typed 'signal' it routed 9.7 m of tracks across it and shredded the GND plane.
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    gnd_plane(board)
    board.Save(os.path.join(HERE, f'{PROJ}.kicad_pcb'))
    ok = pcbnew.ExportSpecctraDSN(board, os.path.join(ROUTE, 'carrier.dsn'))
    print('exported route/carrier.dsn' if ok else 'DSN export FAILED')

def import_ses():
    import pcbnew
    board = pcbnew.LoadBoard(os.path.join(HERE, f'{PROJ}.kicad_pcb'))
    ok = pcbnew.ImportSpecctraSES(board, os.path.join(ROUTE, 'carrier.ses'))
    if not ok:
        sys.exit('SES import FAILED')
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(os.path.join(HERE, f'{PROJ}.kicad_pcb'))
    print('imported route/carrier.ses: %d tracks, %d vias' % (
        sum(1 for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK'),
        sum(1 for t in board.GetTracks() if t.GetClass() == 'PCB_VIA')))

VIA_D, VIA_DRILL, STUB_W = 0.6, 0.3, 0.4      # the Supply class via, and its track width
PLANE = {'GND': 'GND_PLANE', 'AGND': 'AGND_PLANE'}

def repair(report):
    import pcbnew, math
    MM = pcbnew.FromMM
    drc = json.load(open(report))
    board = pcbnew.LoadBoard(os.path.join(HERE, f'{PROJ}.kicad_pcb'))
    items = {}
    for t in board.GetTracks():
        items[t.m_Uuid.AsString()] = t
    pads = [p for fp in board.GetFootprints() for p in fp.Pads()]
    for p in pads:
        items[p.m_Uuid.AsString()] = p

    # 1. tracks that short or violate clearance, and dangling pieces: delete (vias and pads stay,
    #    except a dangling via)
    gone = set()
    for v in drc['violations']:
        if v['type'] in ('shorting_items', 'clearance', 'track_dangling', 'via_dangling'):
            for it in v['items']:
                o = items.get(it['uuid'])
                if o is None or it['uuid'] in gone:
                    continue
                if o.GetClass() == 'PCB_TRACK' or (v['type'] == 'via_dangling' and o.GetClass() == 'PCB_VIA'):
                    print('delete %-14s %-28s %s' % (v['type'], o.GetNetname(), it['description']))
                    board.Remove(o); gone.add(it['uuid'])

    # 2. obstacles, bucketed on a 2 mm grid
    CELL = MM(2)
    grid = {}
    def add(o, bb):
        for gx in range(bb.GetLeft() // CELL, bb.GetRight() // CELL + 1):
            for gy in range(bb.GetTop() // CELL, bb.GetBottom() // CELL + 1):
                grid.setdefault((gx, gy), []).append(o)
    for t in board.GetTracks():
        add(t, t.GetBoundingBox())
    for p in pads:
        add(p, p.GetBoundingBox())
    def near(pt, r):
        out = {}                                       # SWIG proxies are unhashable: key on id()
        for gx in range((pt.x - r) // CELL, (pt.x + r) // CELL + 1):
            for gy in range((pt.y - r) // CELL, (pt.y + r) // CELL + 1):
                for o in grid.get((gx, gy), ()):
                    out[id(o)] = o
        return out.values()
    zones = {z.GetZoneName(): z for z in board.Zones()}
    ib = zones['AGND_PLANE'].Outline().BBox()
    edge = board.GetBoardEdgesBoundingBox()
    COPPER = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu]
    r = MM(VIA_D / 2)

    def hole(o):
        if o.GetClass() == 'PCB_VIA':
            return o.GetDrillValue() / 2
        if o.GetClass() == 'PAD' and o.HasHole():
            return max(o.GetDrillSizeX(), o.GetDrillSizeY()) / 2
        return None

    def via_ok(pt, net):
        m = r + MM(0.6)                       # 0.5 mm board-edge rule, plus the outline line width
        if not (edge.GetLeft() + m < pt.x < edge.GetRight() - m and edge.GetTop() + m < pt.y < edge.GetBottom() - m):
            return False
        # In1.Cu: inside its own plane, clear of the island edge
        # (the island is a rectangle; SHAPE_POLY_SET.SquaredDistance is 0 everywhere inside it)
        dx = max(ib.GetLeft() - pt.x, 0, pt.x - ib.GetRight()); dy = max(ib.GetTop() - pt.y, 0, pt.y - ib.GetBottom())
        if net == 'AGND':
            if min(pt.x - ib.GetLeft(), ib.GetRight() - pt.x, pt.y - ib.GetTop(), ib.GetBottom() - pt.y) < r + MM(0.8):
                return False
        elif math.hypot(dx, dy) < r + MM(1.0):
            return False
        c = pcbnew.SHAPE_CIRCLE(pt, r)
        for o in near(pt, MM(3)):
            h = hole(o)
            if h is not None and (pt - o.GetPosition()).EuclideanNorm() < MM(VIA_DRILL / 2) + h + MM(0.3):
                return False
            if o.GetClass() == 'PAD' and o.GetEffectiveShape(pcbnew.F_Cu if o.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu).Collide(c, MM(0.25)):
                return False                       # no via in or against any pad, own net included
            if o.GetNetname() == net:
                continue
            for ly in COPPER:
                if o.IsOnLayer(ly):
                    cl = max(MM(0.2), o.GetOwnClearance(ly)) + MM(0.02)
                    if o.GetEffectiveShape(ly).Collide(c, cl):
                        return False
        return True

    def stub_ok(a, b, layer, net, owner, w):
        seg = pcbnew.SHAPE_SEGMENT(a, b, w)
        for o in near(a, (b - a).EuclideanNorm() + MM(2)):
            if o is owner or o.GetNetname() == net or not o.IsOnLayer(layer):
                continue
            cl = max(MM(0.2), o.GetOwnClearance(layer)) + MM(0.02)
            if o.GetEffectiveShape(layer).Collide(seg, cl):
                return False
        return True

    def place_via(pt, net):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pt); v.SetWidth(MM(VIA_D)); v.SetDrill(MM(VIA_DRILL))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(board.FindNet(net))
        board.Add(v); add(v, v.GetBoundingBox())

    def ring(c, start):
        for dist in [start + MM(0.2) * k for k in range(10)]:
            for ang in range(0, 360, 30):
                yield pcbnew.VECTOR2I(int(c.x + dist * math.cos(math.radians(ang))),
                                      int(c.y + dist * math.sin(math.radians(ang))))

    def add_stub(a, b, layer, net, w):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(a); t.SetEnd(b); t.SetWidth(w); t.SetLayer(layer)
        t.SetNet(board.FindNet(net)); board.Add(t); add(t, t.GetBoundingBox())

    def from_point(c, layer, net, owner, start, widths):
        for pt in ring(c, start):
            if not via_ok(pt, net):
                continue
            for w in widths:
                if stub_ok(c, pt, layer, net, owner, w):
                    place_via(pt, net); add_stub(c, pt, layer, net, w)
                    return True
        return False

    def stitch_track(t, net):
        a, b = t.GetStart(), t.GetEnd()
        n = max(1, int((b - a).EuclideanNorm() / MM(0.25)))
        pts = [pcbnew.VECTOR2I(int(a.x + (b.x - a.x) * k / n), int(a.y + (b.y - a.y) * k / n)) for k in range(n + 1)]
        for pt in pts:                                 # a via straight on the track
            if via_ok(pt, net):
                place_via(pt, net); return True
        w = min(t.GetWidth(), MM(STUB_W))
        for pt in pts:                                 # else one beside it, on a stub
            if from_point(pt, t.GetLayer(), net, t, t.GetWidth() / 2 + r + MM(0.25), [w, MM(0.25)]):
                return True
        return False

    def stitch_pad(p, net):
        layer = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
        bb = p.GetBoundingBox()
        narrow = min(bb.GetWidth(), bb.GetHeight())
        return from_point(p.GetPosition(), layer, net, p, max(bb.GetWidth(), bb.GetHeight()) / 2 + MM(0.25) + r,
                          [min(MM(STUB_W), narrow), MM(0.25)])

    done, failed = set(), []
    for u in drc['unconnected_items']:
        for it in u['items']:
            o = items.get(it['uuid'])
            if o is None or it['uuid'] in done or it['uuid'] in gone:
                continue
            net = o.GetNetname()
            if net not in PLANE:
                continue
            done.add(it['uuid'])
            if o.GetClass() == 'PCB_TRACK':
                ok = stitch_track(o, net)
            elif o.GetClass() == 'PAD' and not o.HasHole():
                ok = stitch_pad(o, net)
            else:
                continue                           # vias, PTH pads: already on In1
            if not ok:
                failed.append('%s %s' % (net, it['description']))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(os.path.join(HERE, f'{PROJ}.kicad_pcb'))
    print('deleted %d, stitched %d, no room for %d' % (len(gone), len(done) - len(failed), len(failed)))
    for f in failed:
        print('  no room:', f)

if __name__ == '__main__':
    if sys.argv[1] == 'repair':
        repair(sys.argv[2])
    else:
        {'classes': classes, 'export': export, 'import': import_ses}[sys.argv[1]]()
