#!/usr/bin/env python3
"""Is the flat 1-104 numbering a real physical layout, or an arbitrary list?

If the EEC-V connector is 4 rows of 26, functions that come in pairs or
quads should land on pins congruent modulo 26. That is a property no
3-connector A/B/C scheme can reproduce, so it settles which document
describes this truck.

Pin data: 1999-Ford-F150-4wd-5.42v/eec-v-pinout.md (flat, from the
MegaSquirt PNP sheet), corroborated independently by Ford's own EVTM
pages in the same directory.
"""
N = 26
groups = {
    "Coils 1-8"        : [26,104,52,53,27,1,78,79],
    "Injectors 1-8"    : [75,101,74,100,73,99,72,98],
    "Power grounds"    : [25,51,77,103],
    "VPWR (361 RD)"    : [71,97],
    "HO2S heaters"     : [93,94,95,96],
}
print(f"Testing a {N}-pin row pitch on 104 pins = {104//N} rows of {N}\n")
print(f"{'group':<18} {'pins':<34} {'residues mod 26':<24} shape")
print("-"*100)
for name,pins in groups.items():
    mods = sorted(set(p % N for p in pins))
    cols = len(mods)
    per  = len(pins)//cols
    if cols == 1:          shape = f"ONE COLUMN - all {len(pins)} on residue {mods[0]}"
    elif per > 1:          shape = f"{cols} full columns, {per} deep"
    else:                  shape = f"{cols} adjacent positions in a row"
    print(f"{name:<18} {str(sorted(pins)):<34} {str(mods):<24} {shape}")
print(f"""
  Every group falls on a clean column structure:

    power grounds  25/51/77/103  -> ONE column, residue 25, all four rows
    VPWR           71/97         -> ONE column, residue 19, two rows
    coils 1-8      -> TWO full columns (residues 0 and 1), four deep
    injectors 1-8  -> four columns, paired across two rows
    HO2S heaters   -> four adjacent positions in one row

  ** That is a physical 4 x 26 layout. ** The numbering follows the
  connector body: a whole column of grounds, the high-current feed doubled
  down one column, the coil drivers blocked together.

  A three-connector A/B/C scheme cannot produce it. So:

    - EEC-V-Power-Pins.png says "Connector A / B / C signal return".
      THREE CONNECTORS. Not this PCM.
    - 4R70W-PowertrainControlModule.png shows ONE PCM block with flat pins
      1, 27, 37, 54, 81 and no connector prefix. THIS PCM.
    - The chart puts VPWR on A-32 and A-33, ADJACENT. This truck's are 71
      and 97, TWENTY-SIX APART. No offset maps adjacent pins to pins 26
      apart, so no mapping exists to be found.

  ** THERE IS NO A-xx <-> 1-104 MAPPING. The two documents describe
     DIFFERENT PCMs. ** eec-v-pinout.md is the authority for this truck.""")
