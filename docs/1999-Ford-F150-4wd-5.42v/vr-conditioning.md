# VR sensor conditioning

Three sensors on this truck are variable-reluctance and cannot drive a GPIO:

| Sensor | Pins | Confirmed by |
|---|---|---|
| **CKP** — crankshaft position | 21 (+, DK BLU), 22 (−, GRY) | two-wire differential coil |
| **CMP** — camshaft position | 85 (DK GRN), returning on SGND | **VR, single-ended** — **measured 371 Ω 2026-09-17**, so settled beyond the owner's confirmation |
| **OSS** — output shaft speed | 84 | MegaSquirt notes: *"DFIN1 via LM1850"* — the LM1815 VR amplifier |
| ~~TSS~~ | 59 | **Not fitted.** C192 is 4R100-only — confirmed by the owner. The PCM pin exists for other applications |

**CMP is VR — confirmed by the owner.** Pin 85 shows a lone "CMP+" with no
matching negative because it is a **single-ended VR**: the coil's other end
returns on sensor ground (pin 91, SGND) rather than a dedicated wire.

## Channel allocation — this document owns it

Four VR inputs, two MAX9926 packages, **exact fit**. It is a fit rather than a
shortage: the earlier "fourth channel spare" was a byproduct of needing three
channels from two-channel parts, not designed margin.

| Ch | Signal | PCM pin | Circuit | Notes |
|---|---|--:|---|---|
| 1 | **CKP** | 21 / 22 | DK BLU / GRY | **differential** — the only one |
| 2 | **CMP** | 85 (+ SGND 91) | DK GRN | single-ended, **371 Ω measured**. Shield on pin 25 |

> ✅ **OSS: 450–750 Ω**, from the 4R70W service manual's *Resistance/Continuity
> Tests — Output Shaft Speed Sensor*. Same order as CMP's measured 371 Ω, so the
> MAX9926 input network suits both without a per-channel change.
| 3 | **OSS** | 84 | 136 DB/YE, C187 | transmission control: shift scheduling, TCC, EPC |
| 4 | **Transfer case speed** | 7 | 1496 PK, C199 | **road speed** — downstream of the range box |

**No spare.** This table is the count; anything that needs a VR channel adds a
row here first.

> The fourth was described as spare in three separate documents while
> [`../cooling-fans.md`](../cooling-fans.md) §4.4 was spending it on road speed.
> Nothing owned the number, which is how it got allocated twice. See
> [`../review-vr-chain.md`](../review-vr-chain.md) §2.

### The contention is temporal, not absolute

Losing the spare costs **bring-up flexibility**, and
[`../roadmap.md`](../roadmap.md) calls M3/M4 — crank and cam sync — the highest-
risk phase in the project. That is less bad than it sounds:

**M3 and M4 run on a bench with a trigger wheel.** OSS and the transfer case
sensor are not connected then, so **two of the four channels are free for
exactly the phase that most wants them** — a second scope tap, a known-good
reference signal, a substitute sensor.

The squeeze only arrives at M12, by which time crank sync is long proven.

> If permanent margin is wanted, a **third MAX9926 as a DNP footprint** fits the
> board's existing policy — [`../v1-scope.md`](../v1-scope.md): *"Footprints for
> the 'yes' rows cost almost nothing and save a respin."* Two spare pins would
> need routing to the connector. **Not specified**, because no fifth VR sensor
> has been identified: TSS is 4R100-only and not fitted, and the wheel-speed
> sensors belong to the ABS module.

The MAX9926 handles single-ended VR sensors directly. Wire it as:

| MAX9926 | Connect to |
|---|---|
| IN2+ | CMP signal (pin 85) via 2 × 5 kΩ |
| IN2− | **sensor ground (pin 91)** via 2 × 5 kΩ |

### Terminate the CMP shield — at pin 25, to case ground

Ford brings the CMP cable's shield into the PCM on **pin 25** (circuit
567 LB/YE, drained via S199/S101), and terminates it **only there** — the sensor
end is just the shield around the cable. Reproduce that:

| | |
|---|---|
| **Where** | **pin 25**, at the connector entry |
| **To what** | the **case/chassis ground leg** of the star — what `CSEGND` exists for |
| **Not to** | **sensor ground or analogue ground.** A shield carries the noise current it intercepted; dumping that into the reference the signal is measured against injects exactly what the shield was fitted to exclude |
| **How many points** | **one.** A shield grounded at both ends is a loop, and this truck's chassis carries alternator and starter current — such a loop injects far more than it excludes |

