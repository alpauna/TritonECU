# Output driver parts — ignition, injection, relays and solenoids

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

### ✅ MEASURED: **L = 1.5 mH** (LCR meter, 2026-09-18)

> ~~A COP primary of ~5 mH at 8 A stores 160 mJ — about 1.9× margin. But 6 mH at
> 10 A is 300 mJ, exactly at the limit and therefore not acceptable.~~
> **That was a guess, and it was about 3.3× too high.** Energy goes as L, so the
> whole concern evaporates. Numbers below from [`calc/coil_dwell.py`](calc/coil_dwell.py).
>
> Read **1.48 mH** first and **1.50 mH** on a second pass with better leads. The
> difference is **1.35 %**, nothing here is remotely that sensitive, and 1.48
> implied three significant figures the measurement does not support. **1.5 mH**,
> which also makes τ = L/R exactly **3.0 ms** and puts 300 mJ at exactly **20 A**.

| Peak current | At 5 mH *(assumed)* | **At 1.5 mH *(measured)*** | Margin |
|--:|--:|--:|--:|
| 8 A | 160 mJ | **48 mJ** | **6.3×** |
| **10.3 A** — 80 mJ, a healthy COP spark | 265 mJ | **80 mJ** | **3.75×** |
| 12 A | 360 mJ | 108 mJ | 2.8× |
| 16 A | 640 mJ | 192 mJ | 1.6× |
| **20.0 A** | 1000 mJ | **300 mJ** | **1.0× — the rating** |

**The 300 mJ rating is reached at exactly 20.0 A.** The operating point sits **3.75×
under it**. The ISL9V3040 is comfortably the right part and there is no need to
reach for a higher-energy EcoSPARK member.

### Dwell — and it barely depends on the primary resistance

`I(t) = (V/R)(1 − e^(−tR/L))`. Early in the charge curve the rise is set by **L,
not R**: `di/dt = V/L = ` **9.0 A/ms** at 13.5 V.

| Target | Dwell at 13.5 V, R = 0.3 → 0.7 Ω |
|---|---|
| 8.2 A — 50 mJ | **1.01 → 1.18 ms** |
| **10.3 A — 80 mJ** | **1.31 → 1.65 ms** |
| 20.0 A — *the rating* | 2.95 → 5.54 ms |

That sweep was made before R was known, and its conclusion held: **spread across
the whole plausible range of R is ~10 % at the operating point** (all at 13.5 V),
so the dwell was decided to within ten percent without the second measurement.
It is ~60 % at the *rating*, which is why R still mattered for the fault margin —
and that is what the measurement below settles.

**Note what dominates instead: battery voltage.** Across 9 → 14.4 V the dwell
moves **1.9×**, against 10 % for the whole range of R. See the dwell table below.

### ✅ MEASURED: **R = 0.5 Ω** (DCR, good leads)

> ⚠ **A first 2-wire reading gave 1.8 Ω, and that was the leads.** At half an ohm
> the test leads *are* most of a 2-wire reading. 0.5 Ω is also what published
> DG508-family figures predict, and it mattered: 1.8 Ω would have meant the coil
> current-limited itself at 8 A and could never reach the IGBT's rating.
>
> **Why the inductance survived the same bad leads and the resistance did not** —
> leads add roughly 1 mΩ/cm and tens of nH:
>
> | | Lead contribution | Effect on the reading |
> |---|---|---|
> | R = 0.5 Ω | ~1.3 Ω | **3.6× high** |
> | L = 1.5 mH | ~50 nH | **0.003 % high** |
>
> A series error that swamps half an ohm is invisible against 1.5 mH. Worth
> carrying as a habit: **under an ohm, null the leads or use four wires; for
> millihenries, do not bother.**

| At 14.4 V | |
|---|---|
| I<sub>sat</sub> = V/R | 28.8 A |
| τ = L/R | **3.00 ms** |
| Stuck-on energy | **622 mJ — 2.07× the rating** |
| Dwell to reach the rating | **3.56 ms**, ~2.7× nominal |

**The operating point is comfortable.** We charge to **10.3 A for 80 mJ**, which
is **3.75× under** the rating, and τ = 3.00 ms means the ramp is still in its
near-linear region — so dwell is predictable and insensitive to small errors in R.

### The dwell table — this is the deliverable

Target **10.3 A / 80 mJ**. Dwell must track battery voltage:

| V<sub>batt</sub> | Dwell for 80 mJ | Dwell for 50 mJ |
|--:|--:|--:|
| 9.0 V — cranking | **2.56 ms** | 1.81 ms |
| 10.0 V | 2.18 ms | 1.57 ms |
| 12.0 V | 1.69 ms | 1.25 ms |
| 12.6 V | 1.58 ms | 1.17 ms |
| 13.5 V | 1.45 ms | 1.08 ms |
| **14.4 V** | **1.33 ms** | 1.00 ms |
| 15.0 V | 1.27 ms | 0.95 ms |

**2.56 ms at 9 V against 1.33 ms at 14.4 V — a 1.9× span.**

> **And the truck already tells us when it is cranking.** EEC-V **pin 64** —
> `199 LB/YE`, **TR3A** — carries 12 V while cranking, because the DTR sensor is
> also the neutral safety switch and feeds 199 from the start circuit *through*
> the range switch. So it means **cranking in Park or Neutral**, which is a
> better gate for cranking enrichment than a bare start signal would be.
> [`1999-Ford-F150-4wd-5.42v/schematic-findings.md`](1999-Ford-F150-4wd-5.42v/schematic-findings.md) §21. A fixed dwell would
either waste energy and heat the driver at high line, or miss the target while
cranking — which is exactly when spark energy matters most. **The dwell-vs-voltage
table is not optional.**

> This is what `battery voltage` on the ADC is *for*, beyond diagnostics — and
> [`review-ignition-injection.md`](review-ignition-injection.md) already requires
> it to be **sampled away from injection events, not averaged through them**,
> which is why [`adc-front-end.md`](adc-front-end.md) forbids a filter capacitor
> at the divider.

### Part-to-part spread is larger than the measurement — and it self-cancels

**One coil was measured; eight are fitted.** At the nominal 1.33 ms dwell:

| Coil L | Peak current | Energy | vs 300 mJ |
|--:|--:|--:|--:|
| 1.35 mH (−10 %) | 11.22 A | 84.9 mJ | 3.5× |
| **1.50 mH** | **10.33 A** | **80.0 mJ** | **3.8×** |
| 1.65 mH (+10 %) | 9.57 A | 75.5 mJ | 4.0× |

**±10 % of coil spread moves delivered energy by only ~2 %**, because a
higher-inductance coil charges more slowly and the two effects oppose. Margin
stays above 3.5× throughout.

So the 1.48-vs-1.50 question is noise inside noise. **What the dwell calibration
needs margin for is battery voltage — a 1.9× span — not the coil.**

**Overlap is not a constraint anywhere the engine runs.** At the 14.4 V dwell the
90° event spacing collides above **11 300 rpm**. The 2.56 ms cranking dwell would
collide at 5880 rpm — at 9 V, where the engine is turning 200.

### ⚠ The fault case is stuck-on, and it exceeds the rating at any R

A stuck-on output does not climb forever — current saturates at `V/R`:

| R | I<sub>sat</sub> at 14.4 V | Stored | vs 300 mJ | Coil dissipates |
|--:|--:|--:|--:|--:|
| 0.3 Ω | 48.0 A | 1728 mJ | **5.8×** | 691 W |
| **0.5 Ω** *(measured)* | 28.8 A | **622 mJ** | **2.07×** | 415 W |
| 0.7 Ω | 20.6 A | 317 mJ | **1.1×** | 296 W |

