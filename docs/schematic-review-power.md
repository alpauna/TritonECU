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

**Superseded — use 2.2 µF.** Sizing for inrush alone gives 220 nF, but once Q1
is an IRF540NS (§6) the timer can be set by the 400 ms load dump instead, which
is what the LTC4364 was chosen to ride out. 2.2 µF rather than 1.5 µF because
X7R tolerance has to be spent against that 400 ms. See §6.

**[verify]** whether I<sub>TMR(UP)</sub> scales with V<sub>DS</sub> — the
datasheet quotes 55 µA specifically for "a severe output short where
V<sub>OUT</sub> = 0 V", which implies it is lower when the FET is dropping
less. If so the real inrush margin is better than this, but 220 nF costs
nothing and removes the question.

## 4. TVS — the 60 V standoff is coordinated with the 60 V OV, and that was right

**Revised again.** Two earlier revisions treated the TVS level as free to lower.
It is not: **the TVS standoff and the OV threshold are one decision.**

### Why 36 V would be wrong

The LTC4364 is designed to *linearly clamp* everything between the 27 V
regulation point and the OV threshold — that is the entire reason it was chosen
over a crowbar. A TVS is a **transient** device; put it in sustained conduction
and it overheats and fails.

```
OV threshold  = 60 V     ← LTC4364 clamps 27–60 V, then shuts down
SMCJ60A       = 60 V standoff, 66.7 V breakdown
```

So the TVS sits *just above* where the controller stops clamping and starts
disconnecting. Nothing overlaps. **Dropping the TVS to 36 V while OV stays at
60 V puts it in the 36–60 V band the LTC4364 is meant to ride through** — a
stuck regulator at 40 V or a 24 V jump start at 28–29 V would cook it.

The clean statement: **TVS standoff must sit above the OV threshold.** If you
want a lower TVS, lower OV with it.

### DECIDED: SMCJ43A — which means the OV divider changes too

**These are one change, not two.** Moving the TVS to 43 V without moving OV
would put it in conduction across the 43–60 V band the LTC4364 is designed to
clamp through.

| | OV | TVS | Clamp | Q1 must block | FET drop while clamping |
|---|---|---|---|---|---|
| As drawn | 60 V | SMCJ60A | 96.8 V | ≥150 V | 33 V → 26 W |
| **Decided** | **43 V** | **SMDJ43A** | **69.4 V** | **100 V ✓ confirmed** | **16 V → 2.7 W real / 10.7 W max** |

New divider, same 10 kΩ rule:

```
R9 = 10 kΩ        R8 = 86.6 kΩ        R6 = 249 kΩ        total 345.6 kΩ

OV = 1.25 × 345.6 / 10   = 43.2 V
UV = 1.25 × 345.6 / 96.6 =  4.47 V
```

### Why this is the better pairing

- **FET clamping dissipation halves** — 16 V across Q1 instead of 33 V, so 13 W
  rather than 26 W while riding out an overvoltage. That is the number that
  sizes Q1's SOA (§6).
- **69.4 V fits inside a 100 V FET**, which 96.8 V did not.
- **43 V still clears a suppressed load dump.** A modern alternator's internal
  suppression caps pulse 5b at ~35 V, so the LTC4364 clamps through it and the
  engine keeps running. Above 43 V it disconnects instead, which is the right
  answer for a fault that large.
- **Coordination holds at the top.** Highest *sustained* input worth planning
  for is a 24 V jump start at ~29 V, comfortably below the 43 V standoff, so
  the TVS never conducts continuously. It only sees transients above its 47.8 V
  minimum breakdown, by which point OV has already disconnected the load.

### Use SMDJ43A, not SMCJ43A

Same DO-214AB footprint, same 69.4 V clamp, **3000 W instead of 1500 W**. That
matters specifically because of the fuse decision (§5): with no board fuse, the
reverse-battery case now depends on the TVS surviving forward conduction until
the truck's PDB fuse clears, and forward surge capability is exactly what the
bigger die buys. One SMDJ43A also replaces D1+D2 without the sharing assumption
that paralleling two parts requires.

The positive-going transients are undemanding by comparison — ISO 7637 pulse 2a
(50 V, 2 Ω) and pulse 3b (100 V, 50 Ω) both deliver about 1 A into a 48 V
breakdown. Reverse battery is the case that sizes this part.

### Knock-on: D3 becomes optional

With the clamp at 69.4 V against V<sub>CC</sub>'s 80 V maximum, the Zener no
longer has anything to do — the datasheet's R4/D3 network existed to survive a
200 V transient with no TVS in front of it. Keep it as cheap insurance if you
like, but **R4 can then drop to 220 Ω** (VCC floor 4.17 V, giving the 4.47 V UV
threshold 300 mV of margin instead of 120 mV), and D3 still only passes 24 mA
at the TVS clamp. Raise C2 to 470 nF either way to hold the VCC filter RC.

