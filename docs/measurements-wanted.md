# Bench measurements wanted

Components are off a donor truck and available to test. This is the consolidated
list — what to measure, and **what each one closes**. Ordered by how much is
waiting on it.

> ⚠ **Null the leads on anything under ~5 Ω.** Today's coil went from 1.8 Ω to
> 0.5 Ω on good leads and that 3.6× error would have inverted two conclusions.
> Short the probes, note the reading, subtract — or use four-wire.

---

## 1. Solenoid coil resistance — closes the whole "marginal" column ⭐

[`output-drivers.md`](output-drivers.md) carries a table of loads estimated at
*"~0.5–1 A"* and marked **⚠ marginal — measure first**. It is the largest block
of guesswork left in the driver design, and **one resistance measurement per coil
settles all of it**: at 13.5 V, current is just `13.5 / R`.

| Coil | Connector | EEC-V pin | What it decides |
|---|---|--:|---|
| **EGR vacuum regulator (EVR)** | C121 | 47 | PWM driver current and freewheel sizing |
| **EVAP canister purge** | C164 | 56 | same |
| **IMCC** | C118 | — | **and [CONFIRM] whether it is on/off or PWM** — a PWM part will usually be lower resistance |
| ~~**SSA**~~ | — | 27 | ✅ **CLOSED — Ford spec 20–30 Ω**, 0.72 A worst case |
| ~~**SSB**~~ | — | 1 | ✅ **CLOSED — Ford spec 20–30 Ω** |
| ~~**CSS — coast clutch**~~ | — | 20 | ✅ **CLOSED — it does not exist on a 4R70W.** It is a **4R100** part, and the MegaSquirt sheet was developed on a 4R100. Pin 20 is free |
| ~~**TCC**~~ | — | 54 | ✅ **CLOSED — Ford spec 10–16 Ω → 1.44 A worst case.** Higher than assumed; **give it a pour** |
| ~~**EPC**~~ | — | 81 | ✅ **MEASURED — 4.12 Ω, 13.7 mH.** Confirms the NCV8408B; τ = 3.33 ms puts the PWM at **1–2 kHz**. **Still open: its operating current** |

**Also note the part number and any markings on each solenoid** — a datasheet
beats a measurement where one exists, and `4r70W-Test-Key-Solenoid.png` has just
proved the point by closing three of these rows without a meter.

## 2. Inductance — freewheel energy, and the clamp margin

Same meter, same parts: **EVR, EVAP purge, IMCC (if PWM), TCC, EPC**.

⭐ **And SSA/SSB**, whose resistance Ford specifies but whose **inductance is what
the clamp-energy margin actually turns on** — that margin just moved from 7.3× to
**3.5×** when the honest end of Ford's 20–30 Ω range was used
([`output-drivers.md`](output-drivers.md)).

Resistance gives the steady current; **inductance gives the energy the freewheel
diode has to absorb every cycle** (`½LI²`) and the decay time. Those set the
diode and confirm that
[`harness-protection.md`](harness-protection.md)'s *"external freewheel to 12 V"*
is adequate rather than assumed.

## 3. DPFE supply current — firms up the whole VREF budget

[`vref-supply.md`](vref-supply.md) lists the DPFE at **~12 mA, "the largest
single VREF load"**, against a **~25 mA** total. **That number is an estimate**,
and it sized the NCV8772 regulator and the TPS2H160B current limit.

> Power the DPFE from a bench 5.00 V and measure the supply current. Roughly
> half the VREF budget rests on that one figure.

**While it is on the bench, also take the output voltage with both pressure
ports open** — zero differential. That is the **zero offset** the firmware will
subtract, and it costs nothing to capture now.

## 3b. TFT thermistor — two fixed points, no thermometer needed ⭐

The transmission fluid temperature sensor is on the **inner pan harness**, out at
**C183 pin 5** (`923 OG/BK`), returning on pin 2 (`359 GY/RD`). It is an **NTC
thermistor** read against a pull-up inside the ECU, and **we have no curve for
it at all** — `f150-1999-target.md` says only *"NTC, internal ADC"*.

**Two physical fixed points beat any thermometer:**

| | |
|---|---|
| **Ice + water slurry, stirred** | **0.0 °C**, by definition |
| **Boiling water** | **~100 °C** — knock a degree off for altitude |

From those two, β falls straight out:

```
  β = ln(R₀ / R₁₀₀) / (1/273.15 − 1/373.15)
```

and `R(T) = R₀ · exp(β(1/T − 1/T₀))` is the firmware conversion, done.

**A third reading at room temperature, with a thermometer, validates the fit** —
if it lands on the curve the two-point β is good; if not, the thermistor wants
Steinhart–Hart instead of a single β.

### What it decides

| | |
|---|---|
| **Firmware curve** | counts → °C, without guessing at a lookup table |
| **Pull-up value** | sized so the divider spans a useful ADC range across the *operating* band, not the full −40…150 °C survival range |
| **Self-heating** | pull-up current through a low resistance at high temperature warms the sensor it is measuring |
| **VREF budget** | its pull-up was **missing** from [`vref-supply.md`](vref-supply.md)'s load table — CHT and IAT were there, TFT was not |

> **A wrong TFT curve is silent.** It does not set a code; it just shifts at the
> wrong temperatures and locks the converter up when it should not. That makes it
> worth getting right on the bench rather than discovering on the road.

## 4. Already open elsewhere, same trip

| | |
|---|---|
| **O2 heater cold resistance** | Leads nulled — it lands at 0.9–1.8 Ω, the same regime that just bit the coil. Decides whether the driver ever sees 16 W or 49 W — [`output-drivers.md`](output-drivers.md) |
| **Circuit 679 level** | What the speed control servo, GEM and rear air suspension expect — 12 V, 5 V or open-drain. Decides only whether a pull-up gets populated |
| **Donor case: pan depth and sign** | Straight edge across the rails, depth gauge to the pan. Clearance or thermal boss — [`DonorECU/README.md`](DonorECU/README.md) |

## Not worth measuring

| | Why |
|---|---|
| MAF transfer function | Well documented, and it calibrates on the engine |
| DPFE pressure curve | Same — the **zero offset** above is the part worth having |
| CKP/CMP coil resistance | **Done** — 371 Ω, which is what settled CMP as VR rather than Hall |
| A/C clutch coil | Already decided: drive a **relay**, not the clutch |
