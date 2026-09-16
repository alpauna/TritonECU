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
| 1 | **Stepper, NEMA 17 48 mm** | `17HS19-2004S1` — 2.0 A/phase, 0.59 N·m, **2.8 mH**, Ø5 D-shaft 24 mm, 4-lead bipolar | 15 |
| 1 | **Driver** | `DM542` / `DM542T` — 20–50 V, to 4.2 A, step/dir, selectable microstep | 20 |
| 1 | **PSU** | **36 V** — 360 W brick in hand (Aclorol 36 V 10 A). 24 V is the marginal choice, see below | 20 |
| 1 | **Fuse + holder, 4 A slow-blow** | **not optional with a 10 A supply** — see below | 3 |
| 1 | Capacitor, **1000 µF / 63 V** | bulk at the driver's V+ | 2 |
| 1 | **Step generator** | Raspberry Pi Pico (RP2040) — **3.3 V logic, needs the buffer below** | 4 |
| 1 | **Level buffer** | **74HCT125** or 74HCT541, run at 5 V — see below | 1 |
| 1 | Coupling, **5 → 12 mm** | aluminium jaw/spider, D25 L30 | 8 |

### Verified against the 17HS19-2004S1 drawing

Every dimension the mount depends on, checked rather than assumed:

| | drawing | `vr_rig.scad` |
|---|---|---|
| Frame | 42.3 MAX | `nema = 42.3` ✓ |
| Bolt pattern | 31 ±0.2 square | holes at (±15.5, ±15.5) ✓ |
| Pilot boss | Ø22 −0.05, 2 mm tall | 23 mm clearance cut ✓ |
| Shaft | Ø5 −0.012 × 24 mm | `nema_shaft = 5` ✓, coupling is 5 → 12 |
| Body | 48 MAX | reaches x = −147 against a base edge at −150 ✓ |

Two details the drawing adds:

- **The shaft has a 4.5 mm flat** (D-cut). Land the coupling's set screw on it
  rather than on the round — a grub screw on a plain shaft will eventually spin.
- **The motor ships with a 1 m lead and a 2.54 mm 4-pin connector.** The DM542
  takes screw terminals, so that plug gets cut off or adapted. Four leads means
  bipolar, which is what the DM542 drives.

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

### Considered and rejected: NEMA 23, 2.4 N·m, 4.0 A

Bigger is not better here, because **torque is not the binding axis**. The rig
needs 82 mN·m; the NEMA 17 already supplies **7×** that. A 2.4 N·m NEMA 23 supplies
**29×** — more of something already in surplus.

**The figure of merit is `I × L`, not torque.** Current has to reach setpoint
within one step period, so top speed is `rate = V / (I × L)` — and **doubling the
current halves the top speed for the same inductance.**

Candidate specs given: 2.4 N·m holding, **4.0 A/phase, 0.65 Ω**, 1.8°, 8 mm shaft,
24–48 V. Inductance was not quoted, and it is the only number that matters:

| motor | I × L | top speed |
|---|--:|--:|
| **17HS19** — 2.0 A, 2.8 mH | 5.6 mA·H | **1929 rpm** |
| NEMA 23 — 4.0 A, 2.0 mH | 8.0 | 1350 rpm |
| NEMA 23 — 4.0 A, 2.5 mH | 10.0 | 1080 rpm ✗ |
| NEMA 23 — 4.0 A, 3.0 mH | 12.0 | 900 rpm ✗ |
| NEMA 23 — 4.0 A, 3.5 mH | 14.0 | 771 rpm ✗ |

Against a **1200 rpm** target, the NEMA 23 clears it only if **L ≤ 2.25 mH**. This
class typically runs 2.5–3.8 mH, which lands at **900–1080 rpm** — short of the
target, while the NEMA 17 reaches 1929 and keeps 60 % headroom.

*(The linear rise model holds for both: `I × R` is 2.8 V and 2.6 V against a 36 V
supply, so resistance is not the limit — inductance is.)*