**Confirmed:** YJQ40G10A is 100 V, so the 69.4 V clamp has 31 % margin — see §6, which is also where that part turns out to be wrong for Q1.

## 4a. Bidirectional TVS — right instinct, but it moves the problem

Bidirectional (the **CA** suffix — SMCJ60CA) blocks in both directions instead
of forward-conducting. Under reverse battery it does not conduct at all, so the
**LTC4364's back-to-back FETs do exactly what they are specified for** and
nothing blows. That is genuinely better than destroying a TVS and a fuse.

**The catch is negative transients.** ISO 7637-2 pulse 1 is −100 V:

| | Negative clamp | LTC4364 SOURCE rating |
|---|---|---|
| Unidirectional | **−1 V** (forward conduction) | −40 V |
| Bidirectional 60CA | **−96.8 V** | −40 V |
| Bidirectional 43CA | −69.4 V | −40 V |

Per the datasheet, a negative input pulls SOURCE below ground through M2's body
diode, and the LTC4364 responds by shorting HGATE to SOURCE to turn M1 off —
designed behaviour, but only down to **−40 V**. **No bidirectional TVS with
enough standoff for automotive positive transients clamps negative inside
that.** A unidirectional part clamps at −1 V and the question never arises.

### Recommendation: stay unidirectional

The trade is symmetric on paper — reverse battery versus negative transients —
but two things break the tie:

1. **The 3 A fuse (§5) already solves reverse battery.** At 15–25 A²s it opens
   well before the TVS's ~166 A²s. When the PPTCs were taking 3 s this was a
   real hazard; with a fast fuse it costs a 50-cent part and tells the installer
   plainly what they did wrong.
2. **Negative transients are a normal electrical event**, not an installation
   error. Trading routine protection for one-off protection is the wrong way
   round.

Bidirectional would be the right call if the fuse were staying slow — which is
another way of saying §5 and this section are the same decision.

### Also: paralleling two TVS does not give 2× capability

Breakdown-voltage tolerance means the lower-V<sub>br</sub> device takes most of
the current and fails first. One **SMDJ** (3000 W, same DO-214AB footprint)
replaces D1+D2 with no sharing assumption.

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

The *position* is right — [`vref-supply.md`](vref-supply.md) calls for a
resettable backstop on the **VREF output**, and a persistent sensor-harness
short with auto-recovery is exactly what a PPTC is built for. Seconds of trip
time harm nothing there, because nothing upstream is being destroyed while it
heats.

