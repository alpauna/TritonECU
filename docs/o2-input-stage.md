# O2 input stage — four buffered channels

**This document owns the O2 signal conditioning**, for all four sensors and for
every sensor type they might be replaced by. It exists because
[`review-o2-chain.md`](review-o2-chain.md) found the sensors wired straight to
their converters, and a zirconia cell is a high-impedance galvanic source that
both converters load.

One stage, built four times, identical on every channel.

---

## 1. The circuit

```
   EEC-V pin  87 / 60 / 61 / 35
        │
     [ R1 10k ]                     fault-limiting
        │
        ├──[ C1 1n ]───────────── AGND
        │
        ├──[ D1 BAT54S ]──┬────── AGND
        │                 └────── +5VA        clamp at ~5.3 V
        │
        ├──[ R2 10M ]───────────► 455 mV bias node (shared, 8.3k)
        │
        │  << guarded high-Z node >>
        │
        └────────►│+ \
                  │    >───┬───  unity gain
            ┌────►│- /     │
            └──────────────┘
                           │
                       [ R3 1k ]
                           │
                           ├──[ C2 1u ]────── AGND      159 Hz
                           │
                           └──────────────► ADC channel

   JP (not fitted) links the high-Z node to the ADC side, bypassing
   the buffer for a fixed 0-5 V wideband module -- see section 5.
```
| Ref | Value | Job |
|---|---|---|
| **R1** | **10 kΩ**, 1 %, ≥ 0.25 W | bounds fault current into D1 |
| **C1** | **1 nF**, C0G | RF, and it gives D1 something to work against |
| **D1** | **BAT54S** dual Schottky, to AGND and +5 V<sub>A</sub> | the clamp that the ADC used to provide |
| **R2** | **10 MΩ**, 1 % | open-circuit bias — §3 |
| **R3 / C2** | **1 kΩ + 1 µF** X7R | 159 Hz post-buffer filter — §4 |
| **JP** | link across the buffer | bypass for a fixed 0–5 V wideband module — §5 |

Shared by all four channels: the bias divider of §3, and two dual op-amps.

---

## 2. Why R1 is 10 kΩ, and why that costs nothing now

The value is set entirely by fault current, because
[`review-o2-chain.md`](review-o2-chain.md) §2 established that series resistance
stops trading against accuracy once there is a buffer behind it — 10 kΩ × 1 pA
is 10 nV.

D1 holds the node at roughly **5.3 V** (rail + Schottky V<sub>F</sub>):

| Fault | At the pin | Through R1 |
|---|--:|--:|
| Normal charging | 14.4 V | **0.91 mA** |
| Jump start / LTC4364 clamp | 27 V | **2.17 mA** |
| ISO transient | 40 V | 3.47 mA |
| **ISO 7637-2 pulse 1**, 2 ms | **−100 V** | **10.03 mA** |

BAT54S is rated 200 mA continuous, so every one of these is comfortable, and the
sustained cases are milliamps.

### The Schottky is doing something specific

An op-amp's input absolute maximum is normally `V+ + 0.3 V`, enforced by an
internal silicon diode that starts conducting around **`V+ + 0.6 V` = 5.6 V**.
D1 conducts at **5.3 V**, *below* that. So during a short to battery the
Schottky takes the current and the op-amp's internal ESD diode never turns on —
which is the whole reason for choosing Schottky over a signal diode here.

**Nothing in this stage relies on an ESD structure to carry a sustained DC
fault.** That was the concern that made this a finding in the first place: the
ADS8588H's 9 kV clamp is rated for that job and an op-amp's is not.

> The OPA2376 turns out to have more headroom than this was designed against:
> its signal-input absolute maximum is **(V−) − 0.5 V to (V+) + 0.5 V**, so
> −0.5 V to 5.5 V, and it specifies a **±10 mA** input current limit explicitly
> permitting operation beyond the rails when current-limited. D1 at 5.3 V sits
> inside that with margin to spare, and R1 bounds the worst case at 10 mA even
> if D1 were absent. §6.

### Where the fault current goes

Into the **+5 V analog rail**, which carries the ADS8588H (25 mA), two MAX9926s
(20 mA) and the op-amps. Against ~46 mA of standing load, even all four channels
shorted at 27 V injects 8.7 mA — absorbed without the rail moving.

---

## 3. Bias: 10 MΩ to a shared 455 mV node

A picoamp input on an unplugged sensor floats and reads nothing meaningful.
Biasing to ~0.45 V parks an open circuit at a known value, and *"sitting at
455 mV with no switching activity"* is a monitor that has to exist anyway.