**At any plausible resistance a stuck-on coil stores more than the IGBT's
avalanche rating**, and turning it off then dumps that into the device — by which
point the coil is cooking at hundreds of watts anyway. **The measured 0.5 Ω is
the middle row: 622 mJ, 2.07×.**

**This is the number behind the `OE2` watchdog.** At the measured 0.5 Ω a
stuck-on coil is **2.07× the IGBT's rating** and reaches it after 3.56 ms — about
2.7× the nominal dwell. The firmware dwell limit is the first line; the hardware
watchdog is what covers a firmware hang.
[`v1-scope.md`](v1-scope.md) carries it as *"footprint yes, strap OE2 low for
v1"* — that is still the right call for v1, but it is now a quantified risk
rather than a principle.

### Scheduler: dwell overlap is not a constraint

At 8 cylinders the spark events are 90° apart — **2.50 ms at 6000 rpm** against
the measured **1.33 ms** dwell at 14.4 V, so **no overlap below ~11 300 rpm**. With COP each coil has its
own driver so overlap would be legal anyway; it would only mean two coils
charging at once, ~21 A from the harness for a few hundred microseconds.
`SparkScheduler::maxRpmForDwell()` already exposes this end of the trade.

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
- **Two output-enables, and they are a two-key interlock.** The '541 has
  **`OE1` (pin 1) and `OE2` (pin 19), both active-low and ANDed internally** —
  *either* one high forces all eight outputs to high-impedance. Pull both up to
  5 V with 10 kΩ so the outputs are disabled at power-on. Combined with the
  IGBT's internal 10–26 kΩ gate-to-emitter resistor, no coil can be energised
  before something actively permits it.

#### Use the two enables independently

Tying them together works, but wastes the more useful arrangement:

| Enable | Driven by | Meaning |
|---|---|---|
| **`OE1`** | firmware GPIO | "engine position is known and ignition is armed" |
| **`OE2`** | **hardware watchdog** | "firmware is still alive" |

The second one addresses a failure the first cannot. If firmware hangs *while a
coil is charging*, that coil stays energised — 6–10 A continuously into a
primary designed for a few milliseconds of dwell. The coil cooks, and quite
possibly the IGBT with it. No amount of software care helps, because the
software is what stopped.

A supervisor IC with a watchdog input (TPS3823-class) driving `OE2` fixes it in
hardware: firmware must kick it periodically, and if it stops, the buffer goes
high-impedance and every gate is pulled down by the IGBT's own internal
resistor. It costs one part and one GPIO, and it is the difference between a
hung ECU being an inconvenience and a hung ECU being a destroyed coil.

If the watchdog is left for later, fit the footprint and strap `OE2` low.

#### Package current, and why it is fine

The 74HCT541's guaranteed output drive is ±6 mA and absolute maximum is around
25 mA per output — with a further limit on total current through the supply
pins. Nine milliamps per channel is above the guaranteed figure but far below
the maximum, and it is a **transient during the ~1.6 µs gate charge**, not a DC
load.

What makes it comfortable is that the channels never switch together: ignition
events are **45° apart** (see `SparkScheduler`), so at most one or two gates are
in transition at any instant. Eight simultaneous edges would be ~72 mA and
outside the package's supply-pin rating — but that condition cannot arise from
a correct firing order.

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
| 2 | 10 kΩ pull-up — one each on `OE1`, `OE2` |
| 1 | watchdog supervisor driving `OE2` *(optional, recommended)* |

Eleven line items for the whole ignition output stage, watchdog included.

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

> **Pre-schematic reviews:**
> [`review-solenoid-chain.md`](review-solenoid-chain.md) (solenoids and heaters)
> and [`review-ignition-injection.md`](review-ignition-injection.md) (coils and
> injectors — which found that the **IAC valve has no driver assigned**).

> **A pre-schematic review of the solenoid and heater chain is in
> [`review-solenoid-chain.md`](review-solenoid-chain.md)** — four findings, two
> of which share a root: outputs were classified by speed and current, and PWM
> is neither.

## Relays and lamps: Toshiba **TBD62083AFNG**

An 8-channel DMOS sink array, pin-compatible with the ULN2803 family it
replaces. **Chosen deliberately as the simple answer** for the slow low-side
group — relay coils and the MIL — and it is the right part for that job and
no larger one. See §"What it must not drive".

Datasheet: [`Datasheets/TBD62083AFNG-datasheet.pdf`](Datasheets/TBD62083AFNG-datasheet.pdf).

| Parameter | Value |
|---|---|
| Channels | **8**, sink |
| V<sub>OUT</sub> | 50 V max |
| I<sub>OUT</sub> | 500 mA/ch absolute; **400 mA operating**, 1 channel at 25 °C |
| **R<sub>ON</sub>** | **0.7 Ω typ, 1.14 Ω max** at 350 mA |
| **V<sub>IN</sub> (output on)** | **2.5 V min**, 25 V max |
| V<sub>IN</sub> (output off) | 0.6 V max |
| **I<sub>IN</sub> (output on)** | **0.1 mA max** at V<sub>IN</sub> = 2.5 V |
| Clamp diode | **built in, every channel**, to the COMMON pin. I<sub>F</sub> 400 mA |
| Package (FNG) | SSOP18-P-225-0.65, P<sub>D</sub> = 0.96 W |
| T<sub>opr</sub> | **−40 to +85 °C** |

### Why this rather than a ULN2803

Three things, and the first is the one that matters:

- **V<sub>IN(ON)</sub> = 2.5 V, drawing 100 µA.** It switches directly from
  **3.3 V logic**, so it takes an STM32 pin with no level shifter of its own.
  (This originally read "does not care which rail the MCP23S17 chain runs at" —
  that chain is now dropped and the four relay channels are native.) A ULN2803's
  Darlington input wants milliamps of base current per channel and carries a
  package-total limit with it; at 100 µA per channel that constraint disappears.
- **R<sub>ON</sub> 1.14 Ω worst case, not a 1.1 V saturation drop.** At a 200 mA
  relay coil that is **46 mW per channel against 220 mW** for the Darlington —
  roughly five times less heat — and the output actually pulls to near ground,
  so the coil sees effectively the full supply rather than supply minus 1.1 V.
  On a marginal coil at a low battery that difference is the difference between
  pulling in and not.
- **Clamp diodes are built in.** [`harness-protection.md`](harness-protection.md)
  requires a flyback diode across every relay and solenoid load. This part
  satisfies that internally, per channel, which is eight diodes and sixteen pads
  removed from the board.

Pin compatibility with the ULN2803 family is a free hedge: if a channel ever
needs the Darlington's higher voltage tolerance, the footprint already takes it.

### Wiring COMMON — one rail, and which one

**There is a single COMMON pin for all eight clamp diodes.** Every load on the
package therefore returns its flyback to the same rail, which constrains the
layout more than it first appears:

> **Tie COMMON to permanent B+, and feed every relay coil on the package from
> that same permanent B+.**

Two reasons. A clamp tied to a rail *lower* than a load's supply does not
protect that load; and a coil whose supply is off while COMMON is high offers a
leakage path back through the winding. One rail for the whole package avoids
both without any thought at assembly.

This suits the design anyway. [`cooling-fans.md`](cooling-fans.md) §4.6 needs
the fan relay coils on a rail that survives key-off for the run-on to work, and
the [always-on MCU domain](always-on-domain.md) means the ECU is awake to
de-energise them. Permanent B+ for the whole relay group is consistent with
both.

### Channel budget — one package is enough

