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
        ├──[ R2 22M ]───────────► 455 mV bias node (shared, 8.3k)
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
| **R2** | **22 MΩ**, 1 % | open-circuit bias — §3 |
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

## 3. Bias: 22 MΩ to a shared 455 mV node

A picoamp input on an unplugged sensor floats and reads nothing meaningful.
Biasing to ~0.45 V parks an open circuit at a known value, and *"sitting at
455 mV with no switching activity"* is a monitor that has to exist anyway.

**The bias source needs no op-amp.** Its impedance only has to be small compared
with R2, and a plain divider off the analog rail is smaller by three orders:

```
   +5VA ──[ 91k 1% ]──┬──[ 9.1k 1% ]── AGND
                      │
     DAC ──[ 1k 1% ]──┤              455 mV, Zsrc 8.3k, draws 50 uA
                      │
                   [ 100n ]
                      │
                     AGND
```

**The DAC leg is §7** — it turns this node into the excitation source for
in-circuit cell-impedance measurement. With the DAC at reset (high-Z) the node
sits at 455 mV exactly as it would without it, so nothing in the rest of this
section changes.

| | |
|---|---|
| V<sub>bias</sub> | **455 mV** |
| Z<sub>src</sub> | **8.3 kΩ** — 1200× below R2 |
| Draw | **50 µA**, off the **switched** rail, so it never reaches the parked budget owned by [`always-on-domain.md`](always-on-domain.md) |
| Channel-to-channel coupling | **0.038 %** — each channel is isolated by its own 22 MΩ |

### Why R2 is 22 MΩ, and a correction

R2 loads the cell exactly as the ADC used to. **Make it as large as practical** —
there is no opposing term of consequence.

> ⚠ **An earlier revision of this section had this wrong**, and the error is
> worth keeping because it changed a part-selection criterion.
>
> It claimed the op-amp's bias current pulls the other way as `I_B × R2`, and
> built a trade table and a "15 MΩ optimum" on that. **`I_B × R2` is the
> open-circuit value.** Bias current flows into the non-inverting node, whose
> Thévenin impedance is **Rs ‖ R2** — and with a sensor connected, Rs dominates
> completely.

| R2 | Rs | Z = Rs ‖ R2 | I<sub>B</sub> × Z | R2 loading | Total |
|--:|--:|--:|--:|--:|--:|
| 10 MΩ | 100 kΩ | 99.0 kΩ | **20 µV** | 4.41 mV | 4.43 mV |
| **22 MΩ** | **100 kΩ** | **99.5 kΩ** | **20 µV** | **2.01 mV** | **2.03 mV** |
| 47 MΩ | 100 kΩ | 99.8 kΩ | 20 µV | 0.94 mV | 0.96 mV |
| 22 MΩ | *open* | 22 MΩ | 4.4 mV | — | 4.4 mV |

**Bias current contributes 20 µV with a sensor connected.** It only reaches
millivolts on an open circuit — where the node's job is to read *"455 mV, sensor
absent"* and a few millivolts of error is meaningless.

So loading is the only term that matters, and it falls monotonically with R2.

**22 MΩ, not 47 MΩ**, for reasons that are all about the open-circuit case and
the physical part:

| | 10 MΩ | **22 MΩ** | 47 MΩ |
|---|--:|--:|--:|
| Loading at 100 kΩ | 4.41 mV | **2.01 mV** | 0.94 mV |
| Open-circuit offset from I<sub>B</sub> | 2.0 mV | **4.4 mV** | 9.4 mV |
| Bias-node lift per shorted channel | 4.0 mV | **1.8 mV** | 0.8 mV |
| Settling on disconnect | 10 ms | **22 ms** | 48 ms |
| Availability, tolerance, voltage coefficient | good | **good** | poorer |

22 MΩ halves the dominant error against 10 MΩ and halves the fault coupling too,
while keeping the open-circuit offset small and staying on a common value.

