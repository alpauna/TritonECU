# Output driver parts — ignition and injection

Both loads are dumb and low-side switched: permanently at 12 V on one side, the
driver grounds the other. See `custom-board.md` for why their clamping
strategies are opposite.

---

## Ignition: onsemi **ISL9V3040** (EcoSPARK)

Purpose-built ignition IGBT with the clamp integrated — which is the whole
point, because an ignition primary must be *allowed* to fly back to a few
hundred volts, then stopped short of destroying the device.

| Parameter | Value |
|---|---|
| Clamp voltage | **400 V** |
| Collector current | **17 A** |
| V<sub>CE(sat)</sub> | 1.58 V |
| Self-clamped inductive switching energy | **300 mJ** |
| Packages | TO-220 (`P3`), TO-263/D²PAK (`S3S`), TO-252/DPAK (`D3ST`), TO-262 |
| Automotive temp variant | `-F085C` suffix |

Against a coil drawing **6–10 A peak**, the 17 A rating is comfortable.

### Check the energy margin against your actual coil

This is the number that decides whether the part survives, and it depends on
the coil rather than the driver:

```
E = ½ · L · I²
```

A COP primary of ~5 mH at 8 A stores **160 mJ** — about 1.9× margin under the
300 mJ rating. But 6 mH at 10 A is **300 mJ**, exactly at the limit and
therefore not acceptable.

**[CONFIRM]** the primary inductance of the actual coils and set dwell for a
peak current that keeps stored energy comfortably under 300 mJ. Dwell time is
under firmware control, so this is a calibration constraint as much as a parts
one — and `SparkScheduler::maxRpmForDwell()` already exposes the other end of
the same tradeoff.

If the measured energy is marginal, the EcoSPARK family has higher-energy
members; staying within the family keeps the footprint and clamp behaviour.

### Gate drive

**[CONFIRM]** the gate threshold from the datasheet. IGBTs of this class
typically want **V<sub>GE</sub> ≈ 5 V or more** for the quoted V<sub>CE(sat)</sub>,
so a 3.3 V GPIO is unlikely to drive it properly — which is exactly the case
for the gate drivers already planned. Under-driving an IGBT does not stop it
working, it makes it dissipate, so this fails as heat rather than as an
obvious fault.

Plus the 10 kΩ gate pulldown, and a pulldown on the driver input.

---

## Injection: Diodes Inc **ZXMS6005DGQ** (IntelliFET)

A self-protected low-side switch rather than a bare MOSFET, and it removes
several parts from the injector stage.

| Parameter | Value |
|---|---|
| V<sub>DS</sub> | 60 V |
| **Active clamp** V<sub>DS(AZ)</sub> | **60 / 65 / 70 V** (min/typ/max) |
| Clamping energy | **490 mJ** |
| R<sub>DS(on)</sub> | 170–250 mΩ at V<sub>IN</sub> = 3 V, 1 A |
| Input threshold | **0.7 / 1.0 / 1.5 V** |
| Input current | 60–100 µA at 3 V |
| Protection | over-temperature, over-current, over-voltage, ESD |
| Package | SOT-223 |
| Automotive | AEC-Q qualified — the `Q` suffix part |

### Why this one

- **The 60–70 V clamp is exactly the fast-turn-off range** an injector wants.
  No zener to add, no diode to accidentally fit, and no chance of the slow-close
  error a freewheel diode would introduce.
- **It runs directly from a 3.3 V GPIO.** Threshold 1.5 V worst case, input
  current under 100 µA. The datasheet describes it as optimised for 3.3 V and
  5 V microcontrollers. **So the injectors do not need gate drivers** — that is
  eight driver channels removed from the board.
- **Self-protected.** Over-current and over-temperature shutdown mean a shorted
  or seized injector trips the part rather than destroying it, and takes the
  board's ground plane with it.
- Energy is a non-issue: a ~15 mH injector at 1 A stores about **7.5 mJ**
  against a 490 mJ rating.

Dissipation at worst-case 250 mΩ and 1 A is 0.25 W, which SOT-223 handles.

### One consequence of direct drive

Driving from the GPIO means the pin faces the injector circuit rather than
sitting behind a driver. The IntelliFET's ESD-protected input covers the normal
case, and a series gate resistor plus the 10 kΩ pulldown is still worth fitting.

If a uniform "driver on everything" approach is preferred for EMI reasons in a
truck, that is defensible — but it is a choice here, not a requirement.

---

## Summary

| Load | Part | Clamp | Needs a gate driver? |
|---|---|---|---|
| Coil ×8 | ISL9V3040 | 400 V | **Yes** — likely 5 V+ gate |
| Injector ×8 | ZXMS6005DGQ | 60–70 V | **No** — direct from 3.3 V |

Both keep the rule from `custom-board.md`: **clamp both, dissipate neither**,
with the clamp voltage chosen for what the load is meant to do.
