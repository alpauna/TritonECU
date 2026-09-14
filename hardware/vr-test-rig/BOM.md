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
| 1 | Coupling, 5 → 8 mm | aluminium jaw/spider, D19 L25 | 6 |

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
| 1 | Shaft, crank | 8 mm h6 ground steel, 250 mm |
| 1 | Shaft, cam | 8 mm h6 ground steel, 150 mm |
| 4 | Bearing | 608ZZ (8 × 22 × 7) — two shafts, two each |
| 4 | Shaft collar | 8 mm bore, clamp type, for axial location |
| 1 | Bolt, M8 × 25 | the cam trigger lobe, head inward |
| 1 | Nut, M8 | + washer |
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
| 1 | `base` | flat |
| 4 | `bearing_block` | on its back — **two shafts now, not one** |
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
