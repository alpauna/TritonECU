# Always-on MCU domain

**Proposal:** the MCU never fully powers down. It sleeps on a constant 3.3 V
supply and brings the 5 V rails up only when the engine needs to run.

This is how production ECUs are built, and it is a better answer than anything
in [`power-supply-super-cap.md`](power-supply-super-cap.md).

## What it retires

| Open thread | Status |
|---|---|
| Graceful shutdown before the rails collapse | **gone** — nothing collapses |
| KAPWR replacement for fuel trims and DTCs | **gone** — RAM never loses power |
| Supercapacitor hold-up | **gone** — the requirement that justified it is removed |
| Boot delay at key-on | **gone** — already running |

And it fixes something the review had written off. `schematic-review-power.md`
§"auto-retry" concluded that firmware retry-limiting "cannot be the primary fix,
because the MCU loses its rail." **With an always-on domain the MCU survives the
fault and can count retries, latch SHDN#, and log what happened.** The auto-retry
thermal problem becomes solvable in software after all.

Same for FLT#: the 44 ms warning stops being a race against the MCU's own death
and becomes an ordinary interrupt with plenty of time to shed loads and record
the event.

## The number that decides it: parasitic drain

A parked vehicle tolerates roughly **25–50 mA** total, and the truck has its own
draws before ours.

| Item | Sleep current |
|---|---|
| LTC4364 quiescent | **750 µA** |
| STM32F767 Standby + RTC + backup SRAM | **3 µA** |
| Always-on 3.3 V converter, quiescent | ~20 µA |
| INA238 in shutdown | ~2 µA |
| **Total** | **≈ 780 µA** |

```
780 µA × 720 h  =  0.56 Ah/month
group 65 battery ≈ 70 Ah  →  0.8 %/month,  ~5 % over six months
```

Comfortable. **Note what dominates: the LTC4364, at 250× the MCU's draw.**

### Standby, not Stop

| STM32F767 mode | Current | Retained |
|---|---|---|
| Stop, RAM retained | ~350 µA | all 512 KB, instant wake |
| **Standby + backup SRAM** | **~3 µA** | 4 KB + RTC, wakes via reset |

Fuel trims, DTCs and adaptive tables are small — **4 KB is ample**, and Standby
is 100× cheaper. Waking through a reset costs milliseconds, which is nothing
against a key turn. Use Standby; keep anything larger in SD or flash.

## The part: MAX25239AFFA

Datasheet: [`Datasheets/max25239-max25240.pdf`](Datasheets/max25239-max25240.pdf).
It fits the role better than the generic requirement written above.

| | MAX25239AFFA | Why it matters here |
|---|---|---|
| Topology | **H-bridge buck-boost, one inductor** | the "not a plain buck" requirement, met |
| Input | **2 V to 36 V**, 42 V transient | 2 V is far below the 4.2 V system floor |
| Switching | **2100 kHz** | AM-clear, same rationale as the SEPIC |
| Quiescent | **95 µA** no-load, auto skip mode | the always-on number |
| Shutdown | **5 µA** typ, EN low | for the *switched* rail |
| Spread spectrum | ±6 %, SPS pin | the SEPIC design has none |
| Qualification | **AEC-Q100 Grade 1**, −40 to +125 °C | ✓ |
| Current limit | 8.2 A, 6 A continuous | 20× the MCU load |
| Extras | PGOOD, 2.5 ms soft-start, PLL SYNC | |

### Catch: AFFA's *fixed* output is 5 V — 3.3 V needs adjustable mode

From the ordering table:

```
                     ILIM    FIXED VOUT    ADJ VOUT    fSW
MAX25239AFFA/VY+     8.2 A      5 V         < 6.5 V    2100 kHz
```

The **fixed** option on this variant is 5 V. What makes it usable at 3.3 V is
the **adjustable** column: this variant covers anything **below 6.5 V** with an
external feedback divider. So wire it for adjustable mode, not the fixed option.

That same column is the interesting part — see below.

### It must sit behind the LTC4364, not on raw B+

```
MAX25239 transient rating      42 V
SMDJ43A clamp                  69.4 V      ← what raw B+ actually sees
LTC4364 regulated output       27 V        ✓
```

**42 V is below the TVS clamp**, so an always-on rail tapped ahead of the
LTC4364 would be destroyed by the first transient the TVS passes. Behind the
LTC4364 it never sees more than 27 V, and the part's 2 V minimum means the
LTC4364's 4.2 V cutoff remains the system floor — as intended.

### Revised drain budget

| Item | Sleep current |
|---|---|
| LTC4364 quiescent | 750 µA |
| MAX25239 #1, 3.3 V, skip mode | **95 µA** |
| MAX25239 #2, 6 V rail, EN low | **5 µA** |
| STM32F767 Standby + backup SRAM | 3 µA |
| **Total** | **≈ 853 µA** → 0.61 Ah/month |

Unchanged conclusion: comfortable, and still dominated by the LTC4364.

### Package is the practical objection

**FC2QFN, 4.25 × 4.25 mm, 22 pins** — flip-chip QFN, no visible joints, not
hand-solderable. That is a real problem for bench work.

