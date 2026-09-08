# POWER sheet review — 2026-09-08

Review of [`Schematics/POWER_2026-09-08.png`](Schematics/POWER_2026-09-08.png),
rev V1.0. Findings ordered by severity. Numbers marked **[verify]** are read
off a rendered image or from memory of a datasheet and should be confirmed
before committing to fab.

## Confirmed good

- **Q1/Q2 back-to-back, common source** with HGATE→Q1, SOURCE→shared node,
  DGATE→Q2. Body diodes oppose, so reverse input is blocked. Matches the
  LTC4364 datasheet topology exactly.
- **Current limit** = 50 mV / 8 mΩ = **6.25 A**. Sensible for a ~0.8 A load.
- **Clamp** = 1.25 V × (105k + 5.1k)/5.1k = **27.0 V**. Matches the ~30 V surge
  pass-through the SEPIC was sized against.
- **Bulk capacitance** C3+C4 = 1120 µF, and the damping is *better* than the
  1000 µF/50 V part specified in [`power-supply.md`](power-supply.md), because
  35 V parts have more ESR:

  ```
  Z0 = √(5 µH / 1120 µF) = 66.8 mΩ
  Q  = 66.8 / ~40 mΩ     = 1.67
  Zpeak                  = 0.112 Ω     vs 0.208 Ω for the 50 V part
  ```

  Against −1.8 Ω worst case that is 16×, **24 dB of Middlebrook margin**. Do
  not "improve" these to polymer.
- **35 V rating is correct.** 14 V continuous is 40 % of rating; the 27 V clamp
  is below rated voltage, so it is not even a surge condition. Question closed.
- **INA238 reusing the LTC4364 shunt** is a good economy — battery voltage and
  current from one 8 mΩ resistor that had to be there.

## 1. SMCJ60A is the wrong TVS — this one is serious

| | |
|---|---|
| SMCJ60A standoff | 60 V |
| SMCJ60A **clamping voltage** | **96.8 V** at 15.5 A |
| LTC4364 absolute max (VCC, SOURCE, SENSE, OUT, HGATE, DGATE) | **80 V** |
| INA238 common-mode max (IN+, IN−, VBUS) | **85 V** |

**The TVS lets through 17 V more than the part it is protecting can survive.**
R4/D3 shields VCC alone; SOURCE, SENSE, OUT and both gate pins see the full
96.8 V, and so do all three INA238 high-side inputs.

A 60 V standoff is also far higher than a 12 V system needs. The requirement is
only to sit above a 24 V jump start (~28 V):

| Part | Standoff | Clamp | Verdict |
|---|---|---|---|
| SMCJ33A | 33 V | 53.3 V | good margin |
| **SMCJ36A** | 36 V | **58.1 V** | **recommended** |
| SMCJ40A | 40 V | 64.5 V | acceptable |
| SMCJ60A | 60 V | 96.8 V | **exceeds both ICs** |

### Also: paralleling two TVS does not give 2× capability

Breakdown voltage tolerance means the lower-V<sub>br</sub> device takes most of
the current and fails first. **One larger part beats two smaller ones** — an
**SMDJ36A** (3000 W, same DO-214AB footprint) replaces D1+D2 with a single
device and no sharing assumption.

Fixing this also removes the need for R4/D3 (see §4).

## 2. C8 = 56 nF — the fault timer looks orders of magnitude short **[verify]**

On the usual LTC4364 numbers (TMR charges at ~100 µA to ~1.2 V):

```
t_fault = 56 nF × 1.2 V / 100 µA  ≈  0.7 ms
```

Two things have to fit inside that window and neither does:

```
inrush, 1120 µF to 12 V at the 6.25 A limit = CV/I  =  2.15 ms
ISO 7637 load dump the clamp must ride out          =  400 ms
```

If those constants are right, the board **faults on every key-on** and cannot
ride a load dump — which is the entire reason the LTC4364 was chosen over a
crowbar. Sizing for 400 ms needs roughly `400 ms × 100 µA / 1.2 V` ≈ **33 µF**,
which is large but is what the part demands.

This is the trade the LTC4364 exists to make: a long timer means the pass FET
sits in linear mode for 400 ms, which is what sets its SOA (§6). Confirm the
TMR charge current and threshold against the datasheet before choosing.

## 3. The PTCs are undersized and add resistance where it hurts most

2920L030 = **0.30 A hold, 0.60 A trip** each. Two in parallel gives 0.6 A hold.

```
cold crank: 6 V in, ~4 W out, ~85 % eff  →  0.78 A input
```

**That is above the hold current before any derating**, and PPTC hold current
falls roughly 40 % at 85 °C, to ~0.36 A. It will nuisance-trip on the exact
event the whole supply exists to survive.