Johnson noise is a non-issue at either value: **0.64 µV** at the connected-sensor
impedance and **9.5 µV** open, in the 159 Hz bandwidth the post-filter allows.

### One fault couples slightly into the other three

A channel shorted to battery sits at D1's 5.3 V, pushing 0.22 µA through its
R2 into the shared 8.3 kΩ bias node and lifting it **1.8 mV**. Four shorted
channels lift it 7 mV. Small, only present during a fault, and worth knowing
before someone chases it: **a single shorted O2 wire shifts the other three
channels' zero by about 2 mV.**

### Leakage is the real enemy at 22 MΩ, so guard the node

Surface leakage across contaminated FR4 can reach nanoamps, which through 22 MΩ
is **22 mV per nanoamp** — larger than everything this stage was built to fix,
and the one term that genuinely *does* scale with R2. It is why §3 stops at
22 MΩ rather than going further.

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

## 6. The op-amp — OPA2376, checked against both datasheets

**Decided: `OPA2376AQDRQ1`.** Two of them, SOIC-8, AEC-Q100 Grade 1.

> **Watch the part number.** The Q-grade is `OPA2376A**Q**DRQ1`, not
> `OPA2376A**I**DRQ1` — the `I` that marks the industrial grade becomes `Q`. The
> file in `Datasheets/` is named with the `I` spelling; the orderable device in
> TI's own ordering table is `OPA2376AQDRQ1`.

Specifications below are from
[`Datasheets/OPA2376AIDR-Datasheet.pdf`](Datasheets/OPA2376AIDR-Datasheet.pdf)
(SBOS406F, industrial) and confirmed identical in
[`Datasheets/OPA2376AIDRQ1-Datasheet.pdf`](Datasheets/OPA2376AIDRQ1-Datasheet.pdf)
(ZHCS042C, Q1) except where noted. The four confirmations §6 previously
demanded, answered:

| Asked | Datasheet | |
|---|---|---|
| **I<sub>B</sub> at +125 °C** | **≈ 200 pA typical**, Figure 11. 0.2 pA typ / **10 pA max at 25 °C only**; over temperature the datasheet says *"See Typical Characteristics"* | ⚠ **see below** |
| **Input current limit specified** | **±10 mA**, and note (2) is explicit: *"Input terminals are diode-clamped to the power-supply rails. Input signals that can swing more than 0.5 V beyond the supply rails should be current limited to 10 mA or less"* | ✓ |
| **Common-mode range** | **(V−) − 0.1 V to (V+) + 0.1 V** — rail-to-rail, better than assumed | ✓ **see §5** |
| **AEC-Q100** | **Yes — `OPA2376-Q1` exists.** Grade 1, −40 to +125 °C, dual, SOIC-8. Orderable as **`OPA2376AQDRQ1`** | ✓ |

> **I got this wrong first time.** The industrial datasheet's *Other Qualified
> Versions of OPA376* lists only *"Automotive: OPA376-Q1"* — the single — and I
> concluded from that absence that no dual was qualified. The `OPAx376-Q1`
> datasheet (ZHCS042C, revised March 2021) covers **OPA376-Q1, OPA2376-Q1 and
> OPA4376-Q1**. A cross-reference list in an older document is not an inventory,
> and I treated it as one.

Specifications not asked for that turned out to matter:

| | |
|---|---|
| V<sub>OS</sub> | **5 µV typ, 25 µV max** — forty times better than the ≤ 1 mV wanted. Offset is simply not a term in this design |
| dV<sub>OS</sub>/dT | 0.26 µV/°C typ, 1 µV/°C max, **specified only to +85 °C**. Even extrapolated to 125 °C that is 100 µV |
| Signal input abs max | **(V−) − 0.5 V to (V+) + 0.5 V**, i.e. −0.5 V to **5.5 V** — *more* headroom than §2 designed against |
| Output swing from rail | 10 mV typ / 20 mV max at R<sub>L</sub> = 10 kΩ, and our DC load is ~1 MΩ | |
| I<sub>Q</sub> | 760 µA typ, **950 µA max** per amplifier → **3.04 mA typ / 3.80 mA max** for four |
| ESD | HBM 4 kV | |

