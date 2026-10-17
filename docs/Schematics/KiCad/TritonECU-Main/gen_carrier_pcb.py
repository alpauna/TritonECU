#!/usr/bin/env python3
"""Bring the carrier schematic onto TritonECU-Main.kicad_pcb, in KiCad's Python:

  * every schematic part missing from the board is added, linked to its symbol
    (path = sheet / symbol UUID), with its fields, at its PLACE position
  * every pad's net is set from the netlist, existing footprints included, so the
    connector and daughterboard pads follow carrier_pinmap.py and eecv_pins.py
  * parts already on the board are never moved: placement is yours once made

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
    # rails: bulk caps beside the power board connector; VBAT 0R by module pad A9
    P['C001'] = (104.0, 132.0, 0); P['C002'] = (104.0, 137.0, 0); P['R001'] = (44.0, 108.0, 0)
    return P

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
                          fields=dict(re.findall(r'\(field\s*\(name "([^"]+)"\)\s*"([^"]*)"\)', blk)))
    pins = {}
    for blk in nl.split('\n\t\t(net\n')[1:]:
        name = re.search(r'\(name "([^"]+)"\)', blk).group(1)
        for r, p, typ in re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)(?:\s*\(pinfunction "[^"]*"\))?\s*\(pintype "([^"]+)"\)', blk):
            if typ != 'no_connect':      # a no-connect-flagged pin still gets its unconnected-(..) net
                pins[(r, p)] = name
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
    # nets for every pad on the board
    for ref, fp in have.items():
        if ref not in comps:
            continue
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
    unplanned = [r for r in added if r not in P]
    print(f'added {len(added)} footprints, removed {removed}' + (f'; parked off-board, no position yet: {unplanned}' if unplanned else ''))

if __name__ == '__main__':
    main()