**MAX25239EAFNA/VY+** is the same silicon and same options (8.2 A, <6.5 V adj,
2100 kHz) in an **18-pin FCQFN at 5.00 × 5.00 mm** — fewer, larger pads.
Prefer it for anything hand-assembled.

## Architecture: cascade, not two independent rails

**Decided:** MAX25239 makes the main rail, TLV62085 makes 3.3 V from it.

```
B+ ─ TVS ─ LTC4364 ─► MAX25239 ─► 5.5 V ─┬─► TLV62085 ──► 3.3 V   (MCU, SD, peripherals)
                       (always on)        ├─► LDO ───────► 5 V digital
                                          ├─► LDO ───────► 5 V analog
                                          └─► LDO ───────► 5.00 V VREF
```

This replaces the earlier "two independent 3.3 V rails" sketch. Both converters
stay powered when parked; the MCU's Standby mode does the saving.

### TLV62085RLTR

Datasheet: [`Datasheets/TLV62085RLTR-Datasheet.pdf`](Datasheets/TLV62085RLTR-Datasheet.pdf).

| | |
|---|---|
| Input | **2.5 V to 6.0 V** ← the number that sets the main rail |
| Output | 0.8 V to V<sub>IN</sub>, adjustable, **3 A** |
| Switching | 2.4 MHz (DCS-Control, load-dependent) |
| **Quiescent** | **17 µA** no load |
| Shutdown | **0.7 µA**, EN low |
| Light load | **Power Save Mode**, automatic |
| Dropout | **100 % duty cycle** capable |
| Fault | **Hiccup short-circuit protection** |
| Package | VSON-HR (RLT), **2 × 2 mm**, 7 pins |
| Temperature | −40 to +125 °C |

### All-switched settles the rail voltage: use the fixed 5.0 V option

**Decided: two switched rails, no LDOs.** That removes the constraint that
forced 6 V in the first place — [`power-supply.md`](power-supply.md) chose 6 V
purely to give the 5 V LDOs headroom, and with no LDOs there is nothing to give
headroom to.

```
6.0 V nominal → TLV62085 sees 6.12 V at +2 %   over its 6.0 V rating   ✗
5.5 V nominal → 5.61 V                          7 % margin             ✓
5.0 V fixed   → 5.10 V                          18 % margin            ✓✓
```

**Use MAX25239AFFA's fixed 5.0 V option.** It is factory-trimmed to ±2 %, needs
no feedback divider, and gives the TLV62085 real input margin. The adjustable
mode is no longer needed anywhere.

### But VREF still needs isolation — a load switch, not an LDO

Dropping the LDOs drops two things that were doing real work, and only one of
them was headroom.

**A harness short on VREF now pulls down the same 5 V rail that feeds the
AD7606 and both MAX9926s.** A chafed TPS wire would take out crank and cam
conditioning — the engine stops. That is the failure
[`vref-supply.md`](vref-supply.md) exists to prevent.

**Use a current-limited load switch** rather than an LDO. It keeps the
all-switched character — a FET at tens of milliohms, not a linear drop — while
providing an electronic current limit and a fault flag. VREF stays at the rail
voltage; the ADC and the VR conditioners stay up when the harness faults.

### And put a ferrite between the analog and digital sections

The other LDO job was keeping the AD7606 and MAX9926s off the rail that feeds
the 74HCT541 gating eight ignition coils. On one rail, replace that split with a
**ferrite bead plus local bulk** at the analog section. Switching and gate-drive
noise is above 1 MHz, where a ferrite works well, and the AD7606's own 22 kHz
anti-alias filter catches what gets through. Not as good as an LDO's PSRR, good
enough here.

## MAX25239 output capacitor and compensation

Reproducible in
[`../hardware/calc/max25239_comp.py`](../hardware/calc/max25239_comp.py), from
datasheet Equations 8–15.

Compensation is designed where the datasheet says to — **minimum input and heavy
load**, which is the deepest boost and the lowest RHP zero:

```
Vin = 4.2 V (the LTC4364 cutoff), Vout = 5.0 V, Iout = 1.0 A, L = 2.2 µH

D          = 0.160  (boost)
RHP zero   = 255.2 kHz
target fc  =  51.0 kHz     = fsw/41
```

### DECIDED: 4 × 22 µF

| Bank | C effective | Ripple | vs 15.6 µF transient need |
|---|---|---|---|
| 2 × 22 µF, 0805 16 V | 24 µF | 9.8 mV | OK, 1.5× |
| 2 × 22 µF, 1206 25 V | 33 µF | 8.9 mV | OK, 2.1× |
| **4 × 22 µF** | **66 µF** | **7.8 mV** | **OK, 4.2×** |

2 × 22 µF is genuinely sufficient on every criterion — ripple current is only
**0.44 A rms** at the boost corner and Equation 10 asks for 15.6 µF. What makes
4 the better answer is **DC bias derating**: a 22 µF 0805 X7R at 5 V loses
around 45 % of its nominal, so "44 µF" is really ~24 µF, and the margin against
the transient requirement is thinner than the label suggests. Four removes the
question, and matches the datasheet's own 2.1 MHz application circuit.

### Compensation values

```
Rc = 78.7 kΩ        (calculated 78.8 kΩ)
Cc =  2.2 nF        (calculated 2.10 nF)
Cp =  8.2 pF        (calculated 7.9 pF)
```

