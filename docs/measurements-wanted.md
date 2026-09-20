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
| ~~**EPC**~~ | — | 81 | ✅ **4.12 Ω measured, 13.7 mH.** Ford specs **2.48–5.66 Ω**, so ours is mid-range and healthy. **Still open: operating current** |

**Also note the part number and any markings on each solenoid** — a datasheet
beats a measurement where one exists, and `4r70W-Test-Key-Solenoid.png` has just
proved the point by closing three of these rows without a meter.

> ⚠ **The manual does NOT publish inductance.** Searched: no henries anywhere.
> Resistance, yes — SS-1/SS-2 20–30 Ω, TCC 10–16 Ω, **EPC 2.48–5.66 Ω**,
> **OSS 450–750 Ω**, and the whole TFT curve. **Inductance stays a bench job**,
> and it is the only thing the second transmission is still needed for.

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

## ~~3b. TFT thermistor~~ ✅ CLOSED — Ford publishes the table

**No measurement needed.** The 4R70W service manual's *Resistance/Continuity
Tests* gives the full curve, −40 to 150 °C. A single **β = 3987 K** fits it
within a few percent, and the pull-up is sized: **2.2 kΩ to 3.3 V**, giving
30 ADC counts per °C through the band that matters. [`tft-sensor.md`](tft-sensor.md)

> **That is four measurements this manual has now closed** — SSA, SSB, TCC and
> TFT. **Look there first.**

## 4. Already open elsewhere, same trip

| | |
|---|---|
| ~~**O2 heater cold resistance**~~ | ✅ **6.12 Ω measured** — four times the prediction. It is a **mild PTC**, inrush is 2.35 A, and the driver never enters current limit. [`output-drivers.md`](output-drivers.md) |
| **Circuit 679 level** | What the speed control servo, GEM and rear air suspension expect — 12 V, 5 V or open-drain. Decides only whether a pull-up gets populated |
| **Donor case: pan depth and sign** | Straight edge across the rails, depth gauge to the pan. Clearance or thermal boss — [`DonorECU/README.md`](DonorECU/README.md) |

## 5. The 36-1 trigger wheel — the datum everything angular hangs on ⭐

The keyway was observed against the missing tooth on 2026-09-19. It
**falsified `key_to_gap = 0`**, and two of the follow-ups below closed the same
day — including the one that identifies the wheel. See
[the correction](../hardware/vr-test-rig/README.md#corrected-the-keyway-sits-half-a-pitch-from-the-missing-tooth)
and [`calc/trigger_wheel_datum.py`](calc/trigger_wheel_datum.py). The wheel is
already sitting on the 10 mm carrier-template grid, which does most of what is
left for free.

| | What it closes | How |
|---|---|---|
| ~~**Which side the keyway is on**~~ | ✅ **CLOSED** — the first look was from the *back* | Redefined operationally: the gap passes the sensor, then the keyway **5.00°** later. An order of events cannot be mirrored |
| ~~**Dorman or Ford wheel?**~~ | ✅ **CLOSED — it is the Ford wheel** | A universal 36-1 is broached to fit a shaft, so its teeth fall arbitrarily against the key. **This keyway lands on the crank's TDC datum**, which only a factory part does |
| **#1 at TDC — what is in front of the CKP sensor?** ⭐ | **`CKP_GAP_TO_TDC_DEG` itself.** 5.00° is the *wheel's* half; the other half is where the sensor bolts to the block, and no wheel measurement can supply it | Piston stop, bring #1 up, then look at the sensor. Gap ~5° past = the whole chain is consistent |
| **OD** | `wheel_od = 171.45` is already contradicted — the wheel sits *inside* the 157 mm template. Sets shaft height, wheel slot and both sensor brackets | Count 10 mm grid squares across it |
| **Tooth width at the rim** | **Demoted.** 5.00° is the midpoint of two tooth centres, so the width cancels out of the answer entirely. It now only bounds the ±2.5° spread | Calipers, then `360·w/(π·OD)` |
| **Bore, keyway w × d, the three holes' PCD and angles** | `wheel_hub` — spigot, key and bolt circle. All three are currently ratios off a product photo | Calipers; the holes read straight off the grid |

> **The best measurement here is not a measurement.** Once the rig runs, homing
> the stepper on the flute and taking a tooth log reads `key_to_gap` at
> **0.1125°** — 23× better than sighting it by eye, and it does not need the
> flute to be *right*, only *known*.

## Not worth measuring

| | Why |
|---|---|
| MAF transfer function | Well documented, and it calibrates on the engine |
| DPFE pressure curve | Same — the **zero offset** above is the part worth having |
| CKP/CMP coil resistance | **Done** — 371 Ω, which is what settled CMP as VR rather than Hall |
| A/C clutch coil | Already decided: drive a **relay**, not the clutch |
