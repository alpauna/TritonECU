# Analog input chain review — pre-schematic

Review of the analog front end as specified in
[`adc-front-end.md`](adc-front-end.md) and
[`f150-1999-target.md`](f150-1999-target.md) §3, with Ford's diagrams now in the
tree.

**The precision ADC side is in good shape.** The findings are all on the
*internal* ADC, which this project — and this review's author — has repeatedly
called "plentiful" without once counting it.

---

## 1. ~~IMPORTANT — the internal ADC budget has never been counted~~ FIXED

| Demand | Ch | Added by |
|---|--:|---|
| DPFE, TFT, downstream O2 ×2, fuel pump monitor | 5 | `adc-front-end.md` |
| VREF `CS` current sense | 1 | `vref-supply.md` |
| VREF per-feed short-to-battery dividers | 2 | `vref-supply.md` |
| **Solenoid/heater drain sense** | **12** | `output-drivers.md` |
| 1138 / 391 solenoid supply sense | 2 | `output-drivers.md` |
| **Total** | **22** | |

Each of these is a **pin** as well as a channel. "Internal channels are
plentiful" was asserted three separate times while building this up — once to
justify moving `CS` off the precision ADC, once for the VREF feed dividers, once
for the drain sense — **and the running total was never checked against the
STM32F767ZI's actual channel map.**

> **[CONFIRM]** how many distinct external ADC channels the F767ZI exposes on
> this package, and which pins they land on. ADC1/2/3 share heavily, so the
> usable count is not three times sixteen.

**The drain sense is 12 of the 22**, and it is the one to attack first:

- **Only the four HO2S heater channels have an OBD requirement.** The rest is
  nice-to-have diagnosis.
- **EPC has the NCV8408B's gate-current flag instead**, which needs no drain
  sample and no PWM synchronisation.
- The remaining seven could **multiplex** — they are slow, static signals and
  nothing needs them simultaneously.

> **Fixed 2026-09-17, and without multiplexing.** Counted first: **24
> ADC-capable pins, minus 6 consumed by Ethernet RMII** (PA1, PA2, PA7, PC1,
> PC4, PC5 are `ADC123_IN1/2/7/11/14/15`, and `Board.h` already lists them as
> RMII) = **18 available**.
>
> Then reduced demand **23 → 15**, by noticing that most outputs already have
> **better feedback than a drain voltage**: DPFE measures EGR flow, gear-ratio
> mismatch catches the shift solenoids, RPM-versus-OSS catches TCC, idle error
> catches IAC, and EPC has the gate-current flag. Drain sense is kept only where
> nothing else sees the circuit — the **four heaters plus EVAP purge and
> canister vent**, all OBD-II monitors. Only IMCC loses diagnosis outright.
>
> The allocation and the budget now live in
> [`adc-front-end.md`](adc-front-end.md), which owns them.

---

## 2. ~~Two allocated channels are for signals the PCM does not have~~ FIXED

[`f150-1999-target.md`](f150-1999-target.md) §3 lists on the native ADC:

> | Fuel level, A/C pressure, spare | — | P4 ADC |

Ford's diagrams say otherwise:

| | Reality |
|---|---|
| **Fuel level** | Sender goes to the **instrument cluster**, C236 pin 3 — not the PCM |
| **A/C pressure** | There is no analog pressure sensor. The PCM has only the **cycling pressure switch**, a digital input on pin 41 |

Both are recorded in
[`schematic-findings.md`](1999-Ford-F150-4wd-5.42v/schematic-findings.md) §13.
If either is wanted, it is a **harness tap**, not an existing input.

**And the two documents disagree with each other.** `adc-front-end.md` lists the
moved-off channels as *"DPFE, TFT, downstream O2 ×2, fuel pump monitor"* —
neither fuel level nor A/C pressure appears. One list has phantoms, the other
does not, and nothing reconciles them.

> **Fixed 2026-09-17.** Both phantoms struck from `f150-1999-target.md` §3 with
> the reason recorded, and the two documents given distinct jobs: **§3 is an
> inventory of signals, `adc-front-end.md` owns the allocation.** §3 now says so
> at the top, which is what stops them drifting apart again.

---

## 3. The ±10 V range is forced by channel 7, not chosen

`adc-front-end.md` presents the range as a trade:

> ±10 V takes 0–5 V sensors directly with headroom for overshoot. ±5 V doubles
> [the resolution]

But `RANGE` is **one setting shared by all eight channels**, and channel 7 is
**VREF sense at 5.00 V**. On a ±5 V range that is **exactly full scale** — any
positive tolerance, ripple or overshoot clips, and the ratiometric divisor is
the one signal that must never clip.

