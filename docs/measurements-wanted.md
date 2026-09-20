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

> ⚠ **Provenance, because it cost three commits.** The only wheel in this
> building is the **Dorman**. `OriginalUnderDorman.png` and
> `RegisteredOn36-1wheel.png` are **screenshots from the customer review** — a
> stranger's engine, a stranger's wheels, an unknown model year. **This truck's
> timing cover has never been off.** Photographs taken here are `.jpg`; if it is
> a `.png`, it came from somewhere else.

| | What it closes | How |
|---|---|---|
| ~~**Which side the keyway is on**~~ | ✅ **CLOSED twice over** — the first look was from the *back* | Operationally: gap passes the sensor, then the keyway **5.00°** later — an order of events cannot be mirrored. Geometrically: **`FRONT` is cast into the wheel**, so on that face, sweeping clockwise, keyway first then the gap |
| ~~**Dorman or Ford wheel?**~~ | ✅ **CLOSED — it is the Dorman**, cast `FRONT 917-060 53025 TAIWAN` | But **which engine it fits is now open again** — see the next row |
| ~~**Is 917-060 an SBF or a modular part?**~~ | ✅ **CLOSED — modular.** Dorman: 35 teeth, OE cross **XW1Z-12A227-AC**, fits 2001-2010 F-150 4.6 and **2002-2010 F-150 5.4**. The ~135 mm corroborates it | The reseller listing had the OD *and* the engine family wrong |
| ◐ **Is the Dorman defective at all?** | **Hypothesis downgraded.** It needed `key_to_gap(OEM) ≈ 0`, which was assumed and never verified, and the photo's artefact budget (3–7° parallax + 2–3° edge-selection) exceeds the whole 5.00° question. **And 5.00° was never measured** — it is the midpoint of the observed 2.1–7.9° interval, read back as evidence. `key_to_gap ≈ 0` stays falsified; "half a pitch out" does not | Nothing to do. **Stop treating the Dorman as suspect** until something that is not a camera says otherwise |
| ⛔ ~~**OEM vs Dorman: do the gaps coincide?**~~ | **NOT AVAILABLE — the OEM wheel is not in hand.** The stacked-on-the-crank photo is the *reviewer's* engine, not this truck; the timing cover here has never been off. Three rows of this table were written as if it were ours | Needs the timing cover off: damper, accessory drive, front cover. A job, not a measurement |
| **Tooth-log fingerprint of the Dorman** ⭐⭐ | **Per-tooth pitch, runout and gap width to ~0.002°**, with no datum of any kind — `startToothLog()` already captures 720 periods, tagged by tooth index, ≈20 revs. This is the rig's own metrology, and it beats every caliper in this table | Spin it, log it, **twice with a remount and at two speeds**. The remount pair *is* the repeatability floor — nothing smaller than it is real |
| **Genuine `XW1Z-12A227-AC` vs the Dorman** ⭐⭐ — **order now, use last** | **Is 917-060 a faithful copy — is the review real?** And so whether the rig wheel's **5.00°** is an OE value or a defect. Deliberately deferred to the end: by then it is a tooth log at ±0.2°, not a look at a rim | **On arrival (cannot wait):** caliper bore/keyway/bolt circle **against the `.scad` hub, which is cut to the Dorman**, caliper the OD, read the casting, count teeth. **Then shelf it.** Validation is one run at the end |
| ⭐ **Count the teeth on both wheels** | **The cheapest decisive test in this table.** A stagger that *varies* around the rim is arithmetically impossible between two wheels of the same tooth count — mean pitch is 360/N. So either the counts differ (gross, countable) or the varying stagger seen in the review photo is **camera parallax**, which at a 10 mm axial separation and a 35° view manufactures exactly 5.00° | Count them. Dorman publishes 35. Ten seconds, no instrument |
| ⚠ **Phase is invisible to a single-wheel log** | A uniform phase offset logs as a **perfect** wheel — the log resets at the gap, so the gap is the origin and cannot be measured against itself. **This is exactly the error the review alleges** | Stack both wheels keyed and log the union: half a pitch turns the trace into a clean **72-2**. Or add an index ISR recording `_toothLogIdx` + µs-since-last-tooth — two fields, and it yields absolute `key_to_gap` |
| ⛔ ~~**The casting number on the OEM wheel**~~ | **Not readable.** It is behind the timing cover. Moot anyway — it only ever fed a *prediction* of the constant below, which is now measured directly | — |
| **`CKP_GAP_TO_TDC_DEG` — strobe the sync gap** ⭐⭐ | The whole constant in one reading, **with the cover on**: wheel + sensor angle + conditioner, at running speed, on whatever wheel the truck actually has. **It does not care which wheel that is**, which is why losing the wheel-ID thread costs so little | Piston stop on #1 (cover on, one plug out), mark TDC, degree-tape the damper. Trigger a timing light from TritonECU's gap-detect instead of a plug wire, and read the tape |
| ⛔ **Does a 1999 5.4L even use this reluctor?** | ◐ **Argued, never measurable.** The OE number `XW1Z-…` carries Ford's **1999** prefix (`X` = 1999, as `1` = 2001 on the donor PCM), revised to `-AC` and still cataloged for 2001-2010 — one design spanning 1999→2010. **That is a reading of a part number, and it stays one**: the only 1999 wheel in the story is inside this truck's timing cover | No route. **Mark it an argument and move on** — it was propping up a *prediction* of the constant above, which is now measured directly |
| ~~**#1 at TDC — what is in front of the CKP sensor?**~~ | ⛔ **Superseded.** It required seeing the wheel and the sensor at once, i.e. the cover off. The strobe row above gets the same constant — and more of it — through a spark plug hole | — |
| **OD — caliper it** ⭐ | ✅ **171.45 is dead** — the whole-template photo reads **~13.5 squares, ~135 mm**, 25 % under the listing. Now also drives `wheel_bore`, `key_w`, `key_d`. **Print no rig part until this is a caliper reading** | Calipers. The grid got it to ±7 mm; the hub fit needs better |
| **Tooth width at the rim** | **Demoted.** 5.00° is the midpoint of two tooth centres, so the width cancels out of the answer entirely. It now only bounds the ±2.5° spread | Calipers, then `360·w/(π·OD)` |
| **Bore, keyway w × d, the four holes' PCD and angles** | `wheel_hub` — spigot, key and bolt circle. Now **derived from the OD** via the photo's ratios (0.253, 0.15, 0.19), so they are only as good as the caliper above. The old spigot was **9.2 mm oversize on the diameter** and would not have entered | Calipers; the holes read straight off the grid |

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