| Channel | Load | Coil / lamp current |
|--:|---|---|
| 1 | Fuel pump relay | ~150–200 mA |
| 2 | **Cooling fan 1 relay** | ~150–200 mA |
| 3 | **Cooling fan 2 relay** | ~150–200 mA |
| 4 | A/C clutch relay | ~150–200 mA |
| ~~5~~ | ~~MIL~~ | **no discrete MIL circuit exists** — the cluster drives it, over SCP |
| 5–8 | spare | four spare, not three |

**Four used, four spare, one package.** The MIL was a fifth until Ford's cluster diagrams showed it has no PCM wire — see [`schematic-findings.md`](1999-Ford-F150-4wd-5.42v/schematic-findings.md) §11.

Thermally this is not close. Five channels at 200 mA and R<sub>ON(max)</sub>
1.14 Ω is 5 × 0.2² × 1.14 = **0.23 W**. The FNG package allows 0.96 W at 25 °C,
derating 7.7 mW/°C, so at a 60 °C cabin ambient the budget is still **0.69 W**.
Even all eight channels loaded would be 0.37 W.

The **−40 to +85 °C** operating range is comfortable *because*
[`enclosure.md`](enclosure.md) puts the box in the **cabin, behind the
glovebox**. Underhood it would be marginal, and this part choice should be
revisited if the enclosure ever moves.

### What it must not drive

400 mA operating is the honest limit, and several loads on the output list are
well past it. **This package covers relays and the lamp — not the rest of the
slow group:**

| Load | Current | Verdict |
|---|---|---|
| HO2S heaters ×4 | **~1–2 A each** | ✗ far over. Needs its own driver |
| ~~SS1, SS2, CSS~~ | *superseded — and **CSS does not exist on a 4R70W**, see below* | |
| EVAP purge, EGR regulator | ~0.5–1 A, PWM | ⚠ marginal — measure first |
| IMCC | **[CONFIRM]** on/off or PWM, likely ~0.5 A | ⚠ measure first |
| **SSA, SSB** | **0.48–0.72 A** — Ford spec 20–30 Ω | ✗ over the TBD62083. **NCV8405A, as chosen** |
| **TCC** | **0.90–1.44 A** — Ford spec 10–16 Ω | ✗. NCV8405A **with a pour** |
| A/C **clutch coil** driven directly | ~3–4 A | ✗ — drive a **relay**, not the clutch |

The last row is the easy mistake: the A/C clutch itself is a several-amp
electromagnet. The channel above drives a *relay coil*, and the relay carries
the clutch.

Everything in that table is covered by the **NCV8405A** below. Measure the
actual coil currents on the truck before committing — every figure above is an
estimate.

---

## Solenoids and heaters: onsemi **NCV8405ASTT1G**

A three-terminal self-protected low-side MOSFET. It covers everything above the
TBD62083A's 400 mA and below the ignition and injection stages — and, with a
resistor on the drain, it diagnoses its own load.

Datasheet: [`Datasheets/NCV8405ASTT1G-Datasheet.pdf`](Datasheets/NCV8405ASTT1G-Datasheet.pdf).

| Parameter | Value |
|---|---|
| Package | **SOT-223** (`STT1G`). DPAK is `NCV8405ADTRKG` |
| V<sub>GS(th)</sub> | **1.0 / 1.6 / 2.0 V** — drives from 3.3 V or 5 V |
| R<sub>DS(on)</sub> at V<sub>GS</sub> = 5 V | 105 typ / **120 mΩ max** at 25 °C; 185 / **210 mΩ** at 150 °C |
| Current limit | **6.0 / 9.0 / 11 A** at 25 °C; 3.0 / 5.0 / 8.0 A at 150 °C |
| Clamp | **42 V integrated**, E<sub>AS</sub> 275 mJ |
| Thermal | shutdown at 150–200 °C, **automatic restart** |
| P<sub>D</sub> (SOT-223) | 1.0 W on min pad, 1.7 W on a 2″ board. Rθ<sub>JA</sub> 130 / 72 °C/W |
| Qualification | AEC-Q101, survives 53 V load dump |

### Why low-side, and why that settles it

**The truck is already wired this way.** Ford feeds each HO2S heater 12 V and
the PCM supplies the ground — pins 95 and 96 are *"RR / LR HO2S Heat"*. Same for
the solenoids. A low-side driver drops onto the harness that exists; a high-side
part would mean cutting every feed and routing it through the ECU instead.

### The integrated clamp does not replace a freewheel diode

**An earlier revision of this document claimed it did, and that was wrong.** The
EEC-V pinout's note that *"EPC needs a flyback diode to 12 V"* asks for
**recirculation back to the supply**, which is a different thing from avalanche
to ground:

| | Avalanche clamp | Freewheel diode to 12 V |
|---|---|---|
| Decay rate | (V<sub>clamp</sub> − V<sub>supply</sub>)/L — **560 A/s** at 50 mH | I·R/L — **250 A/s** at 25 Ω, 0.5 A |
| Energy goes | **into the FET** | into the load's own resistance |
| Per switching event | every one | none |

On an **on/off** solenoid the clamp is right: fast release is what you want, and
the event happens twice a shift.

On a **PWM** solenoid it is wrong twice over. The clamp's fast decay *creates*
large current ripple, and then the FET dissipates that ripple's energy on every
cycle. A freewheel diode decays slowly, so the ripple is small and almost
nothing reaches the FET. For EPC — a current-controlled pressure solenoid — the
smaller ripple also matters for control quality, which is likely why Ford
specified it.

**So: PWM loads get an external freewheel diode to 12 V. On/off loads do not.**

| Load | Drive | Gate from | Clamp strategy |
|---|---|---|---|
| HO2S heaters ×4 | resistive | expander, 5 V | **nothing** — no stored energy |
| SS1, SS2, CSS | on/off | expander, 5 V | integrated 42 V clamp |
| IMCC | **[CONFIRM]** | expander, or native if PWM | freewheel if PWM |
| **EVAP purge, EGR regulator** | **PWM** | **native timer + buffer** | **freewheel diode to 12 V** |
| **TCC, EPC** | **PWM** | **native timer + buffer** | **freewheel diode to 12 V** |
| **IAC valve** | **PWM** | **native timer + buffer** | **freewheel diode — to VPWR, no new pin** |

**PWM loads take native timer pins, not the expander.** An earlier revision put
EVAP purge and EGR regulator on the MCP23S17 chain, because outputs had been
split into fast and slow by *current and criticality* — and PWM is neither fast
nor critical, so it landed on the slow side. **An SPI expander cannot generate
PWM**: every edge is a bus transaction, with microseconds of latency, no
hardware timing, and jitter from whatever else shares the bus. The pin budget
absorbs the move without comment.

> The expander chain has since been dropped entirely — every signal is native,
> 76 of ~114. This finding was the first crack in it: outputs had been split by
> *current and criticality* when the real question was *what the pin has to do*.
> [`review-expander-chain.md`](review-expander-chain.md)

#### EPC and TCC: the same part, one in DPAK

[`v1-scope.md`](v1-scope.md) listed these as "native PWM", which allocates
*pins* rather than drivers, so neither appeared in the channel budget below.
**They take NCV8405A as well** — the part is rated 6 A and already on the board,
so the only real question is dissipation.

| | Part | |
|---|---|---|
| **TCC** | `NCV8405ASTT1G` SOT-223, **pour it** | **1.44 A worst case** (Ford spec 10–16 Ω) against 1.82 A on a minimum pad — see below |
| **EPC** | **`NCV8408BDTRKG` DPAK** | **4.12 Ω, 13.7 mH measured** → τ = 3.33 ms, 3.50 A full-on, but current-regulated in use so milliwatts. See below |