Check where that puts the poles and zeros:

| | Placed at | Target |
|---|---|---|
| f<sub>ZEA</sub> = 1/(2π·Rc·Cc) | **919 Hz** | f<sub>PBOOST</sub> = 965 Hz ✓ |
| f<sub>P2EA</sub> = 1/(2π·Rc·Cp) | **247 kHz** | RHP zero = 255 kHz ✓ |

Both land where the datasheet wants them.

### Two layout consequences

- **C<sub>p</sub> is 8.2 pF, and board stray on the COMP node is 2–5 pF** — a
  third of the value. Keep COMP compact and away from LX1/LX2. Stray adds to
  C<sub>p</sub>, which lowers f<sub>P2EA</sub> and is conservative, but it makes
  the placement approximate rather than designed.
- **R<sub>c</sub> = 78.7 kΩ is a high-impedance node** next to a 2.1 MHz
  switcher. Short trace, guarded if possible.

### C<sub>p</sub> is not a critical value — defer it to the bench

Deliberately left open until the board exists and board stray on COMP can be
measured rather than guessed (expected ~5 pF). It costs little either way:

| C<sub>p</sub> fitted | Total with 5 pF stray | f<sub>P2EA</sub> | Phase margin at 51 kHz |
|---|---|---|---|
| 8.2 pF | 13.2 pF | 153 kHz | **≈ 59°** |
| 3.3 pF | 8.3 pF | 244 kHz | **≈ 66°** |
| none | 5.0 pF | 404 kHz | ≈ 69°, less HF rolloff on COMP |

Seven degrees, and every option is comfortably above the 45° that matters. The
second pole sits 3–8× above crossover in all three cases, so it is doing very
little at the frequency that decides stability.

**Fit 8.2 pF as the starting value**; if stray measures near 5 pF and the loop
wants the pole back on target, **3.3 pF** puts it there. Use a 0402 footprint so
the swap is trivial.

### Design in a loop-injection point now

The measurement that settles C<sub>p</sub> is a **Bode plot, not a capacitance
reading** — stray on COMP is only interesting through its effect on the loop.
Make that measurable without cutting traces:

- **10–20 Ω in series with the top of the FB divider**, with a test point either
  side. Negligible in normal operation (FB draws ~20 nA), and it is the standard
  injection point for a transformer or isolated generator.
- Sweep 100 Hz to 500 kHz. Target **phase margin > 45°, gain margin > 10 dB**.
- **Measure in boost mode**, around 4.5 V in — that is where the RHP zero lives
  and the only place the design is actually constrained. A clean plot at 13.8 V
  proves very little.

Two resistors and two pads, decided now, save cutting into a working board later.

### One thing that shifts the numbers

The TLV62085's input capacitors sit on this same 5 V rail, so the MAX25239's
true C<sub>OUT</sub> is higher than 66 µF. That pushes the real crossover
*below* 51 kHz — slower, more stable, no action needed. Worth knowing when
the measured loop does not match the calculation.

### And why the bandwidth is conservative

51 kHz is f<sub>sw</sub>/41, well below the f<sub>sw</sub>/10–20 a buck would
allow. That is the RHP zero's doing, and it only exists in boost mode — which
this converter enters **only below 5 V input**, i.e. during severe cranking.
Designing there costs transient response at 13.8 V, and buys one compensation
network that is stable across the entire range. The datasheet's guidance, and
the right trade for a vehicle.

## SPS: yes, enable spread spectrum — but tie it to VCC, not 5 V

### ⚠ SPS is a 2.2 V pin

```
Absolute Maximum:   VCC, SPS to AGND ............ −0.3 V to +2.2 V
                    COMP, FB to AGND ............ −0.3 V to VCC + 0.3 V
```

**"Tie SPS high" means the VCC pin — the internal ~1.8 V bias regulator with its
4.7 µF cap — not the 5 V rail.** Strapping it to 5 V destroys the part. EN is
the exception in this pinout, rated to 42 V; SPS, COMP and FB are all
VCC-referenced.

Easy mistake, and there is no second chance on a flip-chip QFN.

### Why enable it

**It costs nothing on the constraint that chose 2.1 MHz in the first place:**

```
2.1 MHz ± 6 %  =  1.974 – 2.226 MHz
AM band top    =  1.710 MHz
```

The whole spread stays clear of the AM band, with 264 kHz to spare at the bottom.
Spread spectrum does not create energy below the lower edge, so nothing lands in
the band. In exchange it takes **10–20 dB off peak emissions** — which is the
entire reason the frequency was pushed to 2.1 MHz.

### And it costs nothing at the ADC either

The obvious objection is that smearing the ripple spectrum makes it harder to
filter deterministically. The numbers say it does not matter:

```
AD7606 anti-alias filter        22 kHz
switching                      2.1 MHz, 95× above  →  ~40 dB
10 mV rail ripple              →  ~100 µV at the ADC input
±10 V range, 16 bit            305 µV/LSB          →  0.3 LSB
```

Below a bit either way, spread or not. And the TLV62085's DCS-Control is not
fixed-frequency to begin with, so there is no clean beat tone being preserved by
leaving SPS off.

### Make it a strap, not a hard connection

