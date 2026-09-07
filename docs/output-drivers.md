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

### Gate drive — resolved, and simpler than expected

The datasheet leads with **"Logic Level Gate Drive"**, and the part has its own
gate network built in:

| Parameter | Value |
|---|---|
| **R1, internal series gate resistance** | **70 Ω** |
| **R2, internal gate-to-emitter resistance** | **10 kΩ – 26 kΩ** |
| Gate charge Q<sub>G(ON)</sub> | **17 nC** at 10 A, V<sub>GE</sub> = 5 V |
| Gate threshold V<sub>GE(TH)</sub> | 1.3–2.2 V at 25 °C |
| **Gate plateau V<sub>GEP</sub>** | **3.0 V** |
| Datasheet switching conditions | V<sub>GE</sub> = 5 V, **R<sub>G</sub> = 470 Ω** |

**The 10 kΩ gate pulldown is already inside the device** (R2). The boot-state
protection discussed in `custom-board.md` is therefore built in for the
ignition side — an external pulldown is belt-and-braces rather than essential.

**But do not drive it from 3.3 V.** The gate plateau is **3.0 V**, so a 3.3 V
GPIO leaves only 0.3 V of overdrive. Every V<sub>CE(sat)</sub> figure is
characterised at V<sub>GE</sub> = 4.0–4.5 V. At 3.3 V the device conducts but
does not saturate, and the failure is **heat, not a fault** — 6–10 A through an
IGBT that is only partly on.

**No dedicated gate driver IC is needed either.** Gate charge is only 17 nC and
70 Ω of the series resistance is already internal. A plain **5 V logic buffer**
is sufficient.

#### Recommended: one 74HCT541 for all eight coils

- **HCT, not HC.** HCT inputs accept 3.3 V as a valid high (V<sub>IH</sub> =
  2.0 V at V<sub>CC</sub> = 5 V); HC would want 3.15 V minimum and be marginal.
- Powered from **5 V**, so the gate sees a full 5 V — comfortably above the
  3.0 V plateau and matching the datasheet's characterisation.
- Octal, so **one package drives all eight channels**.
- **Its output-enable is the boot interlock.** `OE` is active-low: pull it up to
  5 V with 10 kΩ so the outputs are high-impedance at power-on, and have
  firmware pull it low only once the engine position is known. Combined with
  the IGBT's internal 10–26 kΩ gate-to-emitter resistor, no coil can be
  energised before software says so.

#### The gate RC

**470 Ω series per gate, and no capacitor.**

470 Ω is the datasheet's own switching-characterisation value, so the quoted
turn-off numbers apply directly. With C<sub>iss</sub> ≈ Q<sub>G</sub>/V<sub>GE</sub>
≈ 3.4 nF, that gives τ ≈ 1.6 µs against the internal 70 Ω plus the external
470 Ω — **the RC is formed by the resistor and the device's own input
capacitance. Adding a gate capacitor only slows it further for no benefit.**

Peak gate current is 5 V / 540 Ω ≈ **9 mA**, transient and only during
switching. Within a 74HCT541's capability.

Resulting timings, from the datasheet at these exact conditions: turn-off delay
**4.8 µs**, current fall **2.8 µs**. At 6000 rpm one crank degree is 27.8 µs, so
the fall is **0.1°** — negligible for timing, and fast enough that the primary
collapses sharply rather than bleeding away.

**Do not add an RC snubber across the collector-emitter.** That is the flyback,
and absorbing it costs spark energy — see `custom-board.md`.

#### Ignition BOM, per eight channels

| Qty | Part |
|---|---|
| 8 | ISL9V3040 |
| 1 | 74HCT541 |
| 8 | 470 Ω gate resistor |
| 1 | 10 kΩ pull-up on `OE` |

Ten line items for the whole ignition output stage.

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

### Injector gate network

**220–470 Ω series, 10 kΩ pulldown, and optionally 1 nF to ground.**

Ringing is barely a concern here, because the IntelliFET's input is a **logic
input, not a raw gate** — it draws 60–100 µA and an internal driver handles the
actual MOSFET gate. There is no meaningful gate charge for the GPIO to move and
no LC gate loop to ring.

So the series resistor is there to limit fault current into the GPIO rather than
to damp anything. 220–470 Ω is ample.

A 1 nF cap to ground gives useful noise immunity in a harness environment. With
470 Ω that is a 470 ns time constant — against injector pulse widths of 1–20 ms,
utterly negligible.

| Qty | Part |
|---|---|
| 8 | ZXMS6005DGQ |
| 8 | 470 Ω series |
| 8 | 10 kΩ pulldown |
| 8 | 1 nF (optional) |

No buffer, no driver, no level shift — straight off the P4.

---

## Summary

| Load | Part | Clamp | Drive |
|---|---|---|---|
| Coil ×8 | ISL9V3040 | 400 V | **74HCT541 buffer at 5 V** + 470 Ω. No gate driver IC |
| Injector ×8 | ZXMS6005DGQ | 60–70 V | **Direct from 3.3 V GPIO** + 470 Ω |

Neither needs a dedicated gate-driver IC. One octal buffer covers the entire
ignition side, and the injectors need nothing at all.

Both keep the rule from `custom-board.md`: **clamp both, dissipate neither**,
with the clamp voltage chosen for what the load is meant to do.