Dissipation limits at a 60 °C in-cavity ambient, 150 °C junction, and the hot
R<sub>DS(on)</sub> of 210 mΩ:

| Package and copper | Rθ<sub>JA</sub> | Budget | Max I<sub>rms</sub> |
|---|--:|--:|--:|
| SOT-223, min pad | 130 °C/W | 0.69 W | 1.82 A |
| SOT-223, 1 in² pour | 72 °C/W | 1.25 W | 2.44 A |
| **DPAK, 1 in² pour** | 50 °C/W | 1.80 W | **2.93 A** |

For a PWM load `I_rms = I_peak × √duty`, so DPAK with a pour covers a 3 A peak
at up to ~95 % duty. **That is the threshold to check against**, and EPC on this
transmission runs *high* duty at light load — a 4R70W's EPC gives maximum line
pressure at minimum current, so high duty is a normal cruising condition, not an
extreme.

#### EPC takes the NCV8408B, not the NCV8405A

Same family, same 42 V clamp, same package — built for the higher-current end.
Datasheet:
[`Datasheets/NCV8408BDTRKG-datasheet-C500319.pdf`](Datasheets/NCV8408BDTRKG-datasheet-C500319.pdf).

| | NCV8405A, DPAK | **NCV8408B, DPAK** |
|---|--:|--:|
| R<sub>DS(on)</sub> at 150 °C | 210 mΩ | **120 mΩ** |
| Rθ<sub>JA</sub> | 50 °C/W | 55 °C/W |
| **Max I<sub>rms</sub> at 60 °C** | 2.93 A | **3.69 A** |
| Current limit | 6 / 9 / 11 A | **10 / 13 / 16 A** |
| Load dump | 53 V | **63 V** |
| Thermal shutdown | auto-restart | **latched** |
| E<sub>AS</sub> | 275 mJ | 185 mJ |

Its Rθ<sub>JA</sub> is *worse*, but the on-resistance is nearly half, and that
wins: **the threshold moves from 2.9 A to 3.7 A RMS**, which clears a 3 A peak at
100 % duty rather than sitting on the edge of it.

> ✅ **TCC CLOSED from Ford's own spec** — `4r70W-Test-Key-Solenoid.png`, test
> step A7, gives the shift-solenoid resistances outright:
>
> | Solenoid | Ford spec | I at 14.4 V | P in NCV8405A |
> |---|---|--:|--:|
> | SSA | **20–30 Ω** | 0.48–**0.72 A** | 0.109 W |
> | SSB | **20–30 Ω** | 0.48–**0.72 A** | 0.109 W |
> | **TCC** | **10–16 Ω** | 0.90–**1.44 A** | **0.435 W** |
>
> **TCC is the hot one, and it is worse than this document assumed.** The
> channel-budget table guessed *"~0.5–1 A"* for the shift group. SSA and SSB land
> inside that. **TCC reaches 1.44 A — half again over the top of the estimate —
> because its coil is half the resistance.**
>
> It still fits: against the **1.82 A RMS** a SOT-223 on a minimum pad allows,
> 1.44 A at 100 % duty is **79 % of the limit**. But 26 % of margin on a
> *worst-case* coil is thinner than *"~1 A class"* implied, and a fully applied
> TCC at 100 % duty is an ordinary cruising state, not an extreme.
>
> **Give TCC a pour**, as IAC already has — 2.44 A at 1 in² turns 26 % of margin
> into 70 %. It costs copper, not parts.
>
> ✅ **NOT COOKED — Ford specs EPC at 2.48–5.66 Ω** (`4R70W_Ford_Transmission_Service_Manual[Helms].pdf`,
> *Resistance/Continuity Tests — EPC Solenoid*). **4.12 Ω is mid-range.** The
> second sample is no longer needed to validate this one, and the `L/R²`
> shorted-turn test below is moot for EPC.
>
> ⚠ **But Ford's minimum moves the fault case the wrong way:**
>
> | R | Full-on at 14.4 V | P | T<sub>j</sub> |
> |--:|--:|--:|--:|
> | **2.48 Ω — Ford min** | **5.81 A** | **4.05 W** | **283 °C** |
> | 4.12 Ω — ours | 3.50 A | 1.47 W | 141 °C |
> | 5.66 Ω — Ford max | 2.54 A | 0.78 W | 103 °C |
>
> **At the low end of spec a stuck-on EPC does not trip the NCV8408B's 10 A
> current limit** — 5.81 A is nowhere near it — so the **latched thermal
> shutdown is the only thing that stops it.** That is precisely why this part was
> chosen over the auto-restart sibling, and it is now load-bearing rather than
> belt-and-braces. **Normal operation is unchanged: current-regulated,
> milliwatts.**
>
> ~~One sample, from a failed transmission, and it may be a low one.~~ 4.12 Ω
> sits at the **bottom** of the 3.5–6 Ω band, which is where a coil with shorted
> turns would land. A second unit is being pulled. **There is a clean test**:
> `R ∝ N` and `L ∝ N²`, so lost turns drop L faster than R and the ratio
> **L/R² stays constant** for a healthy part. Ours is **L/R² = 0.807**.
> If the second sample comes out near 0.807 it is unit spread; **if its L/R² is
> higher, this one has shorted turns.**
>
> **Keep both numbers either way, because they are worst-case for different
> things:** the *lowest* resistance is worst for the driver (highest current),
> and the *highest* inductance is worst for the PWM frequency (longest τ). So
> size the thermals on 4.12 Ω even if it proves damaged, and take τ from the
> healthy sample.
>
> ✅ **EPC MEASURED: 4.12 Ω.** That confirms it as the EPC (the 3.5–6 Ω band —
> TCC is 10–16, SSA/SSB 20–30) and it clears the threshold, but not by much:
>
> | Driven | I | P in the FET | T<sub>j</sub> |
> |---|--:|--:|--:|
> | **Full-on, 14.4 V** | **3.50 A** — 95 % of the 3.69 A limit | 1.47 W | **141 °C** |
> | I<sub>L</sub> = 0.5 A, 14 % duty | 0.50 A | 0.004 W | 60 °C |
> | I<sub>L</sub> = 1.0 A, 29 % duty | 1.00 A | 0.034 W | 62 °C |
>
> **But EPC is never driven full-on.** It is a **variable-force** solenoid,
> regulated to a commanded *current* rather than switched hard over. With the
> inductance holding coil current roughly flat at I<sub>L</sub>, the FET conducts
> only during the on-time: `P = I_L² · D · R_DS`, and `D = I_L·R / V`. **At a
> 4R70W EPC's real operating range that is milliwatts.**
>
> So **4.12 Ω does not change the part.** The NCV8408B stays, and its margin at
> the operating point is enormous rather than 5 %.
>
> **And the fault case is already covered by a choice made for this reason.** A
> firmware hang at 100 % duty gives 1.47 W and 141 °C — 9 °C from the limit. That
> is what the NCV8408B's **latched** thermal shutdown is for: it trips, latches,
> and firmware owns the retry. *(§ Latched thermal shutdown is the right
> behaviour.)*
>
> **[MEASURE]** still open: **EPC's operating current**. The resistance is
> settled; the operating current is what actually sets the dissipation, and the
> table above spans milliwatts to 1.47 W across it.

**Latched thermal shutdown is the right behaviour**, and for the same reason the
TPS2H160B's `THER` is strapped to latch: firmware owns the retry, the fault
cannot thermally cycle, and on EPC an auto-restarting driver would oscillate
line pressure.

#### The latch interacts with PWM, and this is easy to miss

The latch clears when the gate is held below V<sub>LR</sub> (~1.4 V) for
**t<sub>LR</sub> = 10 ms minimum**. **PWM pulls the gate low every cycle.** If the
off-time exceeds that, normal operation clears the latch every cycle and the
protection is silently defeated:

| PWM | Period | Off-time at 10 % duty | |
|---|--:|--:|---|
| 50 Hz | 20.0 ms | 18.0 ms | **defeats the latch** |
| 100 Hz | 10.0 ms | 9.0 ms | holds, barely |
| **200 Hz** | 5.0 ms | 4.5 ms | **holds** |

**Drive EPC and TCC at ≥ 200 Hz.** That is a firmware constraint derived from
the driver, and nothing else in the design would have surfaced it.

#### ✅ EPC inductance measured: 13.7 mH — and it adds a second, compatible bound

`L = 13.7 mH` against the measured `R = 4.12 Ω` gives **τ = L/R = 3.33 ms**,
which is *longer than a 200 Hz period*. The coil never settles:

| PWM | τ/T | Ripple p-p at I<sub>L</sub> = 1 A |
|--:|--:|--:|
| **200 Hz** | 0.67 | **1.07 A — 107 %** |
| 500 Hz | 1.66 | 0.43 A — 43 % |
| **1 kHz** | 3.33 | **0.21 A — 21 %** |
| 2 kHz | 6.65 | 0.11 A — 11 % |

**The two constraints do not fight.** 200 Hz was a **floor**, set by the
NCV8408B's latch-clear time — below it, normal PWM off-time clears the latched
thermal shutdown every cycle and defeats the protection. The inductance sets a
requirement on the *other* side: **for current regulation rather than protection,
1–2 kHz.** Both are satisfied together.

> **Some ripple is wanted.** A pressure-control solenoid's valve has static
> friction, and Ford dithers EPC deliberately to break it. So the target is a
> *chosen* ripple, not the smallest achievable one — which makes the low-kHz
> region the right place to be rather than a compromise.

#### And it quantifies why the freewheel diode is not optional

`E = ½LI² = ` **6.85 mJ** per cycle at 1 A. A single such pulse is **27× inside**
the NCV8408B's 185 mJ avalanche rating — which is exactly the reasoning that
makes "the integrated clamp will cope" sound plausible. It does not, because it
is not a single pulse:

| PWM | Clamp dissipation if there were no diode |
|--:|--:|
| 200 Hz | 1.37 W |
| **1 kHz** | **6.85 W** |
| 2 kHz | 13.70 W |

**With the diode instead: 0.355 W**, conducting I<sub>L</sub> through a 0.5 V
V<sub>f</sub> for the 71 % off-time. Schottky, as specified — no reverse recovery
to pay for at kHz rates.

**EPC is now fully characterised except its operating current.**

#### Gate drive: a second 74HCT541, for the same reason as the first

**Every dissipation figure above is R<sub>DS(on)</sub> at V<sub>GS</sub> = 5 V** —
including the 3.69 A that selected this part. Neither driver specifies
R<sub>DS(on)</sub> at 3.3 V, and both have V<sub>GS(th)</sub> up to 2.0–2.2 V, so
at 3.3 V they conduct without being fully enhanced and the number is simply not
guaranteed.

The native timer pins are **3.3 V**. So the four PWM channels — EVAP, EGR, TCC,
EPC — are exactly the ones that would get the weakest gate drive, and EPC is the
one where it matters most.

