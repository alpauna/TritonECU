# VR test rig — bill of materials

Everything needed to turn a 36-1 steel wheel past a Ford CKP sensor at a known
absolute angle, plus the cam channel on a 2:1 gear drive.

Printed parts come from `vr_rig.scad`; see README for orientation, which matters
more than usual here.

---

## Already ordered

| Qty | Item | Note |
|--:|---|---|
| 1 | 36-1 trigger wheel, steel, 150 mm OD, **24 mm keyed bore** | keyway inline with the missing tooth |
| 1 | Ford CKP sensor (VR) + pigtail | `3U2Z145411SMA` connector |
| 1 | Ford CMP sensor + pigtail | same connector family |

---

## Drive

| Qty | Item | Spec | ~$ |
|--:|---|---|--:|
| 1 | **Stepper, NEMA 17 48 mm** | `17HS19-2004S1` — 2.0 A/phase, 0.59 N·m, **2.8 mH**, 5 mm shaft | 15 |
| 1 | **Driver** | `DM542` / `DM542T` — 20–50 V, to 4.2 A, step/dir, selectable microstep | 20 |
| 1 | **PSU** | **36 V** 3 A (100 W) — see below, 24 V is the marginal choice | 20 |
| 1 | **Step generator** | Raspberry Pi Pico (RP2040) | 4 |
| 1 | Coupling, **5 → 12 mm** | aluminium jaw/spider, D25 L30 | 8 |

### Why this motor, and why 36 V rather than 24 V

The torque is not the problem. Spinning up 694 g of steel
(J = 1.95 × 10⁻³ kg·m²) to 1200 rpm in three seconds needs **82 mN·m**, which
almost any NEMA 17 has. **The problem is speed.** 1200 rpm is
**4000 full-steps/s**, and stepper torque there is set by how fast current can
be forced into the winding, not by the holding-torque number on the label:

```
di/dt = V / L        2 A into 2.8 mH
  24 V  ->  233 us          step period at 4000 steps/s = 250 us   (93 %)
  36 V  ->  156 us                                                 (62 %)
```

At 24 V the current barely reaches setpoint before the step ends — torque falls
away right where the rig is most interesting. **36 V buys real margin**, and it
is why the driver is a DM542 (50 V capable) rather than a 2 A stepstick.

Low winding inductance matters for the same reason. **If substituting a motor,
choose on inductance, not holding torque.**

### Why a stepper at all, and the one failure it hides

Open-loop absolute position is exactly what makes this rig a calibration bench:
commanded steps *are* crank degrees. Trust that carefully though —

**Resolution is not accuracy.** 16× microstep gives 0.1125°/step, but a stepper's
inherent accuracy is **±5 % of a full step, ±0.09°**, non-cumulative. The real
figure is a tenth of a degree, not a hundredth. Still comfortably better than the
~0.5° that timing work needs.

**If the motor loses steps, the datum lies silently.** The rig checks itself for
free: the missing tooth passes once per revolution, so if the decoder's gap
detection and the commanded step count ever disagree, steps were lost. Wire that
comparison in from the start rather than trusting the count.

### The Pico is not a placeholder

A rig that only spins at constant speed never tests the case that actually
breaks decoders. **Cranking is violently irregular** — the engine slows against
each compression stroke and speeds up after it, and sync acquisition has to
survive that. RP2040 PIO generates jitter-free steps from a programmed velocity
profile, so cranking irregularity becomes something you *specify* rather than
something you hope to catch. That is the rig's second most valuable capability
after absolute position.

---

## Shafts, bearings, hardware

| Qty | Item | Spec |
|--:|---|---|
| 1 | Shaft, crank | **12 mm h6 ground steel, 200 mm** |
| 1 | Shaft, cam | **12 mm h6 ground steel, 150 mm** |
| 4 | Bearing | **6001-2RS (12 × 28 × 8)** — two shafts, two each |
| 4 | Shaft collar | **12 mm** bore, clamp type, axial location |
| 1 | Base board | **12 mm plywood or MDF, 320 × 240** — see below |
| 1 | Bolt, M8 × 25 | the cam trigger lobe, head inward |
| 1 | Nut, M8 | + washer |
| 1 | **Brass rod, 13 mm dia × 20 mm** *(or lead sinker)* | counterweight — **cut to length to balance** |
| 1 | M3 × 6 grub screw | traps the counterweight |
| — | M4 × 12/16/20 socket cap, M4 nuts | clamps, feet, sensor mounts |
| — | M3 × 8 socket cap ×4 | NEMA 17 face |
| 1 | Parallel key, **8 × 7 × 20 steel** *(optional)* | see below |