Worse, PPTCs of this class are 0.65–1.5 Ω each — 0.33–0.75 Ω paralleled — so
at 0.78 A they drop **0.25–0.6 V**. At a 6 V crank that is headroom the SEPIC
needs.

**Paralleling PPTCs also does not work the way it looks.** When one begins to
trip its resistance rises steeply, pushing current into the other, which then
trips too. The pair does not behave like a single 0.6 A device.

### What the series element is actually for

The LTC4364 already provides overcurrent protection at 6.25 A. Per
[`power-supply.md`](power-supply.md), the fuse exists for exactly one
mode — **the pass FET failing short** — which nothing downstream can
self-protect against. So it should be a **plain fast fuse above the LTC4364
limit**, around 7.5–10 A, with near-zero series resistance. Not a PPTC, and
certainly not two 0.3 A ones.

**[verify]** the `/150` suffix is a 150 V rating and not 15 V. These sit
upstream of the TVS and see the full transient; a 15 V part would arc.

## 4. R4 = 2.2 kΩ in series with VCC is marginal at crank

LTC4364 I<sub>CC</sub> is ~950 µA **[verify]**, so:

```
drop = 2.2 kΩ × 950 µA = 2.1 V      (more while charging gate capacitance)
at a 6 V crank:  6.0 − 2.1 = 3.9 V   ← below the ~4 V VCC minimum
```

The supply browns out its own controller at the bottom of the range.

With the TVS fixed per §1, VCC never exceeds 58 V against an 80 V rating, so
**R4/D3 can be deleted entirely** — keep C2 as the VCC bypass. If a series
element is still wanted for belt-and-braces, use **100 Ω**, which costs 95 mV.

## 5. Check the UV/OV divider taps **[verify]**

R6/R8/R9 = 309k/162k/10k, total 481k. On 500 mV thresholds:

| Tap | Ratio | Trips at |
|---|---|---|
| R8/R9 junction | 10/481 = 0.0208 | **24.0 V** |
| R6/R8 junction | 172/481 = 0.3576 | **1.40 V** |

24.0 V is a sensible OV. **1.40 V is not a usable UV** — it is below the
LTC4364's own VCC minimum, so UV would never assert and there is no defined
turn-off point. If maximum crank ride-through is the intent that is arguable,
but it should be deliberate. A UV around 5.5–6 V wants the tap at ~91 kΩ from
the bottom, not 10 kΩ.

Confirm which pin lands on which junction — if OV is on the 1.40 V tap instead,
the part is held off permanently.

## 6. Q1 SOA in an SO-8 **[verify]**

Only Q1 (HGATE) runs in linear mode, and that is the part that sizes it:

```
load dump, 60 V in clamped to 27 V, 0.8 A   →  26 W for 400 ms  =  10.5 J
in current limit, 33 V across 6.25 A        →  206 W
```

SO-8 SOA at 400 ms is thin for this. Check YJQ40G10A's SOA curve at 400 ms
directly — not its R<sub>DS(on)</sub> or continuous rating, which are
irrelevant here. **DPAK or D2PAK for Q1** if the curve does not cover it. Q2
(ideal diode) only ever conducts fully on, so it can stay small.

## 7. INA238 details

- **No series protection on IN+/IN−.** Standard practice is 10–100 Ω in each
  leg plus a differential cap, which also filters. Cheap insurance on a part
  sitting at battery potential.
- **ADCRANGE vs the current limit.** At 8 mΩ, ADCRANGE=1 (±40.96 mV) reads
  ±5.12 A and saturates *below* the LTC4364's 6.25 A trip, so a fault current
  would be unmeasurable. ADCRANGE=0 (±163.84 mV) gives ±20.5 A. Pick 0 unless
  the extra resolution is needed.

## 8. PGND and GND

D1/D2 return to **PGND**; everything else to **GND**. Correct instinct — surge
current must not share a path with signal ground. Confirm the two are joined at
**exactly one point**, and that the TVS return is the shortest, widest path to
the input connector.

## Summary of changes

| # | Change | Severity |
|---|---|---|
| 1 | D1/D2 → one **SMDJ36A** (58.1 V clamp, under both ICs' limits) | **blocking** |
| 2 | C8: recompute for 400 ms load dump + 2.15 ms inrush | **blocking** |
| 3 | F1/F2 → one ~7.5 A fast fuse, not 2 × 0.3 A PPTC | **blocking** |
| 4 | Delete R4/D3, or R4 → 100 Ω | high |
| 5 | Verify UV tap; 1.40 V is not a UV threshold | high |
| 6 | Verify Q1 SOA at 400 ms; consider DPAK | high |
| 7 | Series R + differential cap on INA238 inputs; ADCRANGE=0 | medium |
| 8 | Confirm single-point PGND/GND tie | medium |
| — | C3–C7 at 35 V: **keep as drawn** | none |
