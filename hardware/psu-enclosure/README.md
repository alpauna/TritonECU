# Bench power-supply enclosure

A printed box for the bench supply that feeds the ECU and the VR test rig:
screw-down lid, 40 mm fan at one end, exhaust grid at the other, and a fused
IEC C14 inlet/switch module on the **back** wall. A small **two-rail DC-DC
module** has the front wall to itself, fed from the 36 V supply inside — its fixed 5 V runs the
VR rig's Pico, its adjustable rail is a bench output.

**This box contains mains wiring.** Read [Safety](#safety) before energising it.

```
                 TOP VIEW  (285 long)

     END A                                      END B
   +--------------------------------------------------+
   +-------------------[ PLUG ]-----------------------+  <- BACK: mains only
   |                            28 mm bay             |
   |--------------------------------------------------|
   |[FAN]                                       ######|
   |   intake -->  air over and under  -->  out ######|  <- exhaust grid
   |--------------------------------------------------|
   |(LV)                        39 mm bay             |
   +--------[ DC-DC ]------------[GLAND]--------------+  <- FRONT: low voltage
             5 V + adj            36 V out
```

**Mains on the back wall, low voltage on the front.** See [the inlet
section](#the-inlet-is-on-the-back-wall).

## Dimensions

| | |
|---|---|
| External | **285 × 226 × 106** mm |
| Bed footprint, tub | **290 × 242** — the fan pad, the plug pad and the DC-DC boss all stand proud |
| Bed footprint, lid | 285 × 226 |
| Clear space for the supply | **279 × 156 × 79** (the 266 × 153 × 77 minimum, with room) |
| Wiring bays | **back 28 mm** (mains only), **front 39 mm** (low voltage), 51 mm behind the DC-DC boss |

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
mod_cut_w/h, mod_depth the DC-DC module's body, and how far it stands behind
mod_flange, mod_lock_w its bezel lip and its snap locks
mod_boss               which is a DECISION, not a measurement — see below
```

The supply's dimensions default to the 266 × 153 × 77 minimum. **The foot
pattern has no default worth trusting** — there is no standard for it. The six
standoffs as shipped are *pads*: they hold the supply 4 mm off the floor so air
can get under it, and that is all they do. Measure the feet, edit
`standoff_xy`, then set `standoff_hole = true` to get M4 clearance holes with
head recesses on the underside of the floor.

The `mod_*` defaults are the module actually in hand — **70.6 × 38.5 × 25.4
behind a 4 mm flange, with two 12.7 mm snap locks centred on the vertical
edges.** The width was 64 until the display was offered up and would not go in
lengthwise; it needed **6.6 mm more**. Height was right first time.
Measure yours. Every clearance on that wall that was tight enough to be worth
arithmetic is an `assert` in the `.scad`, so a wrong number stops the render
rather than the print.

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
| 1 | **PG7 cable gland** or Ø12.5 rubber grommet | 36 V DC output, bay wall |
| — | 16–14 AWG wire + insulated spade terminals | the inlet module ships with a set |
| 4 | Stick-on rubber feet | the floor is flat by design |
| 1 | **DC-DC module, two rails** — fixed 5 V + LCD-set adjustable | **70.6 × 38.5** face, 25.4 deep, 4 mm flange, snap-lock mount. **40 V DC input rating** — confirmed, against a 36 V bus. See below |
| 1 | **Fuse + holder, 1–2 A**, inline | the 36 V tap to the DC-DC. *Not optional* — see below |
| 1 | **PG7 cable gland** or Ø12.5 grommet | low-voltage output, END A wall |
| 1 | **Schottky, 1 A** (1N5819 or similar) | in the 5 V feed to the Pico's `VSYS` |
| — | 20–22 AWG wire, **two colours** | the 5 V pair and the adjustable pair, kept tellable apart |

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
a small fixed buck of its own — **not** off the DC-DC's adjustable rail, for the
reason in [The fan is not a load for the adjustable
rail](#the-fan-is-not-a-load-for-the-adjustable-rail).

### One fan may not be enough under load — measure before adding

Everything measured so far was **unloaded**, which tells you nothing: the fan
never reached its threshold. The one real data point is that a comparable 36 V
supply shipped with **three fans**, which is a manufacturer sizing the same
problem.

| load | heat | airflow at a 15 °C rise |
|---|---|---|
| VR rig, ~100 W drawn | ~14 W | 1.6 CFM |
| moderate | ~25 W | 2.9 CFM |
| near this supply's capacity | ~45 W | 5.3 CFM |

A 40 × 40 × **10** is 5–7 CFM free-air and perhaps **2–3 CFM** through a box and
a grid. That covers the VR rig with thin margin and little else.

**The grid is not the limit**, which is the useful part: 78 × 6 mm diamonds is
2808 mm² against a 1134 mm² fan bore — **2.48×**. If it were restricting, extra
intake would buy almost nothing. It is not, so extra intake delivers.

**Try a thicker fan before a second one.** A 40 × 40 × **20** keeps the 32 mm
bolt pattern and the 38 mm bore, roughly doubles airflow and static pressure,
and fits the existing pad with **longer screws and no change to this model**.
A second fan means a second pad, a second bore and a reprint of the tub.

Electrically there is nothing to do in either case: the fan controller's
AO3400A is rated 5.7 A, so three fans in parallel is 300 mA.

**Get the number first.** Run the VR rig with the ESP32 controller still fitted
— it prints exhaust temperature every 2.5 s — and see where it settles. That is
what it was built for, and it also sets the real thresholds, which are still the
38/32 guess made before anything had run.

### The grid is diamonds, not squares

A square hole in a vertical wall has a flat top edge that has to bridge. A
diamond has an apex, so every one of the 78 holes is self-supporting and nothing
droops into the airstream.

### The inlet is on the back wall

It used to be on the front, sharing that wall with the DC-DC and the output
gland. Two things moved it.

**The back wall was the only surface with nothing on it** — and it was blank
precisely because it had no depth. The supply sat **3 mm** behind it, and the
inlet's rear flange intrudes 12 mm with another 12 mm of booted terminals
behind that. `clr_side` is what buys the room: **28 mm**, leaving 4 mm between
the flange and the supply.

**And it freed the front wall for a wider LCD.** The display needed 6.6 mm more
than the cutout allowed, which would have run the DC-DC's boss into the plug
pad. With the plug gone, it fits with room to spare.

So the walls now read: **mains on the back, low voltage on the front** — the
DC-DC's screen and knob, and the 36 V output. END A is the fan and the LV
gland, END B is nothing but exhaust grid.

It costs 25 mm of box width, 201 → **226**, and the bed footprint goes to
290 × 242. Y was the tight axis when this was drawn against a 300 bed; on a 320
it is the cheap one.

The inlet module is mounted with its **58 mm axis vertical**, so the rocker is
at the top and the fuse drawer pulls out below it. Note the two M3 ears straddle
the cutout on the *short* axis — which is why the 40 mm hole pitch is larger
than the 29 mm cutout it flanks.

The pad is a slab on the *outside* of the back wall, so `plug_pad_w` has to stay
within the wall's length or it hangs in mid-air with nothing behind it. With
285 mm of wall and a 54 mm pad there is no danger, and the `.scad` asserts it
anyway.

### The front bay is still why the DC-DC fits

39 mm of channel alongside the supply. The DC-DC is 25.4 mm deep behind its
panel and its boss steps 12 mm outward, so there is 25.6 mm behind it for
terminals. `gland_x` slides the 36 V output along that wall; the `.scad` asserts
it clears the DC-DC.

## The second supply — a DC-DC module, not a second mains supply

The box gained a second output stage: a two-rail DC-DC with an LCD, panel
mounted at the END A end of the bay. **It is fed from the 36 V supply already in
the box, not from the mains.** That is what makes it a cheap addition — no
second inlet, no second cord, and no more live terminals in a box that already
has a set. Everything it does still sits downstream of the C14's fuse.

| rail | what it is for |
|---|---|
| **fixed 5 V** | the VR rig's Pico, and the DM542's `PUL+ / DIR+ / ENA+` commons |
| **adjustable** | set from the LCD; a bench rail, out through the same gland |

### 40 V in, on a 36 V bus — which makes it the weakest part on that bus

**The module is rated 40 V DC in.** Against 36 V that is 4 V of headroom, about
11 %, and in steady state it is fine: an open-frame supply regulates to a
percent or so and never goes near the ceiling. (Worth saying because most
modules this size stop at 32 V, which this supply would destroy on the first
switch-on. This one clears it.)

What the rating changes is *which part fails first*. The DM542 is rated **50 V**.
The DC-DC is rated **40**. **The lowest-rated thing on the 36 V bus is now the
supply the Pico runs on** — so an excursion that used to threaten only the
driver now takes out the 5 V rail first, and the step generator with it.

That excursion is already documented: [ramp the
decelerations](../vr-test-rig/BOM.md#ramp-the-decelerations--capacitance-cannot-fix-a-hard-stop).
A switching supply cannot sink current, so a hard stop dumps the wheel's energy
into whatever capacitance is on the bus and drives it to 64–120 V. That ramp was
load-bearing before. It is more so now, against a ceiling 10 V lower.

Two things follow:

- **Do not touch the supply's V-ADJ trimmer.** Open-frame supplies commonly trim
  ±10 %, and +10 % of 36 is **39.6 V** — 0.4 V from the module's absolute
  maximum, before any transient at all.
- The 1000 µF at the driver's `V+` is now insurance for the DC-DC as well as for
  the driver. Fit it.

#### And a TVS cannot cover the gap

The reflex is to clamp the bus. It does not work here, and the reason is
arithmetic rather than taste: the part would have to stand off 36 V without
conducting **and** clamp below 40 V, and nothing does both. The lowest standard
device that stands off 36 V is an `SMBJ36A` — breakdown **40.0–44.2 V**,
clamping at **58.1 V**. Its breakdown tolerance alone is wider than the whole
4 V margin: at one end of the spread it begins conducting at the module's
ceiling, and it does not clamp hard until 18 V past it.

The window between 36 V working and 40 V absolute maximum is too narrow for a
transient suppressor to live in. **The ramp is the mitigation; there is no
component to buy instead.**

### Fuse the tap

The 36 V supply will put **10 A into a fault** and has no idea it is a fault.
Put a **1–2 A fuse in the tap**, at the supply's terminal end so it protects the
wire and not just the module. The C14's fuse is sized for the whole supply and
will never notice a shorted DC-DC — which is a fault inside a plastic box.

### The Pico goes on `VSYS`, not `VBUS`

The Pico's **`VBUS` pin is the USB connector's 5 V, directly.** Feeding it means
back-feeding the host's USB port. Use **`VSYS` (pin 39)**, with GND on pin 38 —
that is what the datasheet provides for exactly this. USB reaches `VSYS` through
the on-board Schottky `D1`, so a cable can stay plugged in for programming: `D1`
reverse-blocks and nothing flows back into the port.

Put a **Schottky in the feed** as well, so the module is protected in the other
direction too. 5 V less the drop lands `VSYS` near 4.7 V, comfortably inside its
1.8–5.5 V range.

The part that is an *improvement* rather than a change: `PUL+ / DIR+ / ENA+`
come off this same 5 V rail. [The VR rig BOM](../vr-test-rig/BOM.md) used to
take them from the Pico's `VBUS`, which meant **the driver's opto commons died
the moment the USB cable was unplugged.** On this rail they do not.

The module's 5 V return, the Pico's GND and the 2N7002 sources are one node.
Run the 5 V and its return out as a **pair**.

### Star the ground — it is no longer floating

The optos were never isolating the Pico from the motor supply in the first
place: `PUL+` and `PUL−` are both in the Pico's domain and the barrier is inside
the driver. What changes is the **reference**. A non-isolated buck ties the
Pico's ground to the 36 V supply's negative, which is also the DM542's return —
and 2 A/phase of chopper current flows in that return.

So take the module's input **from the supply's own output terminals**, not
daisy-chained off the DM542's `V+ / V−` screws. Then the motor's return current
never flows through a conductor the Pico's ground shares, and the ripple stays
where it belongs.

One consequence worth knowing about: with the Pico's ground tied to the supply
negative, a USB cable to a PC now joins the PC's ground to it as well. That path
did not exist before.

### The fan is not a load for the adjustable rail

Tempting — the fan wants 12 V, this page used to hand-wave "a small buck module
in the bay", and there is now a rail in the bay that can be set to 12.
**Don't.** It would put the cooling on a knob, in a box whose airflow depends
entirely on that fan and which holds a warm supply and a mains connection. Give
the fan its own fixed source and leave the adjustable rail free.

### Label the two pairs at the gland

Two wire pairs leave the same gland and one of them can be at 30 V. **Two
colours, and a label at both ends.** Swapping them puts the adjustable rail on
the Pico's `VSYS`.

### It sits in still air

The fan blows END A to END B *over and under the supply*; the bay is off to one
side and barely sees it. At the load this rail was added for — a Pico and three
optos, call it 100 mA at 5 V, well under a watt — that does not matter. Start
pulling amps from the adjustable rail and the module wants a heatsink, because
the bay will not cool it.

## How the DC-DC is mounted

### It hangs on its own snap locks

Two tapered locks, one on each **vertical edge** of the cutout, 12.7 mm long,
centred. They start about 1 mm behind the bezel and taper back 3, so they grip a
panel **1 to 4 mm thick**. A 3 mm wall is right at the far end of that taper —
a loose grip on a module standing 25 mm off the panel — so the panel is
**thinned to 2 mm** over a patch reaching 6 mm past the cutout all round.

That relief is cut on the **inside** face. The outside stays flat, so the bezel
lands on plain wall and none of it shows.

Nothing else holds the module: no screws, no brackets. The cutout's left and
right edges are the only surfaces carrying it, so keep them clean and do not put
anything else on them. Printed floor-down they are vertical walls and come out
crisp — but test-fit the module before you wire anything to it.

### The panel steps 12 mm outward

The bay is 39 mm and the module is 25.4 deep, leaving 13.6 mm for its terminals
and the bend in the wire. That is not enough if the terminals exit straight
back, which on these modules they usually do. So the panel sits on a **boss that
steps 12 mm outward**, giving **25.6 mm** of clear bay behind the module.

It costs 12 mm of bed in Y and nothing else: the tub's footprint goes from
290 × 205 to 290 × 213 at the time, and X — the axis that was tight against a
300 bed — did not move. (The back bay has since taken the footprint to
290 × 242; see the inlet section.) The boss's underside is drafted 45° like the fan and
plug pads, so it grows out of a vertical wall with nothing to support, and the
bay simply carries on into it behind a 3 mm skin.

**If your module's terminals exit sideways or upward, set `mod_boss = 0`.** The
module then lands in a flat wall with 13.6 mm behind it and the box keeps its
original 290 × 205 footprint. Decide before you print — this is the one
parameter on the module that changes the shape of the box.

### Why END A, and why the output leaves on the end wall

Three things now share the bay wall, and the order is deliberate: **low voltage
at END A, mains in the middle, 36 V DC at END B.** The DC-DC's output gland is
on the **END A wall**, not the bay wall, so the 5 V and adjustable pairs never
run the length of the bay past the inlet's terminals.

`mod_x` slides the module along the wall like `plug_x` and `gland_x` do — but
the `.scad` asserts that its boss clears the plug pad, so a bad value stops the
render.

## Front wall — jacks and two buttons

```
|-- DC-DC 18.7..109.3 --|   36V 10A   0-30V 3A   5V 3A        POWER
                            (o)(o)    (o)(o)     (o)(o)         (o)
                                                              THERMAL
                                                                (o)
```

**The 12.5 mm hole was never a gland.** It was drawn for a PG7 carrying the 36 V
output; in the build it took the latching relay's power button, and the 36 V now
leaves on banana jacks instead. A second identical button wakes the fan
controller's display.

**The two buttons stack vertically** at the far right. Side by side they cost
40 mm of a wall with 145 to share between them and six jacks; stacked they cost
20, and that difference is what lets the jack pairs sit far enough apart to read
as pairs.

**19.05 mm (0.75") within a pair is a standard, not a preference** — it is what
lets a dual banana plug drop into both posts at once. The gap between pairs is
then whatever is left, and it has to be clearly larger. At 31.15 mm it is 1.64×
the within-pair pitch; the render asserts it stays above 1.5×, because six posts
in an even row is the mistake that puts a 5 V load across 36 V.

Everything is labelled on the outer face — voltage and current above each pair,
`POWER` and `THERMAL` by their buttons. Two identical buttons 26 mm apart are
otherwise a coin toss, and one of them cuts the supply.

Clearances are to the **bodies**, not the bores: a binding post is ~12 mm across
the nut and a button bezel ~16, so clearing the holes by 8 mm left 0.25 mm
between the parts. 14 mm gives 6.25.

### The jacks in the exhaust grid cost 12 %

The first build put them through the END B grid, which works and is worth
knowing the price of: three holes per pair, nine of 78, **2808 → 2484 mm²**.
Against one fan that is still 2.19× the bore and fine.

Against **two** fans it is 1.10×, and even the untouched grid would only be
1.24×. So the grid was already the limit for a second fan before the jacks
touched it — which is the strongest argument yet for the
[thicker fan](#one-fan-may-not-be-enough-under-load--measure-before-adding):
a 40 × 40 × 20 uses the same 38 mm bore and doubles airflow without spending any
grid budget at all.

## Safety

The box is plastic, so there is nothing to bond to earth — but the C14's earth
pin still has to go somewhere. **Run it to the supply's earth terminal.** Do not
leave it unconnected because the enclosure is non-conductive; the supply's
chassis and its output reference need it.

- The lid screws are the only thing between a finger and 120 V. Fit all ten.
- Fuse for the *supply*, not for the socket. The inlet module is rated 10 A;
  that is a ceiling, not a recommendation.
- Use the insulated spade terminals the inlet module ships with, fully seated.
- Fit the cable gland or grommet before pulling the DC output wires through. A
  bare printed hole will cut insulation over time, and the layer lines make it
  worse than a drilled one.
- Strain-relieve the mains wiring inside the bay so a tug on the cord cannot
  reach the terminals.
- **Fuse the DC-DC's 36 V tap at 1–2 A.** A shorted module on a 10 A supply is
  an ignition source, and the C14 fuse is far too big to see it.
- Keep the DC-DC's wiring at the END A end of the bay, clear of the inlet's
  spade terminals. That separation is why the module and its gland are where
  they are; do not undo it by routing the low-voltage pairs past the plug.

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
| `plug_x` | mid | where the inlet lands on the **back** wall |
| `gland_x` | −45 | where the 36 V output leaves the front wall |
| `clr_side` | **28** | back bay — mains only. Set by the inlet's 24 mm reach |
| `grid_pitch`, `grid_sq` | 10, 6 | exhaust open area |
| `mod_cut_w/h`, `mod_depth` | **70.6**/38.5, 25.4 | the DC-DC's body — **measure yours** |
| `mod_boss` | 12 | how far the DC-DC's panel steps out. **0 = flat wall**; changes the box |
| `mod_panel_t` | 2.0 | panel at the cutout. The snap locks grip 1–4 |
| `mod_x` | 64 | where the DC-DC lands along the bay wall |
| `mod_relief_m` | 6 | how far the thinned panel reaches past the cutout |