It would still be **usable**, since 900 rpm covers cranking at 200 and idle at
700, which is where sync acquisition actually fails. It would just have no margin
above idle, in exchange for torque that was already 7× surplus.

Three practical costs on top:

- **The coupling is wrong.** 8 mm shaft against the 5 → 12 mm coupling ordered.
- **The mount is a redesign** — 57.15 mm frame, 47.14 mm M5 bolt circle, 38.1 mm
  boss, against 42.3 / 31 / 22.
- **The 82 mm body overhangs the base by 31 mm.**
- **4.0 A is 95 % of the DM542's 4.2 A ceiling**, against 48 % for the NEMA 17.
  No headroom for a driver that also has to survive a stall.

**If a NEMA 23 is wanted anyway, ask the vendor for inductance** and check
`I × L ≤ 9.0 mA·H` before anything else. That single number decides it.

### A 360 W supply is fine — but fuse it

The stepper draws about **2.2 A worst case** (two phases at 2 A into ~1.4 Ω is
11 W at standstill; call it 60–80 W with driver losses at speed). A 10 A supply is
therefore roughly **4× the load**, which is harmless in itself — a supply delivers
what is drawn, not what it is rated for.

**The risk is what it delivers into a fault.** 36 V × 10 A is **360 W** into a
pinched wire or a failed driver, on a bench rig made largely of printed plastic.
Nothing in the load needs more than ~2.2 A, so **a 4 A slow-blow fuse in the
supply lead** protects the wiring at 1.8× the real draw. Slow-blow because the
driver's input capacitance draws an inrush spike at power-on.

### Ramp the decelerations — capacitance cannot fix a hard stop

A decelerating stepper pushes energy back at the supply, and **a switching supply
cannot sink current**, so it lands in whatever capacitance is on the bus. The
wheel carries **15.4 J at 1200 rpm**, and the arithmetic is unkind:

| bulk cap | bus voltage if 20 % of 15 J returns |
|--:|--:|
| 470 µF | 120 V |
| 1000 µF | 86 V |
| 2200 µF | 64 V |

Against the **DM542's 50 V maximum**, none of those work. **Capacitance is not the
answer — the ramp is:**

| deceleration | power returned |
|--:|--:|
| 0.2 s | 77 W |
| 1 s | 15 W |
| **3 s** | **5 W** |

At a 3-second ramp only ~5 W comes back, which the driver's own losses absorb
without the bus noticing. **The rig has no reason to stop quickly**, so this costs
nothing — but it is a property of the *step generator firmware*, not of the
hardware, and it has to be written in deliberately.

The 1000 µF is still worth fitting as bulk near the driver's V+ — standard
practice for stepper supplies, and it handles the residue. It is insurance, not
the mitigation.

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

### The Pico is 3.3 V and the DM542 wants 5 V — buffer it

The driver's terminals are marked **PUL+ / DIR+ / ENA+ (5V–24V)**. Those inputs
are **optoisolated**, with an internal series resistor sized for 5 V:

| drive | opto current |
|---|--:|
| 5 V (design point) | **14 mA** ✓ |
| 3.3 V direct from the Pico | **7.8 mA** — marginal |

It would probably *work*. That is the problem — **marginal opto drive degrades
edge timing**, and on this rig the step edge *is* the angular datum. An opto run
at half its design current turns on slowly and its delay varies with temperature,
which converts directly into position error at exactly the moment the rig is
supposed to be the trustworthy reference.

**Use a `74HCT125` (quad buffer) or `74HCT541` at 5 V.** The HCT family's input
threshold is 2.0 V, so a 3.3 V GPIO drives it reliably, and its 5 V output drives
the opto at full current. This is the same reason the ECU uses a 74HCT541 on the
ignition outputs.

**Wire common-cathode:** `PUL− / DIR− / ENA−` to ground, and drive `PUL+ / DIR+ /
ENA+` from the buffer. The Pico's `VBUS` supplies the 5 V.

*(Do not wire common-anode with 5 V on the `+` terminals and the Pico sinking on
the `−` side. That puts 5 V through the opto into a 3.3 V GPIO, and back-feeds the
Pico whenever it is unpowered.)*

