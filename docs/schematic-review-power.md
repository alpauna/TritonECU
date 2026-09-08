# POWER sheet review — 2026-09-08

Review of [`Schematics/POWER_2026-09-08.png`](Schematics/POWER_2026-09-08.png),
rev V1.0, checked against the LTC4364-1/-2 datasheet design example (Rev B,
p.19). Two earlier revisions of this review are superseded; the datasheet
constants changed the analysis materially and the corrections are noted inline.

## Confirmed correct

- **Q1/Q2 back-to-back, common source**, HGATE→Q1, SOURCE→shared node,
  DGATE→Q2. Body diodes oppose. Matches the datasheet topology exactly.
- **R<sub>SNS</sub> = 8 mΩ.** Datasheet uses ΔV<sub>SNS(MIN)</sub> = 45 mV, so
  I<sub>LIM(MIN)</sub> = 45 mV / 8 mΩ = **5.6 A**. Sensible for a ~0.8 A load.
- **Clamp** = 1.25 V × (105k + 5.1k)/5.1k = **27.0 V**, matching the datasheet
  example's V<sub>OUT</sub> ≤ 27 V target and the ~30 V surge pass-through the
  SEPIC was sized against.
- **UV/OV divider — correct, and my earlier finding was wrong.** See §1.
- **C3–C7 at 35 V: keep as drawn.** The output is regulated to 27 V, so they
  run at 40 % of rating continuously and below rated voltage even during a
  clamp event.
- **Bulk damping is better than the 50 V part specified in
  [`power-supply.md`](power-supply.md)**, because 35 V parts carry more ESR:

  ```
  Z0 = √(5 µH / 1120 µF) = 66.8 mΩ
  Q  = 66.8 / ~40 mΩ     = 1.67
  Zpeak                  = 0.112 Ω     vs 0.208 Ω for a 50 V part
  ```

  16× below the −1.8 Ω worst case — **24 dB of Middlebrook margin**. Do not
  "improve" these to polymer.
- **INA238 reusing the LTC4364 shunt** — battery current and voltage from a
  resistor that had to be there. It also sits behind the clamp, so its 85 V
  common-mode limit is never approached.

## 1. RETRACTED — the UV/OV divider is right

An earlier revision of this review called the UV tap unusable. That was based
on a 500 mV threshold. **The LTC4364's UV and OV thresholds are 1.25 V**, and
the datasheet gives the divider equations directly:

```
UV:   VIN(MIN) / (R1+R2+R3)  =  1.25 V / (R2+R3)
OV:   VIN(MAX) / (R1+R2+R3)  =  1.25 V / R3
```

With R6/R8/R9 = 309k/162k/10k, total 481k:

| | Calculation | Result | Intended |
|---|---|---|---|
| OV | 1.25 × 481/10 | **60.1 V** | 60 V ✓ |
| UV | 1.25 × 481/172 | **3.50 V** | 3.5 V ✓ |

Both land on target. The 10 kΩ bottom resistor follows the datasheet's own
worked example. Nothing to change here.

## 2. But 3.5 V UV cannot be reached — R4 sets the real floor

The same datasheet page has the constraint that makes the 3.5 V setting
unachievable, and it is about R4, not the divider:

```
R4(MAX) = (VIN(MIN) − 4 V) / 750 µA        ← VCC minimum is 4 V, ICC(MAX) is 750 µA
```

The example picks R4 = 2.2k *for a 6 V minimum input*. Running that backwards
for the value on the schematic:

```
drop across R4 = 2.2 kΩ × 750 µA = 1.65 V
VCC reaches its 4 V minimum when  VIN = 5.65 V
```

**So the supply stops working at 5.65 V regardless of what UV is set to.** The
3.5 V UV threshold never gets to act — the controller browns out first. And no
value of R4 reaches 3.5 V, because V<sub>CC</sub> ≤ V<sub>IN</sub> and the
minimum is 4 V: **the architectural floor is 4 V at the battery terminal.**

### Fix

| | R4 = 2.2 kΩ | **R4 = 470 Ω** | R4 = 220 Ω |
|---|---|---|---|
| Drop at 750 µA | 1.65 V | **0.35 V** | 0.17 V |
| V<sub>IN(MIN)</sub> | 5.65 V | **4.35 V** | 4.17 V |