A 0 Ω to VCC or to AGND, so the choice can be reversed after bench EMI
measurements without cutting the board.

### Two things to check on the bench

- **The modulation rate is not specified.** If it falls inside the 51 kHz loop
  bandwidth the loop would track it and put ripple at that rate on the output.
  For a current-mode converter, frequency modulation barely moves the DC
  transfer function, so this is normally a non-issue — but compare output ripple
  with SPS high and low during bring-up, since it is a two-minute check.
- **Internal spread spectrum is disabled when synced to an external clock.** If
  the two converters are ever PLL-synced, SPS becomes moot and the modulation
  would have to come from the driving clock instead.

## SYNC: tie it to AGND — and note it is *not* a 2.2 V pin

### SPS and SYNC are adjacent straps with completely different ratings

```
VCC, SPS to AGND ......... −0.3 V to +2.2 V     ← tie to the VCC pin
SYNC, PGOOD to AGND ...... −0.3 V to  +6 V      ← 3.3 V logic drives it directly
SUP, EN to AGND .......... −0.3 V to +42 V
```

Easy to conflate: two small strap pins next to each other, one of which dies on
anything above 2.2 V and one of which takes 6 V. **SYNC needs no level shift
from 3.3 V; SPS must never see it.**

### SYNC = 0 V, because that is how the 95 µA is specified

```
Standby Supply Current   ISUP_STANDBY = 95 µA
  conditions:  VEN = VSUP, VOUT = 5 V, no load, **VSYNC = 0 V**
```

**The quiescent figure the whole always-on architecture rests on is measured
with SYNC grounded.** Forced PWM would give that up — the converter would switch
at 2.1 MHz continuously into no load, burning gate charge for nothing.

Nothing is lost by choosing skip: **the part runs fixed-frequency PWM under load
anyway** and only skips once inductor current goes discontinuous:

```
buck mode, 13.8 V in, 5 V out, L = 2.2 µH, 2.1 MHz
ΔIL = Vout (Vin − Vout) / (Vin · L · fsw) = 0.69 A
DCM boundary  =  ΔIL / 2  =  345 mA
```

| Condition | Load | Mode |
|---|---|---|
| Asleep | ~0.1 mA | deep skip ✓ |
| Key on, engine off, MCU + ADC | 300–500 mA | **near the boundary** |
| Running | ~1 A | PWM ✓ |

Only the middle case is ambiguous, and skip-mode ripple there still lands well
under 1 LSB after the ferrite, the local bulk and the AD7606's 22 kHz filter.

**Route SYNC to a GPIO anyway**, defaulting low. It is one trace and no level
shifter, and it leaves forced PWM available if bench work shows a skip artifact
at that intermediate load.

### Polarity, from the pin table

> *Connect SYNC to **AGND to enable skip mode**. Connect SYNC to **VCC to enable
> PWM mode**. Connect SYNC to a valid external clock to synchronize…*

**Low is skip, high is PWM — so SYNC starts and stays low.** High would be the
wrong default, and "high" here means **VCC (~1.8 V)**, not the 3.3 V rail,
though the 6 V rating makes 3.3 V safe to drive.

### But the startup instinct is right, for a different reason

**The MCU is powered by this converter**, so at power-up its GPIO is in reset and
high-impedance. A GPIO alone would leave SYNC **floating** through the entire
startup — undefined mode on the converter that has to come up first.

**Fitted: 10 kΩ to AGND, with SYNC brought out to a GPIO.** Skip mode is
defined before the MCU exists, and a push-pull GPIO overrides it at 330 µA once
running — only in PWM mode, so it costs nothing in sleep.

**This works because STM32 GPIOs go high-impedance in Standby.** The pull-down
is what holds skip mode through the two states where firmware cannot: power-up
before the MCU boots, and Standby while it sleeps. Those are exactly the states
where the 95 µA quiescent matters, so the resistor is doing the load-bearing
work and the GPIO is only an override for the running case.

Driving 3.3 V into SYNC is safe and unambiguous: the pin is rated to 6 V against
AGND, not clamped to V<sub>CC</sub>, so there is no diode to forward-bias by
exceeding the 1.8 V rail.

### SPS is the opposite: hard strap only, never a GPIO

SPS is a **2.2 V** pin. A 3.3 V GPIO driving it destroys the part — the 6 V
tolerance belongs to SYNC and PGOOD, not to SPS. **Strap SPS to VCC with a
0 Ω**, and leave it out of firmware's reach entirely.

### External clock sync: no

Nothing to gain and three reasons not to:

- **There is no second device to synchronise to.** The TLV62085 uses
  DCS-Control and has no SYNC input.
- **It disables the internal spread spectrum**, which was just enabled for real
  EMI benefit.
- **It would make the converter depend on an MCU clock that must survive
  sleep** — the one state where the MCU is meant to be doing nothing.

### Incidental find: the two UVLOs nearly coincide

```
MAX25239  VUVLO_RISE  4.2 – 4.45 V      VUVLO_FALL  1.9 V
LTC4364   UV release              4.47 V
```

The converter starts just as the LTC4364 releases, and once running holds
regulation down to 1.9 V — far below where the LTC4364 disconnects. **So the
LTC4364 remains the system floor with no contention**, and the MAX25239's 2 V
minimum operating spec is backed by a real falling threshold rather than a
typical figure.