### 200 pA at +125 °C, and why it does not matter

§3 originally demanded ≤ 100 pA and called bias current *"the selection
criterion"*. **That requirement was built on a wrong model** — the correction is
in §3. With a sensor connected, bias current sees Rs ‖ R2 ≈ 99 kΩ, so 200 pA
contributes **20 µV**, not millivolts.

| | |
|---|---|
| Connected sensor, 100 kΩ | 200 pA × 99.5 kΩ = **20 µV** |
| Open circuit | 200 pA × 22 MΩ = **4.4 mV**, on a reading whose only job is to say *"sensor absent"* |

**So the part is not marginal on the specification I thought was critical, and
nothing about the bias-current curve constrains this design.** The dominant
error is R2 loading at **2.0 mV**, which is set by R2 and is independent of the
op-amp entirely.

### Would a FET-input op-amp be better? No

Asked and worth recording, because the answer is not obvious:

- **The 200 pA is not the input device.** A CMOS gate passes essentially no DC
  current — that figure is **ESD-diode leakage at the pin**, and a JFET-input
  part carries the same protection structures. Both mechanisms double roughly
  every 10 °C. Changing input topology does not attack the dominant term.
- **Supply and common-mode range rule most JFET parts out.** This stage needs
  **single 5 V** with the input range **including ground**. Precision JFET amps
  generally want ±4 V or more and exclude one rail on the common mode. That is a
  hard constraint here, not a preference.
- **Offset moves the wrong way** — 25 µV max here against typically 100 µV to
  1 mV for JFET-input precision parts.
- **And it would buy nothing**, per the correction above.

### DECIDED: `OPA2376AQDRQ1` — two duals, AEC-Q100

Datasheet: [`Datasheets/OPA2376AIDRQ1-Datasheet.pdf`](Datasheets/OPA2376AIDRQ1-Datasheet.pdf)
(ZHCS042C). There is no trade to make — the Q1 dual gives qualification *and*
the two-package count, and on one specification it is better than the industrial
part rather than merely requalified:

| | Industrial `OPA2376AIDR` | **`OPA2376AQDRQ1`** |
|---|---|---|
| Qualification | none | **AEC-Q100 Grade 1**, −40 to +125 °C |
| Functional safety | — | **documentation available** for OPA376-Q1 / OPA2376-Q1 |
| **dV<sub>OS</sub>/dT** | 1 µV/°C max, **specified only to +85 °C** | **2 µV/°C max, specified −40 to +125 °C** |
| V<sub>OS</sub>, I<sub>B</sub>, V<sub>CM</sub>, I<sub>Q</sub>, abs max | — | **identical** |

The drift entry is the one that matters. §6 had to extrapolate the industrial
part's drift past +85 °C; the Q1 part specifies it across the whole range. Two
µV/°C over 100 °C is **200 µV** — an order below the 2.0 mV loading term and
untroubling, but now it is a specification rather than an assumption.

### One layout consequence from Figure 6-18

Small-signal overshoot against capacitive load reaches **~50 % by 500 pF** and
climbs steeply after 100 pF. Two things follow:

- **The R3-then-C2 topology is load-bearing, not stylistic.** The op-amp drives
  1 kΩ and never sees C2. Putting the capacitor directly on the output would sit
  far off the right of that graph.
- **The guard ring is a real capacitive load.** Its capacitance to the *node* is
  bootstrapped away — that is the point of guarding — but its capacitance to
  ground and adjacent planes is not, and it lands on the output. Keep it to a
  ring, not a pour: tens of pF is ~10 % overshoot, which the 159 Hz filter
  removes anyway, but a large guard *plane* would be a different matter.

---

## 7. Measuring the cell's impedance in circuit