**R4 → 470 Ω, C2 → 470 nF**, then set UV to ~4.5 V. Raising C2 keeps the RC at
221 µs, preserving the datasheet's claim that "high voltage transients up to
250 V with a pulse width less than 20 µs are filtered out at the VCC pin"
(2.2k × 100 nF = 220 µs).

Check D3 still copes: at the datasheet's 200 V transient with a 64 V minimum
Zener, `(200 − 64)/470 = 289 mA × 64 V = 18.5 W`, against the CMZ5945B's 200 W
at 10/1000 µs. Comfortable. With a TVS present it never conducts at all.

### And this changes the system floor

[`power-supply.md`](power-supply.md) states cold-crank ride-through down to
**3.5 V input**, on the SEPIC's capability. That is true of the SEPIC and false
of the system: **the LTC4364 upstream cuts off first.** With Q1/Q2 off, both
body diodes are back-to-back, so nothing passes and the ECU loses power
entirely. The real floor is ~4.4 V with R4 = 470 Ω, or 5.65 V as drawn.

## 3. C8 = 56 nF — the board will fault on inrush

**Corrected.** My earlier estimate used 100 µA/1.2 V from memory. The datasheet
gives two different currents on the same capacitor:

```
overvoltage early warning:   5 µA  to 100 mV
overcurrent shutdown:       55 µA  to 1.35 V     tOC = CTMR × 1.35 V / 55 µA
```

With C8 = 56 nF:

| | |
|---|---|
| OV early warning (FLT#) | 1.12 ms |
| **Overcurrent shutdown t<sub>OC</sub>** | **1.37 ms** |

Now the inrush, which is the problem:

```
COUT = C3+C4+C5+C6+C7 = 1236 µF
t = C·V / ILIM = 1236 µF × 12 V / 5.6 A  =  2.6 ms      >  1.37 ms
```

**Charging the output capacitance takes twice the fault timeout, so the part
current-limits into a fault every key-on.** The datasheet's own example is
consistent with this: at 4 A and t<sub>OC</sub> = 1.15 ms it implicitly
supports only `4 A × 1.15 ms / 12 V` ≈ **380 µF** of output capacitance. The
schematic has 3× that.

### Sizing

```
CTMR ≥ t_inrush × 55 µA / 1.35 V = 2.6 ms × 40.7 nF/ms = 106 nF
```

**Use 220 nF** for 2× margin — t<sub>OC</sub> = 5.4 ms, early warning 4.4 ms,
OV shutdown 59 ms. Q1 then sees `5.6 A × ~6 V average × 2.6 ms` = 0.09 J during
inrush, which is nothing.

**[verify]** whether I<sub>TMR(UP)</sub> scales with V<sub>DS</sub> — the
datasheet quotes 55 µA specifically for "a severe output short where
V<sub>OUT</sub> = 0 V", which implies it is lower when the FET is dropping
less. If so the real inrush margin is better than this, but 220 nF costs
nothing and removes the question.

## 4. The TVS clamp is set by Q1's V<sub>DS</sub>, not by the IC

**Revised twice — here is the correct framing.** The clamping architecture
protects the LTC4364 by itself: during any overvoltage, SOURCE, SENSE and OUT
all sit at the regulated **27 V**, and VCC is held below 71 V by R4/D3 (the
datasheet states this explicitly for a 200 V input transient). So no LTC4364
pin is exposed, and my earlier claims about the 80 V rating and the INA238 were
both wrong.

**What does see the full transient is Q1's drain.** The TVS clamp must sit
below Q1's V<sub>DS</sub> rating with margin:

```
SMCJ60A clamping voltage at 15.5 A   =  96.8 V
```

**[verify] what YJQ40G10A is rated at.** If it is a 100 V part, 96.8 V is 3 %
margin, which is not margin. Either drop to an **SMCJ36A** (58.1 V clamp — the
60 V OV threshold still works, since OV trips at 60 V and the TVS only starts
conducting at 40 V breakdown, which is above the 27 V clamp point) or move Q1
to a 150 V+ device.

### Also: paralleling two TVS does not give 2× capability

Breakdown-voltage tolerance means the lower-V<sub>br</sub> device takes most of
the current and fails first. One **SMDJ36A** (3000 W, same DO-214AB footprint)
replaces D1+D2 with no sharing assumption.

### Consequence worth knowing

D1/D2 are **unidirectional**, so reverse battery forward-conducts them and
shorts the input. That is normal practice and it is what clears the fuse — but
it means the LTC4364's −40 V reverse blocking never gets to act, and protection
falls entirely on the series element opening. Which makes §5 worse.

## 5. The PPTCs — 150 V is confirmed, and it is the only thing that is right

**Voltage rating confirmed at 150 V**, which matters because they sit upstream
of the TVS and see the full transient. Everything else about them is wrong for
this position.

### The 3 s trip time is disqualifying, and it takes the TVS with it

A PPTC is a **thermal** device. It does not interrupt a fault; it warms up over
seconds until its polymer matrix expands. Against the two faults this element
exists to cover:

**Reverse battery.** D1/D2 are unidirectional, so they forward-conduct and the
harness dumps into them until something opens. Comparing what the TVS survives
against what a 3 s trip delivers:

```
SMDJ36A forward surge   ≈ 200 A for 8.3 ms  →  I²t ≈ 166 A²s
PPTC at 3 s, ~60 A harness-limited          →  I²t ≈ 10,800 A²s     65×
```

**The TVS is vaporised long before the PPTC notices.** Protection that destroys
the protector is not protection.

**Pass FET fails short.** The board sits directly across the battery for three
seconds. The LTC4364 shuts down its own path in 5.4 ms (§3); the backstop for
it failing takes 550× longer.

A **7.5 A automotive blade fuse** clears in roughly 10 ms at 100 A, with a
melting I²t around 20–40 A²s — comfortably below the TVS's 166 A²s, so the fuse
opens first. That is what protection coordination looks like.

### The current rating fails in ordinary use, not just at fault

2920L030 = **0.30 A hold** each; two in parallel gives 0.6 A at 20 °C. PPTC hold
current falls to roughly **52 % at 85 °C**, so ~0.31 A in a hot cabin:

| Condition | Input current | vs 0.31 A hold at 85 °C |
|---|---|---|
| Running, 13.8 V, real ~4.6 W load | **0.33 A** | **already tripping** |
| Cold crank, 6 V | **0.77 A** | 2.5× over |
| Design max, 3 A at 6 V | 3.5 A | 11× over |

It nuisance-trips on a hot day at idle, before any fault exists.

### And the series resistance lands where there is none to spare

A 0.30 A / 150 V device in a 2920 is a high-resistance part — 1–3 Ω each, so
0.5–1.5 Ω paralleled, and R<sub>1max</sub> after a trip is typically double
that. At the 0.77 A crank current that is **0.4–1.2 V**, on top of a floor now
known to be ~4.4 V (§2). It eats the cranking margin the SEPIC was chosen for.

**Paralleling PPTCs also does not behave like one bigger device.** As one begins
to trip its resistance rises steeply, pushing current into the other, which then
trips too.

### Where these parts *do* belong

Not wasted — moved. [`vref-supply.md`](vref-supply.md) calls for a resettable
fuse on the **VREF output**, and that is exactly the case a PPTC is built for:
a persistent harness short on a sensor line, a modest current, and auto-recovery
once the fault clears. Seconds of trip time is fine there because nothing
upstream is being destroyed while it heats.

### Replacement — and why not "just use the truck's fuse"

Reasonable question, since **OEM modules generally have no input fuse** — the
EEC-V does not, and neither do most Ford modules. They rely on the power
distribution box. Three things make this board different.

**First, work out what the fuse is actually for.** The LTC4364 already handles
every sustained overcurrent, and better than a fuse does: it limits at 5.6 A
and shuts its own path down in 5.4 ms. So the fuse covers exactly two cases,
both of which are *the protection itself having failed*:

- the pass FET failing short
- reverse battery, where D1/D2 forward-conduct and something must open

**Second, the vehicle fuse is sized for a circuit, not for this board.** A PDB
feed in the 15–20 A class has a melting I²t somewhere around 150–300 A²s,
against the SMDJ36A's ~166 A²s of forward surge. **Relying on it to clear
before the TVS dies is a coin flip.** A small fuse is not a coin flip.

```
3 A fast fuse    I²t ≈ 15–25 A²s     ← opens with 7–10× margin under the TVS
15–20 A PDB fuse I²t ≈ 150–300 A²s   ← at or above what the TVS survives
```

**Third, a big fuse cannot see a soft fault.** Something on the board drawing
4 A continuously is invisible to a 20 A fuse and cooks quietly. It is not
invisible to a 3 A one.

**[verify]** the actual PDB rating for the PCM feed on this truck before
choosing, since the point is to be well below it.

### Size it at 3 A, not 7.5 A

An earlier revision of this review said 7.5 A, reasoning that the fuse must
sit above the LTC4364's 5.6 A limit. That was wrong: the part **only holds
5.6 A for t<sub>OC</sub> = 5.4 ms** before shutting down, so the fuse never
sees sustained limit current.

```
sustained load, 13.8 V           0.33 A          →  11 % of a 3 A fuse
inrush, once per key-on          5.6 A × 2.6 ms  →  I²t = 0.08 A²s
3 A fast fuse melting I²t                        ≈  15–25 A²s      180× margin
```

**[verify]** whether the "-2" suffix latches off or auto-retries. On auto-retry
with an undersized C8 (§3), the board would retry indefinitely and the fuse
would see repeated inrush pulses rather than one. Fixing C8 removes the
question either way.

### Put it inline in the harness, not inside the box

An on-board fuse in a sealed ECU is un-serviceable — blowing it means opening
the enclosure, which is why OEMs do not fit them. An **inline holder in the
harness pigtail** keeps the fast, correctly-sized protection and stays
replaceable at the roadside. For the bench build, a board-mounted holder is
fine and convenient.

**Position is already correct on the schematic:** the fuse must be *upstream*
of the TVS so that TVS conduction clears it. F1/F2 are drawn ahead of D1/D2. ✓

## 6. Q1 SOA **[verify]**

Only Q1 (HGATE) runs in linear mode, and that sizes it. The datasheet's own
guidance: "The pass device, M1, should be chosen to withstand an output short
condition with V<sub>CC</sub> = 14 V."

```
output short at 14 V, 5.6 A limit, for tOC     =  78 W for 5.4 ms  =  0.42 J
clamping a 35 V load dump to 27 V at 0.8 A     =  6.4 W, sustained
```

Check YJQ40G10A's SOA curve at 5–10 ms, not its R<sub>DS(on)</sub> or
continuous rating. **DPAK or D2PAK for Q1** if an SO-8 does not cover it. Q2
only ever conducts fully on, so it can stay small.

## 7. INA238

- **ADCRANGE=0.** At 8 mΩ, ADCRANGE=1 (±40.96 mV) reads ±5.12 A and saturates
  *below* the 5.6 A current limit, so a fault would be unmeasurable.
  ADCRANGE=0 (±163.84 mV) gives ±20.5 A.
- Series resistors in IN+/IN− (10–100 Ω each, plus a differential cap) are
  worth adding for filtering. Refinement, not a protection fix.

## 8. PGND and GND

D1/D2 return to **PGND**, everything else to **GND**. Correct instinct — surge
current must not share a path with signal ground. Confirm the two are joined at
**exactly one point**, and that the TVS return is the shortest, widest path to
the input connector.

## Summary

| # | Change | Severity |
|---|---|---|
| 3 | **C8: 56 nF → 220 nF** — faults on inrush as drawn | **blocking** |
| 5 | F1/F2 → one **3 A** fast fuse, inline in the harness; PPTCs → VREF | **blocking** |
| 2 | **R4: 2.2k → 470 Ω, C2: 100 nF → 470 nF**, UV → ~4.5 V | high |
| 4 | Verify Q1 V<sub>DS</sub> vs the 96.8 V clamp; prefer one SMDJ36A | high |
| 6 | Verify Q1 SOA at 5–10 ms; consider DPAK | high |
| 7 | ADCRANGE=0 | low |
| 8 | Confirm single-point PGND/GND tie | low |
| 1 | UV/OV divider — **no change, it is correct** | none |
| — | C3–C7 at 35 V — **no change** | none |

Also update [`power-supply.md`](power-supply.md): the stated 3.5 V cold-crank
floor is the SEPIC's, not the system's. The LTC4364 cuts off first.