**On the key:** the hub prints its key integrally, which is fine — the drive
torque is 82 mN·m and PETG shrugs at that. A steel parallel key is a dollar and
removes the failure mode entirely, but it needs a keyway *slot* cut in the hub
spigot instead of the printed key. Start printed; the swap is a parameter change,
not a redesign.

---

## Printed parts

| Qty | Part | Orientation |
|--:|---|---|
| — | ~~`base`~~ | **cut from board instead** — the module is the drilling template |
| 4 | `bearing_block` | on its back — two shafts, two each |
| 1 | `motor_mount` | on its back |
| 1 | `wheel_hub` | **bore axis vertical** (concentricity = runout = air gap) |
| 1 | `crank_gear` | **teeth flat on the bed** |
| 1 | `cam_gear` | **teeth flat on the bed** |
| 1 | `cam_target` | bore axis vertical |
| 2 | `sensor_mount` | upright — crank and cam |

~500 g **PETG or ABS, not PLA.** Under-hood parts are not the reason; the reason
is that a PLA clamp creeps under load and lets 694 g of steel walk off a shaft.

### Gears: printed first, steel as a drop-in later

Printed is the right start. The load is two spinning discs, and tooth-to-tooth
error on a printed gear is well under a degree against a cam-phase requirement
that is far looser.

**This is why the module is 2, not 1.** At module 1 a tooth is 1.57 mm thick at
the pitch circle — about four extrusion widths at a 0.4 mm nozzle, where the
profile becomes whatever the slicer felt like. Module 2 gives **3.14 mm, eight
widths**, and 4.5 mm whole depth. The teeth come out as teeth.

The geometry is deliberately standard — **module 2, 20° pressure angle, 20T and
40T, 60 mm centres** — so if printed gears do disappoint, a bought steel or POM
pair drops straight in with no change to the rig.

---

## Going bigger: 12 mm shafts, and what was actually limiting things

The shaft went 8 → 12 mm, which is **5.1× the bending stiffness** — `EI` goes as
`d⁴`, so 50 % more diameter is five times the shaft.

**But the shaft was never the soft part.** Measuring the printed bearing upright
against it:

```
                             EI          tip stiffness
 8 mm steel shaft          40.2 N.m^2
12 mm steel shaft         203.6 N.m^2
upright, 105 tall x 16     24.6 N.m^2      63.7 kN/m     <- softer than the shaft
upright,  78 tall x 24     82.9 N.m^2     524.4 kN/m
```

The bracket was **below even the 8 mm shaft**, and eight times below a 12 mm one.
Stiffening the shaft alone would have moved almost nothing. Three changes, all
free:

**The uprights got shorter.** `shaft_h` was `wheel_od/2 + 12` = 87 mm, which
lifted the wheel clear of the base and left the wheel slot doing nothing at all.
Dropping to 60 runs the wheel *through* the slot as intended, and tip stiffness
goes as `1/h³` — **2.4× for nothing but a number**.

**And thicker**, 16 → 24 mm axially. That axis is the one the bearing load bends,
and stiffness goes as `t³`: another **3.4×**. Together, **8.2× on the bracket.**

**Four foot bolts, not two.** Two bolts on the centreline is a hinge — the
rotating radial load had nothing but bolt preload resisting sideways rock.

**The wheel is now straddled between its bearings** rather than hung outboard,
which takes the cantilever out of the stiffest remaining path.

### The base is a board now

At 320 × 240 the plate is past any hobby printer, and that is the right outcome:
**a printed plate was never sensible for a rig whose job is to vibrate as little
as possible.** Cut it from 12 mm plywood or MDF — stiffer than PETG, several
times heavier so it damps rather than rings, and a saw does not care about bed
size.

`base()` is therefore a **drilling template** as much as a part. The old 10 mm M4
grid is gone: at this plate size it was 660 holes and minutes of render time to
provide mounting points nothing used. Holes now sit only at stations that carry
something — which is what you would mark out by hand anyway.

### Layout

```
        x = -95      -30       0       30        70          95     112
crank   [motor]---[brg]----[WHEEL]---[brg]----[20T gear]
cam                        (y = -60)  [brg]---[40T gear]---[brg]--[target]
```

