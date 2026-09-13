# POWER V1 — BOM and Gerber review, 2026-09-13

Reviewed: `Triton_ECU_BOM_POWER_Power_V_1.csv`,
`TritonECU_Power_V_1_Gerber.zip`, and the matching schematic export.

**Board:** 76.58 × 46.74 mm, 4 layer, 97 vias.

## What the Gerbers confirm

Measured from the flying-probe netlist and by computing polygon areas out of the
copper layers — not read off a picture.

### ✓ The COMP network is placed exactly right

This was flagged as a layout risk because C23 is 3.3 pF, the same order as board
stray:

```
U10 pin 17 (COMP)   (54.55, 21.98)
R21_1               (55.83, 21.72)   1.31 mm from the pin
C23_1               (55.84, 20.57)   1.91 mm from the pin
```

Both inside 2 mm. Nothing to change.

### ✓ Sense devices are close to the shunt

```
R1_1 (IN+ side)  (33.15, 13.44)      R1_2 (VIN side)  (33.15, 19.58)
  → U1_2  SENSE   4.94 mm              → U1_1  OUT      4.11 mm
  → U8_10 IN+     5.55 mm              → U8_9  IN−      7.61 mm
```

Polarity is right: current flows IN+ → R1 → VIN, the LTC4364 reads
(SENSE − OUT) across it, and the INA238's IN+/IN− match that direction.

**[verify in the editor — Gerbers cannot show this]** whether the four sense
connections are **thin traces taken from the shunt pad edges**, or taps off the
VIN/IN+ copper pours. Both sense pairs share nets with the power path — which is
unavoidable with a 2-terminal shunt, so the Kelvin quality is purely geometric.
At 4.5 A, **1 mΩ of shared power copper is 4.5 mV against a 45 mV threshold —
10 % of the current limit**, and the same error in reported battery current.

Note the INA238's two legs are asymmetric — 5.55 mm versus 7.61 mm. Harmless if
they are dedicated sense traces, a direct error if they tap the pour.

## 1. Q2 thermal — 0.33 in² and no thermal vias

Computed from the copper polygons:

```
Q2 tab (net B+)              (13.93, 32.92)
top-layer region containing it   214.6 mm²  =  0.33 in²,  9.8 × 34.0 mm strip
thermal vias within 8 mm              0     (97 vias on the board)
```

The bottom and Inner1 pours do enclose that point geometrically, but they are
**GND**, not B+ — so with no vias they are not a conduction path.

Against the auto-retry case, recomputed for the 10 mΩ shunt:

```
tOC       = 2.2 µF × 1.35 V / 55 µA   =   54 ms
cooldown  = 2.2 µF × 1.35 V / 2.5 µA  = 1188 ms
duty                                   = 4.35 %
fault power  14 V × 4.5 A              =   63 W
average                                = 2.74 W
required  RθJA ≤ (175 − 85)/2.74       =   33 °C/W
estimated for 0.33 in², no vias        =  40–50 °C/W
```

**Context before acting on this.** Normal dissipation is `0.33² × 44 mΩ` =
**4.8 mW**. A clamped load dump is 7 W for 400 ms — a single pulse, ~21–35 °C
rise, fine. The 2.74 W figure applies only to **unlimited auto-retry into a
persistent short**, a fault where the board is already broken.

### The real fix is firmware, and the hardware already supports it

Q3/U_SHDN exists specifically to let the MCU latch the supply off, and the
always-on domain means the MCU survives to do it. **Capping retries at 3 caps
the exposure at 3 × 54 ms spread over ~3.7 s** instead of indefinitely —
comfortably survivable at 0.33 in².

**Promote the retry limit from a nice-to-have to a requirement**, and record it
as a thermal dependency rather than a diagnostic nicety.

### And there is a free copper fix available

**InnerLayer2 is unpoured** — 0 filled regions against Inner1's 3516 mm². On a
4-layer stackup that is an unused layer. Pouring **B+ on Inner2 under Q2 and
stitching the tab down with 6–9 vias** roughly halves R<sub>θJA</sub> without
touching the Inner1 ground plane or the bottom pour, and without carving a slot
in either.

