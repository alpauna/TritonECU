#!/usr/bin/env python3
"""Bring the carrier schematic onto TritonECU-Main.kicad_pcb, in KiCad's Python:

  * every schematic part missing from the board is added, linked to its symbol
    (path = sheet / symbol UUID), with its fields, at its PLACE position
  * every pad's net is set from the netlist, existing footprints included, so the
    connector and daughterboard pads follow carrier_pinmap.py and eecv_pins.py
  * parts already on the board are never moved: placement is yours once made.
    --replace-sheet NAME puts one sheet's parts back at their PLACE positions

  flatpak run --command=python3 --filesystem=$PWD --filesystem=$HOME/Documents/KiCad/Libraries \\
      org.kicad.KiCad gen_carrier_pcb.py

PLACE is a FIRST DRAFT floor plan, by connector position: coil IGBTs in the two
12 mm edge-cooling bands beside the coil columns at each end of the EEC-V, the
injectors in a row under the injector pins. The board outline and connector
position are still estimates (measurements-wanted.md).
"""
import os, re, subprocess, sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = 'TritonECU-Main'
STOCK = '/app/extensions/Library/Footprints/footprints'
USER = os.path.expanduser('~/Documents/KiCad/Libraries')
MM = pcbnew.FromMM

# page coordinates (board top-left is (25, 25)), rotation in degrees, side
def place():
    P = {}
    left = ['1', '3', '7', '2']        # coils on EEC-V pins 26, 52, 78, 104: the left end column
    right = ['6', '5', '4', '8']       # pins 1, 27, 53, 79: the right end column
    for k, c in enumerate(left):       # D2PAK in the 12 mm edge-cooling band, 20 mm pitch
        P[f'Q10{c}'] = (32.0, 38.0 + 20 * k, 0)
        P[f'R10{c}'] = (40.5, 46.0 + 20 * k, 90)
    for k, c in enumerate(right):
        P[f'Q10{c}'] = (176.0, 38.0 + 20 * k, 0)
        P[f'R10{c}'] = (167.5, 46.0 + 20 * k, 90)
    # coil buffer: between the two coil columns, below the module
    P['U101'] = (104.0, 116.0, 0); P['C101'] = (104.0, 125.0, 0)
    P['R109'] = (99.5, 126.0, 90); P['R110'] = (108.5, 126.0, 90)
    # watchdog, below the module (NRST is on header A)
    P['U102'] = (56.0, 117.0, 0); P['C102'] = (56.0, 123.0, 0); P['R111'] = (62.0, 117.0, 90)
    P['Q109'] = (69.0, 117.0, 0); P['JP101'] = (69.0, 123.0, 0)
    # injectors under EEC-V pins 98/72 (8/7) ... 75/101 (1/2): left to right 8 7 6 5 4 3 2 1
    order = ['8', '7', '6', '5', '4', '3', '2', '1']
    for k, n in enumerate(order):
        P[f'Q20{n}'] = (44.0 + 7.4 * k, 52.5, 90)     # drain tab towards the connector
        P[f'R20{n}'] = (44.0 + 7.4 * k, 59.0, 0)
    # VR: 3 x MAX9926 where the VR daughterboard was, right of centre under the
    # connector, near CMP 85, OSS 84, TSS 59, TC 7. Refs follow gen_carrier.vr()'s order.
    r, c = 301, 301
    for chip in range(3):
        xc = 117.0 + 17.0 * chip
        P[f'U30{chip + 1}'] = (xc, 62.0, 0)
        for k in range(3):                                   # 10n closest, then 100n, 1u
            P[f'C{c}'] = (xc - 4.0 + 4.0 * k, 56.0, 0); c += 1
        for ch in range(2):
            y = 70.0 + 7.0 * ch
            for k in range(4):                               # P leg a, b, N leg a, b
                P[f'R{r}'] = (xc - 6.0 + 4.0 * k, y, 90); r += 1
            P[f'C{c}'] = (xc - 3.0 + 6.0 * ch, 85.0, 90); c += 1      # 470 pF across the inputs
            P[f'R{r}'] = (xc - 6.0 + 8.0 * ch, 90.0, 90); r += 1      # COUT pull-up
            P[f'C{c}'] = (xc - 2.0 + 8.0 * ch, 90.0, 90); c += 1      # BIAS
    P['J301'] = (160.0, 98.0, 0); P['R399'] = (100.0, 62.0, 90)
    # solenoids and heaters (74HCT541 #3): heaters, vent, IMCC in the left cooling
    # band below the coils; SSA/SSB (pins 6, 11, right of centre) in the right band.
    # Gate / pulldown / divider-top resistors sit in the 12 mm gaps between FETs.
    for k, n in enumerate(range(1, 7)):
        y = 116.0 + 12.0 * k
        P[f'Q40{n}'] = (31.0, y, 0)
        P[f'R41{n}'] = (27.5, y + 6.0, 0); P[f'R42{n}'] = (31.0, y + 6.0, 0)
        if n <= 5:                                      # drain sense: heaters x4, vent
            P[f'R43{n}'] = (34.5, y + 6.0, 0); P[f'R44{n}'] = (40.0, y + 3.0, 90)
    for k, n in enumerate((7, 8)):
        y = 116.0 + 12.0 * k
        P[f'Q40{n}'] = (177.0, y, 0)
        P[f'R41{n}'] = (174.0, y + 6.0, 0); P[f'R42{n}'] = (179.0, y + 6.0, 0)
    P['U401'] = (48.0, 134.0, 0); P['C401'] = (56.0, 128.0, 90)
    # mux below the module, its eight input caps in a row
    P['U402'] = (82.0, 116.0, 0); P['C402'] = (88.0, 116.0, 90)
    for k in range(8):
        P[f'C{411 + k}'] = (72.0 + 3.2 * k, 122.0, 90)
    # PWM loads (74HCT541 #2): two rows in the open area lower left, freewheel
    # Schottky beside each PWM FET
    rows = [(1, 47.0, 152.0), (2, 62.0, 152.0), (3, 77.0, 152.0), (4, 95.0, 152.0),
            (5, 47.0, 176.0), (6, 62.0, 176.0), (7, 77.0, 176.0)]
    for n, x, y in rows:
        P[f'Q50{n}'] = (x, y, 0)
        P[f'R51{n}'] = (x - 2.0, y + 7.0, 0); P[f'R52{n}'] = (x + 2.0, y + 7.0, 0)
        if n <= 5:
            P[f'D50{n}'] = (x + 8.0, y, 90)
    P['R531'] = (45.0, 144.0, 90); P['R541'] = (49.0, 144.0, 90)      # EVAP drain sense
    P['R565'] = (70.0, 168.0, 90)                                      # VSS pull-up, DNP
    P['U501'] = (92.0, 176.0, 0); P['C501'] = (92.0, 185.0, 0); P['R509'] = (86.0, 185.0, 90)
    for k, ref in enumerate(('R561', 'R562', 'R563', 'R564')):        # supply sense 1138, 391
        P[ref] = (101.0 + 4.0 * (k // 2), 164.0 + 4.0 * (k % 2), 0)
    # relays (TBD62083AFNG): below the VR group, right of the coil buffer; slow
    # outputs, so distance to EEC-V 80/19/18/69 costs nothing. PTCs in a row below.
    P['U601'] = (125.0, 100.0, 0); P['C601'] = (133.0, 100.0, 90)
    for k in range(4):
        P[f'R60{k + 1}'] = (117.0, 96.0 + 3.0 * k, 0)
        P[f'F60{k + 1}'] = (118.0 + 5.0 * k, 109.0, 90)
    # VREF: in the open block right of the relays, clear of the power board's top edge
    # and its MH2 standoff (154, 125). Feed rows on top (channel 2 not fitted), the
    # short-to-battery divider below them, LDO and switch along the bottom.
    for ch in (1, 2):
        y = 97.0 + 7.0 * (ch - 1)
        P[f'U70{2 + ch}'] = (141.0, y, 0); P[f'Q70{ch}'] = (146.5, y, 0); P[f'D70{ch}'] = (153.0, y, 0)
        P[f'C{705 + ch}'] = (140.0, y + 3.5, 0); P[f'C{707 + ch}'] = (143.5, y + 3.5, 0)
    P['R708'] = (139.5, 110.0, 0); P['R709'] = (142.8, 110.0, 0); P['C710'] = (146.1, 110.0, 0)
    P['D704'] = (149.6, 110.0, 0); P['TP701'] = (156.0, 110.0, 0)
    P['U701'] = (147.0, 115.0, 0)                      # origin at the leads, tab to the right
    P['C701'] = (136.3, 113.5, 90); P['C702'] = (138.5, 115.5, 90); P['R701'] = (135.0, 117.0, 0)
    P['C703'] = (153.5, 114.5, 90); P['C704'] = (156.0, 114.5, 90)
    P['U702'] = (162.0, 114.0, 0); P['C705'] = (162.0, 118.5, 0); P['D703'] = (170.5, 112.0, 90)
    for k, ref in enumerate(('R702', 'R703', 'R704', 'R705', 'R706', 'R707')):
        P[ref] = (167.6, 109.8 + 1.8 * k, 0)
    # USB-C on the right board edge (x 183): rotated 90 so the opening faces +x, the
    # footprint's 'PCB Edge' line (local y 3.675) on the edge
    P['J901'] = (183.0 - 3.675, 141.5, 90)
    # rails: bulk caps beside the power board connector; VBAT 0R by module pad A9
    P['C001'] = (104.0, 132.0, 0); P['C002'] = (104.0, 137.0, 0); P['R001'] = (44.0, 108.0, 0)
    return P

# Groups packed into a free rectangle by their real courtyards (shelf packing, in
# the order given) instead of hand coordinates. (refs, (x0, y0, x1, y1))
def _refs(prefix, a, b): return [f'{prefix}{n}' for n in range(a, b + 1)]
PACK = [
    # ADC core, reference, unbuffered inputs, slow MCU-ADC channels: the 15 mm column
    # between the MCU module and the VR group, under the analog pins
    (['U801'] + _refs('C', 801, 809) + _refs('R', 801, 807) + ['U802', 'R808'] + _refs('C', 810, 814) + ['R809']
     + _refs('R', 810, 817) + ['D801'] + _refs('R', 847, 852) + _refs('C', 836, 838) + ['D810', 'D811'],
     (94.4, 64.0, 109.6, 108.5)),          # below R201 / R399
    # knock: right of the VR group, below the coil 5/6 IGBTs' inner edge, near pins 57/32
    (['U805', 'U806', 'C826'] + _refs('R', 837, 846) + ['D808', 'D809'] + _refs('C', 827, 835),
     (158.6, 56.0, 169.2, 92.0)),
    # HO2S x4 buffers: the bottom band. Far from pins 35/60/61/87 - first draft only
    (['U803', 'U804', 'C815', 'C820'] + _refs('R', 818, 836) + _refs('C', 816, 825) + _refs('D', 802, 807),
     (26.5, 187.0, 110.2, 198.0)),         # below R509, left of the power board
    # comms: USB-C and microSD need a board edge; the only free one is the strip right
    # of the power board. SCP/CAN then run ~100 mm to EEC-V 15/16/42/43 - first draft
    (['U903', 'U901', 'U902', 'U904', 'U905'] + _refs('R', 901, 930) + _refs('C', 901, 920)
     + _refs('D', 901, 906) + ['J902'], (170.8, 147.2, 182.6, 198.4)),
]

PARK = (190.0, 30.0, 240.0, 230.0)       # off the right edge: what did not fit, for you to place

def pack(have, refs, rect, gap=0.3, park=True):
    """Shelf-pack refs into rect by courtyard; parts that do not fit go to PARK."""
    x0, y0, x1, y1 = rect
    x, y, row, left = x0, y0, 0.0, []
    for ref in refs:
        fp = have.get(ref)
        if fp is None:
            continue
        fp.SetOrientationDegrees(0)
        fp.SetPosition(pcbnew.VECTOR2I(0, 0))
        c = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
        l, t, w, h = (pcbnew.ToMM(v) for v in (c.GetLeft(), c.GetTop(), c.GetWidth(), c.GetHeight()))
        nx, ny, nrow = x, y, row
        if nx + w > x1:
            nx, ny, nrow = x0, y + row + gap, 0.0
        if w > x1 - x0 or ny + h > y1:
            left.append(ref); continue
        fp.SetPosition(pcbnew.VECTOR2I(MM(nx - l), MM(ny - t)))
        x, y, row = nx + w + gap, ny, max(nrow, h)
    if left and park:
        print(f'  pack: {len(left)} did not fit, parked off-board: {left}')
        pack(have, left, PARK, gap, park=False)

# ---------------------------------------------------------------- netlist
def netlist():
    tmp = os.path.join(HERE, '.gen-netlist.net')
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', tmp,
                    f'{PROJ}.kicad_sch'], check=True, capture_output=True)
    nl = open(tmp).read(); os.remove(tmp)
    comps = {}
    for blk in nl[:nl.index('\n\t(libparts')].split('\n\t\t(comp\n')[1:]:
        ref = re.search(r'\(ref "([^"]+)"\)', blk).group(1)
        sheet = re.search(r'\(sheetpath\s*\(names "([^"]*)"\)\s*\(tstamps "([^"]*)"\)', blk)
        comps[ref] = dict(value=re.search(r'\(value "([^"]*)"\)', blk).group(1),
                          fp=re.search(r'\(footprint "([^"]*)"\)', blk).group(1),
                          uuid=re.search(r'\(tstamps "([0-9a-f-]{36})"\)', blk).group(1),
                          sheetname=sheet.group(1), sheetpath=sheet.group(2),
                          sheetfile=re.search(r'\(name "Sheetfile"\)\s*\(value "([^"]*)"\)', blk).group(1)
                          if 'Sheetfile' in blk else '',
                          fields=dict(re.findall(r'\(field\s*\(name "([^"]+)"\)\s*"([^"]*)"\)', blk)),
                          nobom='(name "exclude_from_bom")' in blk, dnp='(name "dnp")' in blk)
    pins = {}
    for blk in nl.split('\n\t\t(net\n')[1:]:
        name = re.search(r'\(name "([^"]+)"\)', blk).group(1)
        for r, p in re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', blk):
            pins[(r, p)] = name          # no-connect pins too: KiCad gives them an unconnected-(..) net
    return comps, pins