**Decided: yes, and it costs one DAC pin, one resistor and one capacitor.**

The question was why sensor condition should be judged from a bench
characterisation at all, when sensors change over time and the accurate answer
is the one taken in circuit, at temperature, on the sensor actually fitted.

That is right, and it is what a CJ125 does — the `UR` pin is a Nernst-cell
*resistance* measurement, and it is what the legacy firmware read through the
ADS1115 to run the wideband heater PID. §1's stage turns out to already contain
everything needed to do the same for narrowband.

Numbers below are reproduced by [`calc/o2_impedance.py`](calc/o2_impedance.py).

### 7.1 The stage already has the injection path

**R2 is the excitation resistor.** Each channel has a known 22 MΩ from its
high-impedance node to a bias node that is *shared by all four*. Move that node
and a known current flows into every cell at once.

```
   node = (E/Rt + Vb/R2) / (1/Rt + 1/R2),    Rt = Rs + R1
```

Take two bias states and subtract:

```
   ΔV / ΔVb  =  Rt / (R2 + Rt)                     ← E has gone
   Rt        =  R2 · k / (1 − k),      k = ΔV/ΔVb
```

**The sensor's own EMF cancels exactly.** So the measurement needs no stable
mixture, no warm engine and no known lambda — only that `E` does not move much
between the two samples, which §7.4 handles. Op-amp offset, offset drift and
the bias divider's tolerance cancel with it, because they are common to both
states. What is left is R2, which is a 1 % resistor, and ΔVb, which is measured.

### 7.2 Driving it: one DAC pin, zero per-channel parts

**The divider stays.** A DAC output joins the node through R6 = 1 kΩ:

| | |
|---|---|
| DAC at reset (high-Z) | node sits at **455 mV**, the behaviour §3 specifies. **Fail-safe by omission** — firmware that never touches the DAC changes nothing |
| DAC driving | divider attenuates by a known constant, **8.3k/(1k+8.3k) = 0.8925** |
| DAC 0.455 → 3.000 V | **ΔVb = 2271 mV** at the node |
| R6 ‖ divider | ~900 Ω, still **24 000× below R2** — §3's requirement is met with three orders to spare |

Nothing is added per channel. The bias node is already shared and the ADS8588H
samples **simultaneously**, so all four cells are excited and measured in the
same window. The two downstream sensors on the F767's internal ADC hang off the
same bias node and come along for free.

### 7.3 Resolution and disturbance scale the right way

ΔVb = 2271 mV, R2 = 22 MΩ, R1 = 10 kΩ, LSB = 305 µV:

| Cell R<sub>s</sub> | | ΔV seen | LSBs | Current into cell | Disturbs a 1 V swing by | Node τ |
|---|---|--:|--:|--:|--:|--:|
| **10 kΩ** | hot, new | 2.06 mV | 7 | 103 nA | **0.2 %** | 0.02 ms |
| **30 kΩ** | hot, typical | 4.12 mV | 14 | 103 nA | **0.4 %** | 0.04 ms |
| 100 kΩ | warm or aged | 11.30 mV | 37 | 103 nA | 1.1 % | 0.11 ms |
| **300 kΩ** | **§1's row that fails OBD-II** | 31.56 mV | 103 | 102 nA | 3.2 % | 0.31 ms |
| 1 MΩ | cool or failing | 99.70 mV | 327 | 99 nA | 10.0 % | 0.97 ms |
| 10 MΩ | cold | 710 mV | 2327 | 71 nA | 71 % | 6.88 ms |
| **open** | **unplugged** | **2271 mV** | 7443 | 0 | — | 22 ms |

Read the last two columns together, because that is the whole argument:

- **The disturbance self-scales inversely with how much the reading is worth.**
  It is smallest — 0.4 % of a 1 V swing, and transient — on a healthy cell, and
  largest on a sick one whose reading §1 already showed to be unusable.