**But not these parts.** A 120–150 V element trips in 8–16 s and carries 1–3 Ω,
and VREF is a 5 V rail that has no use for the voltage rating. Use a 16 V part
at ~100–150 mA hold, and take the regulator's feedback from the far side of it
so the resistance stays inside the loop — see
[`vref-supply.md`](vref-supply.md#choosing-the-ptc--not-the-150-v-parts).

### DECIDED: no fuse on the board — the truck's PDB fusing is the branch protection

**This is the OEM answer and it is defensible.** The EEC-V has no input fuse and
neither do most Ford modules; PCM power already runs through the power
distribution box. Adding a second series element only adds resistance at low
line, an un-serviceable part inside a sealed box, and one more thing to fail.

What the decision actually rests on: **the LTC4364 is the protection.** It
limits at 5.6 A and shuts its own path down in 5.4 ms — faster and more
precisely than any fuse. The series element was only ever the backstop for the
LTC4364 itself failing, and the PDB fuse fills that role.

### The consequence: the TVS becomes a sacrificial part, and that is acceptable

Under reverse battery, D1/D2 forward-conduct and the PDB fuse is now the only
thing that opens:

```
harness-limited current       ~60–120 A
20 A PDB fuse at ~100 A       ~10–50 ms   →  I²t ≈ 200 A²s
SMDJ36A forward surge                        I²t ≈ 166 A²s
```

Marginal — the TVS probably does not survive. **But its failure mode is
benign:** a TVS fails *short*, which pulls the fault current up and blows the
PDB fuse faster, protecting everything downstream. The sequence is reverse
battery → TVS conducts → TVS fails short → fuse clears → board survives. Two
cheap parts consumed, nothing else damaged.

Treat D1/D2 as **serviceable items to inspect after any reverse-polarity
event**, and keep the footprint accessible.

### This does not reopen the bidirectional question

§4a recommended unidirectional partly because a fast 3 A fuse solved reverse
battery. Without that fuse the argument is weaker, but the conclusion holds:

- Negative transients (ISO 7637 pulse 1) are a **routine electrical event**;
  reverse battery is a **one-time installation error**.
- A bidirectional part would put the LTC4364's SOURCE pin past its −40 V rating
  on every pulse-1 event, to save a $0.50 TVS on an event that should never
  happen twice.

Stay unidirectional.

### [verify] "the truck already has reverse diodes in the fuse box"

Worth confirming against the wiring diagrams already in
[`1999-Ford-F150-4wd-5.42v/`](1999-Ford-F150-4wd-5.42v/), because the two
possibilities behave completely differently:

- **Relay coil suppression diodes** — common in Ford PDB/CJB assemblies, fitted
  across relay coils to catch flyback. These give **no reverse-battery
  protection at all**, and under reverse polarity they forward-conduct and
  become a load themselves.
- **A system reverse-blocking diode** — would have to carry full vehicle
  current, so it would be a large stud-mounted device. Unusual, and its absence
  is why so many vehicles are damaged by reversed jump starts.

If it is the first, nothing above changes. If it is genuinely the second, the
reverse-battery case disappears entirely and the TVS is never at risk — which
would be worth knowing, so it is worth ten minutes with the schematic.

### Schurter 3-101-231 (T9-817, 8 A) — take it for the bench, not the truck

Checked against the [T9-817
datasheet](https://www.schurter.com/en/datasheet/typ_T9-817.pdf). One line
settles it before any trip-curve argument:

| | |
|---|---|
| **Allowable operating temperature** | **−5 °C to +60 °C** (4 A version: −5 to +50 °C) |

**That is disqualifying for a vehicle on its own.** A truck sees −20 °C or
colder in winter and a closed cabin exceeds 60 °C in summer sun — the part is
outside its rating at both ends of an ordinary year. Schurter says as much
directly: automotive requirements to IATF 16949 "can be offered exclusively
with customer-specific, individual agreements", so the catalogue part is not
automotive-qualified.

Three supporting points, none of which are needed once temperature has decided
it:

- **UL 1077 makes it a *supplementary protector***, explicitly not branch
  circuit protection. It is designed to sit behind existing upstream
  protection — which is the role we wanted, but it also means it is not the
  primary interrupter.
- **Minimum trip time is ~0.1 s even at 10× rated**, from the datasheet curve
  (x-axis 1–10× I<sub>n</sub>, y-axis bottoming at 0.1 s). At the ~60 A
  reverse-battery current that is 0.2–0.5 s → roughly **1080 A²s against the
  SMDJ36A's ~166 A²s.** The TVS is still destroyed before it opens, exactly as
  with the PPTCs.
- **12.5 g on THT leads**, wave-solder only, with a moving mechanism. That is a
  vibration-fatigue item in a vehicle.

### What it is genuinely good at

For the **bench supply**, this is the right part and worth buying:

- **Push-to-reset** — during power-supply bring-up you will short things
  repeatedly, and pushing a button beats hunting for fuses.
- **2 kA interrupting capacity at 48 VDC** — genuinely strong, far beyond a
  glass fuse.
- **2500 switching cycles at 150 % I<sub>r</sub>** — it will outlast the
  project.
- Ambient derating is mild compared with a PPTC: the correction factor is 1.21
  at +60 °C (≈17 % less trip current) against roughly 48 % for a polyfuse.

**Take the 4 A version, not 8 A.** The board draws 0.33 A running — 8 % of a
4 A part — and the once-per-key-on inrush of 5.6 A for 2.6 ms is far too brief
to trip anything (1.4× rated needs on the order of a second). A 4 A breaker
catches a bench mistake meaningfully sooner than an 8 A one, and the LTC4364
covers everything below it anyway.

### Put it inline in the harness, not inside the box

An on-board fuse in a sealed ECU is un-serviceable — blowing it means opening
the enclosure, which is why OEMs do not fit them. An **inline holder in the
harness pigtail** keeps the fast, correctly-sized protection and stays
replaceable at the roadside. For the bench build, a board-mounted holder is
fine and convenient.

**Position is already correct on the schematic:** the fuse must be *upstream*
of the TVS so that TVS conduction clears it. F1/F2 are drawn ahead of D1/D2. ✓

## 6. Q1 — YJQ40G10A is right for Q2 and wrong for Q1

Datasheet: [`Schematics/YJQ40G10A-Datasheet.pdf`](Schematics/YJQ40G10A-Datasheet.pdf).

### The good news: 100 V, which validates the 43 V decision

```
BVDSS = 100 V

SMCJ60A clamp  96.8 V  →   3 % margin      not margin
SMDJ43A clamp  69.4 V  →  31 % margin      ✓
```

The TVS change in §4 was not a refinement — it was necessary for this FET.

### The problem: it is a switching FET in a 3.3 × 3.3 mm package

| | |
|---|---|
| Technology | **split-gate trench** — optimised for switching |
| Package | **DFN 3.3 × 3.3 mm** |
| R<sub>θJA</sub> | 25 typ / **30 max °C/W** even for t ≤ 10 s |
| R<sub>θJC</sub> | 1.8 / 2.3 °C/W |
| V<sub>GS(th)</sub> | **1.0 – 2.5 V** (wide spread) |
| **SOA curve** | **not published** |

Three independent problems, any one of which is disqualifying for a **linear**
pass element:

1. **No SOA curve.** Q1 spends its working life in linear mode — during
   clamping and during current limit. A part with no published safe operating
   area cannot be verified for the only job it has here. That is the finding;
   the rest is why it would fail anyway.

2. **Split-gate trench is the wrong device class.** These are built for low
   R<sub>DS(on)</sub> and low Q<sub>gd</sub> (C<sub>rss</sub> = 18 pF, which is
   excellent for switching). In linear mode they suffer thermal instability —
   current concentrates in the lowest-V<sub>th</sub> cells, which heat, which
   lowers their V<sub>th</sub> further. The **1.0–2.5 V threshold spread**
   makes that sharing worse. Linear-mode SOA for parts like this sits well
   below the thermal limit, which is exactly why hot-swap designs use planar or
   explicitly linear-rated FETs.

3. **The package is too small.** 30 °C/W for pulses up to 10 s leaves almost no
   thermal headroom.

### The case that sizes it is the output short, not the clamp

The datasheet's own guidance: *"The pass device, M1, should be chosen to
withstand an output short condition with V<sub>CC</sub> = 14 V."*

```
short:  14 V × 5.6 A = 78 W  for tOC = 5.4 ms (with C8 = 220 nF)  =  0.42 J

Tj rise < 100 °C needs  Zθ(5.4 ms) < 1.28 °C/W
    D2PAK   ≈ 0.5–1 °C/W    ✓
    DPAK    ≈ 1–2 °C/W      marginal
    DFN3.3  ≈ 1.5–3 °C/W    ✗
```

**Correction to §4:** an earlier revision put the clamping dissipation at 13 W
using 0.8 A. That was the *12 V input* current. While clamping, the LTC4364
holds the output at 27 V, so Q1 carries the load current **at 27 V**:

| | Current through Q1 | Q1 dissipation at 43 V in |
|---|---|---|
| Real ~4.6 W load | 0.17 A | **2.7 W** |
| 18 W design rating | 0.67 A | 10.7 W |

At the real load, clamping is easy — 400 ms at 2.7 W is a ~20–40 °C rise on any
sensible package. At the 3 A design rating it is marginal. This is more support
for [`power-supply.md`](power-supply.md)'s own conclusion that 2 A gives 3×
margin on the real load and 3 A is headroom for loads not yet stated.

### Keep it for Q2

Q2 is the ideal-diode FET. It is either fully enhanced or fully off — **never
linear** — so none of the above applies, and 15 mΩ at 40 A in a 3.3 mm package
is genuinely good there. Buy two part numbers, not one.

### DECIDED: Q1 → IRF540NS (D2Pak)

Datasheet: [`Schematics/IRF540-Datasheet.pdf`](Schematics/IRF540-Datasheet.pdf).
It clears every criterion, and the first one is the one that mattered:

| Criterion | IRF540NS |
|---|---|
| **Published SOA curve** | **Fig 8, with 100 µs / 1 ms / 10 ms single-pulse lines** ✓ |
| Technology | **planar HEXFET** — not trench; well-behaved in linear mode ✓ |
| V<sub>DSS</sub> | **100 V** vs the 69.4 V clamp — 31 % margin ✓ |
| Package | **D2Pak** ✓ (TO-262 through-hole available as IRF540NL) |
| R<sub>θJC</sub> | 1.15 °C/W max |
| R<sub>θJA</sub> | 40 °C/W, PCB mount |
| T<sub>J</sub> | **175 °C** — 25 °C more headroom than the trench part |
| R<sub>DS(on)</sub> | 44 mΩ — irrelevant here: 28 mW at 0.8 A |

Against the sizing case:

```
output short:  14 V × 4.1 A = 57 W        far inside the 10 ms SOA line
               Zθ(10 ms) ≈ 0.12 °C/W  →   ΔTj ≈ 7 °C
```

The 10 ms SOA line at 14 V sits in the tens of amps. We need 4.1 A.

### And that headroom buys real load-dump ride-through

With Q1 no longer the constraint, C8 can be sized for what the system actually
wants rather than for the FET's survival. The binding requirement becomes the
**400 ms ISO 7637 load dump** — the event the LTC4364 was chosen to ride out:

| C8 | OC shutdown (55 µA) | OV shutdown (5 µA) | OV early warning (100 mV) |
|---|---|---|---|
| 56 nF (drawn) | 1.4 ms | 15 ms | 1.1 ms |
| 300 nF | 7.4 ms | 81 ms | 6 ms |
| **1.5 µF** | **36.8 ms** | **405 ms** ✓ | **30 ms** |

**C8 = 1.5 µF.** Check each consequence against the IRF540NS:

```
inrush 3.6 ms         vs  36.8 ms timer                      10× margin ✓
short  57 W × 36.8 ms = 2.1 J,  Zθ(37 ms) ≈ 0.3 °C/W  →  ΔTj ≈ 17 °C ✓
clamp  16 V × 0.44 A = 7.0 W for 405 ms, Zθ ≈ 3 °C/W  →  ΔTj ≈ 21 °C ✓
```

All three trivial. **This is what the right FET buys** — not a smaller
component, but the freedom to set the fault timer by the vehicle's requirements
instead of the silicon's.

The 30 ms of **early warning on FLT#** is a bonus worth wiring to a GPIO: it is
enough notice to shed injectors and coils before the rail disconnects.

### Sizing C8 properly: 2.2 µF, and it must be ceramic

At 56 nF the tolerance of the capacitor was irrelevant. At 1.5 µF it sets
whether the board survives a load dump, so it has to be sized from worst case,
not nominal.

**X7R stacks two errors against the 400 ms target:**

```
capacitance tolerance    ±10 %
X7R temperature coeff.   ±15 %  over −55 to +125 °C
                         ------
worst case               ≈ −23 %

1.5 µF  →  405 ms nominal  →  312 ms worst case      short of 400 ms ✗
2.2 µF  →  594 ms nominal  →  457 ms worst case      ✓
```

**Use 2.2 µF.** The knock-ons stay comfortable on the IRF540NS:

```
OC shutdown  = 2.2 µF × 1.35 V / 55 µA = 54 ms      15× the 3.6 ms inrush ✓
short        = 57 W × 54 ms = 3.1 J,  ΔTj ≈ 20 °C   ✓
clamp        = 7.0 W × 594 ms,        ΔTj ≈ 28 °C   ✓
early warning= 2.2 µF × 0.1 V / 5 µA  = 44 ms       ✓
```

**[verify]** the min/max on I<sub>TMR</sub> — the datasheet quotes 5 µA and
55 µA as typicals. If the spread is ±20 %, that compounds with the −23 % above
and 3.3 µF may be needed to hold 400 ms at every corner.

### It must be X7R or C0G — never tantalum or electrolytic

The TMR pin charges at **5 µA**. Any leakage current is a direct timing error at
that scale:

- **X7R / C0G ceramic**: insulation resistance > 10 GΩ, so leakage at 1.35 V is
  sub-nanoamp. Invisible.
- **Tantalum or aluminium**: leakage is specified in **microamps** — the same
  order as the charging current. The timer would run long, short, or not
  complete at all, and it would drift with temperature.

Specify **16 V or 25 V rating in 0805**. TMR only reaches 1.35 V so DC bias
derating is small at those ratings, but a 6.3 V part in 0402 can lose 20–30 %
of its capacitance at bias — which lands straight in the timing.

### Auto-retry confirmed — and the duty cycle cannot be tuned away

The "-2" auto-retries. Into a persistent short that gives:

```
fault on                                      54 ms
cooldown, TMR discharge at ~2.5 µA  [verify]  1.19 s
duty                                          4.3 %
average dissipation in Q1   57.4 W × 0.043  ≈  2.5 W
```

**The duty cycle is fixed by the ratio of the two TMR currents, not by C8:**

```
duty = tOC / (tOC + tcool) = (1/55) / ((1/55) + (1/2.5)) = 4.3 %
```

Both times scale with C8 identically, so it cancels. **2.5 W of average
dissipation is a property of the part, and the only levers are Q1's thermal
path or stopping the retries.**

### The primary fix is copper, not firmware

A D2Pak at the datasheet's 40 °C/W "PCB mount" figure gives
`85 + 2.5 × 40 = 185 °C` — past the 175 °C limit. The requirement is:

```
RθJA ≤ (175 − 85) / 2.5  =  36 °C/W
```

A D2Pak on roughly **1 in² of 2 oz copper reaches 25–30 °C/W**, giving
Tj ≈ 147 °C. Size the pour for this deliberately — it is the one number that
makes auto-retry safe unconditionally.

**Why firmware cannot be the primary fix:** the fault that motivates this is a
short on the LTC4364's output, which discharges C_out through the fault. The
MCU loses its rail immediately and is not running to count anything. Retry
limiting only helps where the MCU survives.

### Firmware retry limiting — worth having, for the cases where it runs

A configurable max-retry count latching SHDN# is right for the faults that do
*not* kill the rail: a partial overload rather than a dead short, an
intermittent harness fault, a downstream branch drawing too much. It also
converts an invisible slow cook into a logged, reportable event.

**Distinguishing the two FLT# causes** is the design detail, because FLT#
asserts for both the OV early warning and an overcurrent fault, and they want
opposite responses:

| FLT# with… | Means | Response |
|---|---|---|
| INA238 bus voltage **high** | OV early warning, 44 ms to go | shed injectors and coils, flush |
| INA238 bus voltage normal, current at limit | overcurrent fault | count it; latch SHDN# after N |

That is a second payoff from reusing the LTC4364's shunt for the INA238 — the
same part that measures battery current also disambiguates the fault pin.

**The OV early warning is the case that earns FLT# its GPIO**, because there the
MCU is definitely alive and 44 ms is real notice.

### Sizing C8 properly: 2.2 µF, and it must be ceramic

At 56 nF the tolerance of the capacitor was irrelevant. At 1.5 µF it sets
whether the board survives a load dump, so it has to be sized from worst case,
not nominal.

**X7R stacks two errors against the 400 ms target:**

```
capacitance tolerance    ±10 %
X7R temperature coeff.   ±15 %  over −55 to +125 °C
                         ------
worst case               ≈ −23 %

1.5 µF  →  405 ms nominal  →  312 ms worst case      short of 400 ms ✗
2.2 µF  →  594 ms nominal  →  457 ms worst case      ✓
```

**Use 2.2 µF.** The knock-ons stay comfortable on the IRF540NS:

```
OC shutdown  = 2.2 µF × 1.35 V / 55 µA = 54 ms      15× the 3.6 ms inrush ✓
short        = 57 W × 54 ms = 3.1 J,  ΔTj ≈ 20 °C   ✓
clamp        = 7.0 W × 594 ms,        ΔTj ≈ 28 °C   ✓
early warning= 2.2 µF × 0.1 V / 5 µA  = 44 ms       ✓
```

**[verify]** the min/max on I<sub>TMR</sub> — the datasheet quotes 5 µA and
55 µA as typicals. If the spread is ±20 %, that compounds with the −23 % above
and 3.3 µF may be needed to hold 400 ms at every corner.

### It must be X7R or C0G — never tantalum or electrolytic

The TMR pin charges at **5 µA**. Any leakage current is a direct timing error at
that scale:

- **X7R / C0G ceramic**: insulation resistance > 10 GΩ, so leakage at 1.35 V is
  sub-nanoamp. Invisible.
- **Tantalum or aluminium**: leakage is specified in **microamps** — the same
  order as the charging current. The timer would run long, short, or not
  complete at all, and it would drift with temperature.

Specify **16 V or 25 V rating in 0805**. TMR only reaches 1.35 V so DC bias
derating is small at those ratings, but a 6.3 V part in 0402 can lose 20–30 %
of its capacitance at bias — which lands straight in the timing.

### [verify] Is the "-2" latch-off or auto-retry?

This now matters more than it did. Auto-retry into a persistent short repeats
the fault at a duty cycle set by the TMR discharge current:

```
fault on           54 ms
cooldown at ~2.5 µA discharge from 1.35 V, 2.2 µF   ≈ 1.19 s
duty                                                  4.3 %
average dissipation in Q1   57 W × 0.043            ≈ 2.5 W
```

A D2Pak at 40 °C/W sustains about **2.2 W at 85 °C ambient**. So on auto-retry
the average is right at the package limit, and Q1 would slowly heat while the
short persists. On latch-off there is no issue at all.

If it is auto-retry, the fixes are a larger copper pour under Q1, the TO-262
version bolted to the enclosure, or having firmware latch the supply off via
SHDN# after a few FLT# events — the last being free, and the right behaviour
anyway for a fault that is not going to clear itself.

### Two things this changes elsewhere

1. **Gate slew control is no longer needed.** §"the bigger lever" proposed a
   HGATE capacitor to keep inrush out of current limit. With a 36.8 ms timer
   against 3.6 ms of inrush there is nothing to solve, and inrush energy is
   ½CV² = 0.089 J either way — nothing for a D2Pak. Skip it; fewer parts.
2. **Steady-state clamping is still bounded by the timer, not the package.**
   At 40 °C/W a D2Pak sustains ~2.2 W at 85 °C ambient, below the 7.0 W of
   clamping — but the TMR disconnects at 405 ms, so Q1 never sees it
   continuously. If sustained clamping is ever wanted, that is what the TO-262
   version bolted to the enclosure is for.

### Gate drive checked — and the maximum is the constraint, not the minimum

DGATE drive (V<sub>DGATE</sub> − V<sub>SOURCE</sub>), no fault:

| V<sub>CC</sub> | Min | Typ | Max |
|---|---|---|---|
| 4 V | **5 V** | 8.5 V | 12 V |
| 8 – 80 V | 10 V | 12 V | **16 V** |

**The 16 V maximum is the part that matters, and it rules out most logic-level
FETs.** Logic-level devices are typically rated ±12 V or ±16 V V<sub>GS</sub> —
against a 16 V drive that is zero margin, and a gate-oxide failure is a
dead short from gate to source. **IRF540N is ±20 V**, leaving 4 V. That was luck
rather than judgement in the selection above, but it is the right answer, and it
is worth stating as a criterion: **V<sub>GS(max)</sub> ≥ 20 V.**

### The minimum is fine, because the current is small

At the input floor, drive is **5 V min** against V<sub>GS(th)</sub> up to 4.0 V —
1 V of worst-case overdrive, which looks alarming until it is compared with what
the FET actually has to pass:

```
gfs = 21 S min
overdrive needed to carry 0.8 A in saturation  =  0.8 / 21  =  38 mV

available worst case  1 V   →  26× more than required
```

The device is deep in the ohmic region even at 1 V of overdrive. Scaling
R<sub>DS(on)</sub> from 44 mΩ at ~7 V of overdrive gives roughly **310 mΩ** at
1 V, so:

```
drop per FET at 0.8 A     0.25 V
Q1 + Q2 in series         0.50 V        dissipation 0.2 W each — trivial
```

That is a triple-stacked worst case: maximum V<sub>th</sub>, minimum drive, and
minimum input all at once. What the board will actually measure:

| Condition | Drive (typ) | Overdrive on a 3 V V<sub>th</sub> | R<sub>DS(on)</sub> | Drop, Q1+Q2 at 0.8 A |
|---|---|---|---|---|
| At the floor, V<sub>CC</sub> = 4 V | **8.5 V** | 5.5 V | ~56 mΩ | **90 mV** |
| Running, V<sub>CC</sub> ≥ 8 V | **12 V** | 9 V | 44 mΩ | **70 mV** |
| Stacked worst case | 5 V | 1 V | ~310 mΩ | 500 mV |

So in practice the pass pair costs under 100 mV across the whole input range,
and the 0.5 V figure is a margin calculation rather than a prediction. The
minimums are what the design has to survive; the typicals are what it will
show on the bench.

### So quote the input floor honestly

```
LTC4364 VCC minimum                4.0 V
+ R4 (220 Ω) at 750 µA             0.17 V
                                   ------
supply cuts off at                 4.17 V at the battery terminal

at 4.4 V in, worst-case FET drop   0.50 V
SEPIC therefore sees               3.90 V     against its 3.5 V minimum ✓
```

It works, with about 0.4 V of margin at the very bottom in a stacked worst case.
[`power-supply.md`](power-supply.md) should quote **~4.4 V at the battery
terminal**, not the SEPIC's 3.5 V.

### The absolute maximum contradicts the drive spec — and that is the useful part

```
Absolute Maximum:   DGATE, HGATE .... SOURCE − 0.3 V to SOURCE + 10 V   (Note 3)
Electrical Char.:   DGATE − SOURCE ... 10 V min / 12 V typ / 16 V max
```

**The typical drive exceeds the absolute maximum**, which is not an error.
Note 3 resolves it:

> *Internal clamps limit the HGATE and DGATE pins to minimum of 10 V above the
> SOURCE pin. Driving these pins to voltages beyond the clamp may damage the
> device.*

So the "SOURCE + 10 V" figure is the **guaranteed minimum clamp level**, not a
ceiling on the part's own output. The charge pump runs up to the clamp — 12 V
typical, 16 V maximum — and the rating is a restriction on what *we* may apply
from outside.

Two consequences, and the second is the one that changes the schematic:

**1. The FET rating is set by 16 V, not 10 V.** The clamp is a *minimum* of
10 V and the pump drives to it, so the gate can reach the 16 V electrical
maximum. **V<sub>GS(max)</sub> ≥ 20 V** remains the criterion — IRF540N ✓.

**2. Nothing external may force these pins.** The 10 V limit is a real
constraint on anything *we* connect:

- **No gate-source Zener.** Standard practice on a discrete gate driver, wrong
  here — a 12 V clamp fights the charge pump, and a 10 V one prevents full
  enhancement at exactly the moment R<sub>DS(on)</sub> matters.
- **No pull-up or pull-down to a rail.**
- **A slew capacitor, if one were ever fitted, goes HGATE-to-SOURCE, never
  HGATE-to-GND.** SOURCE moves with the input. A ground-referenced capacitor
  would hold the gate up while SOURCE fell, sourcing current *into* the internal
  clamp — which is exactly what "driving these pins beyond the clamp may damage
  the device" describes. Referenced to SOURCE it simply rides along and drives
  nothing.

That last point is a third reason the HGATE slew capacitor proposed earlier
stays dropped — it was already unnecessary once C8 grew, and it would have to be
referenced carefully if it ever came back.

**HGATE and DGATE share this rating**, so the Q1 side is covered by the same
answer as Q2: the charge pump fully enhances an IRF540N (V<sub>GS(th)</sub>
2.0–4.0 V) at every input above the 4.2 V cutoff.

### Setting the current limit — 4 A is right, but not for the reason it looks like

**The short-circuit energy is invariant.** t<sub>OC</sub> has to exceed the
inrush time or the board faults at every key-on (§3), and inrush time is
`C·V/I_LIM`. So:

```
E_short = 14 V × ILIM × tOC     and    tOC ∝ 1/ILIM

        →  E_short = constant = 0.42 J     at any current limit
```

Lowering the limit does not remove energy from Q1. It trades **power for
time**.

That still helps, because peak junction rise is `P × Zθ(t)` and Zθ goes roughly
as √t in the single-pulse regime — so **ΔT<sub>j</sub> ∝ √I<sub>LIM</sub>**:

| R<sub>SNS</sub> | I<sub>LIM(MIN)</sub> | Short power | Inrush | t<sub>OC</sub> | C8 | Relative ΔT<sub>j</sub> |
|---|---|---|---|---|---|---|
| 8 mΩ (drawn) | 5.6 A | 78 W | 2.6 ms | 5.4 ms | — | 1.00 |
| **11 mΩ** | **4.1 A** | 57 W | 3.6 ms | 36.8 ms | **1.5 µF** | **0.85** |
| 15 mΩ | 3.0 A | 42 W | 4.9 ms | 9.8 ms | 400 nF | 0.73 |
| 25 mΩ | 1.8 A | 25 W | 8.2 ms | 16.7 ms | 680 nF | 0.57 |

**4 A buys 15 %.** Useful, free, and nowhere near enough to rescue a DFN 3.3 —
Q1 still needs a published SOA curve in a DPAK or D2PAK.

### What 4 A does decide: the output rating

This is the real content of the choice. Required limit at the input floor:

| Output design point | At 6 V in | At 4.4 V in |
|---|---|---|
| Real ~4.6 W load | 0.90 A | 1.23 A |
| **2 A / 12 W** | 2.35 A | **3.2 A** ✓ |
| 3 A / 18 W | 3.53 A | **4.8 A** ✗ |

**A 4 A limit is a decision to build a 2 A supply.** It covers 12 W down to the
4.4 V floor with margin, covers 18 W only above ~5.5 V input, and gives the
real load 3.3×. That matches
[`power-supply.md`](power-supply.md)'s own conclusion — 2 A is 3× the actual
load, and 3 A was headroom for loads not yet stated.

**R<sub>SNS</sub> = 11 mΩ** (45 mV / 4 A), with **C8 = 300 nF**. Note the
datasheet example lands on the same 4 A target and picks 10 mΩ, which would
give 4.5 A.

### The bigger lever: keep inrush out of current limit entirely

The invariance above only holds because startup *uses* the current limit. It
does not have to. **Slewing HGATE with a gate capacitor** keeps inrush below the
limit, so TMR never starts at power-up and t<sub>OC</sub> is freed to be short:

```
hold inrush to 1 A with 1236 µF   →  dV/dt = 1 A / 1236 µF = 809 V/s
                                  →  ramp to 12 V in 14.8 ms
C_gate = I_HGATE(UP) / (dV/dt)    →  ~25 nF at 20 µA          [verify I_HGATE]

then tOC need only cover a genuine fault:  1–2 ms
E_short = 14 V × 4.1 A × 2 ms = 0.11 J        ← 4× less than 0.42 J
```

Inrush energy in Q1 is unchanged at ½CV² = 0.089 J either way — that is fixed
by the capacitance — but it is spread over 15 ms instead of concentrated, and
the *short-circuit* case improves four-fold.

**[verify]** against the datasheet whether HGATE slew control with an external
capacitor is supported here, and what I<sub>HGATE(UP)</sub> is. If it is, this
is worth more than any R<sub>SNS</sub> change.

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
| 3 | **C8: 56 nF → 2.2 µF X7R/C0G, 16 V** — faults on inrush as drawn; 2.2 µF holds 400 ms load-dump ride-through at worst-case tolerance | **blocking** |
| 5 | **Delete F1/F2** — truck PDB fusing is the branch protection; PPTCs → VREF | **blocking** |
| 2 | **R4: 2.2k → 220 Ω, C2: 100 nF → 470 nF**; UV = 4.47 V from §4 divider | high |
| 4 | **TVS → one SMDJ43A + OV divider → 249k/86.6k/10k**; verify Q1 ≥100 V | high |
| 6 | **Q1 → IRF540NS (D2Pak)**; keep YJQ40G10A for Q2 | resolved |
| 7 | ADCRANGE=0 | low |
| 8 | Confirm single-point PGND/GND tie | low |
| 1 | UV/OV divider — **no change, it is correct** | none |
| — | C3–C7 at 35 V — **no change** | none |

Also update [`power-supply.md`](power-supply.md): the stated 3.5 V cold-crank
floor is the SEPIC's, not the system's. The LTC4364 cuts off first.