**The bias source needs no op-amp.** Its impedance only has to be small compared
with R2, and a plain divider off the analog rail is smaller by a thousand:

```
   +5VA ──[ 91k 1% ]──┬──[ 9.1k 1% ]── AGND
                      │
                   [ 100n ]        455 mV, Zsrc 8.3k, draws 50 uA
                      │
                     AGND
```

| | |
|---|---|
| V<sub>bias</sub> | **455 mV** |
| Z<sub>src</sub> | **8.3 kΩ** — 1200× below R2 |
| Draw | **50 µA**, off the **switched** rail, so it never reaches the parked budget owned by [`always-on-domain.md`](always-on-domain.md) |
| Channel-to-channel coupling | **0.083 %** — each channel is isolated by its own 10 MΩ |

### What 10 MΩ buys and what it costs

R2 loads the cell exactly as the ADC used to, and the op-amp's bias current
through R2 is an error in the other direction. At a 100 kΩ source, rich peak:

| R2 | Loading error | Bias-current error @ 1 nA | @ 100 pA |
|--:|--:|--:|--:|
| 1 MΩ | 45.0 mV | 1.0 mV | 0.1 mV |
| 3.3 MΩ | 13.6 mV | 3.3 mV | 0.3 mV |
| **10 MΩ** | **4.5 mV** | 10.0 mV | **1.0 mV** |
| 22 MΩ | 2.0 mV | 22.0 mV | 2.2 mV |

**10 MΩ is right only with a genuinely picoamp part** — 4.5 mV of loading and
1 mV of bias error, against the 82 mV being removed. With a 1 nA part there is
no good value at all, which is why §6 makes bias current the selection criterion
rather than a checkbox.

> **Settled at 10 MΩ.** The chosen part is ~200 pA at +125 °C, so the real total
> is **6.5 mV**. The optimum moves to 15 MΩ for 6.0 mV, which is not worth
> chasing. Worked through in §6.

### One fault couples slightly into the other three

A channel shorted to battery sits at D1's 5.3 V, pushing 0.48 µA through its
R2 into the shared 8.3 kΩ bias node and lifting it **4 mV**. Four shorted
channels lift it 16 mV. Small, only present during a fault, and worth knowing
before someone chases it: **a single shorted O2 wire shifts the other three
channels' zero by 4 mV.**

### Leakage is the real enemy at 10 MΩ, so guard the node

Surface leakage across contaminated FR4 can reach nanoamps, which through 10 MΩ
is tens of millivolts — larger than everything this stage was built to fix.

**Ring the high-impedance node with a guard trace driven from the buffer
output.** The buffer is unity gain, so guard and node sit at the same potential,
no voltage appears across the surface path, and leakage current goes to zero.
This costs one trace and is the standard electrometer technique.

Conformal coating is a reasonable belt-and-braces addition but is not a
substitute — coating slows contamination, guarding removes the driving voltage.

---

## 4. The post-buffer filter, and why it is not on the input

An RC at the **input** would be wrong: the source impedance is the sensor's, and
that varies from 10 kΩ hot to megohms cold, so the corner frequency would move
with sensor temperature. Putting it **after** the buffer fixes R at a value we
choose.

| R3 + C2 | Corner | Gain error into 1 MΩ | Spread over R<sub>IN</sub> ±15 % |
|---|--:|--:|--:|
| **1 kΩ + 1 µF** | **159 Hz** | **−0.100 %** | **0.031 %** |
| 2.2 kΩ + 470 nF | 154 Hz | −0.220 % | 0.067 % |

**1 kΩ + 1 µF.** 159 Hz passes narrowband switching (1–10 Hz) and wideband
dynamics intact while removing harness pickup, and the residual loading is a
tenth of a percent with a thirtieth of a percent of uncalibratable spread — two
orders below the 82 mV this stage exists to remove.

Note the topology: **R3 first, then C2 to ground.** The op-amp drives the
resistor, so C2 is isolated from its output and cannot destabilise it. Never the
other way round.

The ADS8588H's own 22 kHz second-order anti-aliasing filter remains in circuit
behind this and is unaffected.

---

## 5. Input range — the one place narrowband and wideband differ

The buffer must swing to ground for narrowband. It does **not** need to reach
5 V, and that turns out to matter, because relaxing it allows a much lower bias
current:

| Source | Range needed | Fits (V+) − 1.3 = 3.7 V? |
|---|---|---|
| Narrowband HEGO | 0.0 – 1.0 V | ✓ |
| **CJ125 `UA`** | **0.19 – 3.14 V** | ✓ |
| External module, configurable output | set it 0 – 3.5 V | ✓ |
| External module, fixed 0 – 5 V | 0.0 – 5.0 V | ✓ — **see the note below** |

The CJ125 figures are read off the Bosch LSU 4.9 characteristic table in the
legacy firmware (`src/CJ125Controller.cpp`): the 23-point curve spans ADC 39 to
643 of 1023 over 5 V, so **0.19 V at lambda 0.65 and 3.14 V at lambda 10.1**.
Stoich sits at 1.50 V.

**So a common-mode range of ground to (V+) − 1.3 V covers narrowband and the
on-board CJ125 outright**, and covers an external module whenever its output
span is configurable — which the mainstream ones are.

> **The datasheet is kinder than this table assumed.** The OPA2376's common-mode
> range is **(V−) − 0.1 V to (V+) + 0.1 V** — genuinely rail-to-rail — so a fixed
> 0–5 V module works directly. What the 1.3 V figure actually bounds is where
> **CMRR, PSRR and I<sub>Q</sub> are specified**: above (V+) − 1.3 V the part
> operates but its CMRR minimum of 76 dB no longer applies. The cost is a few
> millivolts of offset shift in the top 1.3 V of a 5 V span — irrelevant on a
> linear-in-lambda wideband signal, and never reached by narrowband or CJ125.

**JP is therefore an unfitted option rather than a requirement.** It remains on
the board because a 0 Ω pad costs nothing: linking it bypasses the buffer for a
fixed 0–5 V module, at R1 + R3 = 11 kΩ into the ADC, or 1.1 % of gain — a fixed
constant folded into the transfer function that such a module needs entered
anyway.

> This is the payoff from [`review-o2-chain.md`](review-o2-chain.md) §5: **the
> wideband decision stays open, and none of it changes this board.**

---

## 6. The op-amp — OPA2376, checked against the datasheet

Datasheet: [`Datasheets/OPA2376AIDR-Datasheet.pdf`](Datasheets/OPA2376AIDR-Datasheet.pdf)
(SBOS406F). The four confirmations §6 previously demanded, answered:

| Asked | Datasheet | |
|---|---|---|
| **I<sub>B</sub> at +125 °C** | **≈ 200 pA typical**, Figure 11. 0.2 pA typ / **10 pA max at 25 °C only**; over temperature the datasheet says *"See Typical Characteristics"* | ⚠ **see below** |
| **Input current limit specified** | **±10 mA**, and note (2) is explicit: *"Input terminals are diode-clamped to the power-supply rails. Input signals that can swing more than 0.5 V beyond the supply rails should be current limited to 10 mA or less"* | ✓ |
| **Common-mode range** | **(V−) − 0.1 V to (V+) + 0.1 V** — rail-to-rail, better than assumed | ✓ **see §5** |
| **AEC-Q100** | **No.** `OPA2376AIDR` is industrial, −40 to +125 °C. The datasheet's *Other Qualified Versions* lists only **`OPA376-Q1` — the single**, not the dual | ✗ **open** |

Specifications not asked for that turned out to matter:

| | |
|---|---|
| V<sub>OS</sub> | **5 µV typ, 25 µV max** — forty times better than the ≤ 1 mV wanted. Offset is simply not a term in this design |
| dV<sub>OS</sub>/dT | 0.26 µV/°C typ, 1 µV/°C max, **specified only to +85 °C**. Even extrapolated to 125 °C that is 100 µV |
| Signal input abs max | **(V−) − 0.5 V to (V+) + 0.5 V**, i.e. −0.5 V to **5.5 V** — *more* headroom than §2 designed against |
| Output swing from rail | 10 mV typ / 20 mV max at R<sub>L</sub> = 10 kΩ, and our DC load is ~1 MΩ | |
| I<sub>Q</sub> | 760 µA typ, **950 µA max** per amplifier → **3.04 mA typ / 3.80 mA max** for four |
| ESD | HBM 4 kV | |

### 200 pA is twice the target, and the design absorbs it

§3 asked for ≤ 100 pA. Re-running the trade against the real figure:

```
   R2      loading    bias current     total
  4.7M      9.57 mV      0.94 mV      10.51 mV
   10M      4.50 mV      2.00 mV       6.50 mV
   15M      3.00 mV      3.00 mV       6.00 mV   <- optimum
   22M      2.05 mV      4.40 mV       6.45 mV
```