## FB: use adjustable mode, not the fixed option

The pin table gives the other half of the fixed-output story:

> *Connect FB to a resistor-divider between OUT and AGND to set the desired
> output voltage… **Connect FB to V<sub>CC</sub> for the fixed output voltage
> option**.*

So the fixed 5.0 V is selected by tying FB to VCC — no divider at all. **That
also removes the loop-injection point** designed in above, because there is no
external feedback path to inject into.

### The trade

| | Fixed (FB → VCC) | Adjustable |
|---|---|---|
| Accuracy | **±2 %** | ~±3 % worst case |
| Parts | none | 2 resistors |
| Sleep drain | 0 | **+78 µA** |
| **Loop measurable in circuit** | **no** | **yes** |
| Output trimmable | no | yes |

**Use adjustable.** The reasoning:

- **The injection point is worth more than the 1 %.** This board has an RHP zero
  in boost mode and a compensation network calculated rather than measured;
  being able to take a Bode plot on the first article is the difference between
  knowing and hoping.
- **The 5 V rail's absolute accuracy has already been made irrelevant.** VREF is
  this rail through a load switch, and the decision above is to **sample VREF on
  an ADC channel and divide** — so ratiometric sensors self-correct regardless.
  Nothing else on the rail cares about 1 %.
- **78 µA is 9 % of the sleep budget**, taking it to ~945 µA and 0.68 Ah/month.
  Still about 1 % of the battery per month.

```
Vfb = 0.800 V

R_top = 53.6 kΩ, R_bot = 10.2 kΩ   →   Vout = 0.8 × 63.8/10.2 = 5.004 V
divider current = 0.8 / 10.2 kΩ    =   78 µA
```

**Do not raise the divider impedance to save that current.** FB leakage is
0.02 µA typical but **1 µA maximum**, so at 78 µA of divider current the
worst-case error is 1.3 %; at 20 µA it would be 5 %.

### PGOOD

> *Pull up PGOOD with an external resistor to V<sub>CC</sub> or a positive
> voltage lower than 5.5 V.*

So **3.3 V is a legal pull-up rail** — take PGOOD straight to an MCU input, no
level shifting. It asserts low below 93 % of regulation and releases above 94 %,
which is a cheap independent check on the rail the MCU is running from.

## The 2.5 V ADC reference

Right call — an external reference on the AD7606's REFIN beats the internal one
on drift, which is the term that matters over a −40 to +125 °C ECU:

```
AD7606 internal   ~10 ppm/°C  →  ~1650 ppm over range  =  16 mV on ±10 V
ADR4525            2 ppm/°C   →  ~330 ppm              =   3.3 mV
```

16 mV is nothing on a MAP sensor and **3.5 % on a narrowband HO2S switching
around 450 mV** — which lands directly in fuel trim. That is what buys the part.

### It fixes absolute accuracy, not ratiometric accuracy

Worth being precise, because this is easy to conflate:

| Measurement | Tracks | Improved by a 2.5 V reference? |
|---|---|---|
| HO2S, absolute voltages | ADC reference | **yes** |
| TPS, MAP, three-wire sensors | **VREF** | **no** |

Ratiometric sensors report a fraction of VREF, so their accuracy depends on
VREF, not on the ADC's reference. **Sample VREF on an ADC channel and divide** —
with the AD7606 sampling simultaneously, VREF and the sensor are captured at the
same instant, so supply ripple cancels exactly. That is worth more than any
regulator on VREF, and it is free.

### Filtering the reference — RC beats an LC pi here

Filtering its input is correct: a reference's PSRR is strong at DC and poor by
2 MHz, which is exactly where both switchers live.

But at 950 µA of supply current with 2.5 V of headroom to spare, **a series
resistor outperforms a ferrite**:

```
R = 100 Ω, C = 10 µF ∥ 100 nF

corner        1 / (2π × 100 × 10 µF)          =  159 Hz
attenuation   at 2.1 MHz, ESL-limited          ≈  78 dB
cost          950 µA × 100 Ω                   =  95 mV
headroom left 5.0 − 0.095 = 4.9 V, against ~3.0 V needed   ✓
```

**No resonance, no ferrite to characterise, two components.**

The 100 nF matters: a 10 µF ceramic self-resonates near 1.6 MHz, so above that
it is inductive and its own ESL sets the floor. The small cap carries the high
end.

**Firmware consequence: allow ~10 ms after enabling the reference** before the
first valid conversion. `5 × RC = 5 ms` for the input to settle, plus the
reference's own turn-on time. Since the reference is gated for sleep (below),
that delay lands at key-on, where 10 ms is nothing against an engine start.

### If a pi filter is used instead, check its resonance

A ferrite is the right choice over a wound inductor there — it is lossy, so the
LC is damped rather than peaking. But it is not fully damped:

```
typical bead ≈ 1 µH at low frequency, with C = 1 µF
f0 = 1 / (2π √(1 µH × 1 µF))  =  159 kHz
```

**That is inside the range both converters actually visit.** The MAX25239 in
skip mode and the TLV62085 in Power Save Mode both drop their switching
frequency at light load, which is precisely the always-on sleep condition. A
filter that peaks where the supply is noisiest is worse than no filter.

