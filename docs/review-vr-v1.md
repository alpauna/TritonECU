# VR board V1 review — 2026-09-13

`TritonECU_VR_Schematic_V_1` + `TritonECU_VR_V_1_Greber.zip`.
**35.43 × 33.91 mm, 2 layer.** Four VR channels from two MAX9926UAEE+T.

Checked against the MAX9924–MAX9927 datasheet and the repo's own
[`1999-Ford-F150-4wd-5.42v/vr-conditioning.md`](1999-Ford-F150-4wd-5.42v/vr-conditioning.md).

## Correct as drawn

| | |
|---|---|
| **Mode A2 strapping** — ZERO_EN = GND, INT_THRS1/2 = GND | ✓ exactly Table 1 |
| **EXT1, EXT2 left unconnected** | ✓ *"Leave EXT unconnected in Modes A1, A2"* |
| **COUT/DIRN open-drain, 10 kΩ to 3.3 V** | ✓ the part runs on 5 V but the pull-up rail alone sets the logic level |
| **10 kΩ in every input leg** | ✓ *"Add a series 10 kΩ resistor to each input"* |
| **Filter cap between the op-amp inputs** | ✓ *"Add a filter capacitor between the operational amplifier inputs"* |
| **VR pairs adjacent on U3, GND at both ends** | ✓ pairs stay together down the harness |
| Four channels for crank, cam and two spare | ✓ — **but the spares are now spent**: OSS and the transfer case speed sensor. [`review-vr-chain.md`](review-vr-chain.md) §2 |

One thing Mode A2 gets for free and is worth knowing: the datasheet warns that
*"the series resistors lower the gain of the input amplifier and should be
accounted for when setting the trigger threshold."* With the **internal adaptive
threshold** that correction happens by itself — the threshold tracks ⅓ of the
previous peak whatever the gain is.

## 1. BLOCKING — the eight VR input resistors are 0402

```
R1, R8, R9, R10, R11, R12, R13, R14   RC0402FR-0710KL   R0402
```

[`vr-conditioning.md`](1999-Ford-F150-4wd-5.42v/vr-conditioning.md) already
calls this: *"0805 minimum… 0603 is genuinely marginal and 0402 is out."*

```
0402 max working voltage     50 V
VR peak at engine speed    > 100 V
```

**Essentially all of that appears across the series resistor**, because the far
end is clamped by the MAX9926's internal ESD diodes to within a diode drop of
the 5 V rail. That is a 2× overvoltage on every tooth at high rpm — and these
parts fail by voltage breakdown and repetitive pulse stress, not by heating, so
the 1 W of instantaneous dissipation is not the number that matters.

**Change the eight input legs to 0805**, or better **2 × 4.99 kΩ 0805 in series
per leg** for 300 V of headroom. **R2–R7 (the output pull-ups) stay 0402** —
they sit on 3.3 V logic with no voltage stress.

## 2. HIGH — VCC bypassing is 100 nF only, and the datasheet is specific

```
C2, C5   100 nF   and nothing else
```

> *Bypass the power supply with multiple capacitor values in parallel… a
> parallel combination of **10 nF, 0.1 µF and 1 µF, with the 10 nF placed
> closest** between the VCC and GND pins… through wide traces (preferably
> planes), and **without vias in the high-frequency current path**.*
>
> *The use of an **internal charge pump** for the front-end amplifier makes this
> more important.*

A charge pump draws current in pulses, which is why the datasheet is unusually
prescriptive here. **Add 10 nF and 1 µF at each device**, with the 10 nF nearest
the pins.

## 3. [verify] — BIAS1 and BIAS2 are tied to GND

Table 1 gives Mode A2's bias source as **"Internal Ref"** (V<sub>INT_BIAS</sub>
= 2.46 V), and the text says that reference is used *"instead of an external
voltage connected to the BIAS input."* The external divider is described only
for **"Modes A1, B, and C."**

The datasheet gives explicit guidance for the sibling pin — *"Leave EXT
unconnected in Modes A1, A2"* — and **says nothing about BIAS in A2.**