## 2. BOM — the shunt looks like a 5 % part

```
R1   FRM252WJR010TN   FOJAN   10 mΩ   2512
```

The **`J`** in that code conventionally denotes **±5 %**. The shunt sets the
current-limit trip point *and* the INA238's battery-current accuracy, and the
whole reason for moving to 2512 was precision.

**[verify] the tolerance and TCR**, and if it is 5 % / thick-film, substitute a
**1 %, ≤50 ppm/°C metal-element** part. The cost difference is cents; 5 %
initial plus a thick-film TCR of 200 ppm/°C compounds to roughly **10 % of
error** across temperature.

## 3. BOM — the 5 V output caps are 10 V parts

```
C9–C14   GRM21BZ71A226ME15L   22 µF 0805   →  "1A" = 10 V rating
```

C13/C14 sit on the 3.3 V rail and are fine. **C9–C12 are the MAX25239's output
bank at 5 V** — 50 % of rated voltage, where a high-density 0805 typically loses
**50–60 %**:

```
design assumption      88 µF nominal → 66 µF effective   → Rc 78.7 kΩ, fc 51 kHz
10 V parts at 5 V bias 88 µF nominal → 36–44 µF effective → fc ≈ 84 kHz
```

That moves crossover from f<sub>ZRHP</sub>/5 to about **f<sub>ZRHP</sub>/3**,
costing roughly 7° of phase margin — an estimated 59° rather than 66°. **Still
acceptable, so this is not blocking** — but DC bias derating is the least
well-characterised number in the whole loop, and a **16 V or 25 V part** puts it
back on the design assumption for no other change.

## 4. BOM — Q4 should be BSS123, which is already on the BOM

```
Q3   BSS123     Vgs(th) 0.5–1.5 V    (the SHDN pull-down)
Q4   BS170FTA   Vgs(th) 0.8–3.0 V    (the ENOUT level shifter)
```

In the level shifter the FET must enhance on `Vgs = 3.3 − Vdiode ≈ 2.6 V`. A
worst-case BS170 at 3.0 V threshold **never turns on**, leaving the low level at
one body-diode drop — ~0.7 V at 25 °C, ~0.8 V at −40 °C, against an STM32
V<sub>IL</sub> of 0.99 V.

**Use BSS123 for Q4 as well.** It enhances properly, giving a low of tens of
millivolts instead of a diode drop, it is rated 100 V against the BS170's 60 V,
the footprint is the same SOT-23-3, and it **deletes a BOM line**.

## 5. ~~[verify]~~ RETRACTED — the MAX25239 footprint is correct

```
U10   MAX25239AFFA/VY+   footprint "FC2QFN-20_L4.3-W4.3-P0.40-TL_MAX25240AFFD-VY"
```

**Checked against the actual pad geometry — it is right, and my concern was
wrong.** The 20 pads are not two missing pins. **PGND1 (5, 6) and PGND2 (9, 10)
are each merged into one large pad:**

```
pin 5  (−2.298, +1.630)  GND   pad 1.31 × 1.56 mm   ← covers bumps 5 and 6
pin 9  (−2.298, −1.630)  GND   pad 1.31 × 1.56 mm   ← covers bumps 9 and 10
everything else                pad 0.25–0.96 mm wide
```

Merging adjacent same-net bumps under one pad is correct QFN practice, and the
wide pads sit in the same rows and vertical extents as their neighbours with
0.26 mm of clearance. Every net assignment also checks out: BST1/BST2, SUP ×2,
LX1/LX2 to L2, OUT ×2, EN ← ENOUT, FB ← M_VCC (the fixed 5 V option), COMP,
SPS, SYNC, PGOOD → 5_GOOD, AGND.

**Nothing to change, and PGND 6 and 10 are connected by virtue of the merge.**

