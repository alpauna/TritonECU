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

## The rig's zero is NOT the engine's zero — do not let this constant leak

The wheel is made with the gap at TDC #1 because that is the convenient
convention for a wheel sold to be configured. **The Ford 36-1 wheel on the truck
is under no such obligation**, and the factory CKP sensor sits where the block
casting put it, not where the convention would like it.

So there are really two numbers, and only one of them is zero:

| | gap → TDC #1 |
|---|---|
| This rig | **0°**, by construction |
| The 5.4L on the truck | **fixed, non-zero, and unmeasured** |

A decoder tuned on the bench until it reports the right angle, then moved to the
engine with that constant baked in, fires the plugs wrong by exactly the offset.
Spark at the wrong angle is not a debugging inconvenience — it is detonation, and
on a 5.4L it is pistons.

**So the offset is an explicit named constant, not an implicit zero.** Something
like `CKP_GAP_TO_TDC_DEG`, set to 0 for the rig and to the measured figure for the
truck, selected by build target. If the decoder ever computes an angle without
going through it, that is the bug.

### Measuring it on the truck, independent of any electronics

Do not trust a mark, and do not infer it from the old PCM's behaviour. Establish
TDC mechanically:

1. Pull #1 plug, fit a **piston stop**, and bring the crank up gently by hand
   until it touches. Mark the damper against a fixed pointer.
2. Rotate the other way until it touches again. Mark again.
3. **True TDC is exactly halfway between the two marks** — this cancels the error
   in where the stop happens to sit, which is why it beats a single mark.
4. With the damper at true TDC, scope the CKP and rotate to find where the gap
   falls. The angle between them is the constant.

The piston-stop bisection is the whole point: the stop's position does not need to
be known or repeatable, because it appears identically in both marks and
subtracts out.

### The cam sets which revolution, and it is also phase-referenced now

The cam runs 2:1, one revolution per two of the crank, so the CMP pulse is what
distinguishes compression from exhaust — the crank alone cannot. With the keyway
as a hard datum the M8 lobe's phase can be **set deliberately rather than
discovered**: put it well away from the gap so the sync window is unambiguous, and
record the angle here once it is set.

## Print it bore-axis vertical

**Concentricity between the 24 mm spigot and the 8 mm bore is wheel runout, and
runout is air-gap modulation.**

Printed with the axis vertical, both diameters are formed by the same X-Y motion
on every layer — concentric to printer X-Y accuracy, around ±0.05 mm. Printed on
its side, one diameter becomes a stack of layers and the other does not.

At ±0.05 mm on a 1 mm gap that is 5 % amplitude modulation once per revolution,
which **Mode A2's adaptive threshold is built to track** — and which a real
engine has anyway. Printed sideways it would be several times worse.

## Gear on the hub, or gear on the shaft?

The flange carries a 3 × M4 bolt circle, so the crank gear can mount directly to
the hub — one rigid assembly, no separate alignment.

**The alternative is a gear clamped to the shaft separately**, which gives axial
freedom. That matters here: at a 30 mm gear centre distance the cam shaft passes
through the plane of a 150 mm crank wheel, so the gear and the wheel must sit at
**different stations along the shaft**. Either arrangement works — just place the
gear away from the wheel, not beside it.

## Set `wheel_bore`, `key_w` and `key_d` from the real wheel

Defaults are 24.0 / 8.0 / 3.3 mm — the DIN 6885 sizes for a 24 mm shaft. **Check
them against what actually arrives**; aftermarket wheels are not obliged to be
standard, and a key that does not fit is a reprint rather than a redesign.