| Reading | Evidence |
|---|---|
| Grounding is harmless | I<sub>BIAS</sub> is specified as an **input** current, ≤ 1 µA, in *"Modes A1, A2, B, C"* — a high-impedance input even in A2, so an ignored pin |
| Grounding shorts something | V<sub>INT_BIAS</sub> = 2.46 V is documented **under the BIAS heading**, which is how a reference brought out for decoupling would be specified |

**Safest change: replace the short with a 0.1 µF to GND.** That satisfies both
readings — it decouples the pin if it carries the internal reference, and does
nothing if the pin is ignored. Leaving it open would also be defensible and
matches how EXT is treated.

Low risk to build either way: if BIAS is wrong there will be no output pulses
at all, so it fails loudly rather than subtly.

## 4. Note — the input filter corner is 8 kHz, not 16 kHz

`vr-conditioning.md` says 1 nF with 10 kΩ puts the corner "near 16 kHz". That is
the single-ended figure. **Differentially the time constant is (R1 + R2)·C:**

```
τ  = 20 kΩ × 1 nF = 20 µs      f_c = 7.96 kHz
```

36-1 wheel at 6000 rpm = **3.6 kHz**, so only **2.2× headroom**, and the group
delay matters for timing:

| Engine speed | Tooth frequency | Group delay | In crank degrees |
|---|---|---|---|
| 600 rpm (cranking) | 0.36 kHz | 19.96 µs | **0.07°** |
| 6000 rpm | 3.6 kHz | 16.6 µs | **0.60°** |

**0.60° of retard at 6000 rpm is a real timing offset**, and it is not constant
in degrees, so it cannot be trimmed out with a single number. It *is* computable
from the tooth period, so firmware can correct it exactly — but that has to be a
deliberate decision rather than a surprise found while chasing a timing
discrepancy.

The alternative is **470 pF**, which moves the corner to 17 kHz and the error to
0.28° at 6000 rpm, at the cost of half the noise rejection. Either is defensible;
doing neither is not.

## Summary

| # | Change | Severity |
|---|---|---|
| 1 | **Eight VR input legs 0402 → 0805**, or 2 × 4.99 kΩ 0805 | **blocking** |
| 2 | **Add 10 nF + 1 µF** at each MAX9926 VCC, 10 nF closest | high |
| 3 | BIAS1/BIAS2: replace the short to GND with 0.1 µF, or leave open | verify |
| 4 | Decide: compensate the 0.60° filter delay in firmware, or fit 470 pF | decision |

---

# Revision — 2026-09-13

## Fixed

| | |
|---|---|
| Input legs → **0805** (`ARG05DTC5001`, Viking) | ✓ the blocking item |
| **1 µF added** to each VCC (C3, C7) | ✓ |
| Filter caps → **470 pF, 0805, C0G, 200 V** | ✓ good part — C0G is stable and low-loss, and 200 V is generous |

## The resistance halved as well — defensible, with a limit

The recommendation was **2 × 5 kΩ in series per leg** = 10 kΩ at 300 V. What was
fitted is **one 5 kΩ per leg** = 5 kΩ at 150 V. Both numbers moved.

**Electrically it is fine.** The binding spec is the datasheet's absolute
maximum, `Current into IN+, IN−: ±40 mA`:

```
VR peak   current through 5 kΩ     voltage across the 0805
 100 V         18.9 mA                    94 V     ✓
 150 V         28.9 mA                   144 V     ← 0805's 150 V rating reached
 200 V         38.9 mA                   194 V     ✗ (current still inside ±40 mA)
```

**The resistor's voltage rating runs out before the pin current does** — at
about **155 V of VR peak**. So 5 kΩ in 0805 is good to ~150 V, which covers a
100 V sensor with 1.5× margin.

Lower series resistance also **raises the input gain**, which helps cranking
sensitivity — and the datasheet's warning that *"the series resistors lower the
gain… and should be accounted for when setting the trigger threshold"* costs
nothing here, because Mode A2's adaptive threshold tracks it automatically.

