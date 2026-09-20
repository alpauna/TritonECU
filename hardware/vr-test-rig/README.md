# 36-1 VR trigger wheel test rig

A motor-driven bench rig for **M3 crank sync** — real VR sensor, real trigger
wheel, known shaft position.

`vr_rig.scad` holds every printed part. Set `part = "..."` at the top and render
one at a time.

---

## ⚠ Bearing blocks: print the fit gauge first

**The first PETG set split.** Bearings pressed in, and all but one delaminated
within the hour.

`brg_press` was **−0.05**, which looks like 0.05 mm of interference and is
harmless at 2.8 MPa. **But an FDM bore prints undersize** — extrusion overlaps
on the inside of a curve, and a horizontal bore sags at its crown, so 0.2–0.4 mm
on diameter is routine. That turns 0.05 into 0.25–0.45, and the hoop stress with
it:

| Real interference | Hoop stress | |
|--:|--:|---|
| 0.05 mm | 2.8 MPa | fine |
| 0.35 mm | 19.3 MPa | marginal |
| **0.45 mm** | **24.9 MPa** | **past PETG's ~22 MPa interlayer** |

**And interlayer is the number that matters.** At the 3 and 9 o'clock positions
of a *horizontal* bore the hoop stress runs in **Z**, and the radial crack plane
there contains the bore axis and the radius — **which is the layer plane**. The
block doesn't crack, it **delaminates**, splitting out through the 4 mm side wall
at bore mid-height, right where the gusset root sits as a stress riser.

**The one that survived is bore-diameter lottery, not margin** — it printed
perhaps 0.05 mm looser than its siblings.

### A thicker wall is the wrong fix

Everyone reaches for it first. It doesn't work: a thicker hub is a **stiffer**
hub and develops proportionally more contact pressure for the same interference.

| Wall | Block width | Hoop stress |
|--:|--:|--:|
| 4 mm | 36 mm | 19.3 MPa |
| 8 mm | 44 mm | **18.2 MPa** |

Doubling the wall buys **6 %**, for 8 mm of extra width.

### The fix: clearance plus retaining compound

`brg_press` is now **+0.30** — the pocket is modelled *oversize*, aiming at a
small clearance once the print shrinks it. The bearing is held by **Loctite
638/609**, which wants 0.05–0.25 mm of gap and puts **zero hoop stress** into the
plastic. The shoulder still locates it axially.

```bash
openscad --export-format binstl -o stl/fit_gauge.stl -D 'part="fit_gauge"' vr_rig.scad
```

**Print `fit_gauge` first.** Three pockets at +0.15 / +0.30 / +0.45, in the *same
orientation* as the real block — horizontal and vertical bores do not shrink
alike. Try a 6001 in each, and set `brg_press` to whichever slides in with a
whisker of play. **Printers differ by more than the failure margin does.**

### The rule this leaves behind

Swept the rest of the rig: **every other fit is clearance** (`shaft_dia + clr`,
`wheel_bore − clr`), and **every other load-carrying bore prints with its axis
vertical** — hub, wheel hub, cam target, and the hub's split clamp all put their
hoop or bending stress *in-layer*. The bearing block was the only part that got
**both** wrong at once, which is why it was the only one that failed.

> **Two questions for any new part that takes a bearing, a bush or a pressed pin:**
> 1. Is the load **across layers**? A bore's hoop stress is in Z at its 3 and 9
>    o'clock positions whenever the **bore axis is horizontal**.
> 2. Is the interference **real**, or is it the modelled number? They are not the
>    same, and the gap between them is bigger than the margin.

> **The other lever, if you want belt and braces:** print the block with the
> **bore axis vertical**. The hoop stress then lies entirely in-layer — ~50 MPa
> instead of ~22, a **2.3× gain** — at the cost of support under the foot flange.


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

### ~~On this wheel the keyway is inline with the gap — the offset is zero~~

