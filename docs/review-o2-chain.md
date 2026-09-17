# O2 chain review — narrowband today, wideband as an option

This chain was never reviewed on its own. It was covered incidentally by
[`review-analog-chain.md`](review-analog-chain.md) (which checked the *channel
allocation* and found it correct) and by
[`review-solenoid-chain.md`](review-solenoid-chain.md) (which checked the
*heaters* and found them correct). **Nothing checked the signal path itself**,
and that is where the problem is.

The review also settles the wideband question, because the input stage that
fixes narrowband is the same one wideband needs.

---

## 0. What exists today

Four sensors, confirmed against Ford's diagrams in
[`1999-Ford-F150-4wd-5.42v/schematic-findings.md`](1999-Ford-F150-4wd-5.42v/schematic-findings.md) §3:

| Sensor | Signal pin | Heater pin | Heater feed | Signal lands on |
|---|--:|--:|---|---|
| LF — bank 1 upstream | **87** | 94 | 391 RD/YE | ADS8588H **ch 2** |
| RF — bank 2 upstream | **60** | 93 | 391 RD/YE | ADS8588H **ch 3** |
| LR — bank 1 downstream | **61** | 96 | 1138 VT/WH | STM32 internal ADC |
| RR — bank 2 downstream | **35** | 95 | 1138 VT/WH | STM32 internal ADC |

**The heater half is in good shape** and this review does not disturb it:
power-fed by the truck and PCM-grounded, so low-side `NCV8405A`; resistive, so
no freewheel diode; drain-sense on all four because the OBD-II heater monitor
has no other observer. The expander review moves their gates behind a third
74HCT541, which also gives them the hardware `OE` that
[`review-expander-chain.md`](review-expander-chain.md) §4 wants.

**The signal half connects the sensor straight to the converter.** The
justification is in [`f150-1999-target.md`](f150-1999-target.md): *"True bipolar
±10 V / ±5 V inputs, so 0–5 V sensors connect directly with no scaling
op-amps."*

That is correct for TPS, MAP and MAF. **A HEGO is not a 0–5 V sensor.**

---

## 1. IMPORTANT — the cell is a high-impedance source into a 1 MΩ input

A zirconia narrowband sensor is a **galvanic cell**, not a driven output. Its
source impedance is tens of kΩ hot and climbs into the MΩ as it cools or ages.
The ADS8588H presents **1 MΩ resistive**, so the two form a divider:

```
  source Z     gain     450 mV reads     900 mV reads    error at rich peak
     10 k      99.0 %       446 mV           891 mV            -9 mV
     30 k      97.1 %       437 mV           874 mV           -26 mV
    100 k      90.9 %       409 mV           818 mV           -82 mV
    300 k      76.9 %       346 mV           692 mV          -208 mV
      1 M      50.0 %       225 mV           450 mV          -450 mV
```