So ±10 V is not a preference. **It is forced**, and it costs a bit of resolution
on every other channel:

| Range | Volts per count | 0–5 V sensor uses |
|---|---|---|
| ±10 V | 305.18 µV | 25 % of the span |
| ±5 V | 152.59 µV | 50 % — **but VREF clips** |

Worth stating as a consequence rather than a preference, because it is the kind
of thing someone later "optimises" by switching to ±5 V.

---

## 4. Series resistance into the ADC inputs is unspecified

[`harness-protection.md`](harness-protection.md) says of analog inputs:

> series resistance + clamp. The **ADS8588H's** 9 kV input clamp does most of
> this

**No value is given anywhere.** And it interacts with the converter: this is a
**500 kSPS simultaneous-sampling** part, so series resistance feeds the sampling
capacitor through an RC that must settle inside the acquisition window.

> **[DECIDE]** the series value against the ADS8588H's acquisition time and
> input impedance. Too small and the clamp carries more fault current than it
> needs to; too large and channels do not settle.

> **CLOSED on the four O2 channels**, and the reason generalises. The trade above
> only exists on an *unbuffered* input, where series resistance adds into the
> 1 MΩ divider. Behind the picoamp buffer that
> [`review-o2-chain.md`](review-o2-chain.md) §2 requires for other reasons,
> 10 kΩ × 1 pA is 10 nV — so the resistor is sized purely for fault current.
> **Still open on the remaining channels**, which stay unbuffered.

Also worth flagging: **the bench part is far less protected than the production
part.** ADS8588H has a 9 kV clamp; the AD7606 has **±16.5 V**. Bench work on a
live harness is being done with an order of magnitude less headroom than the
board is designed around.

---

## 5. Checked and clear

| | |
|---|---|
| **Eight channels, exactly allocated** | MAF differential on ch 0, TPS, O2 ×2 upstream, CHT, IAT, VBAT, VREF sense. No spare, none over |
| **MAF is one channel, not two** | It is a true differential pair — which is the entire reason for this converter family, and the reason the count works |
| **Four O2 sensors, correctly split** | Ford's diagrams confirm four: **#11 / #21 upstream** on 391 RD/YE, **#12 / #22 downstream** on 1138 VT/WH. Upstream pair on the precision ADC (fuelling), downstream pair on the internal ADC (catalyst monitoring, slow). The split matches what each is for |
| **Ratiometric cancellation** | Requires VREF and the sensor on the **same simultaneous-sampling converter**, which is why ch 7 is spent on VREF. Both candidate parts sample simultaneously |
| **Knock correctly excluded** | A piezo needing a charge amp and windowed sampling, not a routine channel |
| **TR sensor is *not* on VREF** | `vref-supply.md` carried a `[CONFIRM]` on this. The diagrams settle it: the DTR is a **switch array** with a 270 Ω resistor, returning on SIGRTN — four digital inputs, no VREF load. **Closes that item** |

---

## 6. A limitation worth recording rather than fixing

**The ratiometric correction cancels VREF variation. It does not cancel SIGRTN
offset.**

Sensor and VREF are both measured against the ADC's own ground, so a
SIGRTN-to-AGND offset lands in *both* the numerator and the denominator of the
ratio — added, not multiplied, so it does not divide out.

Fixing it properly means measuring each sensor differentially against SIGRTN, at
a channel each. Measuring the offset once on a spare channel would correct all
of them — **but there is no spare channel** (§5).

The magnitude argues for leaving it: ~25 mA of sensor return through harness
resistance is **single-digit millivolts**, well under the sensors' own tolerance.
But the diagrams also showed SIGRTN is **one heavily-spliced net** carrying every
sensor on the truck, so it is a shared-fate path — worth knowing about before
something else is hung on it.

---

## Summary

| # | Finding | Action |
|---|---|---|
| 1 | ~~Internal ADC demand ~22, never counted~~ | **FIXED** — 18 available (Ethernet takes 6), demand cut 23 → 15 |
| 2 | ~~Phantom channels; two docs disagree~~ | **FIXED** — struck, and the two docs given distinct jobs |
| 3 | ±10 V is forced by VREF sense, not chosen | record it as forced so it is not "optimised" later |
| 4 | Series resistance into the ADC unspecified | **[DECIDE]** against acquisition time |

Finding 1 is the one with a lesson in it. Each *individual* decision to move a
signal to the internal ADC was correct — `CS` at ±17 %, the feed dividers, the
drain sense. **What was missing was anyone adding them up**, and the phrase
"internal channels are plentiful" did the work of a budget three times over
without ever being one.