def load(fpid):
    lib, name = fpid.split(':')
    if lib == 'Samacsys':
        path = f'{USER}/Samacsys.pretty'
    elif lib == PROJ:
        path = os.path.join(HERE, f'{PROJ}.pretty')
    else:
        path = f'{STOCK}/{lib}.pretty'
    try:
        fp = pcbnew.FootprintLoad(path, name)
    except AttributeError:
        sys.exit(f'cannot load {fpid} from {path}')
    assert fp, fpid
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp

def main():
    os.chdir(HERE)
    if any(f.startswith('~') and f.endswith(('.kicad_sch.lck', '.kicad_pcb.lck')) for f in os.listdir('.')):   # the project window alone holds nothing
        sys.exit('project is open in KiCad - close it first')
    comps, pins = netlist()
    board = pcbnew.LoadBoard(f'{PROJ}.kicad_pcb')
    have = {fp.GetReference(): fp for fp in board.GetFootprints()}
    nets = {}
    def net(name):
        if name not in nets:
            n = board.FindNet(name)
            if not n:
                n = pcbnew.NETINFO_ITEM(board, name); board.Add(n)
            nets[name] = n
        return nets[name]
    P = place()
    stale = [ref for ref in have if ref not in comps]      # no longer in the schematic
    added = []
    for ref, c in sorted(comps.items()):
        if ref in have or not c['fp']:
            continue
        fp = load(c['fp'])
        fp.SetReference(ref); fp.SetValue(c['value'])
        fp.SetPath(pcbnew.KIID_PATH(f"{c['sheetpath']}{c['uuid']}"))
        fp.SetSheetname(c['sheetname']); fp.SetSheetfile(c['sheetfile'])
        for k, v in c['fields'].items():
            if k not in ('Footprint', 'Datasheet', 'Description'):
                fp.SetField(k, v); fp.GetField(k).SetVisible(False)
        board.Add(fp)
        x, y, rot = P.get(ref, (190.0, 30.0 + 4 * len(added), 0))   # unplanned parts park off the right edge
        fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        fp.SetOrientationDegrees(rot)
        have[ref] = fp; added.append(ref)
    replaced = set(added)
    if '--replace-sheet' in sys.argv:              # re-place one sheet's parts at PLACE
        sheet = sys.argv[sys.argv.index('--replace-sheet') + 1]
        for ref, c in comps.items():
            if c['sheetname'].strip('/') == sheet and ref in P and ref in have:
                x, y, rot = P[ref]
                have[ref].SetPosition(pcbnew.VECTOR2I(MM(x), MM(y))); have[ref].SetOrientationDegrees(rot)
        replaced |= {ref for ref, c in comps.items() if c['sheetname'].strip('/') == sheet}
    for refs, rect in PACK:                    # packed groups: only parts just added or replaced
        if any(r in replaced for r in refs):
            pack(have, [r for r in refs if r in replaced], rect)
    # nets for every pad on the board
    for ref, fp in have.items():
        if ref not in comps:
            continue
        fp.SetExcludedFromBOM(comps[ref]['nobom']); fp.SetDNP(comps[ref]['dnp'])
        fp.SetValue(comps[ref]['value'])
        for p in fp.Pads():
            if not p.GetNumber():
                continue
            n = pins.get((ref, p.GetNumber()))
            if n:
                p.SetNet(net(n))
            elif p.GetNetCode():
                p.SetNetCode(0)          # the schematic no longer gives this pad a net
    removed = []
    for ref in stale:                 # removed last: a Remove before FootprintLoad breaks the IO plugin
        board.Remove(have.pop(ref)); removed.append(ref)
    board.Save(f'{PROJ}.kicad_pcb')
    packed = {r for refs, _ in PACK for r in refs}
    unplanned = [r for r in added if r not in P and r not in packed]
    print(f'added {len(added)} footprints, removed {removed}' + (f'; parked off-board, no position yet: {unplanned}' if unplanned else ''))

if __name__ == '__main__':
    main()