### Microstepping is capped by pulse rate, not by resolution

The driver takes **pulses/rev** directly rather than a multiplier, and at
**1200 rpm = 20 rev/s** the input frequency is simply `20 × pulses/rev`:

| pulse/rev | at 1200 rpm | resolution | |
|--:|--:|--:|---|
| 1600 | 32 kHz | 0.225° | |
| **3200** | **64 kHz** | **0.1125°** | **the sweet spot** |
| 6400 | 128 kHz | 0.056° | |
| 8000 | 160 kHz | 0.045° | near the limit |
| 12800 | 256 kHz | 0.028° | **exceeds ~200 kHz** |
| 25600 | 512 kHz | 0.014° | exceeds |

**[CHECK] the driver's maximum input frequency** — 200 kHz is typical for this
class, and at 20 rev/s that caps pulses/rev at **10 000**.

Chasing finer microstepping past 3200 buys nothing anyway: the motor's *inherent*
accuracy is ±5 % of a full step, **±0.09°**, so 0.1125° already sits at the point
where resolution stops being the limit.

**Set SW4 off** (half current at standstill) so the motor is not heating at full
current between runs.

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
| 2 | **Rod, 8 mm × 300 mm, 304 stainless** | **base spine** — no precision needed; the base is sized to use it uncut |
| 1 | Bolt, M8 × 25 | the cam trigger lobe, head inward |
| 1 | Nut, M8 | + washer |
| 1 | **Brass rod, 13 mm dia × 20 mm** *(or lead sinker)* | counterweight — **cut to length to balance** |
| 1 | M3 × 6 grub screw | traps the counterweight |
| — | M4 × 12/16/20 socket cap, M4 nuts | clamps, feet, sensor mounts |
| — | **M3 × 8 socket cap ×4** | NEMA 17 face — **not longer, see below** |
| 1 | Parallel key, **8 × 7 × 20 steel** *(optional)* | see below |

**On the M3 screws: do not substitute longer ones.** The 17HS19 drawing specifies
`4-M3 DEPTH 4.5 MIN` — a shallow blind tapped hole. Through a 4 mm mount plate:

| | thread needed | result |
|---|--:|---|
| **M3 × 8** | 4 mm | **clamps, 0.5 mm spare** |
| M3 × 10 | 6 mm | **bottoms out — never clamps** |
| M3 × 12 | 8 mm | bottoms out |

The instinct that a longer screw is safer is backwards here: it reaches the bottom
of the hole and stops, leaving the motor loose under a head that feels tight.
4 mm of M3 engagement is 1.3 × diameter, against a mount carrying 0.08 N·m.

**On the key:** the hub prints its key integrally, which is fine — the drive
torque is 82 mN·m and PETG shrugs at that. A steel parallel key is a dollar and
removes the failure mode entirely, but it needs a keyway *slot* cut in the hub
spigot instead of the printed key. Start printed; the swap is a parameter change,
not a redesign.

---

## Printed parts

| Qty | Part | Orientation |
|--:|---|---|
| 1 | `base` *(or `base_a` + `base_b`)* | flat — 280 × 240 fits a 300 bed whole |
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

### The base: two spine rods do the work

The plate shrank to **280 × 240** — the 320 was over-generous, since the parts
only span 264 mm. That fits a 300 mm bed whole.

An 8 mm PETG sheet is still a floppy thing. **Two full-length 8 mm steel rods,
carried in ribs under the plate, take it from `EI` 20.5 to 826 N·m² — forty
times.**

**The offset is what does it, not the diameter.** A rod lying on the neutral axis
can only contribute its own `I`; moved off it, the *section* does the work
through `A·d²`:

| rod | buried in the plate | in a rib, 15 mm down |
|--:|--:|--:|
| 5 mm | 33 N·m² (1.6×) | **613 (30×)** |
| 6 mm | 46 (2.2×) | 691 (34×) |
| **8 mm** | 101 (4.9×) | **826 (40×)** |
| 10 mm | 217 (10.6×) | 987 (48×) |