- **Peak injected current is ~115 nA.** A zirconia cell does not notice 115 nA.
  There is no polarisation mechanism at that level and nothing to damage.
- **An unplugged channel saturates**, giving the full 2271 mV. That is a positive
  signature rather than the present inference from *"it is sitting near 455 mV
  with no activity"* — which a sensor stuck at stoich also produces.

### 7.4 The one real problem: `E` drifts while you measure

`E` cancels only if it is the same in both samples, and a switching narrowband
slews about **1 V in 20 ms = 50 V/s**. Two samples 2 ms apart see **100 mV** of
drift — **24× the 4.12 mV signal at 30 kΩ.** A single before/after pair is not
good enough, and this is the thing that would have made a naive implementation
produce confident nonsense.

**Square-wave the bias node and detect synchronously.** Drift becomes a
common-mode term that ±1 demodulation rejects. The frequency is boxed in from
both sides:

| | Post-filter gain | |
|--:|--:|---|
| 5–10 Hz | 1.000 | **too close to the cell's own 1–10 Hz switching** |
| **50 Hz** | **0.954** | **4.6 % loss — picked** |
| 100 Hz | 0.846 | |
| 200 Hz | 0.622 | §4's 159 Hz filter is eating it |
| 500 Hz | 0.303 | |

50 Hz sits in the gap: 5–50× above anything the cell does, and only 4.6 % down
through the R3/C2 filter, which is a fixed constant and calibrates out.

Budget inside one 10 ms half-period:

| | |
|---|---|
| Settle R3/C2 (τ = 1.00 ms) | discard **5 ms** |
| Settle the node (τ ≤ 0.96 ms up to R<sub>s</sub> = 1 MΩ) | covered by the same wait |
| Sample the remaining 5 ms at 500 kSPS | **2497 samples** |
| 25 cycles = **0.5 s** | 124 850 samples → noise ÷ 353 → **0.9 µV** |

Against the 4.12 mV worst case — which is the *healthiest* cell, and so the
smallest signal — that is **0.02 %**. The measurement is better than the sensor.

### 7.5 Above 1 MΩ the time constant is itself the signal

Node τ = (R<sub>t</sub> ‖ R2)·C1 reaches 6.9 ms at 10 MΩ and 22 ms open, so a
10 ms half-period stops fully settling. That is not a failure mode: incomplete
settling at a *known* excitation is still monotonic in R<sub>t</sub>, and the
regime where it happens is the one where amplitude has already saturated.
**Report "> 1 MΩ" and stop.** Nothing downstream needs to distinguish 4 MΩ from
9 MΩ — both mean the same thing.

### 7.6 What this buys

| | |
|---|---|
| **Light-off, measured** | Cell impedance falls steeply with temperature, so *"hot enough to believe"* becomes a threshold on R<sub>s</sub> instead of a timer or a coolant-temperature proxy. Closed loop starts when the sensor says so |
| **Heater ramp, closed loop** | The PWM ramp in [`output-drivers.md`](output-drivers.md) exists to spare the ceramic from thermal shock. Ramping against measured impedance targets the ceramic's actual temperature rather than an assumed heating curve |
| **Ageing, trended** | [`review-o2-chain.md`](review-o2-chain.md) §1 **is an impedance table** — 300 kΩ is the row that fails the 0.7 V OBD-II amplitude threshold. Logging R<sub>s</sub> per sensor per trip converts that row from a hazard into a scheduled replacement |
| **Fault discrimination** | A lean-looking reading separates into *lean mixture* (R<sub>s</sub> normal), *tired sensor* (R<sub>s</sub> high), *unplugged* (open) and *shorted* (R<sub>s</sub> ≈ 0) without anyone moving a wire |

### 7.7 The firmware constraint

**Measure in the heater PWM's off-window.** Heater current shares harness ground
with the cell, and 50 Hz modulation against a PWM'd heater will otherwise beat
against it and produce a slow spurious drift in the demodulated result.

