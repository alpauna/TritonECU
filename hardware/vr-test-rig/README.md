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