**Buffer them to 5 V with a second `74HCT541`**, the same part and the same
argument as [the ignition stage](#recommended-one-74hct541-for-all-eight-coils):
HCT inputs take 3.3 V as a valid high, the output is a full 5 V, and one octal
package covers four channels with four to spare.

Use its enables the same way: **both `OE` pulled up to 5 V through 10 kΩ**, so
the outputs are high-impedance at power-on. [`custom-board.md`](custom-board.md)
already asks for this — *"the fuel pump relay and the EVAP, EGR and IMCC
solenoids … all should default off."*

~~The expander-driven channels need no buffer, **provided the MCP23S17 chain
runs at 5 V.**~~ **Struck — the requirement was wrong and is now resolved.**

At V<sub>DD</sub> = 5 V the MCP23S17's own V<sub>IH</sub> is
0.8 V<sub>DD</sub> = **4.0 V** — the same figure this document computes for the
drain-sense divider below — so a 3.3 V SPI master cannot clock it. It also put
5 V on the ADS8588H static pins, whose absolute maximum is DVDD + 0.3 V.

**Settled: the chain runs at 3.3 V, and these eight gates are buffered by a
third 74HCT541 at 5 V.** The buffer this requirement existed to avoid costs one
20-pin part that already appears twice on this board, and it brings a hardware
`OE` the chain wanted anyway. See
[`review-expander-chain.md`](review-expander-chain.md) §1, §2 and *Resolved*.

> The **2.2 kΩ** series gate resistor below forms a divider with the NCV8408B's
> **25.5 kΩ internal gate resistance**, so 5 V arrives as 4.6 V. Small, but it
> stacks with the above — another reason not to start from 3.3 V.

#### A PWM-friendly diagnostic comes with it

Gate input current is **25 µA normal, 440 µA latched** — an 18× step. That
matters because the drain-sense scheme above **needs synchronising to the PWM**,
and this does not:

| Series gate R | Normal | Latched |
|---|--:|--:|
| 2.2 kΩ | 110 mV | **0.97 V** |
| 4.7 kΩ | 235 mV | **2.07 V** |

Against the part's **25.5 kΩ internal gate resistance**, a 2.2 kΩ series
resistor is negligible for switching speed. Worth considering on the two PWM
channels in place of a synchronised drain sample.

E<sub>AS</sub> is lower than the NCV8405A's — 185 mJ against 275 mJ — which
costs nothing here, because these channels have **freewheel diodes and the clamp
should never engage.** It matters only if a freewheel diode opens.

#### The freewheel returns: two spare EEC-V pins

A freewheel diode goes *across the load*, and the ECU only sees the low side —
the solenoid feeds run out in the harness. Ford's diagrams show **neither feed
reaches the PCM**:

| Feed | Serves | Source |
|---|---|---|
| **1138 VT/WH** | TCC, EPC (and SSA/SSB, which need no diode) | BJB fuse 24, 15 A, off the PCM power relay |
| **391 RD/YE** | EVAP purge, EGR regulator, IMCC | Battery Junction Box |
| 361 RD | *the PCM's own VPWR* | a third branch |

Returning the diodes to VPWR would recirculate out through the connector, across
the Battery Junction Box and over two fuses. **28 EEC-V pins are unused**, so
bring the real feeds in instead:

| New pin | Circuit | Chosen because |
|--:|---|---|
| **82** | **1138 VT/WH** | adjacent to EPC on pin 81 |
| **48** | **391 RD/YE** | sits between EGR (47) and EVAP (56) |

Two wires buy a **local, tight recirculation loop** for all five PWM solenoids
instead of one that leaves the box.

**Diode spec:** the shared pin carries the sum of its group's recirculation
current — worst case ~4 A on pin 82 if TCC and EPC switch together, ~1.5 A on
pin 48. **≥ 60 V, 3 A, Schottky, AEC-Q101.** Schottky rather than fast-recovery:
no reverse recovery at PWM rates, and the lower V<sub>f</sub> gives the slower
decay that is the whole point. The 60 V is because the diode sits reverse-biased
at the supply whenever the FET is on, and that supply reaches ~35 V in a load
dump.

#### IAC: the one PWM load whose return is already inside the box

| | |
|---|---|
| PCM pin | **83**, circuit 264 WH/LB, C110 |
| Feed | **361 RD** — *the ECU's own VPWR*, at pins 71 and 97 |
| Current | ~1–2 A (Ford IAC, ~6–13 Ω) |
| Driver | **NCV8405A, SOT-223 with a 1 in² pour** |
| Gate | **74HCT541** channel 5 of 8 |

Because its feed *is* VPWR, **IAC needs no new connector pin** — unlike the five
solenoids on 1138 and 391. Its freewheel diode returns to a node already
present.

> **Connect that diode on the *connector side* of the current shunt.** The
> LTC4364's 10 mΩ shunt sits between the VPWR pins and the internal rail, and
> the INA238 measures across it. Returning the diode to the *internal* rail
> would push recirculation current **backwards through the shunt** and corrupt
> the battery-current reading at PWM rate. Returned at the pin, the loop closes
> through the harness and never touches it.

Thermally, SOT-223 with a pour carries **2.44 A RMS**, and for a PWM load
`I_rms = I_peak × √duty`.

> **[MEASURE]** the IAC valve's resistance and duty range. **Above 2.44 A RMS it
> wants DPAK**, the same threshold question as EPC.

#### Sense both new pins — they earn a second job

Put a **100 kΩ / 10.5 kΩ divider** on each into an internal ADC, the same
network as the drain sense. It pays for itself twice:

- **EPC's open-loop compensation gets the real supply voltage.** The section
  below proposes compensating duty for `V × duty / R(T)` using V<sub>BAT</sub>
  and TFT. **Pin 82 is strictly better than V<sub>BAT</sub>** — it is the actual
  solenoid supply, after the fuse and the harness drop.
- **A blown BJB fuse 24 becomes one DTC instead of four.** Without this, losing
  1138 presents as TCC, EPC, SSA and SSB all failing at once with nothing to
  distinguish it from a harness or driver fault.

> These are two new **12 V entries into the box**. They are fused upstream
> (15 A on 1138), but they must be routed as harness-facing power rather than
> signal, and kept away from the analogue section.

#### Open-loop duty is a control decision, not a driver one

The legacy firmware drove both as **open-loop duty** (`tccDuty`, `epcDuty`), with
no current feedback. A production PCM closes the loop on EPC current, and the
reason is physical: **solenoid copper rises ~40 % in resistance from 20 °C to
120 °C**, so a fixed duty delivers ~40 % less current hot than cold. On EPC that
is line pressure drifting with transmission temperature.

Closing the loop in hardware would mean a sense resistor and an amplifier on
that channel. **It is probably unnecessary here:** battery voltage and **TFT are
already inputs**, and current ≈ V<sub>bat</sub> × duty / R(T) is a compensation
that costs nothing but arithmetic. Worth doing before adding hardware.

~~Two channels short becomes **eleven NCV8405A channels plus one NCV8408B**.~~

**Superseded by the channel budget below: thirteen channels, twelve NCV8405A
plus one NCV8408B.** This line predated the canister vent solenoid, which was
found reading Ford's diagrams, and the IAC driver, assigned in a later review.
A fourteenth channel — **VSS out** — is added below.

This also bounds
[`review-protection-sweep.md`](review-protection-sweep.md) §A1, which found
clamp energy rising 4× in a load dump. Once the loads are classified, **only the
~~three~~ two on/off shift solenoids can clamp at all — ⚠ three again on a
4R100**, whose coast clutch is a 20–30 Ω on/off load
([`4r100-deltas.md`](4r100-deltas.md)) — the heaters store
nothing, the PWM loads recirculate through their freewheel diodes, and **CSS does
not exist on a 4R70W** (see below).

| At 14.4 V | Clamp energy | Margin on E<sub>AS</sub> = 275 mJ |
|---|--:|--:|
| **0.5 A** — Ford's 30 Ω end | 37.5 mJ | 7.3× |
| **0.72 A** — Ford's 20 Ω end, **worst case** | **77.8 mJ** | **3.5×** |

> ⚠ **Corrected.** This said *"a Ford shift solenoid's real ~0.5 A"* and quoted
> **7.3×**. 0.5 A is the **30 Ω end** of Ford's specified 20–30 Ω — the
> optimistic one. **Energy goes as I², so at 20 Ω the margin more than halves,
> to 3.5×.** Still comfortable, and now a specified range rather than a single
> assumed value.

The `[MEASURE]` narrows to **SSA and SSB only**, and their *resistance* is now
specified by Ford — what remains is their **inductance**, which is what the
energy above actually turns on.

### Drain-voltage sense — the load diagnoses itself

A pull-down at the drain plus a divider into an expander input turns each
channel into a fault detector. **Toggling the FET is what makes it work**: one
reading is ambiguous, two are not.

| FET | Drain reads | Meaning |
|---|---|---|
| OFF | **high** (~12 V through the load) | healthy |
| OFF | **low** | **open load** — burnt element, unplugged connector |
| ON | **low** (~0.2 V) | healthy |
| ON | **high** | **short to battery**, or the FET is in current limit / thermal shutdown |

That last row is the *"HO2S heater circuit high"* fault — the P0135 family — and
it is the one a dumb driver cannot report at all.

**The pull-down is not optional.** Without it an open load floats and the
off-state test reads whatever the node happens to be holding.

#### Sizing the divider — and why it is not a logic input

The obvious implementation is a divider into a spare expander bit. **There are
no values that work.** The drain must read high at 12 V and must not exceed the
rail at 14.4 V charging:

```
12.0 V, engine off  ->  ABOVE VIH = 4.0 V   ratio >= 0.333
14.4 V, charging    ->  BELOW the 5 V rail  ratio <= 0.347
```

A **4 % window**, before resistor tolerance, V<sub>IH</sub> tolerance or supply
variation. The cause is structural: a logic input forces the threshold into
hardware, and the normal supply range is wider than the gap between "high" and
the rail.

**Sense into an STM32 internal ADC and put the threshold in software.**

| Drain | ADC sees |
|---|--:|
| 0.2 V, on | 0.02 V |
| 12.0 V, off | 1.13 V |
| 14.4 V, off, charging | 1.36 V |
| 35 V, load dump | 3.30 V |

**100 kΩ / 10.5 kΩ**, ratio 0.094 — scaled so a *load dump* lands at full scale
rather than so 12 V does. That is
[`review-protection-sweep.md`](review-protection-sweep.md)'s Pattern A applied
deliberately: size the divider against the fault coinciding with a load dump,
not against the nominal. **No clamp is then needed** below 35 V.

The analogue value is also a better diagnostic than a bit — a partially shorted
heater element reads between the states rather than tipping one way.

**Internal ADC channels are not plentiful** — [`adc-front-end.md`](adc-front-end.md)
counts **18 available**, Ethernet RMII having taken six. So drain sense is fitted
only where nothing else sees the circuit:

| Sensed | Why |
|---|---|
| **HO2S heaters ×4** | OBD-II heater circuit monitor |
| **EVAP purge, canister vent** | OBD-II EVAP monitor |

Everything else has better feedback than a drain voltage: **DPFE** measures EGR
flow, **gear-ratio mismatch** catches the shift solenoids, **RPM vs OSS** catches
TCC, **idle error** catches IAC, and EPC has the **NCV8408B's gate-current
flag** — which also needs no PWM synchronisation. Only IMCC loses diagnosis, and
it is the one load with neither a regulatory requirement nor a natural feedback
path.

> **Confirmed from Ford's diagrams.** The heaters are power-fed and
> PCM-grounded: upstream pair on **391 RD/YE** returning to PCM pins **93/94**,
> downstream pair on **1138 VT/WH** returning to pins **95/96** — two different
> supply circuits. See
> [`schematic-findings.md`](1999-Ford-F150-4wd-5.42v/schematic-findings.md) §3.
> The whole low-side case for this part rested on this.

### Channel budget

| Channels | Load | PCM pin | Drive |
|--:|---|--:|---|
| 4 | **HO2S heaters** | 93, 94, 95, 96 | resistive, ~1–2 A each |
| 1 | EVAP canister purge | **56** | PWM |
| 1 | EGR vacuum regulator | **47** | PWM |
| 1 | **Canister vent solenoid** | **67** | on/off — *newly found* |
| 1 | IMCC | 46 | **[CONFIRM]**, leans on/off |
| 2 | SSA, SSB | 27 (*6), 1 (*11) | on/off |
| 1 | **TCC** | 54 | PWM, SOT-223 |
| 1 | **EPC** | 81 | PWM — **NCV8408B** DPAK |
| 1 | **IAC valve** | **83** | **PWM, SOT-223 with a pour** — see below |
| 1 | **VSS out** | **68** | frequency out, ~156 Hz — see below |
| **14** | | | |

Pin numbers and circuits are from Ford's own diagrams —
[`schematic-findings.md`](1999-Ford-F150-4wd-5.42v/schematic-findings.md).
Two corrections fell out of reading them:

- **A third EVAP solenoid exists**, the canister vent solenoid (C413, pin 67),
  which appeared in no list in this tree.
- **Only two shift solenoids appear** at the transmission connector, SSA and
  SSB. The CSS coast-clutch channel came from the MegaSquirt sheet and is not on
  Ford's 4R70W diagram. **[CONFIRM]** — it changes the count.

### VSS out — the fourth no-driver instance, closed

`review-ignition-injection.md` found tach and VSS with no driver assigned.
**Half of that was a phantom**: Ford's cluster diagrams show no discrete tach
output at all — the cluster takes engine speed over SCP.
[`schematic-findings.md`](1999-Ford-F150-4wd-5.42v/schematic-findings.md) §12.

What is real is **pin 68, circuit 679 GY/BK**, feeding the speed control servo
(C157), the GEM (C267) and the rear air suspension module (C277).

| | |
|---|---|
| Driver | **NCV8405A #13**, and it goes on **74HCT541 #2** |
| Why not #3 | **#3 is full at 8** — HO2S ×4, CVS, IMCC, SSA, SSB. The obvious home for a slow output has no room |
| Frequency | ~156 Hz at 8000 pulses/mile and 70 mph, against a part already running EPC at ≥200 Hz |

**Drive it open-drain, and leave the pull-up unpopulated.**

The open `[CONFIRM]` is what those three modules expect on 679 — 12 V, 5 V or
open-drain. **Open-drain with no pull-up is safe under all three readings**,
because the receiving modules set their own high level. Fit the pull-up
footprint and populate it only if measurement shows they need a driven high.

That ordering is the point: driving 12 V into a module that pulls up to 5 V is
the failure, and it is only reachable by populating first and measuring after.

### TACH and SPEED out — two reserved pins that stop on the board

There is no OEM discrete tach, and the OEM road-speed signal already has its
own driver and its own connector pin. Neither of these is that.

These are **two clean square-wave outputs on a test header** — engine speed and
road speed — for a scope, a bench rig or an aftermarket gauge. GPIOs are cheap
against 34 spare, so both are reserved now rather than requiring a respin later.

```
   GPIO --[ series R ]--> TACH  --+
                                  |  4-pin header, 3.3 V logic
   GPIO --[ series R ]--> SPEED --+  GND at both ends for probing
                                     ** STOPS HERE **
```

**Neither reaches the EEC-V connector.** `SPEED` in particular is *not* the VSS
output above — that one is `NCV8405A #13` to pin 68, open-drain, feeding three
OEM modules. This is a separate signal at logic level that happens to carry the
same information.

Expanding either later costs: one channel on 74HCT541 #2 (**2 spare** after
VSS), one NCV8405A, and a connector pin. The connector pin is the part to check
first — the OEM pinout has no tach assignment to inherit, and pin 68 is already
committed.