Fix either way: **put 10 Ω in series with the bead**. It damps the resonance,
costs 9.5 mV, and adds attenuation. Or move `f0` well below the PSM range with a
larger output capacitor.

### The output side matters more than the input

The AD7606 is a SAR converter, so **REFIN sees charge kicks on every
conversion**, not a steady load. Two things follow:

- Put **10 µF + 100 nF right at the REFIN pin**, short traces. This is the
  decoupling that actually sets reference settling between samples, and no
  amount of input filtering substitutes for it.
- **Confirm the reference is stable driving that capacitance.** Some precision
  references oscillate into large ceramic loads, and the ones that do not
  usually say so explicitly. Check before committing to the part.

Place the reference, its RC and its output caps all on the **analog side** of
the section ferrite, so this filtering cascades with that rather than duplicating
it.

### DECIDED: ADR431BRZ (2.5 V, SOIC-8)

Datasheet:
[`Datasheets/ADR430_431_433_434_435.pdf`](Datasheets/ADR430_431_433_434_435.pdf).

| | ADR431B |
|---|---|
| Output | 2.500 V, **±1 mV** initial (±0.04 %) |
| Tempco | **3 ppm/°C** |
| Noise | 3.5 µV p-p (0.1–10 Hz), 80 nV/√Hz at 1 kHz |
| Output current | **30 mA source**, 20 mA sink |
| Quiescent | 580 µA typ, **800 µA max** |
| **Supply range** | **4.5 V to 18 V**, headroom V<sub>IN</sub> − V<sub>OUT</sub> ≥ **2 V** |
| Long-term stability | 40 ppm / 1000 h |
| Pins | 2 VIN, 4 GND, 5 TRIM, 6 VOUT, **7 COMP** |

### Correction: I overstated the drift benefit earlier

An earlier revision claimed the AD7606's internal reference costs "3.5 % on a
narrowband HO2S". **That was wrong** — it treated a reference error as a
full-scale offset. A reference error is a **gain** error, so it scales with the
reading, not with the range:

| | Drift over −40…+125 °C | Gain error |
|---|---|---|
| AD7606 internal, ~10 ppm/°C | 1650 ppm | **0.165 %** |
| ADR431B, 3 ppm/°C | 495 ppm | **0.05 %** |

On a 450 mV HO2S that is 0.74 mV versus 0.22 mV. Both are small. The ADR431 is
a 3.3× improvement on a term that was already minor.

**The real wins are elsewhere:** ±1 mV initial accuracy against the internal
reference's typical ±0.1–0.2 %, plus 40 ppm/1000 h long-term stability and
3.5 µV p-p noise — which is 1.4 ppm, or 14 µV on a 10 V reading, comfortably
under a 305 µV LSB.

### The 10 µF question is answered — and it needs the COMP network

The open item was whether the reference is stable driving the 10 µF at REFIN.
The datasheet answers both halves:

> *Other than a 0.1 µF capacitor at the output to help improve noise
> suppression, **a large output capacitor at the output is not required for
> circuit stability**.*

So it is stable either way. But large capacitance is not free:

> *…references are used increasingly to drive the reference input of an ADC that
> may present a dynamic, switching capacitive load. **Large capacitors, in the
> microfarad range, reduce the change in reference voltage to less than one-half
> LSB**.*
>
> *…With various values of capacitive loading, the **predicted noise peaking
> becomes evident**.*
>
> *The **82 kΩ resistor and 10 nF capacitor** eliminate noise peaking. Leave the
> COMP pin unconnected if unused.*

ADI explicitly endorses microfarad-range output capacitance for driving an ADC
reference input — which is exactly the AD7606 charge-kick problem — and gives
the fix for the noise peaking it causes.

**Fit all three: 10 µF + 100 nF at REFIN, and 82 kΩ + 10 nF on COMP.** The COMP
network is easy to leave off, since the part works without it and the penalty is
noise rather than oscillation.

### Change the input filter to 47 Ω / 22 µF

The **4.5 V minimum supply** is the tightest spec in the part, against a 5 V
rail set by a 1 % divider and a ±1.75 % feedback reference:

```
5 V rail, worst-case low                        4.836 V
100 Ω × 800 µA (the earlier value)             −0.080 V  →  4.756 V, 256 mV margin
 47 Ω × 800 µA                                 −0.038 V  →  4.798 V, 298 mV margin
```

**47 Ω with 22 µF** holds the same corner — `1/(2π·47·22 µF)` = **154 Hz**
against the 159 Hz of 100 Ω / 10 µF — while halving the drop. Same attenuation,
more headroom, no downside. Keep the 100 nF alongside.

### Gating is confirmed necessary

The pinout is DNC / VIN / NIC / GND / TRIM / VOUT / COMP / DNC — **there is no
enable pin**. At 800 µA maximum it would take the sleep budget from 945 µA to
1745 µA, nearly doubling it, for a part that is only useful while converting.

**External load switch, GPIO-driven.** And leave TRIM unconnected: ±1 mV initial
accuracy is already 0.04 %, so there is nothing worth trimming.

### Settling: the 10 ms guidance holds

