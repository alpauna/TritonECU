# Bench power-supply enclosure

A printed box for the bench supply that feeds the ECU and the VR test rig:
screw-down lid, 40 mm fan at one end, exhaust grid at the other, and a fused
IEC C14 inlet/switch module on a long side.

**This box contains mains wiring.** Read [Safety](#safety) before energising it.

```
                 TOP VIEW  (285 long)

     END A                                      END B
   +--------------------------------------------------+
   |[FAN]                                        ######|
   |          power supply  266 x 153 x 77       ######|   <- exhaust grid
   |                                             ######|
   +-------------------[PLUG]--[GLAND]-----------------+
    intake  ------>  air over and under  ------>  out
                          the supply
```

## Dimensions

| | |
|---|---|
| External | **285 × 201 × 106** mm |
| Bed footprint, tub | **290 × 205** — the fan and plug pads stand proud of the walls |
| Bed footprint, lid | 285 × 201 |
| Clear space for the supply | **279 × 156 × 79** (the 266 × 153 × 77 minimum, with room) |
| Wiring bay | 39 mm wide alongside the supply |

`openscad` echoes all of these on every render, so they follow the parameters
rather than this table. Re-read them after changing anything.

**The tub needs a genuine 300 × 300 bed**, with 5 mm to spare on each side in X.
Print it with a *skirt*, not a brim — a brim will not fit. If your printer
cannot reach 290, drop `clr_fan` from 10 to 6 and re-render; you lose plenum
depth at the fan and nothing else.

## Measure these before printing

The `.scad` is parametric but it cannot guess:

```
psu_l, psu_w, psu_h    the supply's real outside dimensions
standoff_xy            the supply's mounting-foot pattern
```

The supply's dimensions default to the 266 × 153 × 77 minimum. **The foot
pattern has no default worth trusting** — there is no standard for it. The six
standoffs as shipped are *pads*: they hold the supply 4 mm off the floor so air
can get under it, and that is all they do. Measure the feet, edit
`standoff_xy`, then set `standoff_hole = true` to get M4 clearance holes with
head recesses on the underside of the floor.

## Bought parts

| Qty | Item | Notes |
|--:|---|---|
| 1 | **40 × 40 × 10 mm fan**, 12 V | 32 mm bolt centres, Ø3.5 holes — the WINSINN drawing |
| 1 | **IEC C14 inlet + rocker + fuse module** | BIQU 10 A 250 V; 58 × 48 face, 50 × 29 × 19 rear flange, M3 ears at 40 mm |
| 1 | 5 × 20 mm fuse | size it to the supply, not to the socket's 10 A rating |
| 10 | **M3 × 12 socket head** | lid |
| 4 | **M3 × 10 self-tapping** | fan, through its own Ø3.5 holes into the pad |
| 2 | **M3 × 12 self-tapping** | plug ears, into the 7 mm pad |
| 4 | M4 × 10 | supply feet, *once you have measured them* |
| 1 | **PG7 cable gland** or Ø12.5 rubber grommet | DC output |
| — | 16–14 AWG wire + insulated spade terminals | the module ships with a set |
| 4 | Stick-on rubber feet | the floor is flat by design |

## Printed parts

| Qty | Part | Orientation |
|--:|---|---|
| 1 | `tub` | **floor down**, open side up |
| 1 | `lid` | **outer face down** — see below |

**Print the lid upside down, outer face on the bed.** Modelled ribs-down as it
sits on the box, so flipping it makes every rib and the locating ring grow
*upward*. Nothing then overhangs except a 1.5 mm annular bridge over each screw
counterbore, which any printer manages. Printed the other way up, four ribs and
a 250 mm ring are all overhang.

**PETG or ABS, not PLA.** This one is not about stiffness — it is that the box
holds a warm supply and a mains connection, and PLA softens at temperatures a
loaded supply reaches in a closed box.

Walls and floor are 3 mm; 3 perimeters and 25 % infill is plenty. The lid wants
**4 perimeters** so the screw counterbores have solid material around them.

## How it is put together

### The lid seat is a rim band, not corner posts

With 3 mm of clearance beside the supply there is nowhere to put a corner post —
it would land inside the supply. So the screws go into a band that thickens the
wall inward around the whole top rim, sitting **entirely above the supply**
where the volume is free anyway. It costs 17 mm of height and no floor area.

The band's underside is a 45° taper (`rim_taper = rim_w`, keep them equal), so
it prints with no support and leaves no drooping ledge over the supply. Its
inner face is the rabbet the lid's locating ring drops into, which is what stops
the lid sliding and closes the dust gap.

Ten M3s: four along each long wall, one at each end.

### The fan mounts outside

Inside would cost 10 mm of a 10 mm plenum, and the supply is only 10 mm away.
The pad on the outside also gives the M3s **8 mm of plastic** to cut into
instead of 3.

**Mount it as an intake** — airflow arrow and label pointing *into* the box. Air
enters at END A, splits between the 4 mm gap under the supply and the space over
it, and leaves through the grid at END B. Blowing the length of the supply is
the whole reason the fan and grid are on opposite ends rather than opposite
sides. Run the fan off the supply's own DC output if the voltage matches, or off
a small buck module in the bay.

### The grid is diamonds, not squares

A square hole in a vertical wall has a flat top edge that has to bridge. A
diamond has an apex, so every one of the 78 holes is self-supporting and nothing
droops into the airstream.

### The bay is why the plug fits at all

The inlet module's rear flange stands **19 mm** proud of the panel, and the
spade terminals and their boots add more again. That cannot happen on the wall
the supply is pressed against, so a 39 mm channel runs down one long side. The
pad takes 7 mm of the flange, so it intrudes 12 mm, **leaving 27 mm** between
the flange's back face and the supply for terminals and wire bends. The DC
output gland shares the same channel.

The module is mounted with its **58 mm axis vertical**, so the rocker is at the
top and the fuse drawer pulls out below it. Note that the two M3 ears straddle
the cutout on the *short* axis — which is why the 40 mm hole pitch is larger
than the 29 mm cutout it flanks.

`plug_x` and `gland_x` are parameters. Slide them along the wall to land beside
the supply's own AC input and DC output terminals.

## Safety

The box is plastic, so there is nothing to bond to earth — but the C14's earth
pin still has to go somewhere. **Run it to the supply's earth terminal.** Do not
leave it unconnected because the enclosure is non-conductive; the supply's
chassis and its output reference need it.

- The lid screws are the only thing between a finger and 120 V. Fit all ten.
- Fuse for the *supply*, not for the socket. The module is rated 10 A; that is a
  ceiling, not a recommendation.
- Use the insulated spade terminals the module ships with, fully seated.
- Fit the cable gland or grommet before pulling the DC output wires through. A
  bare printed hole will cut insulation over time, and the layer lines make it
  worse than a drilled one.
- Strain-relieve the mains wiring inside the bay so a tug on the cord cannot
  reach the terminals.

## Rendering

```bash
./render.sh          # both parts to stl/
```

Or one at a time:

```bash
openscad -D 'part="tub"' psu_enclosure.scad
openscad -D 'part="lid"' psu_enclosure.scad
```

`part = "assembly"` (the default when you open the file) shows the tub, the lid
in place, and **ghosts** of the supply, the fan and the plug module. The plug
ghost is the one to look at: it is the check that the bay is deep enough.

STL export is not byte-deterministic — rendering the same unchanged file twice
produces different files. **`psu_enclosure.scad` is the source of truth**; the
STLs are a convenience so the parts can be printed without installing OpenSCAD.
Re-run `render.sh` after any change and do not read anything into the diff.

## Parameters worth knowing

| Parameter | Default | What it moves |
|---|--:|---|
| `psu_l/w/h` | 266/153/77 | everything — **measure yours** |
| `standoff_xy`, `standoff_hole` | pads, off | the supply's foot pattern |
| `clr_fan` | 10 | plenum depth at the fan end, and total length |
| `bay_w` | 39 | wiring channel; the plug needs most of it |
| `rim_w`, `rim_taper` | 6, 6 | lid seat. **Keep them equal** — that is the 45° |
| `boss_d` | 9 | lid screw engagement. Heat-set inserts? 7 is enough |
| `lid_screw` | 2.6 | M3 self-tapping pilot. Heat-set M3 insert: **4.2** |
| `fan_guard` | true | concentric webs over the fan bore |
| `plug_x`, `gland_x` | mid, −45 | where the inlet and output land along the wall |
| `grid_pitch`, `grid_sq` | 10, 6 | exhaust open area |