### Two cautions

### ✅ MEASURED: 6.12 Ω cold — and the PTC assumption was wrong

~~O2 heaters are PTC — cold inrush is several amps against ~1.5 A steady. The
part current-limits briefly at 6 A minimum, which is a soft-start rather than a
fault, and firmware must not read it as one.~~

**Measured on a new sensor: 6.12 Ω across the two white heater wires.** This
section predicted **0.9–1.8 Ω**, from *"PTC cold resistance is typically 1/5 to
1/10 of hot."*

**Cold/hot is 0.68, not 0.1–0.2. It is a mild PTC, not a lamp filament** — the
1/5-to-1/10 rule holds for incandescent filaments and some ceramic PTCs, and
nothing had checked whether it held here.

| | Predicted (0.9 Ω) | **Measured (6.12 Ω)** |
|---|--:|--:|
| Inrush at 14.4 V | 6.00 A *(limited)* | **2.35 A** |
| Reaches the 6 A current limit? | **yes** | **no — not close** |
| Peak FET dissipation | **54 W** | **1.16 W** |
| Four channels, harness | 24 A | **9.4 A** |

**The driver is never stressed.** There is no current-limit event, so there is
nothing to soft-start out of — and the firmware note about not reading current
limit as a fault becomes moot, because it will not happen.

Through the thermal tape at 2.93 °C/W, 1.16 W is **3.4 °C** of rise. The tape's
180 °C short-term rating stops being a consideration too.

#### PWM the heaters — but the driver was never the reason

Two separate problems that look like one, and answering the driver question
does not answer the other.

**The driver copes unaided.** Current limit *is* a soft start; it will survive a
cold PTC indefinitely. **But look at what coping costs it:**

```
  steady 1.5 A at 13.5 V -> hot resistance 9.0 ohm
  PTC cold resistance is typically 1/5 to 1/10 of hot

  cold R   load drops   FET drops   FET power
  1.80R       10.8 V       2.7 V      16.2 W
  0.90R        5.4 V       8.1 V      48.6 W
```

In current limit the FET drops whatever the cold heater does not, so it is
dissipating **tens of watts in a SOT-223** until the PTC warms enough to fall
below 6 A — hundreds of milliseconds, four channels, every cold start. Against
a steady-state 0.47 W that already gives a 61 °C rise on a minimum pad.

~~**And the harness sees 24 A** across four channels clamping together.~~
**Measured: 9.4 A across all four**, against 6 A steady.

**The real reason is the sensor.** A cold zirconia element with exhaust
condensation on it cracks when heated fast. OEMs **delay** the heater until the
exhaust is above dew point and *then* ramp duty — the delay matters as much as
the ramp, and neither has anything to do with the driver.

So: three things, in descending order of importance, none of which changes the
hardware.

| | |
|---|---|
| **1. Delay** turn-on after a cold start — time or CHT based | protects the sensor. The part that actually matters |
| **2. Ramp** duty from cold rather than stepping to 100 % | ~~keeps the driver out of current limit~~ — **measured, it never enters current limit at all.** The ramp is entirely for the ceramic |
| **3. Stagger** the four channels | ~~24 A becomes 10.5 A~~ — **measured inrush is 9.4 A across all four**, so this is now a nicety rather than a need. The firmware is sequencing them anyway |

#### The ramp does not have to run open loop

Rows 1 and 2 above are both guesses about the sensor's temperature — a timer, or
coolant temperature standing in for exhaust temperature.
[`o2-input-stage.md`](o2-input-stage.md) §7 measures the **cell's own
impedance** in circuit, and cell impedance falls steeply with temperature. So
the ramp can target the ceramic's actual state instead of an assumed heating
curve, and closed loop can start when the sensor says it is hot rather than when
a timer expires.