## 6. [verify] C2/C3 must be aluminium electrolytic, not polymer

```
C2, C3   HV1V567M1010PZ   HONOR   560 µF, 10 × 10.3 mm can
```

The 10 mm can and the `M` (±20 %) tolerance both point to aluminium
electrolytic, which is correct. **Confirm it is not a polymer hybrid** — their
ESR is the input filter's damping, and a low-ESR substitution raises Q from
about 1.7 to 14. See [`power-supply.md`](power-supply.md).

## 7. Smaller items

- **Two SMDJ43A (D1, D2).** One is 3000 W and enough; paralleled TVS do not
  share, because the lower-V<sub>br</sub> part takes the surge.
- **L2 = CYA0650-2.2UH** — confirm I<sub>sat</sub> ≥ **4.3 A**.
- **L1 = CR4015-R50N, 500 nH** — at 2.4 MHz, 5 → 3.3 V that is 0.94 A pk-pk,
  about 94 % ripple at a 1 A load. Check TI's recommended value for the
  TLV62085; 1 µH would halve it.
- **TLV62085 feedback divider is 672 kΩ** (R19 510 k / R20 162 k), 4.9 µA.
  Deliberate for the sleep budget, but check FB leakage against it and whether
  TI specifies a feedforward capacitor across R19.

## Summary

| # | Item | Severity |
|---|---|---|
| 2 | Shunt tolerance — `J` suggests 5 %, want 1 % / ≤50 ppm/°C | **high** |
| 5 | Count the MAX25239 footprint pads (22, not 20) | **high** |
| 4 | Q4 → BSS123 (already on the BOM, deletes a line) | medium |
| 3 | C9–C12 → 16 V or 25 V | medium |
| 1 | Q2 copper: make the firmware retry limit a requirement; consider pouring Inner2 | medium |
| 6 | Confirm C2/C3 are aluminium, not polymer | medium |
| — | Verify Kelvin sense geometry in the editor | medium |
| 7 | One SMDJ43A; L1/L2 saturation and value; TLV62085 divider | low |
| ✓ | COMP placement, sense-device proximity, polarity | **good as drawn** |


---

# Revision check — 2026-09-13, `_V_1` export

## Fixed

| | |
|---|---|
| **Q3 and Q4 are both BSS123** | ✓ and it deleted a BOM line |
| **InnerLayer2 is poured** — 2999 mm² where it had 0 filled regions | ✓ |

## Retracted

**The MAX25239 footprint** — see §5. 20 pads is correct because two PGND pairs
are merged. My finding was wrong.

## Still as drawn

Routing and placement are unchanged between exports (top-layer draws 4543 →
4530, vias 97 → 97, R1/U1/U8 pad coordinates identical), so these are as before:

- **R1 = FRM252WJR010TN.** If the `J` is ±5 %, it wants replacing.
- **C9–C12 are 10 V parts on the 5 V rail.** Not blocking — ~59° of estimated
  phase margin — but 16 V or 25 V returns it to the design assumption.
- **D1, D2 are still two SMDJ43A.**
- **L1 500 nH / L2 2.2 µH** unchanged.

### ⚠ Pouring Inner2 does not help Q2 without vias

```
Q2 tab (B+)                       (13.93, 32.92)
top-layer B+ region               214.6 mm²   unchanged
InnerLayer2 region under the tab  2971.6 mm²  new
vias within 8 mm of the tab       0           unchanged
```

**The two halves of that recommendation only work together.** With no stitching,
the Inner2 pour is separated from the tab by prepreg and conducts almost nothing
— and if that pour is GND rather than B+, vias alone would not help either; it
needs a **B+ island on Inner2 under Q2**, stitched with 6–9 vias.

Alternatively **treat the firmware retry limit as the fix** — which was the
primary recommendation, and which the hardware already supports through
Q3/U_SHDN. Capping retries at 3 bounds the exposure at 3 × 54 ms rather than
indefinitely, and 0.33 in² is comfortable for that. **Pick one; the current
state has neither.**