```
input RC        5 × 47 Ω × 22 µF        = 5.2 ms   ← dominant
10 µF at 30 mA source                   = 0.8 ms
reference turn-on, CL = 0               =  10 µs
```

About 6 ms total, so **10 ms after enabling before the first valid conversion**
stands.

### Filtering the reference — RC beats an LC pi here

Filtering its input is correct: a reference's PSRR is strong at DC and poor by
2 MHz, which is exactly where both switchers live.

But at 950 µA of supply current with 2.5 V of headroom to spare, **a series
resistor outperforms a ferrite**:

```
R = 100 Ω, C = 10 µF ∥ 100 nF

corner        1 / (2π × 100 × 10 µF)          =  159 Hz
attenuation   at 2.1 MHz, ESL-limited          ≈  78 dB
cost          950 µA × 100 Ω                   =  95 mV
headroom left 5.0 − 0.095 = 4.9 V, against ~3.0 V needed   ✓
```

**No resonance, no ferrite to characterise, two components.**

The 100 nF matters: a 10 µF ceramic self-resonates near 1.6 MHz, so above that
it is inductive and its own ESL sets the floor. The small cap carries the high
end.

**Firmware consequence: allow ~10 ms after enabling the reference** before the
first valid conversion. `5 × RC = 5 ms` for the input to settle, plus the
reference's own turn-on time. Since the reference is gated for sleep (below),
that delay lands at key-on, where 10 ms is nothing against an engine start.

### If a pi filter is used instead, check its resonance

A ferrite is the right choice over a wound inductor there — it is lossy, so the
LC is damped rather than peaking. But it is not fully damped:

```
typical bead ≈ 1 µH at low frequency, with C = 1 µF
f0 = 1 / (2π √(1 µH × 1 µF))  =  159 kHz
```

**That is inside the range both converters actually visit.** The MAX25239 in
skip mode and the TLV62085 in Power Save Mode both drop their switching
frequency at light load, which is precisely the always-on sleep condition. A
filter that peaks where the supply is noisiest is worse than no filter.

Fix either way: **put 10 Ω in series with the bead**. It damps the resonance,
costs 9.5 mV, and adds attenuation. Or move `f0` well below the PSM range with a
larger output capacitor.

### The output side matters more than the input

The AD7606 is a SAR converter, so **REFIN sees charge kicks on every
conversion**, not a steady load. Two things follow:

- Put **10 µF + 100 nF right at the REFIN pin**, short traces. This is the
  decoupling that actually sets reference settling between samples, and no
  amount of input filtering substitutes for it.
- **Confirm the reference is stable driving that capacitance.** Some precision
  references oscillate into large ceramic loads, and the ones that do not
  usually say so explicitly. Check before committing to the part.

Place the reference, its RC and its output caps all on the **analog side** of
the section ferrite, so this filtering cascades with that rather than duplicating
it.

### Budget the reference's supply current — it can double the parked drain

Precision references are not low-power parts:

| Part | Drift | Supply current |
|---|---|---|
| ADR4525 | 2 ppm/°C | **950 µA** |
| ADR3425 | 8 ppm/°C | 100 µA |
| REF3025 | 75 ppm/°C | 42 µA |

**950 µA would more than double the 875 µA sleep budget** for a part that is
only useful while the engine runs. **Gate it** — a GPIO-driven load switch, or a
reference with a shutdown pin — and keep the good drift spec. Do not compromise
to 75 ppm/°C to save current that switching off saves anyway.

### Revised drain budget

| Item | Sleep current |
|---|---|
| LTC4364 quiescent | 750 µA |
| MAX25239 #1, 3.3 V, skip mode | **95 µA** |
| MAX25239 #2, 6 V rail, EN low | **5 µA** |
| STM32F767 Standby + backup SRAM | 3 µA |
| **Total** | **≈ 853 µA** → 0.61 Ah/month |

Unchanged conclusion: comfortable, and still dominated by the LTC4364.

### Package is the practical objection

**FC2QFN, 4.25 × 4.25 mm, 22 pins** — flip-chip QFN, no visible joints, not
hand-solderable. That is a real problem for bench work.

**MAX25239EAFNA/VY+** is the same silicon and same options (8.2 A, <6.5 V adj,
2100 kHz) in an **18-pin FCQFN at 5.00 × 5.00 mm** — fewer, larger pads.
Prefer it for anything hand-assembled.

## Architecture: cascade, not two independent rails

**Decided:** MAX25239 makes the main rail, TLV62085 makes 3.3 V from it.

```
B+ ─ TVS ─ LTC4364 ─► MAX25239 ─► 5.5 V ─┬─► TLV62085 ──► 3.3 V   (MCU, SD, peripherals)
                       (always on)        ├─► LDO ───────► 5 V digital
                                          ├─► LDO ───────► 5 V analog
                                          └─► LDO ───────► 5.00 V VREF
```

This replaces the earlier "two independent 3.3 V rails" sketch. Both converters
stay powered when parked; the MCU's Standby mode does the saving.

### TLV62085RLTR

Datasheet: [`Datasheets/TLV62085RLTR-Datasheet.pdf`](Datasheets/TLV62085RLTR-Datasheet.pdf).