This is the same 1 MΩ loading arithmetic
[`adc-front-end.md`](adc-front-end.md#the-battery-sense-divider) works through
for the battery divider. It was applied there and not here.

### Correcting what I said about this last turn

I described this as *"it biases low, which reads as lean, which adds fuel."*
**That is wrong, and the reason is worth keeping.**

A narrowband cell is extraordinarily steep near stoich — roughly 0.1 V to 0.9 V
across lambda 0.99 to 1.01, or **40 V per lambda**. A switching controller
compares against a 450 mV threshold, so a gain error moves the threshold in
*lambda* terms by almost nothing:

| Threshold-referred error | Δ lambda | Δ AFR |
|--:|--:|--:|
| 41 mV | 0.0010 | **0.015** |
| 82 mV | 0.0021 | **0.030** |
| 208 mV | 0.0052 | **0.076** |

**Closed-loop fuelling barely notices.** The damage is elsewhere.

### Where it actually bites: the OBD-II monitors

The HO2S monitors test **amplitude and activity**, not the crossing point. They
require the signal to reach roughly **above 0.7 V rich** and below 0.3 V lean:

```
     10 k source  ->  peak 891 mV   PASS
     30 k source  ->  peak 874 mV   PASS
    100 k source  ->  peak 818 mV   PASS
    300 k source  ->  peak 692 mV   FAILS the 0.7 V threshold
      1 M source  ->  peak 450 mV   FAILS
```

The compression is multiplicative, so it eats the **rich end only** — the lean
end is already near zero and stays there. The failure signature is therefore
*"sensor reaches lean but never reaches rich"*, which is exactly the
**P0133 / P0134 / P0136 lazy-or-dead-sensor** family.

**It fails toward false DTCs, and it fails worst on cold and aged sensors** —
the two cases where you most need to tell a struggling sensor from a broken one.
A healthy warm sensor at 30 kΩ passes everything; the design only misbehaves in
the region it exists to diagnose.

### The downstream pair have the same problem in a worse form

They sit on the **STM32 internal ADC**, which is a **switched-capacitor** input,
not a resistive one. There is no fixed divider — instead the sampling capacitor
must charge through the source impedance inside the sampling window, so the
error is a **settling** error that depends on sample time, and beyond some
source impedance it simply does not converge.

Worse, a switched-cap mux carries residue from the previously sampled channel,
so a high-impedance channel picks up **crosstalk from its neighbour** in the
scan order. On a chain that also carries six drain-sense channels switching
between 0 V and ~4 V, that is not a hypothetical.

> **[CONFIRM]** the maximum external impedance for the F767's ADC at the longest
> sampling time and the intended ADC clock. The mechanism is certain; the number
> is not, and there is no STM32 datasheet in the repo.

---

## 2. The fix: one buffer per channel — and it pays for itself twice

A unity-gain buffer with a **picoamp-class input** removes the divider entirely.
Two things come with it that are worth as much as the fix.

### It closes the open `[DECIDE]` on series protection resistance

[`review-analog-chain.md`](review-analog-chain.md) §4 records that
[`harness-protection.md`](harness-protection.md) asks for *"series resistance +
clamp"* on analog inputs and **no value is given anywhere**, with a `[DECIDE]`
against acquisition time.

On an unbuffered channel that decision is genuinely hard: series resistance adds
straight into the 1 MΩ divider above, so protection and accuracy trade directly.
**Behind a buffer they stop trading.** A picoamp input turns any series
resistance into zero error — 10 kΩ × 1 pA is 10 nV — so the resistor can be
sized purely for fault current.

### But it moves the protection boundary, and that must be deliberate

The ADS8588H's **9 kV clamp is one of the two reasons that part was chosen**.
Putting a buffer in front of it means the *buffer* now faces the harness, and a
general-purpose op-amp has nothing like that ruggedness.

**The clamp does not disappear, it relocates:** series resistance plus
rail-clamp diodes ahead of the buffer, sized so a short to battery is bounded by
the resistor and carried by the clamp. This is the pattern already established
three times in this project — see
[`vref-supply.md`](vref-supply.md) and [`f150-1999-target.md`](f150-1999-target.md)
§5.3. It is not new work, but it is **not free either**, and any claim that "the
ADC's clamp protects this input" stops being true the moment the buffer goes in.

### What the op-amp has to be

| Requirement | Value | Why |
|---|---|---|
| ~~Input bias current ≤ 100 pA at +125 °C~~ | **not a constraint** | ~~*the selection criterion*~~ — **wrong**, see the correction in §3 |
| Input offset | ≤ 1 mV | against a 450 mV switch point |
| Input range | **rail-to-rail**, includes ground | narrowband sits at 0.1 V; wideband reaches 5 V |
| Output | rail-to-rail | same |
| Supply | single 5 V analog | the rail is already there |
| Qualification | **AEC-Q100**, −40 to +125 °C | consistent with the rest of the board |

**Input bias current at temperature is the specification that matters, and it is
not the one datasheets lead with.** A CMOS op-amp quoting "0.2 pA typical"
quotes it at 25 °C; the term is ESD-diode leakage, which roughly doubles every
10 °C. At 125 °C the same part can be three orders of magnitude worse. Against
the 10 MΩ bias resistor of §3, 1 nA is **10 mV of error** — larger than the
loading error being fixed.

> **[DECIDE]** the part. `OPA2376-Q1` is the obvious starting candidate — CMOS,
> RRIO, AEC-Q100 — but **[CONFIRM]** its bias current over the full temperature
> range, not the 25 °C headline, and check it against a zero-drift alternative.
> Two duals cover all four channels.

---

## 3. An unbiased high-impedance input has no open-circuit diagnostic

Connecting a picoamp input to a sensor that has been unplugged leaves the node
floating. It will drift somewhere — probably to a rail via clamp leakage — and
whatever it reads is not a defined value.

Ford biases these inputs to about **0.45 V** for exactly this reason: an open
circuit parks at the bias voltage and the diagnostic becomes *"sitting at 0.45 V
with no switching activity"*, which is a monitor that already has to exist.

The bias resistor loads the cell just as the ADC did, so it has to be large —
and then the op-amp's bias current flowing through it becomes an error, which is
where §2's temperature requirement comes from. The two pull opposite ways:

```
  error at a 100 k source, rich peak:

     R_bias      loading      bias current @ 1 nA      @ 100 pA
      1 M        45.0 mV            1.0 mV              0.1 mV
    3.3 M        13.6 mV            3.3 mV              0.3 mV
     10 M         4.5 mV           10.0 mV              1.0 mV
     22 M         2.0 mV           22.0 mV              2.2 mV
```

~~**With a genuinely picoamp part, 10 MΩ is the right value** — 4.5 mV of loading
and 1 mV of bias error against the 82 mV it replaces. With a 1 nA part there is
no good value, which is the point of making bias current the selection criterion
rather than an afterthought.~~

> ⚠ **The bias-current column above is wrong, and so is the conclusion drawn
> from it.** `I_B × R_bias` is the **open-circuit** value. Bias current flows
> into the non-inverting node, whose Thévenin impedance is **Rs ‖ R_bias**, and
> with a sensor connected Rs dominates — at 100 kΩ and 200 pA the real
> contribution is **20 µV**, not millivolts.
>
> There is therefore no opposing term, bias current is **not** a selection
> criterion, and R_bias should simply be large. Settled at **22 MΩ** in
> [`o2-input-stage.md`](o2-input-stage.md) §3, where leakage — which *does*
> scale with R_bias — sets the upper limit instead.

### The bias source needs no op-amp

A common mistake here is to buffer the 0.45 V reference. It does not need it —
the bias source impedance only has to be small compared with **10 MΩ**, and a
plain divider off the 5 V analog rail is smaller by a factor of a thousand:

| Divider from 5 V | V<sub>bias</sub> | Z<sub>src</sub> | Draw | Channel-to-channel coupling |
|---|--:|--:|--:|--:|
| **91 kΩ / 9.1 kΩ** | **455 mV** | 8.3 kΩ | 50 µA | **0.083 %** |

One divider, one 100 nF, and a 10 MΩ per channel. All four channels share it;
they are isolated from each other by 10 MΩ against an 8.3 kΩ source. The 50 µA
comes off the **switched** 5 V analog rail, so it never reaches the parked
budget owned by [`always-on-domain.md`](always-on-domain.md).

---

## 4. Wideband — three architectures, and only one of them is cheap

The good news first: **wideband does not suffer §1 at all.** Every wideband
architecture presents a low-impedance, actively driven 0–5 V output, whether
that is an external module's analog out or a CJ125's `UA` pin. The loading
problem is narrowband-specific.

### W1 — external controller module, 0–5 V analog out

AEM X-Series, Innovate LC-2, 14Point7 Spartan 3 and similar: a sealed box that
owns the sensor, the heater, the pump-current loop and the calibration, and
hands back a linear 0–5 V.

| | |
|---|---|
| **Board cost** | **zero** — it lands on ch 2 / ch 3, already allocated to upstream O2 |
| Heater control | theirs |
| Calibration | theirs, including the sensor's trim resistor |
| Cost of reversal | unplug it |
| Against | an extra box and loom per bank; the transfer function is theirs and must be entered in config; their internal filtering adds latency you cannot see or remove |

### W2 — CJ125 on the board, as the legacy ESP32 firmware does

`src/CJ125Controller.cpp` is a working dual-bank implementation: per bank an SPI
chip-select, a 100 Hz heater PWM, `UA` on an ADC and `UR` on an ADC, driving the
condensation / ramp / PID heater state machine.

**It fits, and that is not obvious.** Working it against the owned budgets:

| Resource | Need | Where it comes from | After |
|---|--:|---|---|
| `UA` ×2 | 2 precision ch | **ch 2 / ch 3, freed** — the narrowband upstream channels are what wideband replaces | 8/8, unchanged |
| `UR` ×2 | 2 internal ch | 3 spare, per [`adc-front-end.md`](adc-front-end.md#the-internal-adc-budget) | 17/18, **1 spare** |
| Heater PWM ×2 | 2 timer pins | ~114 native pins, 37 used — [`platform-decision.md`](platform-decision.md) | fine |
| SPI `CS` ×2 | 2 pins | same | fine |

The pin budget stopped being a constraint when the platform moved to the
STM32F767ZI, which is what makes this affordable. **The ADC budget is the tight
one, and it clears by a single channel.**

| | |
|---|---|
| **Against** | **Sourcing.** Bosch has effectively withdrawn the CJ125; what is available is module-grade rather than reel-grade. **[CONFIRM]** before designing it in — this is the risk that decides W2 |
| | The two upstream heater channels change from **on/off to PWM**, which per [`output-drivers.md`](output-drivers.md#the-integrated-clamp-does-not-replace-a-freewheel-diode) means they need a freewheel diode that the narrowband heaters correctly do not |
| | The heater profile is not a duty number — condensation phase, ramp, then PID against a calibrated `UR`. That logic exists in the legacy tree and would need porting, not writing |
| **For** | No external boxes; full visibility of `UR`, `UA`, diagnostics and heater state, which the sealed modules do not expose |

### W3 — a current-production integrated lambda AFE

The honest position: **I do not have a part to recommend.** NTK and Elmos both
make lambda front-ends used by OEMs, and there may be a current AD/TI part, but
I am not confident enough in availability or specification to name one, and this
is not a place to guess. **[SURVEY]** before ruling W2 in on sourcing grounds
alone — if a current-production part exists it beats a withdrawn one outright.

---

## 5. One input stage serves all of it

This is the finding that makes the wideband question cheap to defer.

```
  EEC-V pin ──[ 10k series ]──┬──[ clamp to 0 V / 5 V ]
                              │
                       [ 10 M ]──── 0.455 V bias node (91k/9.1k off 5 V)
                              │
                              └──► unity-gain buffer ──► ADC channel
```

| Source | Needs the buffer? | Needs the bias? | Works with this stage? |
|---|---|---|---|
| Narrowband HEGO | **yes** — §1 | **yes** — §3 | ✓ |
| External wideband, 0–5 V out | no | harmless: 10 MΩ against a low-Z output | ✓ |
| CJ125 `UA` | no | harmless, same reason | ✓ |

**Build the buffered stage for narrowband, and the wideband decision becomes a
populate-and-config change rather than a board change.** Nothing in §4 asks for
a different input stage; W1 and W2 differ in what they put *in front* of it.

Two consequences worth stating plainly:

- **The ±10 V range is mostly unused on these channels** and that is fine. At
  ±10 V an LSB is 305 µV, so a 450 mV switch point is resolved to 0.07 %. There
  is no case for gaining up the narrowband signal, and doing so would break
  wideband compatibility — which is precisely the trap this section avoids.
- **The downstream pair need the buffer regardless of which way you go**, since
  catalyst monitoring stays narrowband under every option. Four buffers, not
  two.

---

## 6. What changes beyond the input stage if you go wideband

Not a board question, but it belongs in the decision:

| | |
|---|---|
| **Sensors and bungs** | LSU 4.9 is a different sensor with a different connector and a **per-sensor calibration trim resistor in its plug**. The thread is the same M18 × 1.5, so the bungs carry over, but the sensors and pigtails do not |
| **The catalyst monitor changes shape** | The OBD-II cat monitor compares upstream switching against downstream switching. With a wideband upstream there is no upstream switching to compare — the algorithm becomes lambda-vs-downstream-voltage, which is what OEMs with wideband uses do, but it is not the same code |
| **Closed loop gets better in the place it matters** | A narrowband controls *only* at stoich. Wideband gives real closed-loop authority at part-throttle lean cruise and under enrichment, which is the actual reason to want it on a 5.4 |
| **The ADR4525 argument survives** | Wideband output is linear in lambda, so a reference error becomes a proportional AFR error rather than a threshold shift. The precision reference matters **more** under wideband, not less |
| **Heater current** | LSU 4.9 heaters are comparable to the narrowband units they replace, so [`power-supply.md`](power-supply.md#current-budget-first--it-decides-the-topology) is not disturbed — these are 12 V loads and never touched the 5 V rail |

---

## 7. Recommendation

**Build the buffered input stage now, on all four channels. Defer the wideband
decision, and take W1 first if you take it at all.**

> **Built.** The stage is specified in
> [`o2-input-stage.md`](o2-input-stage.md), which now **owns** this conditioning
> for all four channels. One open item remains: the op-amp, against four
> datasheet confirmations.

1. **Four buffers, 10 kΩ series, rail clamps, 10 MΩ bias to a shared 455 mV
   divider.** This is required for narrowband correctness regardless of what
   happens later, it closes the open `[DECIDE]` on series resistance, and it is
   the same stage every wideband path wants.
2. **If and when you switch: W1.** It costs nothing on the board, it is
   reversible in an afternoon, and it tells you whether wideband earns its place
   on this engine before you commit silicon to it.
3. **W2 only if W1 proves the value and sourcing clears.** It fits the budgets
   with one internal ADC channel to spare and there is working code to port —
   but a withdrawn part is a poor foundation, and **[SURVEY]** W3 first.

The thing not to do is design the input stage around narrowband in a way that
forecloses wideband. §5 shows that costs nothing to avoid.

---

## Summary

| # | Finding | Severity |
|---|---|---|
| 1 | The narrowband cell is a high-impedance source into a 1 MΩ resistive input — up to **−82 mV at a normal 100 kΩ**, worse cold and aged. The fuelling impact is negligible because the cell is 40 V/lambda near stoich, but it compresses the **rich peak below the OBD-II 0.7 V threshold** at 300 kΩ, generating false lazy-sensor DTCs exactly on the sensors being diagnosed | important |
| 1b | The downstream pair have it worse: a **switched-cap** input makes it a settling error, plus mux crosstalk from six drain-sense channels sharing the scan | important |
| 2 | Adding a buffer **relocates the protection boundary** off the ADS8588H's 9 kV clamp onto the op-amp. Series resistance and rail clamps must move in front of it — and behind a buffer the series value stops trading against accuracy, closing `review-analog-chain.md` §4 | important |
| 3 | A picoamp input with no bias network has **no open-circuit diagnostic**. ~~10 MΩ~~ **22 MΩ** to a 455 mV divider. ~~*and op-amp bias current at +125 °C becomes the part-selection criterion*~~ — **that part was wrong**, see the correction in §3: bias current contributes 20 µV with a sensor connected, and leakage sets the limit on R<sub>bias</sub> instead | important |
| — | Corrected from last turn: I called this a lean-bias fuelling error. It is not; it is a diagnostic-amplitude error | correction |

**Wideband:** all three architectures present a low-impedance output, so none of
them suffer finding 1. The buffered stage in §5 serves narrowband, an external
module and an on-board CJ125 without modification, so **the wideband decision
does not need to be made now** — which is the useful result, given that W2's
viability turns on a `[CONFIRM]` about a part Bosch no longer really sells.