> ⚠ [`eec-v-pinout.md`](eec-v-pinout.md) lists pin 25 as a **power ground**, from
> the MegaSquirt sheet. Ford's diagram says otherwise. Wiring it as a power
> ground would put engine-bay ground current into the sensor cable shield — see
> [`schematic-findings.md`](schematic-findings.md) §15.

**Use the same series resistance in both legs.** The differential amplifier's
common-mode rejection depends on the two paths being balanced — grounding IN2−
directly while IN+ sees 10 kΩ throws that away, and CMRR is the whole reason
for using a differential input in an engine bay.

## Why it cannot be done in software

A VR sensor is a coil and a magnet. Its output amplitude is proportional to
tooth speed, which spans a very wide range:

- **Cranking (~200 rpm):** a few hundred millivolts.
- **Redline:** tens of volts, enough to need clamping.

A fixed comparator threshold cannot serve both ends. Set it high enough to
reject noise at speed and the engine will not sync while cranking — which is
precisely when sync must be established. Set it low enough to catch cranking
and it triggers on ringing at speed.

The answer is an **adaptive-threshold zero-crossing detector**: track the
signal's own peak amplitude and set the threshold as a fraction of it.

## Recommended part: MAX9926

rusEFI's VR conditioner board (`hardware/VR_Board` in
[rusefi/rusefi](https://github.com/rusefi/rusefi), GPLv3) uses the
**MAX9926UAEE+** — a dual-channel adaptive VR interface in QSOP-16. Two
channels per package covers CKP and CMP, or CKP and OSS, from one part.

The full BOM is published (`vrs_io_1.csv`), which is a working reference rather
than a datasheet application note:

| Ref | Value | Part |
|---|---|---|
| U101 | MAX9926/9927 | MAX9926UAEE+ |
| C101, C102 | 1000 pF | input coupling |
| C103 | 10 µF | bulk |
| C104 | 0.1 µF | decoupling |
| R102–R112 | 5 kΩ | input network |
| R101, R113, R114 | 10 kΩ | |
| R137, R141 | 1 kΩ | |

rusEFI's own `VR_discrete/readme.md` points at
[mck1117/vr-interface](https://github.com/mck1117/vr-interface) as "much more
proven" than their discrete attempt — worth reading before designing one.

---

## Why not the LM1815

The LM1815 is the obvious alternative — *the* classic VR adaptive sense amplifier,
what MegaSquirt uses (and what the OSS note above refers to). Assessed against
the TI datasheet, **SNOSBU8F, September 2000, revised March 2013**.

### Correction to an earlier claim in this file

An earlier revision of this section called the LM1815 "believed obsolete or
NRND." **That was unfounded.** TI publishes it as **PRODUCTION DATA** with a 2013
revision and a live product folder. Confirm the lifecycle state before committing
to it, as with any part — but it was wrong to put obsolescence on the list of
reasons against it, and it is removed.

### Where the LM1815 is genuinely better: it triggers on true zero crossing

This is a real advantage and the earlier note understated it.

The LM1815 **arms** on an adaptive threshold (80 % of the peak stored on the pin 7
detector) and then **triggers on the negative-going zero crossing** — specified at
**0 mV typical, ±25 mV worst case**. Arming is amplitude-dependent; the timing
edge is not.

That matters for a timing application in a way a fixed fraction of peak does not:

- **Zero crossing is the true tooth reference.** A VR sensor outputs dΦ/dt, so it
  crosses zero exactly when the tooth is centred on the pole. No calibration
  constant, no waveform-shape dependence.
- **It is immune to tooth-to-tooth amplitude change.** A part that triggers at a
  fraction of the *previous* peak fires early when the current tooth is stronger
  than the last one. That is precisely what happens under acceleration — and
  cranking, where the engine surges between compression strokes, is nothing but
  acceleration and deceleration. A zero-crossing trigger has no such term.

### And where it bites back, from the same datasheet

> *"If the input signal amplitude falls faster than the voltage stored on the peak
> detector capacitor there may be a loss of output signal until the capacitor
> voltage has decayed to an appropriate level."*

**Missed teeth under rapid deceleration** — the arming threshold is stranded high
while the signal collapses. That is the *other* half of every compression stroke.
So the trade is real in both directions: exact timing when it fires, against a
dropout mode a fraction-of-peak trigger degrades through more gracefully.

### The decisive reason is still the input topology

**"Ground Referenced Input"** — the datasheet's own feature list. The LM1815 takes
a current-mode input referred to its own ground, so one side of the CKP's floating
two-wire coil gets tied down, and whatever sits between sensor ground and board
ground arrives as signal. The MAX9926's differential input rejects it.

In a bay containing a 40 kV ignition system, **common-mode rejection is the whole
reason to prefer one part over another**, and it is the one thing the LM1815
structurally cannot offer.

### Other differences worth recording

| | LM1815 | MAX9926 |
|---|---|---|
| Channels per package | 1 (14-SOIC/PDIP) | 2 |
| Input | ground referenced | differential |
| Supply | 2–12 V (**12 V abs max**) | 5 V |
| Input current abs max | **±30 mA** | ±40 mA |
| Design input current | 3 mA → `Rext(min) = Vpeak/3mA` | — |
| Minimum signal | 150 mV p-p | — |
| Automotive qual | none | AEC-Q100 |

Note the series resistor sizing is **tighter**, not looser: at 3 mA design current
a 150 V peak wants ~50 kΩ, against the 5 kΩ used here.

Three VR channels means **three LM1815s** and three sets of arming and peak-detect
components, against two MAX9926s. **The fourth channel is no longer spare** —
[`../cooling-fans.md`](../cooling-fans.md) §4.4 takes road speed from the
transfer case speed sensor (pin 7), so all four are allocated. See
[`../review-vr-chain.md`](../review-vr-chain.md) §2.

### RESOLVED — the timing advantage does not exist

The MAX9926 datasheet (now in the repo) settles it. **Table 1, Mode A2:
ZERO_EN = GND, INT_THRS = GND → Zero Crossing ENABLED, Adaptive Peak Threshold
ENABLED.**

The two parts use **the same architecture**: arm on an adaptive fraction of the
previous peak, then trigger on the zero crossing. The 33 % figure is the *arming*
threshold, not the trigger point — see the correction below. And on the numbers
the MAX9926 is the tighter of the two:

| | LM1815 | MAX9926 |
|---|--:|--:|
| Zero-crossing threshold | ±25 mV | **−6.5 / +10 mV** |
| Propagation delay | — | **50 ns** (zero-crossing path) |
| Adaptive arming threshold | **80 % of peak** | **33 % of peak** |

### The arming threshold is where the MAX9926 pulls decisively ahead

The LM1815 arms at **80 %** of the previous peak; the MAX9926 at **33 %**. So a
tooth must reach 80 % of its predecessor to be seen by the LM1815, against 33 %
for the MAX9926.

**The MAX9926 tolerates a 3:1 amplitude collapse between teeth. The LM1815
tolerates 1.25:1.** That is the dropout mode quoted above, quantified — and
cranking, where the engine slows hard against each compression stroke, is exactly
where amplitude collapses tooth to tooth. The MAX9926 also backs it with an
explicit 85 ms watchdog that resets the threshold, where the LM1815 relies on an
RC decay at pin 7.

### Decision

**Stay with the MAX9926**, and now on the merits rather than on sunk cost. It
matches the LM1815's zero-crossing timing, beats it on zero-crossing threshold
and on arming margin where cranking actually lives, adds a differential input the
LM1815 structurally cannot offer, and puts two channels in a package. The boards
being already fabricated is now the *least* of the reasons.

## Configuration — use Mode A2

The MAX9926 has four operating modes, selected by strapping two kinds of pin.
Zero-crossing is global (one `ZERO_EN` pin); the adaptive threshold is
**per channel** (`INT_THRS1`, `INT_THRS2`), so the two channels can run
differently if ever needed.

| Mode | ZERO_EN | INT_THRS | Zero crossing | Adaptive threshold | Bias source |
|---|---|---|---|---|---|
| A1 | VCC | VCC | on | on | **external divider** |
| **A2** | **GND** | **GND** | **on** | **on** | **internal 2.5 V** |
| B | VCC | GND | on | off | external |
| C | GND | VCC | off | off | external |

**Mode A2** is the right choice here. It keeps both features that matter and
uses the internal 2.5 V reference, which eliminates the external VCC/2
resistor-divider and its 0.1 µF + 10 µF bypass on *each* BIAS pin that Mode A1
would need. Same behaviour, fewer parts, less to get wrong.

Mode B is worth remembering as a later option, not a starting point: it
disables the internal adaptive threshold and takes the threshold from `EXT`,
typically a filtered PWM from the MCU. That would allow an rpm-dependent
threshold implemented in firmware — interesting once there is real cranking
data, pointless before it.

Mode C is a plain comparator and throws away the reason for using this part.

### Mode B is the upgrade path, and it needs a DAC — not yet

Table 1 also offers **Mode B**: `ZERO_EN = VCC`, `INT_THRS = GND` → zero crossing
**enabled**, adaptive peak threshold **disabled**, bias **external**. The
datasheet's own words:

> *"In Mode B … an external threshold voltage is applied at EXT allowing
> application-specific adaptive algorithms to be implemented in firmware."*

That keeps the zero-crossing trigger — the part that makes timing amplitude-
independent — while handing the **arming** threshold to software. It is a real
capability, and it addresses the one weakness Mode A2 has.

**Mode A2 arms reactively**, at 33 % of the *previous* peak. Cranking is where
that is worst, because the engine surges and collapses across every compression
stroke, so the previous tooth is a poor predictor of the next. Firmware that
already knows crank position and instantaneous speed could set the threshold
**predictively**, per tooth.

The bandwidth is not a problem. At 6000 rpm a 36-1 wheel delivers a tooth every
**278 µs**, and a 24-bit SPI write at 10 MHz takes **2.4 µs**.

**The candidate part is the [DAC70508](../Datasheets/dac70508-datasheet.pdf)** —
8 channels of 14-bit against 4 VR channels, SPI to 50 MHz, −40 to +125 °C,
internal 2.5 V/5 ppm reference, 3 × 3 mm, with CRC on the interface.

### Why not now

- **VR V1 cannot do it.** The board is strapped for Mode A2 with EXT
  unconnected. Mode B is a respin, not a firmware change.
- **Mode B also needs external bias.** A2's internal 2.46 V reference goes away,
  so each channel gains a divider and its filtering — more parts, more variables,
  which is exactly what Mode A2 was chosen to avoid.
- **The problem may not exist.** Mode A2 tolerates a **3:1** amplitude collapse
  between teeth. Whether cranking on this engine actually exceeds that is
  measurable, not arguable.

**The trigger for revisiting this is specific:** if the rig or the truck shows
**missed teeth or lost sync during cranking** that trace to arming rather than to
signal amplitude, Mode B plus a DAC is the answer. Until then it is a solution
without a demonstrated problem, and the rig exists precisely to find out.

### Strapping for Mode A2

| Pin | Name | Connect to |
|---|---|---|
| 13 | ZERO_EN | **GND** — note it is internally pulled up to VCC through 10 kΩ, so it must be actively pulled low |
| 1 | INT_THRS1 | GND |
| 8 | INT_THRS2 | GND |
| 3 | BIAS1 | **GND** — confirmed by datasheet **Figure 3, "Operating Mode A2"**, which shows BIAS tied straight to ground. The general pin description ("connect to an external resistor-divider") applies to Modes A1/B/C only |
| 6 | BIAS2 | GND |
| 2 | EXT1 | leave unconnected |
| 7 | EXT2 | leave unconnected |
| 12 | DIRN | leave unconnected — quadrature direction output, not useful for CKP or OSS |

### Power and outputs

| Pin | Name | Notes |
|---|---|---|
| 14 | VCC | **5 V** |
| 11 | GND | |
| 4 | COUT1 | **open-drain** — 10 kΩ pull-up |
| 5 | COUT2 | **open-drain** — 10 kΩ pull-up |

**Pull COUT up to 3.3 V, not 5 V.** The part runs from 5 V but the output is
open-drain, so the pull-up rail alone sets the logic level. That makes it
directly compatible with the ESP32-P4 with **no level shifter** — which is why
an open-drain output was chosen by the part's designers, and it is worth not
undoing by pulling up to 5 V out of habit.

Decoupling: 10 nF, 0.1 µF and 1 µF in parallel, with the **10 nF closest** to
the VCC/GND pins. The datasheet is unusually insistent about this because the
front-end amplifier uses an internal charge pump.

### Inputs — the 10 kΩ series resistors are not optional

| Pin | Name |
|---|---|
| 16 | IN1+ |
| 15 | IN1− |
| 9 | IN2+ |
| 10 | IN2− |

**A 10 kΩ series resistor in every input leg**, per the datasheet: it limits pin
current when the sensor voltage exceeds VCC and turns on the internal ESD
diodes. A VR sensor at engine speed swings far above 5 V, so this is a
guaranteed condition on this application, not an edge case.

Add a **filter capacitor across the op-amp inputs** to limit input bandwidth.

**Get the corner right: it is differential, not single-ended.** With a series
resistor in *each* leg and the capacitor between them, the time constant is
`(R1 + R2) · C`, so 10 kΩ legs with 1 nF is **8 kHz, not the 16 kHz** an earlier
revision of this document claimed.

That matters, because a 36-1 wheel at 6000 rpm is **3.6 kHz** — only 2.2×
below an 8 kHz corner, and the group delay lands in the timing:

```
group delay = τ / (1 + (f/f_c)²)

10 kΩ + 1 nF     τ = 20 µs    f_c =  8.0 kHz  →  16.6 µs at 6000 rpm = 0.60 crank°
 5 kΩ + 470 pF   τ = 4.7 µs   f_c = 33.9 kHz  →   4.65 µs            = 0.17 crank°
```

**The board is built with 5 kΩ and 470 pF** — 0.17° is small enough to ignore
rather than compensate, which is why it was chosen over 10 kΩ/1 nF. The cost is
13 dB less attenuation at 1 MHz (29 dB against 42 dB), so if the crank signal
proves noisy on the engine, this is the first term to revisit.

Note the series resistors also lower the input amplifier's gain — but in Mode A2
**that cannot affect timing at all**. The arming threshold tracks 33 % of the
previous peak whatever the gain is, and the output edge comes from the zero
crossing, which gain cannot move: scaling a waveform does not shift where it
crosses zero. The datasheet's warning to "account for it when setting the trigger
threshold" applies to the fixed-threshold modes.

#### Package these for voltage, not for power

**0805 minimum, and preferably two in series per leg.**

The binding constraint on these resistors is **maximum working voltage**, not
dissipation. A VR sensor's output rises with tooth speed and can exceed **100 V
peak** at engine speed — the same property that makes it useless at cranking
makes it brutal at redline. Almost all of that appears across the series
resistor, because the far end is clamped by the MAX9926's internal ESD diodes
to within a diode drop of the 5 V rail.

Typical thick-film chip resistor working-voltage ratings:

| Size | Max working voltage |
|---|---|
| 0402 | 50 V |
| 0603 | 50 V |
| **0805** | **150 V** |
| 1206 | 200 V |

So 0603 is genuinely marginal and 0402 is out. 0805 at 150 V has real margin
against a 100 V sensor peak.

**Better: split each leg into two resistors in series** — 2 × 4.7 kΩ or 2 × 5 kΩ
in 0805. That doubles the working-voltage headroom to 300 V, halves the voltage
stress and the pulse energy in each part, and costs one extra footprint per leg.

**As built: one 5 kΩ 0805 per leg.** The binding spec turns out to be the
datasheet's absolute maximum — `Current into IN+, IN−: ±40 mA` — and 5 kΩ gives
18.9 mA at a 100 V peak. The **0805's 150 V rating runs out first, at about
155 V of VR peak**; the current limit is not reached until ~205 V.

So the board is good to ~150 V of sensor output. **That number has never been
measured on this engine** — do it during M3 bring-up, and add the second 5 kΩ
per leg only if it goes higher.

This is very likely what rusEFI did: their VR board BOM lists **ten 5 kΩ
resistors**, and four input legs at two apiece accounts for eight of them. Two
5 kΩ in series is the 10 kΩ the datasheet asks for, built to survive the
voltage.

Dissipation is not the issue — 100 V across 10 kΩ is 10 mA and 1 W, but only
for the microseconds of a tooth peak, so average power is negligible. Chip
resistors fail here by **voltage breakdown and repetitive pulse stress**, not by
overheating, and both are addressed by more package and more parts in series.

**[CONFIRM]** the datasheet's own pin table describes pin 15 (IN1−) as
"Noninverting Input 1" and pin 16 (IN1+) as "Inverting Input 1" — the
descriptions look transposed relative to the names. Trust the names. Polarity
is in any case testable on the bench, and an inversion only changes which edge
the decoder should trigger on.

### How the adaptive threshold behaves

Two mechanisms, and both matter for cranking:

- **The 1/3 figure is the ARMING threshold, not the trigger point.** This file
  previously implied the comparator switched at 1/3 of peak. It does not. Mode A2
  enables *both* blocks: the input must first rise past **33 % of the previous
  cycle's peak** to arm, and the output edge is then produced by the
  **zero-crossing detector** at **−6.5 / +10 mV**. Adaptive arming is what tracks
  a signal from a few hundred millivolts at cranking to tens of volts at speed;
  the zero crossing is what makes the *timing* independent of amplitude.
- If the input stays below the threshold for more than **85 ms**, an internal
  watchdog drops the threshold to its minimum, so recognition recovers after an
  intermittent connection. At 200 rpm cranking a 36-1 tooth arrives every
  ~8.3 ms, so normal cranking never trips it — it is there for faults.

## Channel count — three, so two packages

| Channel | Sensor | Package |
|---|---|---|
| 1 | **CKP** (differential) | MAX9926 #1, ch 1 |
| 2 | **CMP** (single-ended) | MAX9926 #1, ch 2 |
| 3 | **OSS** (differential) | MAX9926 #2, ch 1 |
| — | spare | MAX9926 #2, ch 2 |

Three channels across two dual packages. The spare channel is genuinely useful
later: it takes the **transfer case speed sensor (C199)** on this 4x4, or TSS if
a 4R100 ever appears behind this engine.

The knock sensor is **not** one of these — it is a piezo needing a charge
amplifier and a sampled ADC channel, not edge detection.

---

## Build sheet — MAX9926, Mode A2, two channels

Channel 1 = **CKP** (crank, C102). Channel 2 = **OSS** (output shaft speed,
C187) — or CMP, if that turns out to be VR rather than Hall.

### Connections

| Pin | Name | Connect to |
|---|---|---|
| 1 | INT_THRS1 | GND |
| 2 | EXT1 | *no connection* |
| 3 | BIAS1 | GND |
| 4 | COUT1 | 10 kΩ to **3V3**, and to P4 **GPIO2** |
| 5 | COUT2 | 10 kΩ to **3V3**, and to P4 **GPIO3** |
| 6 | BIAS2 | GND |
| 7 | EXT2 | *no connection* |
| 8 | INT_THRS2 | GND |
| 9 | IN2+ | OSS+ via 2 × 5 kΩ in series |
| 10 | IN2− | OSS− via 2 × 5 kΩ in series |
| 11 | GND | GND |
| 12 | DIRN | *no connection* |
| 13 | ZERO_EN | **GND** (must be actively pulled low — internal 10 kΩ pull-up to VCC) |
| 14 | VCC | **5 V**, decoupled |
| 15 | IN1− | CKP− via 2 × 5 kΩ in series |
| 16 | IN1+ | CKP+ via 2 × 5 kΩ in series |

Plus: 1 nF across IN1+/IN1−, and 1 nF across IN2+/IN2−.

### Bill of materials

| Qty | Part | Notes |
|---|---|---|
| 1 | MAX9926UAEE+ | QSOP-16 |
| 8 | 5 kΩ, **0805** | input series — two per leg, four legs |
| 2 | 1 nF | across each channel's inputs; ~16 kHz corner with 10 kΩ |
| 2 | 10 kΩ | COUT pull-ups **to 3.3 V** |
| 1 | 10 nF | VCC decoupling — **closest to the pins** |
| 1 | 0.1 µF | VCC decoupling |
| 1 | 1 µF | VCC decoupling |

Total 15 passives and one IC. No BIAS divider, no bypass pair per channel, no
EXT network — all of which Mode A1 or B would have added.

### Two things to get right

1. **Pull COUT up to 3.3 V, not 5 V.** The part runs on 5 V; the open-drain
   output takes its level from the pull-up rail. Pull to 3.3 V and it lands
   directly on the P4 with no level shifter. Pull to 5 V out of habit and it
   damages the input.
2. **ZERO_EN must be actively tied low.** It has an internal 10 kΩ pull-up to
   VCC, so leaving it floating gives Mode A1 — which then also needs the
   external BIAS dividers that A2 avoids. A missing pulldown here fails
   quietly, as a part that mostly works.

### First bench test

Feed a signal generator into IN1+/IN1− and watch COUT1:

1. **1 kHz sine, 500 mV peak** — a stand-in for cranking. COUT should give one
   clean edge per cycle.
2. **Raise the amplitude to 10 V.** The edge should stay at the same *phase* —
   that is the zero-crossing behaving as advertised, and it is the property
   ignition timing depends on. If the edge moves with amplitude, the part is in
   the wrong mode.
3. **Sweep 100 Hz to 4 kHz** — 170 rpm to 6700 rpm on a 36-tooth wheel.
4. **Note which edge** (rising or falling) corresponds to the tooth. Polarity
   depends on wiring, and the datasheet's pin table appears to transpose the
   IN1+/IN1− descriptions, so determine it rather than assume it. The decoder
   does not care which, only that it is consistent.