| | |
|---|---|
| Input | **2.5 V to 6.0 V** ← the number that sets the main rail |
| Output | 0.8 V to V<sub>IN</sub>, adjustable, **3 A** |
| Switching | 2.4 MHz (DCS-Control, load-dependent) |
| **Quiescent** | **17 µA** no load |
| Shutdown | **0.7 µA**, EN low |
| Light load | **Power Save Mode**, automatic |
| Dropout | **100 % duty cycle** capable |
| Fault | **Hiccup short-circuit protection** |
| Package | VSON-HR (RLT), **2 × 2 mm**, 7 pins |
| Temperature | −40 to +125 °C |

### Set the main rail at 5.5 V, not 6.0 V

The TLV62085's **6.0 V absolute input maximum** collides with the 6 V main rail
that [`power-supply.md`](power-supply.md) chose for LDO headroom:

```
6.0 V nominal ± 2 % regulation  →  6.12 V     over the TLV62085's rating ✗
5.5 V nominal ± 2 % regulation  →  5.61 V     7 % margin                ✓
```

**5.5 V satisfies both constraints:**

- TLV62085 input stays inside 2.5–6.0 V with real margin
- The 5 V LDOs keep **0.5 V of headroom** — enough for low-dropout parts at the
  25–150 mA these rails draw, where 1 V was never actually required
- MAX25239AFFA's adjustable range is "< 6.5 V", so 5.5 V is in range

Do **not** use the part's fixed 5.0 V option: it leaves the 5 V LDOs no headroom
at all, and VREF in particular has to be a regulated 5.00 V isolated from the
switcher.

### This largely defuses MAX25239 Note 5

[`power-supply.md`](power-supply.md) flags *"output short circuit not allowed"*
as the blocking question for using the MAX25239 more widely. In **this**
topology it matters much less: the MAX25239's output faces **three LDOs and one
buck, every one of them internally current-limited**, and never a connector,
harness or anything a fault can reach. The TLV62085 brings its own hiccup
protection, and VREF's harness exposure sits behind an LDO plus a PTC.

The question still needs answering before the MAX25239 drives anything external.
It is no longer blocking for this arrangement.

### Revised drain budget

| Item | Sleep current |
|---|---|
| LTC4364 quiescent | 750 µA |
| MAX25239, 5.5 V, skip mode | 95 µA |
| **TLV62085, Power Save Mode** | **17 µA** |
| 5 V LDO quiescents (or disabled) | ~10 µA |
| STM32F767 Standby + backup SRAM | 3 µA |
| **Total** | **≈ 875 µA** → 0.63 Ah/month |

Cascading costs 17 µA over the parallel arrangement. Irrelevant against the
LTC4364's 750 µA.

### Two notes, neither blocking

- **Not AEC-Q100.** Every other part in this chain is automotive-qualified —
  LTC4364, MAX25239 Grade 1, LM5155-Q1. The TLV62085 is rated −40 to +125 °C,
  which is the Grade 1 *temperature* range, but without the qualification,
  PPAP or change control. For a one-vehicle build that is a reasonable trade;
  it should be a stated choice rather than an oversight.
- **2.1 MHz and 2.4 MHz beat at 300 kHz**, which is inside CISPR 25's band. It
  mostly stays internal — the TLV62085 is a point-of-load, so its switching
  appears as load modulation that the MAX25239's output capacitors absorb rather
  than as harness current. DCS-Control is also not rigidly fixed-frequency, so
  there is no clean tone to beat against. Worth a look on the bench, not worth
  designing around.
- Power Save Mode drops the switching frequency at light load, potentially into
  the AM band — but that only happens with the MCU asleep and the vehicle
  parked, when the radio is off too.

## Tapping point: after the LTC4364, not before

Simplest and protected. The cost is the LTC4364's 750 µA running permanently,
which the budget above absorbs.

The alternative — tapping raw B+ so the MCU can shut the LTC4364 down via SHDN#
— would cut the parasitic to tens of microamps, but it needs a **second
transient-protection chain** for a rail that must survive load dump and reverse
battery on its own. **Not worth it at 0.56 Ah/month.** Revisit only if the truck
sits for many months at a time.

## The new requirement this creates: low-battery self-disable

An always-on load is a permanent path to a flat battery. The design has to be
able to give up.

**Firmware does this for free**, using the INA238 already on the shunt:

```
bus voltage < ~11.5 V for N seconds
  → write learned state to SD
  → enter Standby (3 µA)
  → wake only on ignition, never on the RTC
```

Below that threshold the battery is already too weak to be worth defending, and
3 µA is close enough to nothing that it cannot be what fails to start the truck.
The LTC4364's UV pin cannot serve here — it is set at 4.47 V, which is a
brownout threshold, not a battery-protection one.

**This is not optional.** Without it, a slow parasitic drain plus a marginal
battery becomes a no-start that looks like a dead ECU.

## Open questions

- **Wake source wiring.** Switched ignition into an MCU pin needs level shifting
  and its own transient protection — it is a harness-facing input.
- **Whether the SD card stays on the switched rail.** It probably should; it is
  a large sleep load otherwise, and nothing needs it while parked.
- **Watchdog behaviour in Standby**, so a hung MCU cannot sit awake drawing
  hundreds of milliamps in a parked truck.