**So: acceptable, with one thing to do.** The VR peak on this engine has never
been measured. **Measure it during M3 bring-up** — a scope on the crank sensor
at whatever rpm the bench can reach, extrapolated. If it stays under ~140 V, the
board is right as built. If it goes higher, add the second 5 kΩ per leg.

## The filter moved a long way — know where it landed

Both R and C changed, so the corner moved four-fold:

```
was   2 × 10 kΩ + 1 nF     τ = 20 µs    f_c =  8.0 kHz
now   2 ×  5 kΩ + 470 pF   τ = 4.7 µs   f_c = 33.9 kHz
```

| | was | **now** |
|---|---|---|
| Group delay at 6000 rpm | 16.6 µs | **4.65 µs** |
| …in crank degrees | 0.60° | **0.17°** |
| …at 600 rpm cranking | 0.07° | 0.017° |
| Attenuation at 1 MHz | 42 dB | **29 dB** |

**0.17° is small enough to ignore** rather than compensate, which is the right
outcome. The cost is 13 dB less rejection of ignition-coil noise — the
differential input's CMRR does most of that work anyway, but it is now the term
to look at first if the crank signal proves noisy on the engine.

## Still open

### 10 nF is missing from the VCC bypass

```
fitted:    100 nF (C2, C6)  +  1 µF (C3, C7)
datasheet: 10 nF  +  0.1 µF  +  1 µF,  "with the 10 nF placed closest"
```

Two of the three values. The 10 nF is the one the datasheet specifically says to
place nearest the pins, and the reason it is prescriptive at all is the
**internal charge pump** in the front-end amplifier, which draws current in
pulses. Cheap to add.

### BIAS1 and BIAS2 are still tied to GND

Unchanged — both share the GND net with INT_THRS1/2. See §3 above: replacing the
short with **0.1 µF to GND** satisfies both readings of the datasheet, or leave
the pins open to match how EXT is handled.

## Where this leaves M3

**Nothing here blocks bench bring-up.** On a signal generator the VR peak is
whatever you set it to, so the 150 V question is a vehicle question, not a bench
one. Build it, drive 36-1 into it, and confirm the decoder against
`test_crank`'s 10 native tests running on real edges instead of synthetic ones.


---

# Both items closed — 2026-09-13

## 10 nF fitted

```
C2, C7   GRM033R71C103KE14D   10 nF   0201
C3, C8   CC0402KRX7R7BB104   100 nF   0402
C4, C9   CL10B105KO8NNNC       1 µF   0603
```

Exactly the trio the datasheet asks for, and **in ascending package size** —
which is the right order, since the 0201 has the lowest ESL and is the part that
has to sit closest to the pins.

## BIAS grounded is correct — and the design doc already said so

Datasheet **Figure 3, "MAX9924/MAX9926 Operating Mode A2"** shows **BIAS tied
straight to ground**, alongside ZERO_EN, INT_THRS and GND, with EXT left
unconnected. The board matches it exactly.

The general pin description — *"connect to an external resistor-divider and
bypass to ground with a 0.1 µF and 10 µF capacitor"* — describes **Modes A1, B
and C**, which is also what the "Bias Reference" section says: *"In Modes A1, B,
and C, a well-decoupled external resistor-divider generates a VCC/2 signal."*

[`vr-conditioning.md`](1999-Ford-F150-4wd-5.42v/vr-conditioning.md) had this
right already — *"BIAS1: GND — required in A2"* — and the review second-guessed
it against the general pin description instead of the mode-specific text. The
figure reference is now recorded in that doc so it cannot be re-litigated.

## The board is complete

Nothing outstanding. The one open question is a **measurement, not a change**:
the VR peak on this engine, which decides whether 5 kΩ in 0805 (good to ~150 V)
needs the second resistor per leg. That is a vehicle question and M3 is a bench
exercise, so it does not gate anything now.