> **Falsified by the part.** `key_to_gap = 0` came from a vendor product photo.
> With the wheel in hand the keyway lines up with **the gap between the missing
> tooth and the next tooth** — the midpoint between two tooth centres, so
> **5.00° exactly, whatever the tooth width.** See
> [the correction below](#corrected-the-keyway-sits-half-a-pitch-from-the-missing-tooth).

The hub cuts its index flute at `key_to_gap`, so the flute on the flange OD
points at the missing tooth. Once the wheel is bolted on the teeth all look
alike; the flute is how you find the gap by eye.

The stepper drives the crank shaft 1:1, so steps map straight to crank degrees —
1.8°/step full, 0.1125° at 16× microstep. Home the stepper with the flute at the
sensor and **every commanded step count is a known crank angle**. The decoder can
then be checked on *absolute* position, not merely on whether it counts teeth and
finds *a* gap. That is the strongest test this rig can perform.

---

## The truck measures the same — so the rig is a calibration bench

Measured on the engine: the factory 5.4L puts the gap at TDC #1 as well. Rig and
truck share one datum, so `CKP_GAP_TO_TDC_DEG = 0` for both.

> ⚠ **This claim does not survive the wheel being identified.** The rig's wheel
> is a Dorman **917-060**, cast into the part. It *is* a modular V8 reluctor —
> Dorman lists **2002-2010 F-150 5.4** among others — but two things still break
> the shared datum: the applications **start at 2001 and the truck is a 1999**,
> and a customer review of this exact part reports that **its teeth do not match
> the OEM wheel**, causing timing codes and rough running.
>
> What the rig still is: the best available test of *decoder behaviour* — sync
> acquisition, cranking profiles, tooth counting, noise. What it is **not**, until
> the truck is measured separately, is the instrument that calibrates the truck's
> timing. And the older half of this claim has the same problem it always had:
> **how the engine figure was derived is not written down anywhere**, so it
> cannot be audited now that one of its inputs has moved.

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

~~**So the datum holds.** The keyway really is on the missing tooth, which is what
makes `CKP_GAP_TO_TDC_DEG = 0` and the whole absolute-position method work.~~

> **Superseded — and the 2.3° was the clue, not the noise.** The part says the
> keyway sits in the gap *after* the missing tooth, **5.00°** from its centre —
> half a pitch. The photo said 2.3°. Both readings sighted a radius outward from
> the keyway, which is the noisy end of the wheel by a factor of 3–5. See
> [the correction](#corrected-the-keyway-sits-half-a-pitch-from-the-missing-tooth).

It is also **already drilled** — four holes are visible. Wheel retention is
answered; the hub's bolt circle just has to match whatever they actually are.

### Corrected: the keyway sits half a pitch from the missing tooth

**Measured on the physical wheel, 2026-09-19**, and corrected the same day after
the first look turned out to be *from the back of the wheel*:

> The keyway lines up with **the gap between the missing tooth and the next
> tooth**.

#### 5.00°, and this time the tooth width does not matter

That gap runs from the missing tooth's edge to the next tooth's edge, so its
centre is the **midpoint between two tooth centres** — one at the missing
position, one a pitch away. Midpoint of 0° and 10.00° is **5.00°**, and the tooth
width cancels:

```
gap spans   w/2  ..  pitch - w/2          (w = tooth width)
centre    = (w/2 + pitch - w/2) / 2 = pitch/2 = 5.00 deg   for any w
```

`key_to_gap = 5.0` is therefore **exact and duty-free**, where the first reading
— "the rear edge of the tooth just forward" — gave 7.5° *and needed the tooth
width to say so*. The rear edge is the far boundary of this very gap, so the two
readings are the same feature described twice; the second one is simply the
better description, because the centre of a gap is a stronger datum than its
edge.

The remaining uncertainty is the **width of the gap the keyway sits in**: 10 − w,
so **±2.5°** at 50 % duty. That is now the *only* thing tooth width is needed
for, and it bounds the answer rather than setting it.

> **TDC falls between two tooth positions, not on one.** 5.00° is half a pitch,
> so if the keyway is the crank's TDC datum then TDC lands exactly midway between
> tooth centres — the furthest point from any edge. That is a sensible thing to
> design on purpose, and a strange thing to happen by accident.

#### Sign, settled — by the engine rather than by the wheel

The rig's own convention was ambiguous and the first reading got it backwards
(the wheel was face-down). The fix is to stop defining it geometrically:

> **`key_to_gap` is the crank rotation from the gap passing the sensor until the
> keyway passes the sensor.** Always positive. **+5.00°.**

That is operational — it names two events in the order they happen, so it cannot
be mirrored by picking up the wheel the other way round. It is also exactly how
the part was read: *the missing tooth goes by, and TDC is coming up.*

⚠ The `.scad` still needs a geometric sense for the index flute, and **that one
does depend on which way the rig spins.** It is flagged in the file.

#### The part is marked — it IS the Dorman, and the inference above was wrong

The front face is cast **`FRONT 917-060 53025 TAIWAN`**. It is the Dorman
917-060, exactly the part the `.scad` was dimensioned from.

> ~~*"A keyway that falls on the crank's TDC datum is a factory part. This is the
> Ford 5.4L crank trigger wheel, not the Dorman."*~~ **Wrong, and the flaw was in
> the premise:** it equated *aftermarket* with *universal*. The 917-060 is an
> **OE-replacement reluctor for a named application**, not a blank broached to
> fit a shaft — so its keyway is cut to put the gap where that engine's ECU
> expects it. The keyway relating to TDC is exactly what a direct-fit replacement
> part does, and it needed no Ford casting to explain.

**It is not a Small Block Ford part either — that was the listing's third error.**
Dorman's own catalogue puts 917-060 on **modular V8s**: 2001-2010 F-150 4.6,
**2002-2010 F-150 5.4**, Crown Victoria, Mustang, Explorer, Expedition,
Navigator, Mountaineer. **35 teeth**, steel, cross-referenced to OE
**XW1Z-12A227-AC**. The ~135 mm we measured is a modular reluctor's size, and it
agrees.

So the engine-family objection is withdrawn. **Two better ones replace it.**

| | |
|---|---|
| **5.00° is the rig's `key_to_gap`** | ✅ measured, and it is this wheel's |
| **5.00° is the truck's `CKP_GAP_TO_TDC_DEG`** | ❌ **still no** — for the two reasons below |

**First: the applications start at 2001, and the truck is a 1999.** Every listed
year is 2001 or later. Whether the 1999 5.4L uses this reluctor at all is
**[CONFIRM]**, and it is not safe to assume — 2001 is exactly the kind of
boundary a crank-trigger revision lands on.

**Second, and this is the one that matters:** a customer review of this exact
part reports

> *"The teeth on the wheel don't exactly match up to the OEM one, this matters
> because this is where the computer reads off the crank sensor. Use this
> pulsator ring and your engine will have timing codes and run rough."*

#### That review may be describing the number we measured

The README's prior belief was that **the factory wheel puts the gap at TDC** —
`key_to_gap ≈ 0`. This Dorman measures **5.00°**. That is **exactly half a tooth
pitch**, and half a pitch of crank-angle error is precisely the magnitude that
makes an engine *run badly and set codes* rather than *not start*:

| error | symptom |
|---|---|
| a whole pitch, 10° | gross; likely no-start or violent misfire |
| **half a pitch, 5.00°** | **runs, runs rough, sets timing codes** ← the review |
| a degree or two | probably unnoticed |

**This is a hypothesis, not a conclusion** — "the teeth don't match" could also
mean tooth width, profile or runout. But it is testable in one reading: **measure
the OEM wheel's key-to-gap.** If it comes back near 0 while this one is 5.00°,
the review is explained, and this project measured a documented defect without
knowing the defect existed.

#### The operational rule, either way

> ⚠ **Do not fit this wheel to the truck.** It is a bench part. Whatever the
> cause, a part with a user-reported timing defect does not belong on the vehicle
> the ECU is being developed against — a wheel that makes the *factory* PCM run
> rough would contaminate every comparison against it.

**And TritonECU is immune to the defect in a way the factory PCM is not**, which
is worth noticing. The OEM PCM has gap-to-TDC baked in; ours has
`CKP_GAP_TO_TDC_DEG` as a **named, calibratable constant** — the decision
[recorded above](#the-truck-measures-the-same--so-the-rig-is-a-calibration-bench)
to keep it a named constant rather than a disappeared zero. Calibrate to whatever
wheel is actually fitted and a 5° offset is a number, not a fault. That immunity
is exactly why the constant must be **measured on the truck, with the truck's own
wheel**, and never inherited from the bench.

#### The rig does not care — and is arguably better off

A wheel whose gap sits half a pitch from where the factory puts it is **still a
perfectly good 36-1 wheel**. The rig tests *decoder behaviour*: sync acquisition,
cranking profiles, tooth counting, noise. None of that depends on where TDC is.

In fact a non-zero offset makes the **better** test article. A bench that always
calibrates to zero never exercises the offset at all, so any code path that
silently assumes `CKP_GAP_TO_TDC_DEG == 0` would pass every test and fail on the
truck. **This wheel forces the constant to be real.**

#### `FRONT` closes the mirroring problem permanently

The face-down reading happened because nothing on the wheel said which way it
faced. **Something does** — `FRONT` is cast into it. Every future reading has an
unambiguous reference, and the geometric sense can finally be written down.

**Given: the marked FRONT face, and the engine turns clockwise seen from the
front.** A fixed sensor meets features in *counter-clockwise* order — with the
wheel turning clockwise, the feature that arrives next is the one currently
counter-clockwise of the sensor. The gap arrives first and the keyway 5.00°
later, so the keyway is 5.00° **counter-clockwise** of the gap:

> **On the face marked `FRONT`, sweeping clockwise, the keyway comes first and
> the missing tooth 5.00° after it.**

That is a one-glance check, and it is the form the `.scad` needs for the index
flute.

#### What 5.00° is *not*: it is not `CKP_GAP_TO_TDC_DEG`

This is the wheel's half of the answer, and it is worth being precise about the
other half:

```
CKP_GAP_TO_TDC_DEG  =  key_to_gap  +  angle( sensor , keyway-at-TDC )
                       ^^^^^^^^^^     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                       5.00 deg,      set by where the sensor BOLTS TO
                       the wheel      THE BLOCK. Not a wheel property.
```

The gap is detected when the gap passes **the sensor**; TDC happens when the
crank reaches a particular orientation. Those coincide only if the sensor is
mounted exactly where the keyway points at TDC, which would be luck. So the
sequencing claim — *gap first, TDC second* — is right and is the useful half,
but the magnitude still needs the engine.

**And the engine settles it in one measurement, with no protractor:** bring #1 to
TDC on a piston stop, then look at what is in front of the CKP sensor. If the gap
has just gone past by about 5°, the whole chain is consistent and
`CKP_GAP_TO_TDC_DEG` is confirmed small. If the gap is somewhere else entirely,
the second term above is not zero and this is exactly how you find out.

#### Why the old photo said 2.3° — the keyway is the noisy end

Both the photo reading and the first physical reading sighted a radius *from the
keyway out to the rim*, and **that is backwards.** A radial line's angular error
is `δ/r`, so a linear error costs angle in inverse proportion to how far out the
feature sits — and the keyway is the innermost feature on the wheel:

| feature | radius | 1 mm error costs |
|---|--:|--:|
| **keyway** | ~14–22 mm | **2.6–4.1°** — up to 0.41 pitch |
| tooth at the rim | ~64–86 mm | 0.7–0.9° — under 0.09 pitch |

**3–5× noisier at the keyway end**, which is where both readings started. It also
explains how a wheel could be read face-down without the error being obvious: at
that noise level, 2.3° and 5.0° and 7.5° all look like "about on the gap".

#### The rig can measure this on itself, to 0.1°

None of the above needs a protractor, and none of it needs the flute to be right
first. `key_to_gap` only has to be *known*, not *correct*:

1. Cut the flute at 5.00° and print the hub.
2. Mount the wheel, home the stepper against the flute.
3. Spin it and take a tooth log — `CrankSensor::startToothLog()` already exists.
4. The gap's position relative to home falls out at **0.1125°** per step at 16×
   microstepping.

That is **23× finer than sighting it by eye**, and it turns a printed feature
into a measured constant. Which is the real lesson:

> **The index flute should never have been the datum.** It is an eyeball aid for
> finding the gap on a wheel whose teeth all look alike. The moment the decoder's
> absolute-angle check inherits its zero from a printed flute, a systematic error
> in that flute is subtracted out of every test the rig runs — the rig would
> confirm its own mistake. The constant belongs in firmware, measured.

### The OD is **~135 mm**, not 171.45 — the vendor listing is wrong by 25 %

A third photo put the **whole template** in frame on a light background, which is
what the first two were missing. Two independent scales now sit in the same
image:

| scale reference | | |
|---|--:|--:|
| Plate outline | 157 × 173 mm | known |
| **Pin-field slot** | **101.4 mm** | known, and *local* to the plate rather than at its edges |
| **The wheel** | **~13.5 grid squares** | **≈ 128–141 mm** |

`wheel_od = 171.45` would be **17.1 squares.** It is not close.

> Two earlier attempts at this got it wrong in opposite directions and both are
> struck: *"the template proves it without measuring anything"* assumed a plate
> width that ran off frame, and the ratio that replaced it leaned on a pixel
> estimate of that same bad frame. **The fix was not better arithmetic, it was a
> better photograph** — put the whole reference in the picture.

**135 is still an estimate.** Caliper it before printing any rig part: this one
number now drives the bore and keyway as well as the geometry.

### The photo's *ratios* survived what its absolute dimension did not

The product photo gave bore/OD = **0.253**, and `wheel_bore` was set to
0.253 × 171.45 = **43.4**. The ratio was never the problem — **a ratio is
scale-free, so it cannot be wrong about size.** It was multiplied by the wrong
number.

The `.scad` now derives them, so measuring the OD propagates by itself:

```
wheel_bore = 0.253 * wheel_od        43.4  ->  34.2
key_w      = 0.15  * wheel_bore       6.5  ->   5.1
key_d      = 0.19  * wheel_bore / 2   4.1  ->   3.25
```

⚠ **The old `wheel_hub` spigot would not have entered the wheel** — 43.4 against
a ~34 mm bore is 9 mm of interference on the diameter. That part must be
re-rendered, not just re-checked.

### And the rig's geometry inverts — the wheel no longer reaches the base

| | at 171.45 | **at 135** |
|---|--:|--:|
| Wheel dip below shaft height | 25.7 mm | **7.5 mm** |
| Rim to ground | 16.3 mm | **34.5 mm** |
| **Base wheel slot** | 114.4 mm | **0 — not needed at all** |

The slot is gone. [Below](#two-consequences-and-one-of-them-is-not-obvious) this
file argues at length that the wheel is *bigger* than assumed, so the shaft had
to be **dropped** until the wheel ran *through* a slot in the base — and that the
slot was "the plate's weakest section". **All of that was reasoning from the bad
OD.** At 135 mm a 60 mm shaft holds the rim 34.5 mm clear of the ground with the
base untouched, and `shaft_h` can now come *down* for a shorter, stiffer upright
rather than being held up to clear a slot that does not exist.

### RESOLVED — it is a modular part, and the listing was wrong twice

Dorman's catalogue: **917-060**, steel, **35 teeth**, OE cross
**XW1Z-12A227-AC**, fitting 2001-2010 F-150 4.6, **2002-2010 F-150 5.4**, Crown
Victoria, Mustang, Explorer, Expedition, Navigator, Mountaineer. The ~135 mm we
measured is a modular reluctor's size and **corroborates the catalogue against
the listing** — which had both the OD and the engine family wrong.

**But the calibration-bench claim does not come back**, for two reasons that have
nothing to do with engine family: the applications begin at **2001** and the
truck is a **1999**, and a review of this part reports its teeth do not match
OEM. Both are covered
[above](#that-review-may-be-describing-the-number-we-measured).

> **It is the Dorman**, and the part says so: `FRONT 917-060 53025 TAIWAN` is
> cast into the front face. So the photo above is a photo of *this* wheel, the
> 2.3° and the 5.00° are two readings of one part, and the part wins.

### Corrected: the keyway is NOT a DIN 8 mm key

The slot measures **15 % of the bore diameter** wide and 19 % of the bore radius
deep. At a 24 mm bore that is **≈3.6 × 2.3 mm** — less than half the DIN 6885
8 × 3.3 this file previously assumed for a 24 mm shaft.

**A printed 8 mm key would simply not have entered the slot.** `key_w` and
`key_d` now carry the photo-derived figures, still marked MEASURE.

### ~~Settled: the vendor's own listing~~ — the listing does not describe the part

> **Struck.** Measured against the carrier-template grid the OD is **~135 mm**,
> not the listed 6-3/4" / 171.45 — wrong by 25 %. See
> [the measurement](#the-od-is-135-mm-not-17145--the-vendor-listing-is-wrong-by-25-).
> The bore and keyway derived from it were wrong by the same factor, and the
> listing's *"Small Block Ford"* application was wrong too — Dorman's own
> catalogue puts this part on **modular V8s**, not an SBF.

~~**6-3/4" OD and .120" thick** — a Small Block Ford 36-1 that sits between the
harmonic balancer and the crank pulley. In millimetres:~~ *(Neither figure nor
the engine family survived. Dorman's catalogue: a **modular V8** reluctor,
**35 teeth**, OE **XW1Z-12A227-AC**.)*

| | was assumed | ~~"actual"~~ | **measured** |
|---|--:|--:|--:|
| OD | 150 | ~~171.45~~ | **~135** |
| Thickness | 5.0 | 3.05 | still from the listing |
| Bore | 38 (guess) | ~~43.4~~ | **~34.2** — 0.253 × OD, the ratio was fine |

**The lesson is which number to trust.** The photo gave *ratios* and the vendor
gave an *absolute*, and it was the absolute that failed. A ratio is scale-free,
so it cannot be wrong about size — and multiplying a good ratio by a bad
dimension is precisely how 43.4 happened.

### Two consequences, and one of them is not obvious

**The wheel is bigger, so it dips deeper.** An 85.7 mm radius against a 60 mm
shaft height puts the rim **25.7 mm below the base top** — leaving barely **6 mm
to the ground** on the old 24 mm feet.

**The fix is taller feet, not a taller shaft.** Both would clear it, but
`shaft_h` is what every upright is cut to, and bracket stiffness goes as `1/h³`:
raising the shaft from 60 to 70 would cost **~30 % of the brackets' stiffness**
for nothing. Raising the feet costs nothing at all. `foot_h` is now **34 mm**,
giving 16 mm of clearance.

**The slot and the plate both grew** — a 114 mm slot, and the crank sensor now
stands off at y = 109, so `plate_w` goes 240 → **260**. Still 300 × 260, which a
320 mm bed takes whole.

### What that means for print order

With OD and thickness now published, only the **bore** is still derived. It
affects `wheel_hub` alone — the spigot, the keyway and the clamp — so that is the
one part still worth holding.

| safe to print now | gated, and on what |
|---|---|
| `crank_gear`, `cam_gear` | `wheel_hub` — wheel bore + keyway |
| `cam_target` | `sensor_mount` ×2 — **sensor barrel length** |
| `bearing_block` ×4 | `base` — plate width follows the sensor station |
| `motor_mount` | |

The bearing blocks and motor mount are cut to `shaft_h` alone, so they are
settled. The base is **back on the gated list** — its width is now driven by
where the sensor has to stand.

## 5. The sensors are flange-mounted, which broke the mount design

The product photos show what these actually are: an **O-ring'd barrel that drops
into a bore, with a single bolt through an ear beside it**. Not a plain cylinder.
`sensor_mount` was a pinch clamp, and a pinch clamp is the wrong object.

**The consequence is not cosmetic — insertion depth is fixed by the flange.**
The sensor cannot be slid in or out to set the air gap, because the flange face
bottoms on the mounting surface. So:

- The mount is a **plate normal to the sensor axis**: the barrel passes through
  it, the ear lies flat on its outboard face, and the bolt goes in alongside.
- **The bolt runs PARALLEL to the barrel.** The *flange plate* is what sits
  perpendicular to the barrel, and a bolt normal to that plate is therefore
  parallel to it. An intermediate revision of this file read "90 degrees to the
  barrel" as describing the bolt and made it crosswise — that was wrong, and the
  bolt would have passed through the sensor body.
- **It is an M8**, not the M6 first assumed.
- **`gap_slot` went 14 → 30 mm.** The slotted feet are now the *only* air-gap
  adjustment, and they also have to absorb the uncertainty in barrel length.
- **The station formula was wrong.** It positioned the mount by its own width;
  with a flange sensor the tip lands `sensor_barrel_len` from the mounting face,
  so the old formula would have driven the barrel tip **8 mm inside the wheel**.

### The flange offsets are measured; one dimension is still missing

From the barrel's edge to the bolt centre: **CKP 14.0 mm, CMP 12.7 mm**. Adding
the 7.15 mm barrel radius gives the offset from the barrel *axis*:

| | edge → bolt | **axis → bolt** |
|---|--:|--:|
| CKP | 14.0 mm | **21.15 mm** |
| CMP | 12.7 mm | **19.85 mm** |

They differ by only 1.3 mm, so **one slotted mount takes both** — the bolt slot
spans 19.85 to 21.15 with room either side, and takes an **M8**.

The ear is offset straight *up* from the barrel in the model. The sensor turns
freely in its bore, so that direction is ours to pick, and up keeps the mount
narrow in X rather than widening the base.

### The pad is sized from the ear, not from its bolt

Both ears are **19 mm wide with a rounded tip**, and reach **25.4 mm (CKP)** and
**19.1 mm (CMP)** past the barrel's edge — so 32.55 and 26.25 mm from its axis.
The seating pad is sized to the larger, which makes the mount **47.0 × 46.0 ×
99.6 mm**.

**The bolt is not centred on the tip radius on either sensor**, which is why the
pad had to be sized from the reach rather than inferred from the bolt:

| | bolt from axis | ear tip from axis | ear past the bolt |
|---|--:|--:|--:|
| CKP | 21.15 | 32.55 | 11.4 mm |
| CMP | 19.85 | 26.25 | 6.4 mm |

### The crank figures cross-check; the cam's still do not

A later measurement gave **6 mm from the bolt hole's outer edge to the flange's
outer radius**. That is an independent route to the same number, and on the crank
sensor it lands:

| | bolt centre | tip via the 6 mm rule | tip as stated | differ |
|---|--:|--:|--:|--:|
| **CKP** | 21.15 | 31.15 | 32.55 | **1.4 mm** |
| CMP | 19.85 | 29.85 | 26.25 | **3.6 mm** |

So the crank ear is confirmed from two directions and the pad (sized to 32.55)
covers it. **The cam's numbers still disagree with themselves**, in the same
direction as the tip-radius check above — its stated reach is shorter than its own
bolt position implies. Worth one more look, though it changes nothing: the pad is
sized to the larger ear and the bolt slot spans both.

### A tape reading with a different datum is not a contradiction

The flange top measured **1.875″** against a tape standing on the bench. If the
sensor were resting on its *barrel*, a 32.55 mm tip would read **1.563″**. The
7.9 mm difference is the connector stalk holding it up off the table — a
different zero, not a different flange. Worth stating because it looks like a
9 mm error until you ask what the tape was measuring from.

### Flange face → sensing tip: 57 mm and 38.1 mm

Those were recorded first as "body length". They are the **barrel**, which is what
positions the mount — and 57 mm is nearly twice the 30 that was assumed.

**Two things follow, and neither is cosmetic.**

**The boss went 10 → 30 mm.** At 10 mm a 57 mm barrel would hang **47 mm into
free air** off a single thin plate. On the engine that barrel sits in a deep bore;
on a rig it has nothing. A 30 mm boss supports over half of it, costs only
plastic, and pulls the mount 10 mm inboard — which the plate width is grateful
for.

**The plate had to become asymmetric.** A 57 mm barrel puts the crank sensor's
outboard edge near **+152 mm**. A symmetric plate answers that with **334 mm**,
past a 320 bed. But the −Y side only needs 105 (the cam gear reaches −102), so:

```
        Y from -105 to +157   =  262 mm
```

**Shifting the plate rather than growing it** keeps the whole rig on a 320 bed —
300 × 262. Symmetry was costing 72 mm for nothing.

## 5. Settle two things the drawings leave open

**Wheel axial retention — answered.** The photo shows the wheel is **already
drilled**, four holes. The hub's bolt circle needs matching to them (count,
diameter and radius), which is a parameter, not a redesign.

**Cam lobe phase.** With the keyway as a datum the M8 lobe's angle can be *set*
rather than discovered. Put it well away from the crank gap so the sync window is
unambiguous, then **record the angle here** — it becomes a known constant the
decoder can be tested against, exactly like the gap-to-TDC zero.


---

# Check models: print the sensors and hold them up

`part = "sensor_ckp"` and `"sensor_cmp"` model the two VR sensors — and they are
built from **the same parameters the mount is**, on purpose.

That is the entire value. If the printed model does not match the real sensor,
then the mount is wrong *in the same way*, because both read from the same
numbers. It is a 20 g print that tests every dimension in this file at once:

| | CKP | CMP |
|---|--:|--:|
| Barrel Ø | 14.3 | 14.3 |
| Barrel length, flange face → tip | 57.0 | 38.1 |
| Flange reach from barrel axis | 32.55 | 26.25 |
| Bolt centre from barrel axis | 21.15 | 19.85 |
| Flange width | 19.0 | 19.0 |
| Bolt | M8 | M8 |
| **Printed envelope** | **70.5 × 20.3 × 63.0** | **64.2 × 20.3 × 44.1** |

**What to compare, in order of how much it costs to be wrong:**

1. **Barrel length.** It sets where the sensor stands, and through that the base
   plate width. Wrong here and the base reprints.
2. **Flange reach and bolt position.** Wrong here and only `sensor_mount`
   reprints.
3. Flange thickness and the connector tails — **these are guesses**, marked as
   such in the file. They affect nothing structural; the tail is there so the
   thing reads as a sensor when held next to one.

### Corrected before the first print, from a look at the render

Three errors, caught by comparing the model to the real part on screen rather
than in the hand — which is the cheaper end of the same idea:

**The flange does not stop at the barrel.** It carries on past it with the same
radius as the bolt end, so the paddle is rounded at *both* ends. Measured from
the barrel's outer surface to the flange's far edge: **6 mm on the crank, 3 mm on
the cam.** The first model hulled from a circle *at* the barrel, which cut that
off.

**Nothing projects behind the flange face.** The first model had a connector
block standing proud of the back. Both tails lie **flush, in the flange's own
plane**.

**The two connectors are nothing alike**, which took a couple of passes:

- **Crank** — **one straight leg at 90° to the ear**, lying flush in the flange's
  plane. The *"L" is the ear and that leg together*, not a leg that bends again.
  An intermediate version added a second leg off the first and pointed it 180°
  the wrong way.
- **Cam** — **no side tail at all.** Its connector is a **14 mm socket on the
  flange's back face, coaxial with the barrel and pointing 180° away from it**.

| | CKP | CMP |
|---|--:|--:|
| Envelope | 45.7 × 42.0 × 63.0 | 36.4 × 19.0 × 58.1 |
| Z span | −6 … 57 | **−20 … 38.1** |

On the crank the ear reaches +32.5 in X and the tail +32.5 in Y, so the L is
square and symmetric about the barrel — an easy thing to check by eye.

### The cam socket points away from the mount, which is lucky

It protrudes 14 mm behind the flange face, and the flange seats on the mount's
**outboard** face. Since the socket runs opposite the barrel, it heads *away* from
the plate into free air — so **no relief is needed**. Had it pointed the other way
it would have fouled the mount and wanted a through-hole, which is exactly the
sort of thing a check model is for.

Print flange-down, no supports needed. The barrel's O-ring groove and tapered tip
are cosmetic, included only so the shape reads correctly in the hand.