**Keep R2 = 10 MΩ.** The optimum has moved to 15 MΩ but 10 MΩ is only 8 % worse
in total error, and 10 MΩ is the easier value to buy, guard and keep clean.

**6.5 mV against the 82 mV this stage removes**, so the buffer still wins by
more than an order of magnitude. But two honest caveats:

- It is a **typical** curve. There is no maximum specified above 25 °C, so a
  worst-case part at 125 °C is unquantified. The curve's dashed extrapolation
  reaches 1 nA by ~145 °C, which would be 10 mV.
- This is the term that would **dominate** if the ECU were ever mounted
  under-hood. At cabin temperatures it is a few hundred microvolts. Another
  reason the mounting decision in
  [`adc-front-end.md`](adc-front-end.md) deserves to be made explicitly.

### The open question: qualification

Every other active part on this board is AEC-Q100 or Q101. **This one would be
the first deliberate exception**, because TI qualified the single and not the
dual:

| | **4 × OPA376-Q1** | **2 × OPA2376AIDR** |
|---|---|---|
| Qualification | **AEC-Q100** | industrial, −40 to +125 °C |
| Packages | 4 | **2** |
| Specs | same silicon — **[CONFIRM]** against its own datasheet | **confirmed, in hand** |
| Board area | 4 × SOT-23-5 or SC-70 is *smaller* than 2 × SOIC-8 | 2 × SOIC-8, easier to hand-solder |

**[DECIDE]** — this is a judgement about how strictly the Q100 rule binds, not a
technical difference, and it is the last open item in this document.

## 7. Bill of materials

Per channel, ×4:

| Ref | Part | Note |
|---|---|---|
| R1 | 10 kΩ 1 % 0805 | fault limiting |
| R2 | **10 MΩ 1 %** 0805 | bias — guard the node |
| R3 | 1 kΩ 1 % 0603 | filter |
| C1 | 1 nF C0G 0603 50 V | RF |
| C2 | 1 µF X7R 0603 16 V | filter |
| D1 | **BAT54S** SOT-23 | dual Schottky, AGND / +5 V<sub>A</sub> |
| JP | 0 Ω 0603, **not populated** | §5 bypass |

Shared:

| Ref | Part | Note |
|---|---|---|
| U1, U2 | **OPA2376AIDR** SOIC-8 ×2, or **OPA376-Q1** ×4 — **[DECIDE]**, §6 | the only open item |
| R4 | 91 kΩ 1 % 0603 | bias divider top |
| R5 | 9.1 kΩ 1 % 0603 | bias divider bottom |
| C3 | 100 nF X7R 0603 | bias decoupling |
| C4, C5 | 100 nF X7R 0603 | op-amp supply decoupling, one per package |

**28 passives, 4 diodes and 2 op-amps** for all four channels.

---

## 8. What this changes elsewhere

| Document | Change |
|---|---|
| [`harness-protection.md`](harness-protection.md) | Already updated: the O2 inputs no longer sit behind the ADS8588H's 9 kV clamp — D1 and R1 are their protection now |
| [`review-analog-chain.md`](review-analog-chain.md) | Finding 4, the unspecified series resistance, is **closed on these four channels** at 10 kΩ. Still open on the rest, which stay unbuffered |
| [`adc-front-end.md`](adc-front-end.md) | Channels 2 and 3 are marked buffered. **No channel count changes** |
| [`power-supply.md`](power-supply.md) | Four amplifiers at 950 µA max plus a 50 µA divider — **3.85 mA worst case**, booked as **4 mA** against a 425 mA budget. Noted, not material |
| [`always-on-domain.md`](always-on-domain.md) | **Nothing.** Every element here is on the switched analog rail and draws zero when parked |

## 9. Open items

| | |
|---|---|
| **[DECIDE]** | **qualification only** — 4 × `OPA376-Q1` (AEC-Q100) against 2 × `OPA2376AIDR` (industrial). §6. The electrical design is settled either way; it is the same silicon |
| **[CONFIRM]** | the F767's maximum external ADC impedance, for the two downstream channels. The buffer makes it moot — output impedance there is 1 kΩ, far inside any plausible limit — but the number was never established and is worth having |
| **[MEASURE]** | source impedance of the truck's actual HO2S at operating temperature, once one is on the bench. Every error figure here is quoted against an assumed 100 kΩ, and the real number would let the residual 4.5 mV be stated rather than estimated |
