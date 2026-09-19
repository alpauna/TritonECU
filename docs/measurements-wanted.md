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
| **EPC** | C183 | 81 | already NCV8408B DPAK; confirms |

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
