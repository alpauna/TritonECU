# 36-1 VR trigger wheel test rig

A motor-driven bench rig for **M3 crank sync** — real VR sensor, real trigger
wheel, known shaft position.

`vr_rig.scad` holds every printed part. Set `part = "..."` at the top and render
one at a time.

---

## ⚠ The wheel cannot be printed

A VR sensor is a permanent magnet and a coil. It produces voltage from the
**change in magnetic reluctance** as ferromagnetic teeth pass the pole piece.
PLA, PETG and ABS are magnetically indistinguishable from air.

**A printed wheel produces zero output.** Not a weak signal — nothing.

Iron-filled filaments do not rescue it either: the particles are discontinuous,
giving a relative permeability of a few against **~1000+ for mild steel**. The
magnetic circuit needs a continuous path.

So the rig is *printed*, the wheel is *bought*:

- an aftermarket **36-1 steel trigger wheel** (the Megasquirt/aftermarket world
  is full of them, commonly 5–7" diameter), **mild steel — not austenitic
  stainless**, which is non-magnetic, or
- the **actual Ford reluctor** off a spare damper, which has the advantage of
  being exactly what the ECU will see in the truck.

## Motor: a stepper, and the reason is ground truth

A bench rig beats a signal generator for two reasons. One is the **real VR
waveform** — amplitude that scales with speed, real edge shapes, real noise. The
other is **knowing exactly where the wheel is**.

A signal generator gives the second but not the first. A drill gives the first
but not the second. **A stepper gives both.**

| | Stepper | BLDC + ESC | Drill |
|---|---|---|---|
| Known speed | **exact** | needs a sensor | no |
| **Known position** | **exact** | no | no |
| Cranking speed (150–300 rpm) | **excellent** | poor, cogs | no |
| Top speed | ~1200 rpm | thousands | thousands |

### Why ~1200 rpm is enough

**The electrically hard case is cranking, not redline.** A VR sensor puts out
perhaps 0.5–1 V at 200 rpm and 50–100 V at 6000 — Mode A2's adaptive threshold
exists precisely for the bottom of that range. A motor that is excellent from
150 to 1200 rpm covers the entire difficult region.

High rpm stresses *firmware timing* rather than the sensor, and the 10 native
tests in `test_crank` already cover 200–6000 rpm logically. **The bench rig's job
is the analog end**, which is the half that cannot be tested in software.

If high-rpm timing later needs proving on real hardware, a GT2 belt at 3:1 gets
3600 rpm from the same motor without redesigning anything.

### Drive it from the STM32 under test

The elegant version: **generate the step pulses from the same MCU that is
decoding the VR signal.** One timer produces steps, another captures COUT edges,
and firmware compares its own commanded position against what the decoder
reports — in one program, with no external reference to trust.

That turns the rig from "does it look right on a scope" into an assertion.

## Bought parts

| | |
|---|---|
| **36-1 steel trigger wheel** | mild steel, see above |
| **Ford CKP sensor**, 1999 5.4L | the real sensor, not a substitute — the point is the real waveform |
| NEMA 17 stepper | 1.5–2 A, 5 mm shaft |
| Stepper driver + 24 V supply | TMC2209 or DRV8825; 24 V is what buys the top of the speed range |
| 8 mm ground steel rod | ~150 mm |
| 2 × **608ZZ** bearings | 22 × 8 × 7 mm |
| 5 → 8 mm flexible coupling | jaw or helical — a printed rig will have misalignment |
| M4 hardware, M3 × 4 for the motor | |
| **Feeler gauges** | the air gap is the experiment |

## Measure these three before printing

The `.scad` is parametric but it cannot guess:

```
wheel_od      trigger wheel outside diameter
wheel_thk     wheel thickness
wheel_bore    centre bore
sensor_dia    VR sensor barrel diameter
```

Also check the wheel's bolt pattern against `hub()` — it assumes 3 × M4 on a
circle, which is a guess.

## Printing

**PETG or ABS, not PLA.** PLA creeps under sustained load and softens near a
stepper that has been running.

- **Bearing blocks and sensor mount: 5 perimeters, ≥40 % infill.** These carry
  load and set the air gap.
- **Print the bearing blocks lying on their backs**, bore axis vertical. That
  keeps the bore round and puts the shaft load into layer *shear* rather than
  pulling layers apart.
- Bearing pocket is sized at `brg_od - 0.05` for a light press. If it will not
  seat, open `brg_press` toward `+0.10` rather than forcing it — a cracked block
  moves the air gap.

## The air gap is the experiment, not a setting

Ford's CKP gap is around 1.0–1.5 mm, but the slotted feet on `sensor_mount()`
exist so it can be **swept**. Sweeping it is most of the value of the rig:

- how VR amplitude scales with gap, at fixed rpm
- the gap at which the adaptive threshold stops finding teeth at cranking speed
- whether the missing-tooth gap is still unambiguous at the extremes

## Safety

A 150 mm × 5 mm mild steel wheel is about **0.7 kg**, and at 1200 rpm it stores

```
E = ½Iω²  =  ½ × 1.94e-3 × 125.7²  ≈  15 J
```

Not lethal; it will still take a fingertip. The hub is a **split clamp with
through-bolts, not a grub screw**, for exactly this reason. Do not stand in the
plane of the wheel while it spins, and fit a guard before running it unattended.

## What this rig actually answers

1. **VR amplitude versus rpm** — including the peak, which settles the one open
   hardware question on the VR board: whether 5 kΩ in 0805 (good to ~150 V of
   sensor output) needs a second resistor per leg. See
   [`../../docs/review-vr-v1.md`](../../docs/review-vr-v1.md).
2. **Does the zero crossing land mid-tooth?** Scope COUT against a known shaft
   angle. This is the claim Mode A2 is chosen for.
3. **Minimum rpm at which sync holds**, and how the 85 ms watchdog behaves when
   it does not.
4. **Missing-tooth detection** against commanded position, not against itself.

---

# Add the cam channel — and drive it with gears

**Yes, include CMP.** Not as a convenience: the crank/cam *relationship* is the
thing that cannot be tested any other way.

## Why the cam has to be on the same rig

Crank sync tells you where you are **within a revolution**. Cam sync tells you
**which revolution** — compression or exhaust for a given cylinder. On a 4-stroke
the cam turns at half crank speed, and everything sequential depends on that
relationship being right.

**Two signal generators cannot test this.** They can each produce a correct
waveform, but not one that is *mechanically phase-locked* to the other with real
jitter and real drift. A rig with a 2:1 gear pair produces exactly what the
engine produces, including the imperfections.

[`sensors-to-run.md`](../../docs/1999-Ford-F150-4wd-5.42v/sensors-to-run.md)
already records that with coil-on-plug and sequential injection **CMP is
mandatory, not optional**. Building the rig crank-only means building it twice.

It also unlocks the failure modes that only exist with both present:

- cam signal lost mid-run, and whether sync recovers or limps
- **cam pulse landing on or near the missing tooth** — the nastiest case, and
  one you can only find by sweeping the phase
- sync-loss and re-sync behaviour from an arbitrary starting position

## Gears, yes — but the reason is compliance, not slip

**A properly tensioned GT2 toothed belt does not actually slip.** The slippage
instinct applies to friction drives. What a belt *does* have is **compliance**,
and under the torque ripple of a microstepping motor that shows up as **phase
jitter between crank and cam** — which is precisely the quantity being measured.

**Gears are the right call**, and their usual drawback does not apply here:
backlash matters at reversals, and this rig only ever turns one way, so it is
taken up once and stays taken up.

```
crank gear  20T          cam gear  40T          exactly 2:1
module 1 → 30 mm centre distance
```

**Printed spur gears are fine.** The load is two spinning discs. Tooth-to-tooth
error on a printed gear is well under a degree, against a cam-phase accuracy
requirement of perhaps ±5 crank degrees for correct stroke decisions.

### Layout note

At a 30 mm centre distance the cam shaft passes through the plane of a 150 mm
crank wheel. **Separate them axially** — gears meshing at one end, the two
targets on different stations along their shafts. Parallel shafts, two bearing
pairs, one motor on the crank shaft.

## The cam target is much easier than the crank wheel

CMP produces **one pulse per cam revolution** — a single feature, not 35.

So while the crank wheel must be a bought steel 36-1, the **cam target can be a
printed disc carrying one steel insert**: a bolt head, a dowel pin, a cut tab.
Only that one feature has to be ferromagnetic.

**That halves the bought-parts problem.** One steel wheel, not two.

## Make the cam phase adjustable — this is the point of the rig

Mount the cam target on a **hub that can be loosened, rotated and re-clamped.**

Fixed phase proves the decoder works at one relationship. **Adjustable phase lets
you sweep it**, which is how you find the case where the cam pulse coincides with
the missing tooth — a real engine has exactly one such relationship, and whether
your decoder survives it should not be discovered in the truck.

## What this makes the rig

M3 *and* M4 on one fixture, with the mechanical relationship the engine actually
has. The VR board has four channels; crank and cam use two, leaving room to add
an OSS target on the same shaft later for the transmission work.


---

# Bench notes for when the sensors arrive

## Measure both coils first

Before anything is wired, **measure resistance across each sensor's two pins**
and write it down.

- It confirms VR rather than Hall — a coil reads a few hundred ohms to ~2 kΩ.
- It is the **source impedance in series with the VR board's 5 kΩ legs**, which
  sets how much signal actually reaches the MAX9926.

Mode A2's adaptive threshold absorbs the gain effect either way, but the number
is worth having when a reading later looks wrong.

## Label them now, not later

CKP and CMP use the **same two-cavity connector**, which is convenient for wiring
and a trap on a bench. Once both are off the desk and into the rig they are
indistinguishable at a glance.

Mark the sensors and both pigtails **before** the first one gets plugged in.

## Two sensor mounts, independently adjustable

Print `sensor_mount()` twice. The crank and cam air gaps are separate
experiments and their specs may differ — each mount bolts to the base on its own
slots, so they can be set and swept independently.

## The measurement that closes an open hardware question

With a real sensor on a driven wheel, **measure VR peak voltage against rpm**.

That answers the one item left open on the VR board: whether 5 kΩ in 0805 — good
to about **150 V of sensor output** — needs the second resistor per leg before
the board goes in the truck. See
[`../../docs/review-vr-v1.md`](../../docs/review-vr-v1.md).

Extrapolate from whatever speed the rig reaches to 6000 rpm; VR output scales
with tooth speed, so a measurement at 1200 rpm scales to a defensible estimate
for redline.


---

# The cam trigger bolt — two things to get right

A bolt is the right idea. Two adjustments before drilling.

## Captive head plus a nut is right — but point the head inward

**The captive arrangement is the correct call.** A hex pocket puts the plastic in
**compression between head and nut** instead of relying on threads cut into
printed plastic, and the pocket gives anti-rotation for free.

**Flip which end faces the sensor, though.** Two independent reasons point the
same way:

**Mechanically, the head belongs on the inside.** Centripetal force pushes the
bolt *outward*. With the head in an inner pocket it bears against that load and
**cannot pull through** — the retention is geometric rather than relying on the
nut. A head on the outside means the nut is the only thing holding it in.

**Magnetically, it halves the feature width:**

```
M8 hex head, outward    13.0 mm across flats   ← ~2× the sensor pole
M8 shank end, outward    8.0 mm                ← matches a 5–8 mm pole
```

So: **head in a hex pocket on the inside, shank protruding outward, nut on the
inside as a jam nut.** Nothing steel on the outside except the 8 mm shank end
— which is exactly the feature you want.

**Keep the outside clear of other steel.** A nut or washer on the sensor side
adds a second, wider feature right where the measurement happens.

Air gap is then set by protrusion — bolt length and washers under the head give
the coarse setting, and the sensor mount's slots do the rest.

## Why width matters at all

A VR sensor's pole piece is roughly **5–8 mm**. A feature much wider than the
pole does not give a stronger pulse — it gives **two**.

The output is `-N·dΦ/dt`. A feature about the width of the pole produces one
bipolar swing with a single zero crossing at its centre. A **wide** feature
produces a positive pulse as the leading edge arrives, a **flat region with no
output** while it fully covers the pole, then a negative pulse as the trailing
edge leaves — and Mode A2 arms on each peak and triggers on each crossing.

**M8 is fine once the shank faces out** — the 8 mm end lands right in the pole's
range. It is only the 13 mm head that would have given two edges.

Two edges per revolution is survivable in any case: a real engine's cam target
is often a large vane and the decoder picks one edge consistently. But one clean
pulse is simpler to reason about on a bench where the decoder is what you are
trying to prove, not work around.

## Check the bolt is actually magnetic

**A2 and A4 stainless is austenitic and non-magnetic** — the same trap as the
trigger wheel. Plain, zinc-plated or black-oxide steel is fine.

**Touch a magnet to it before fitting.** Thirty seconds, and the failure mode
otherwise is a cam channel that produces nothing while everything looks correct.

## Mount it radially, in the rim

Thread it **radially into the rim with the head facing outward**, not axially
into the face. Two reasons:

- The crank sensor looks radially at the wheel's teeth. A radial cam bolt means
  **both sensor mounts are the same part in the same orientation.**
- **Threading the bolt in or out trims the cam air gap** directly, independently
  of the sensor mount.

Retain it with a locknut or thread-lock. The loads are trivial — a 5 g bolt at
30 mm radius and 600 rpm cam speed is about **0.6 N** — but a fastener working
loose in a spinning disc is not worth the risk for the cost of a nut.

## If you balance it, use a non-ferrous counterweight

The obvious fix for the imbalance is an identical bolt opposite. **Do not** — it
is also steel, and the sensor will see it. **One pulse per cam revolution
becomes two**, and it will look exactly like a decoder fault.

Brass or aluminium if you balance it at all. At these speeds the imbalance does
not need correcting.


---

# The wheel is 24 mm keyed — hub, and what the keyway is really for

A 24 mm bore is a **shaft size, not a bearing size** — common bearing IDs step
8, 10, 12, 15, 17, 20, **25**. So the wheel does not go on its own bearings; it
goes on an adapter.

`wheel_hub()` does that: **24 mm keyed spigot → 8 mm clamped bore**, with a bolt
circle on the flange so the 20T crank gear mounts to the same part.

## The keyway is an angular datum, not a torque path

The torque is trivial. Accelerating a 0.7 kg wheel to 1200 rpm in two seconds is

```
T = Iα = 1.94e-3 × 62.8 = 0.12 N·m      →  10 N at the 12 mm bore radius
```

A printed key carries that without thinking about it.

**What the keyway actually buys is repeatability.** Remove the wheel and refit
it, and it returns to *the same angle*. On a rig whose entire purpose is
comparing decoded position against commanded position, that is the difference
between a datum and a guess.

### On this wheel the keyway is inline with the gap — the offset is zero

No protractor needed. `key_to_gap = 0`, and the hub cuts its index flute at that
angle, so the flute on the flange OD points at the missing tooth. Once the wheel
is bolted on the teeth all look alike; the flute is how you find the gap by eye.

The stepper drives the crank shaft 1:1, so steps map straight to crank degrees —
1.8°/step full, 0.1125° at 16× microstep. Home the stepper with the flute at the
sensor and **every commanded step count is a known crank angle**. The decoder can
then be checked on *absolute* position, not merely on whether it counts teeth and
finds *a* gap. That is the strongest test this rig can perform.

---

## The truck measures the same — so the rig is a calibration bench

Measured on the engine: the factory 5.4L puts the gap at TDC #1 as well. Rig and
truck share one datum, so `CKP_GAP_TO_TDC_DEG = 0` for both.

It stays a **named constant rather than a disappeared zero** — not out of caution
about the measurement, but because the decoder needs somewhere to put the sensor
and conditioner offsets below, and they are not zero.

What this buys is bigger than skipping a calibration step. Because the rig's
absolute angle now *is* the engine's absolute angle, anything measured on the
bench transfers directly. **The rig stops being a functional check and becomes
the instrument that calibrates the truck's timing**, with no engine running.

### Still to pin down: which edge of the gap

A 36-1 wheel has 10° tooth pitch, so the missing tooth leaves a **20° span**
between the tooth before it and the tooth after. "The gap is at TDC" is therefore
ambiguous by up to 20° until the convention is stated:

- centre of the gap, or
- last tooth before it, or
- first tooth after it

Worth writing down which one the measurement used, since the decoder never fires
on the gap anyway — it *syncs* on the gap and then counts teeth to the spark
angle, so the count has to start from a named tooth.

### The conditioner's switch point is not the tooth edge

A VR sensor outputs dΦ/dt, so flux peaks — and the output crosses zero — when a
tooth is **centred on the pole piece**, not when its edge arrives.

Mode A2 switches at exactly that zero crossing. Table 1 of the MAX9924–MAX9927
datasheet: **ZERO_EN = GND, INT_THRS = GND → zero crossing enabled, adaptive peak
threshold enabled.** Both blocks are live. The adaptive threshold (33 % of the
previous peak) only decides *whether* the channel arms; the edge itself comes from
the zero-crossing detector at **−6.5 / +10 mV**.

**So the trigger point is the tooth centre, and nothing moves it.** Not amplitude,
not rpm, not acceleration — scaling a waveform cannot shift where it crosses zero.
There is no amplitude-dependent timing term to calibrate out.

*(An earlier revision of this file claimed Mode A2 switched at ⅓ of peak and that
the rig would need to characterise the resulting offset against rpm. That was
wrong — the 33 % is the arming threshold, and there is no such offset.)*

Propagation delay is **50 ns** on the zero-crossing path. At 6000 rpm that is
**0.0018°** — three orders of magnitude below anything that matters, and below
what the rig could measure. It needs no sweep and no correction.

What the rig should still measure is **amplitude against rpm**, because that
decides whether the 5 kΩ series resistors are right and whether the ±40 mA input
limit is approached. That is a signal-integrity question, not a timing one.

---

# Rendering the model

`vr_rig.scad` is plain OpenSCAD — no libraries, and nothing newer than 2015-era
language features, so the distro package is sufficient.

```sh
sudo apt install openscad          # Mint 22.3 ships 2021.01, which is fine here
```

The Flathub build (`flatpak install flathub org.openscad.OpenSCAD`) is newer if
you want it, but this file asks nothing of it.

## GUI

Open the file, then **Design → Preview (F5)** to look at it and **Render (F6)**
before exporting. Edit `part =` at the top to choose what is shown; `"assembly"`
is a clearance check, not something to print.

## Batch — every printable part to STL

`render.sh` does the lot — `-D` overrides the `part` variable per invocation and
`xargs -P` spreads them across cores (`base` is the slow one at ~25 s):

```sh
cd hardware/vr-test-rig
./render.sh        # all 8 parts, binary STL, one per core
```

Note the quoting: `part` is a *string*, so the inner quotes have to survive the
shell. `-D part=wheel_hub` without them passes an undefined variable and renders
the assembly instead — silently, which is the annoying part.

**The committed STLs churn on every render.** OpenSCAD 2021.01 is not
byte-deterministic — rendering the same unchanged file twice produces different
files. So a git diff on `stl/` means nothing, and "are these current?" cannot be
answered by hash. **`vr_rig.scad` is the source of truth**; the STLs are a
convenience so the parts can be printed without installing OpenSCAD. Re-run
`render.sh` after any change and do not read anything into the diff.

Print quantities: **4 × bearing_block** (two shafts), **2 × sensor_mount** (crank
and cam), 1 each of the rest. **`base` is not printed** — it is a 320 × 240 board,
and the module is its drilling template. See [BOM.md](BOM.md). `hub` is the superseded 25.4 mm plain-bore version, kept only
for reference — **`wheel_hub` is the one that fits the wheel you bought.**

## The gears

`spur_gear(z)` generates real involute teeth — no library, no bought gears
needed to start. `part = "crank_gear"` and `"cam_gear"`.

The involute is built from `inv(a) = tan(a) - a`: at radius `r` the flank sits at
polar angle `inv(acos(rb/r))`, offset so it crosses the pitch circle at half a
tooth thickness. Below the base circle the involute does not exist, so the flank
runs radially to the root — correct here because at 20° PA the root is inside the
base circle for any `z < 41`, and both gears qualify.

Checked before committing: **20T clears the undercut limit** (17.1 teeth at 20°
PA, so no profile shift needed), and tip thickness is **1.39 mm on the 20T,
1.52 mm on the 40T** — teeth, not knife edges.

The split clamp's slit **stops at the gear face** so it never cuts through a
tooth; the boss grips the shaft and the gear body just goes along.

Print **teeth flat on the bed**, for the same reason the hub prints bore-up: the
profile is then an X-Y path rather than a layer stack.

See [BOM.md](BOM.md) for why module 2 and not module 1, and for the printed-now,
steel-later path.


---

# Rendered and checked

All eight parts export clean on OpenSCAD 2021.01 — no warnings, no errors — and
the gear geometry was verified against the numbers rather than eyeballed:

```
crank_gear   tip radius 22.000 mm   20 teeth   18.000 deg pitch
cam_gear     tip radius 42.000 mm   40 teeth    9.000 deg pitch
```

Bounding boxes match design intent to 0.02 mm, and `cam_target` was checked to
confirm the counterweight boss stays inside the 30 mm rim — it must never
protrude toward the sensor across a 1 mm air gap.

## Two things that check caught

**The key was not a key.** It spanned `wheel_bore/2 - key_d` to `wheel_bore/2`,
which is *inside* the spigot — it stood proud by 0.13 mm and would have engaged
nothing. The key has to run outward from the spigot surface into the slot cut in
the wheel's bore. Now 3.33 mm proud, as a DIN 6885 key on a 24 mm bore should be.

**`Volumes: 2` is not a fault.** Every split-clamp part reports it. CGAL counts
the unbounded outer volume alongside the solid, so a healthy single body reports
two. Confirmed by walking the mesh: one connected component. Worth knowing before
it sends you hunting for a stray fragment.

## Tessellation is deliberate, not default

`$fn = 64` everywhere cost minutes — the base's 192-hole M4 grid alone is 12 288
facets of subtraction. Chord error is `r(1 - cos(180/n))`, so a 4.4 mm clearance
hole at `$fn = 16` is off by 0.04 mm, under what the printer resolves. The
facets are now spent only where a fit depends on them:

| | | |
|---|--:|---|
| `hole_fn` | 16 | M3/M4 clearance |
| `$fn` | 32 | general |
| `fit_fn` | 64 | bearing pocket, shaft and sensor bores |
| `root_fn` | 120 | gear root circle |

`base` went from over two minutes to 26 s, with nothing given up that a 0.4 mm
nozzle could reproduce.


---

# Before the parts arrive

Four things, none of which need a single bought component.

## 1. Print it — this is the long pole

Twelve pieces from eight files. Orientation matters more than usual on two of
them (`wheel_hub` bore-axis vertical, gears teeth-flat) — see the table above.

## 2. Order the rest of the BOM

The wheel and both sensors are ordered. Everything in
[BOM.md](BOM.md) under **Drive** and **Shafts, bearings, hardware** is not.

## 3. Write the step generator

RP2040 PIO, and it can be written and tested with a logic analyser before any of
the rig exists. **Deceleration ramps are a firmware requirement, not a nicety** —
see [BOM.md](BOM.md): the wheel's 15 J has nowhere to go on a switching supply,
and no practical bulk capacitor absorbs a hard stop. **The valuable part is not constant-speed stepping** — it is a
programmed *cranking* profile, with the engine slowing against each compression
stroke and surging after it. A rig that only spins smoothly never tests the
regime where sync acquisition actually fails.

## 4. Measure the wheel BEFORE printing the base or brackets

The product photo (Dorman **917-060**, square-on so the ratios are trustworthy)
was measured, and it settles two things and unsettles a third.

### Confirmed: it is genuinely 36-1, and the keyway is on the gap

| | |
|---|---|
| Tooth pitch | **10.00°** → 36 positions |
| One wide space | **2.00× pitch** — the missing tooth |
| Missing tooth at | 102.7° |
| **Keyway at** | **105.0°** |
| **Apart** | **2.3°** — inside the measurement's own precision |

**So the datum holds.** The keyway really is on the missing tooth, which is what
makes `CKP_GAP_TO_TDC_DEG = 0` and the whole absolute-position method work.

It is also **already drilled** — four holes are visible. Wheel retention is
answered; the hub's bolt circle just has to match whatever they actually are.

### Corrected: the keyway is NOT a DIN 8 mm key

The slot measures **15 % of the bore diameter** wide and 19 % of the bore radius
deep. At a 24 mm bore that is **≈3.6 × 2.3 mm** — less than half the DIN 6885
8 × 3.3 this file previously assumed for a 24 mm shaft.

**A printed 8 mm key would simply not have entered the slot.** `key_w` and
`key_d` now carry the photo-derived figures, still marked MEASURE.

### Unsettled: the diameter

**bore / OD = 0.253**, measured square-on. "150 mm OD with a 24 mm bore" is
**0.160** — those cannot both be true:

| if | then |
|---|---|
| bore is 24 mm | **OD ≈ 95 mm** |
| OD is 150 mm | **bore ≈ 38 mm** |

`wheel_od` is set to 95 as the value a 24 mm bore implies, and the SCAD now
echoes the ratio and complains if the measured numbers disagree with the photo —
so a typo is caught before a print, not after.

### What that means for print order

`wheel_od` cascades: it sets the base slot, the crank sensor station, and the
shaft height that every upright and mount is cut to. At 95 mm the wheel clears
the base entirely and **the slot vanishes to zero** — which also means
`shaft_h = 60` is taller than needed, and a shorter upright is a stiffer one.

| safe to print now | wait for the wheel |
|---|---|
| `crank_gear`, `cam_gear` | `base` / `base_a` / `base_b` — slot |
| `cam_target` | `wheel_hub` — bore and keyway |
| | `bearing_block`, `sensor_mount`, `motor_mount` — all cut to `shaft_h` |

Print the gears and the cam target while the wheel is in transit. They depend on
nothing that is still in doubt.

## 5. Settle two things the drawings leave open

**Wheel axial retention — answered.** The photo shows the wheel is **already
drilled**, four holes. The hub's bolt circle needs matching to them (count,
diameter and radius), which is a parameter, not a redesign.

**Cam lobe phase.** With the keyway as a datum the M8 lobe's angle can be *set*
rather than discovered. Put it well away from the crank gap so the sync window is
unambiguous, then **record the angle here** — it becomes a known constant the
decoder can be tested against, exactly like the gap-to-TDC zero.