A **5 mm rod in a rib beats a 10 mm rod buried in the plate.** Position dominates
size, and it is not close.

The rods sit at **y = ±58** — clear of the wheel slot (±36.6) and 9 mm from the
nearest cam-block bolt, with the −58 rod running directly beneath the cam shaft.
They also **bridge the wheel slot**, which is the plate's weakest section.

### 304 stainless is a good choice here, and not only on price

**Stiffness is unchanged for practical purposes.** 304's modulus is 193 GPa
against mild steel's 200, so the spine gives **819 N·m² instead of 826** — still
40× the bare plate. A 4 % difference on a bench rig is noise.

**And 304 is austenitic, so it is non-magnetic.** That removes a question rather
than answering one: a ferromagnetic rod running the length of the base, 58 mm off
the shaft centreline, would at least invite asking whether it perturbs the VR
magnetic circuits. It does not arise. Same property that made brass and lead the
only candidates for the cam counterweight.

**Cutting it is the part to avoid** — 304 work-hardens, so a hacksaw that rubs
instead of cutting will glaze the surface and stop progressing. Which is why the
base is sized around the rod rather than the other way round.

### One piece or two — a 320 mm bed makes it a choice again

The base is **300 × 240**, sized so a **300 mm rod is used uncut**.

On a **320 mm bed that leaves 10 mm clear each side**, so the one-piece `base`
becomes printable. Take it if it will run — a seam that does not exist needs no
argument. **[CHECK] the printer's *usable* area first**: nominal bed size and
printable area often differ by bed clips, a purge line, or a nozzle that cannot
reach the far corner.

`base_a` + `base_b` stay available and are not a downgrade: they split at
**x = −60** into **90 + 210 mm**, the seam lands in the only empty span on the
board where the flexible coupling already absorbs misalignment, and the spine
rods run through both halves as the splice. If a 300 mm flat part lifts a corner
— which is where warp bites on a big plate — that is the fallback, not a defeat.

### Print the base LIGHT — the spine makes infill almost irrelevant

A printed plate is a sandwich: solid skins carry the bending, sparse core carries
shear. So infill matters less than volume fraction suggests even before the rods
are added — and **once the spine is in, it barely matters at all**:

| infill | plate alone | with spine | gain |
|--:|--:|--:|--:|
| **10 %** | 12.7 N·m² | **568** | 45× |
| 20 % | 13.6 | 597 | 44× |
| 40 % | 15.3 | 655 | 43× |
| 100 % | 20.5 | 819 | 40× |

**10 % infill keeps 69 % of what a solid plate gives** — and that 69 % is still
**45× a bare plate at the same infill**. On a 300 × 240 part that is many hours
and a few hundred grams saved for stiffness nobody will miss.

This is the spine earning its keep twice: it was added to make the plate stiff,
and the consequence is that the plate no longer has to be.

**The seam location is the whole trick.** x = −60 is the only empty span on the
board, between the motor and the first bearing, where the flexible coupling
already absorbs misalignment by design. A seam under the gear mesh, or between
the crank bearings, would sit exactly where alignment matters.

**And the spine rods span the seam**, so it needs no separate dowels — continuous
steel through both halves is a far better splice than short pins at the joint.
Epoxy the rods in and the two pieces become one board. At 300 mm they run the
full length with nothing to trim.

*(A dowel through the plate itself was the original thought, but the plate is
only 8 mm thick — an 8 mm rod does not fit inside it. The ribs are what create
somewhere to put them, and the offset they give is what makes them worth having.)*

### Layout

```
        x = -95     -30      0      30        70        88       110
crank   [motor]--[brg]---[WHEEL]--[brg]-----[20T gear]
cam                       (y=-60)  [brg]----[40T gear]--[target]--[brg]
spine   ================ 8 mm rod at y = +58 ==================
        ================ 8 mm rod at y = -58 ==================
seam            | x = -60, between motor and first bearing
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