PWMing the heaters was decided separately, for the ceramic's sake — and it is
what makes the off-windows exist. **The two decisions reinforce each other**:
the heater PWM gives §7 its quiet windows, and §7 gives the heater ramp its
feedback. Neither was designed for the other.

## 8. Bill of materials

Per channel, ×4:

| Ref | Part | Note |
|---|---|---|
| R1 | 10 kΩ 1 % 0805 | fault limiting |
| R2 | **22 MΩ 1 %** 0805 | bias — guard the node, §3 |
| R3 | 1 kΩ 1 % 0603 | filter |
| C1 | 1 nF C0G 0603 50 V | RF |
| C2 | 1 µF X7R 0603 16 V | filter |
| D1 | **BAT54S** SOT-23 | dual Schottky, AGND / +5 V<sub>A</sub> |
| JP | 0 Ω 0603, **not populated** | §5 bypass |

Shared:

| Ref | Part | Note |
|---|---|---|
| U1, U2 | **OPA2376AQDRQ1** SOIC-8 ×2 | AEC-Q100 Grade 1 dual, §6 |
| R4 | 91 kΩ 1 % 0603 | bias divider top |
| R5 | 9.1 kΩ 1 % 0603 | bias divider bottom |
| C3 | 100 nF X7R 0603 | bias decoupling |
| **R6** | **1 kΩ 1 % 0603** | **DAC → bias node, §7** |
| C4, C5 | 100 nF X7R 0603 | op-amp supply decoupling, one per package |

**29 passives, 4 diodes and 2 op-amps** for all four channels — R6 is the
only part §7 adds, and it is shared by all of them.

---

## 9. What this changes elsewhere

| Document | Change |
|---|---|
| [`harness-protection.md`](harness-protection.md) | Already updated: the O2 inputs no longer sit behind the ADS8588H's 9 kV clamp — D1 and R1 are their protection now |
| [`review-analog-chain.md`](review-analog-chain.md) | Finding 4, the unspecified series resistance, is **closed on these four channels** at 10 kΩ. Still open on the rest, which stay unbuffered |
| [`adc-front-end.md`](adc-front-end.md) | Channels 2 and 3 are marked buffered. **No channel count changes** |
| [`power-supply.md`](power-supply.md) | Four amplifiers at 950 µA max plus a 50 µA divider — **3.85 mA worst case**, booked as **4 mA** against a 425 mA budget. Noted, not material |
| [`always-on-domain.md`](always-on-domain.md) | **Nothing.** Every element here is on the switched analog rail and draws zero when parked |
| [`output-drivers.md`](output-drivers.md) | The heater PWM decided there acquires a second job: its **off-windows are when §7 measures**, and its ramp can close the loop on measured impedance instead of running on a timer |
| [`pin-budget.md`](pin-budget.md) | **+1 pin** — one DAC output (PA4 or PA5) for §7. 78 of ~114 |

## 10. Open items

| | |
|---|---|
| ~~**[DECIDE]** the op-amp~~ | **Closed** — `OPA2376AQDRQ1`, §6 |
| **[CONFIRM]** | the F767's maximum external ADC impedance, for the two downstream channels. The buffer makes it moot — output impedance there is 1 kΩ, far inside any plausible limit — but the number was never established and is worth having |
| ~~**[MEASURE]** source impedance on the bench~~ | **Superseded by §7.** The board measures it in circuit, on every sensor, continuously. A bench figure would have been one number from one sensor on one day; §7 gives four numbers per trip for the life of the truck |
| **[CONFIRM]** | the F767 DAC's output impedance and its true reset-state leakage, for §7. The 1 kΩ series resistor makes the first moot and the 91k/9.1k divider makes the second benign, but neither is yet read off the datasheet |
| **[MEASURE]** | cell impedance against temperature for the sensors actually fitted, to set the §7 light-off threshold. This is a calibration the board performs on itself during the first warm-ups, not a bench task |