Stations are spaced against real part extents, not by eye: a bearing block's
upright runs ±18 mm about its station and its foot ±26, so the gear boss has to
start beyond x = 48 or it lands **inside** the block. The cam shaft sits on the
negative side so it and the crank sensor do not both push the board wider.

---

## Balancing the cam trigger — brass or lead

The M8 bolt is a lump of steel bolted to one side of a spinning disc. **About
19 g at a 25 mm radius, so 480 g·mm of imbalance**, which at 1200 rpm crank
(600 cam) is **1.9 N rotating**.

That is not a structural worry. It matters because **vibration modulates the air
gap, and air gap is the measurement the rig exists to make.** VR output amplitude
is strongly gap-dependent, so an unbalanced target corrupts exactly the data you
came for. `cam_target` now carries a counterweight boss 180° from the bolt.

### Brass or lead — both reach balance, so take brass

The pocket is **13.4 mm bore × 21 mm deep**, a slip fit on **13 mm rod stock**.
Capacity is **25 g of brass or 34 g of lead**, and the job needs about 20 g — so
either material gets there and the choice is free on that count.

**The bore follows the rod, not the other way round.** A printed pocket is a
one-line parameter; bought stock is bought. If you would rather use 14 mm rod,
change `cw_dia` to 14.4 and `cw_boss` to 20.4 and reprint — that is the whole
change.

**Take brass.** Rod stock cuts to length with a hacksaw, handles like any other
metal, and needs no precautions. Lead works and is denser, but the density buys
nothing here because the pocket is already big enough; if you do use it, drop in
a sinker or shot and **do not melt or file it** — that is where lead becomes a
hazard rather than an inert lump in a sealed pocket.

### Cut the rod to length — do not trust the arithmetic

The pocket is deliberately **deeper than needed**. Expect roughly **15 mm of
14 mm rod**, but treat that as a starting point:

```
bolt imbalance to cancel          480 g.mm
  printed boss itself, 4.8 g       93 g.mm   (a fifth of the job, free)
  brass rod, ~15 mm                387 g.mm
```

Too many unknowns feed that sum — your actual bolt and nut mass, print infill,
filament density. **Balance it on knife edges and cut the rod until it sits
still.** That takes five minutes and beats any calculation, including this one.

Rod length by diameter, if you have other stock:

| rod dia | rod alone | with the boss's 88 g·mm |
|--:|--:|--:|
| 12 mm | 25.6 mm | ~21 mm |
| **13 mm** | **21.6 mm** | **~18 mm** |
| 14 mm | 18.8 mm | ~15 mm |
| 16 mm | 14.4 mm | ~12 mm |

### Spare brass is not wasted

A 20 mm offcut of the size you do not use makes the best **air-gap gauge** you
could ask for. Brass is non-magnetic, so you can set the gap with the sensor
powered and the channel live — a steel feeler gauge sitting in the gap changes
the very magnetic circuit you are trying to set.

Face the offcut flat, or slice it to a known thickness, and it becomes a
go/no-go for the 1 mm gap that does not perturb the measurement.

### The counterweight must not be ferrous

The boss reaches r = 29 mm against a 30 mm rim, so it passes the sensor on every
revolution. **A steel counterweight would be a second VR trigger**, and the cam
channel would read two pulses per turn — destroying the one thing the cam is
there to do, which is tell compression from exhaust.

Brass and lead are both non-ferromagnetic and invisible to the sensor. That is
the real reason the choice is between those two, and not a free pick.

### You do not need it perfect

Residual force scales *linearly* with residual imbalance:

```
unbalanced      480 g.mm   1.89 N
80 % corrected   96 g.mm   0.38 N
```

So getting most of the way there gets most of the benefit. **Static balance is
enough** — the target is a thin disc, so there is no meaningful couple to chase.
Rest the cam shaft on two level edges and add weight until it stops rolling to a
preferred position.

---

## Safety

| Qty | Item |
|--:|---|
| 1 | Polycarbonate sheet, 3 mm, ~200 × 200 mm — guard over the wheel |

694 g of steel at 1200 rpm carries **15 J**. That is not catastrophic, but it is
roughly a hammer blow, and printed clamps are the thing holding it. Guard it,
and keep the speed sweep to 1200 rpm — at 6000 rpm the same wheel holds 375 J,
which is a different conversation entirely.

---

## Rough total

About **$65–90** of bought parts beyond the wheel and sensors, most of it the
motor, driver and supply.