**It runs the other way too:** that measurement has to happen while the heater is
off, or heater current sharing harness ground beats against it. PWM is what
creates the off-windows. The two decisions were reached independently and each
turns out to supply what the other needs.

> ~~**[MEASURE]** the cold resistance of one sensor.~~ ✅ **Done: 6.12 Ω**, and
> it removed the question rather than answering it — see above. The ramp's
> starting point is now set by **the ceramic's tolerance for thermal shock**, not
> by the driver, because the driver never gets warm.
>
> ⚠ **Null the leads first.** Hot is 9.0 Ω, so cold is **0.9–1.8 Ω** — the same
> sub-2-ohm regime that made the coil primary read 3.6× high on a 2-wire
> measurement. And here the error does not merely shrink the answer, **it
> inverts it**: adding the ~1.3 Ω those leads contributed puts the reading at
> 2.2–3.1 Ω, at which the heater never pulls the 6 A limit and the driver
> appears to dissipate **nothing at all** instead of 16–49 W.
>
> | True cold R | Real FET power in limit | Read with +1.3 Ω of leads | Apparent FET power |
> |--:|--:|--:|--:|
> | 0.90 Ω | **48.6 W** | 2.20 Ω | **1.8 W** |
> | 1.80 Ω | **16.2 W** | 3.10 Ω | **0 W** |
>
> Four-wire, or short the probes and subtract. The whole reason this
> measurement exists is to decide between those columns.

**SOT-223 wants copper.** At 1.5 A and the hot R<sub>DS(on)</sub> of 210 mΩ that
is 0.47 W. On a minimum pad at 130 °C/W that is a 61 °C rise — about 121 °C
junction at a 60 °C cabin ambient, inside the 150 °C limit but not by much. On a
2″ pour at 72 °C/W it is a 34 °C rise and ~94 °C. **Pour copper, or use DPAK for
margin.**

**For PWM loads, synchronise the drain sample to the PWM state.** Sampling
mid-chop reads whatever the duty cycle happened to be at that instant, not the
health of the load.

---

## Considered and rejected: Infineon **BTS71040-4ESA** (SPOC™+2)

A 4-channel SPI high-side switch, 4 × 22.5 mΩ, with proportional current sense,
open-load detection in both states, and short-to-battery/ground diagnosis.
Recorded here because it is a genuinely strong part and will otherwise be
proposed again.

Datasheet: [`Datasheets/BTS710404ESAXUMA1-datasheet.pdf`](Datasheets/BTS710404ESAXUMA1-datasheet.pdf).

**It was considered for two jobs and lost both.**

### Not for VREF — the overload threshold is the wrong order of magnitude

| | |
|---|---|
| `IL(OVL0)` overload trip | **44–53 A** (35–39 A at 150 °C) |
| What [`vref-supply.md`](vref-supply.md) requires | **250 mA** with a fault flag |

A 44 A trip protects the silicon, not a 22 AWG harness wire — which is exactly
the argument `vref-supply.md` already used to demote the PTC to a backstop:
*a current limit only protects what it is set below*. Enforcing the limit from
the current sense in firmware is possible (k<sub>ILIS</sub> = 2000) but replaces
a microsecond hardware limit with a millisecond software loop. **VREF went to
the TPS2H160B-Q1 instead** — same idea, adjustable down to 250 mA.

### Not for the heaters — it is high-side, and the truck is not

Electrically it fits well: 4 channels for 4 heaters, 3 A nominal against 1–2 A
loads, with exactly the per-channel diagnostics OBD-II heater monitoring wants.
But it would require **cutting each heater's 12 V feed and routing four new runs
through the ECU**, abandoning the PCM heater pins. The NCV8405A gets comparable
fault coverage on the wiring that is already in the truck.

### What would bring it back

- **If the enclosure leaves the cabin.** AEC-Q100 **Grade 1** against the
  TBD62083A's 85 °C ceiling — see [`enclosure.md`](enclosure.md).
- **If proportional current measurement is ever needed** rather than the
  NCV8405A's high/low fault detection.
- Its 0.4 µA sleep current is invisible against the 780 µA
  [always-on](always-on-domain.md) budget, so that is never the objection.

The objection is fit, not quality: its sweet spot is 3 A high-side with
diagnostics, and this truck's loads are either well under it (relay coils, where
a dumb sink array is cheaper and simpler) or well over it (fans at 15–20 A, fuel
pump at 5–8 A).

---

## Summary

| Load | Part | Clamp | Drive |
|---|---|---|---|
| Coil ×8 | ISL9V3040 | 400 V | **74HCT541 buffer at 5 V** + 470 Ω |
| Injector ×8 | ZXMS6005DGQ | 60–70 V | **Direct from 3.3 V GPIO** + 470 Ω |
| Relays ×5, MIL | **TBD62083AFNG** | **built in**, to COMMON | **Direct from the expander**, 3.3 V or 5 V |
| Heaters ×4, solenoids ×8 | **NCV8405ASTT1G** | 42 V integrated — **PWM loads use a freewheel diode instead** | **Direct**, V<sub>GS(th)</sub> ≤ 2 V. Drain sense for diagnosis |
| **EPC** (PWM, high current) | **NCV8408BDTRKG** | 42 V, latched shutdown | **Direct**; ≥ 200 Hz PWM — see above |
| VREF feeds ×2 | **TPS2H160B-Q1** | 40 V rated | **High-side** from the 5 V rail, 250 mA limit, `CS` diagnosis |

None of the four needs a dedicated gate-driver IC. One octal buffer covers the
entire ignition side, the injectors need nothing at all, one sink array covers
every relay on the truck with three channels to spare, and one self-protected
FET type covers every remaining low-side load — while telling you when that load
has failed.

All four keep the rule from `custom-board.md`: **clamp both, dissipate
neither**, with the clamp voltage chosen for what the load is meant to do.

---

## ✅ CSS — it does not exist on a 4R70W, and that explains the MegaSquirt sheet

**The coast clutch solenoid is a 4R100 part.** The MegaSquirt mapping this
project has been cross-checking against **was developed on a 4R100**, not the
4R70W in this truck — which is why `CSS` appears on pin 20 of that sheet and
nowhere in Ford's 4R70W material.

That closes the `[CONFIRM]`, and it explains a pattern rather than just one
entry:

| | |
|---|---|
| **Connector C183** | ⭐ **ten cavities, four solenoids, and pins 1/9/10 empty** |
| **Ford's 4R70W wiring diagram** | no coast clutch solenoid |
| **Ford test step A7** | tests SSA, SSB, TCC — and stops |
| **MegaSquirt sheet** | lists CSS on pin 20 |

**C183 is the one that settles it** — a connector sheet listing every cavity,
with three of them empty. A fifth solenoid would have somewhere to go and does
not. See [`1999-Ford-F150-4wd-5.42v/transmission.md`](1999-Ford-F150-4wd-5.42v/transmission.md).

**Nothing on the board changes.** CSS was never in the thirteen NCV8405A
channels — the channel budget is HO2S ×4, EVAP purge, EGR regulator, canister
vent, IMCC, SSA, SSB, TCC, IAC and VSS out — and `pin-budget.md` was corrected
away from the `SS1/SS2/CSS` naming earlier. **EEC-V pin 20 is simply free.**

> **The wider lesson, and it is worth carrying.** The MegaSquirt sheet is a
> *different transmission's* mapping applied to this truck. Every transmission
> entry taken from it needs a Ford source behind it — and every one that matters
> now has: TR1/TR2/TR3A/TR4 against connector C182, TFT/TCC/EPC/SSA/SSB against
> the 4R70W diagram. **CSS was the only one left unconfirmed, and it was the one
> that was wrong.**