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
