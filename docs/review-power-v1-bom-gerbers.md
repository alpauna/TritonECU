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

The datasheet backs this up — it groups exactly those pairs as single functional
nodes:

```
pins  2, 3   SUP      pins  5, 6   PGND1
pins 12, 13  OUT      pins  9, 10  PGND2
```

So merging 5+6 and 9+10 under one land each is consistent with the part's own
pin grouping. (SUP and OUT were left as separate pads, which is a choice rather
than an inconsistency.)

**The definitive reference, if you want certainty before ordering:**

```
Package Code           F224A4FY+1
Outline Number         21-100399
Land Pattern Number    90-100137     ← this is the document to check
```

**CLOSED 2026-09-13** — the package drawing settles it without needing the land
pattern document. `MAX25239AFF` shows **PGND1 (5, 6) and PGND2 (9, 10) as single
stepped lands carrying two pin numbers each**, while **SUP (2, 3) and OUT
(12, 13) are separate pads**. That is exactly the footprint's pattern.

Geometry agrees:

```
pin 5 land   1.31 × 1.56 mm    5× the width of its 0.25 mm neighbours
pin 9 land   1.31 × 1.56 mm
outer extent from the package centre:
   +X edge (16–21)   2.20 mm
   +Y / −Y edges     2.42 mm
   pins 5, 9         2.30 / 2.31 mm      ← same band, not outliers
pad field    4.61 × 4.84 mm on a 4.25 × 4.25 body   (0.18–0.30 mm overhang)
```

Pin 5's land spans X −2.95 to −1.64, which straddles where bumps 5 and 6 sit
along that edge. The footprint is correct as drawn — **no need to chase land
pattern 90-100137.**

### Incidental: the MAX25239's own thermals are comfortable

```
θJA   33.3 °C/W   4-layer JEDEC board
      22.4 °C/W   4-layer EV kit board
θJCb   6.4 °C/W
```

At 5 W out and ~92 % efficiency the loss is about 0.43 W, so roughly a **14 °C
rise** on a JEDEC 4-layer board. No action needed — noted because it is the one
thermal number on this sheet that was never checked.

## 6. [verify] C2/C3 must be aluminium electrolytic, not polymer

```
C2, C3   HV1V567M1010PZ   HONOR   560 µF, 10 × 10.3 mm can
```

The 10 mm can and the `M` (±20 %) tolerance both point to aluminium
electrolytic, which is correct. **Confirm it is not a polymer hybrid** — their
ESR is the input filter's damping, and a low-ESR substitution raises Q from
about 1.7 to 14. See [`power-supply.md`](power-supply.md).

## 7. Smaller items

- ~~**Two SMDJ43A (D1, D2).**~~ **The board has one.** `D2` has no footprint —
  the placement list is `D1`, `D3`, `D4`. One is 3000 W and enough anyway, since
  paralleled TVS do not share. **The BOM's quantity 2 is wrong** — see the PGND
  section at the end.
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
- ~~**D1, D2 are still two SMDJ43A.**~~ **Wrong — that read the BOM, not the
  placement. `D2` is not on the board.**
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

---

# Gerber revision 2 — the vias landed on the wrong FET

Diffed against the previous export: **6 vias added, 2 removed** (97 → 101).

```
( 30.99,  9.78)  0.70 mm from Q1_8   net IN+
( 30.99, 10.54)  0.72 mm from Q1_7   net IN+
( 30.99, 11.30)  0.76 mm from Q1_6   net IN+
( 30.99, 11.94)  0.76 mm from Q1_5   net IN+
( 33.37, 15.21)  1.78 mm from R1_1   net IN+
( 51.00, 18.49)  1.97 mm from C21_2
```

Four of them stitch **Q1's drain**. Q2's tab still has **zero vias within 8 mm**,
and its top-layer B+ copper is unchanged at 214.6 mm².

## The two FETs do opposite jobs

| | | Dissipation |
|---|---|---|
| **Q1** | YJQ40G10A, DFN-8, **DGATE** ideal-diode FET | fully on or fully off, **never linear** → `0.33² × 15 mΩ` = **1.6 mW** |
| **Q2** | IRF540NS, TO-263, **HGATE** pass element | **runs in linear mode** during clamping and current limit → **2.74 W** average under auto-retry |

**Q1 has no thermal problem to solve.** Q2 is the one that heats, and it is at
the far left of the board:

```
Q1 drain pads   (31.68,  9.7–11.6)   ← where the vias went
Q2 tab (B+)     (13.93, 32.92)       ← where they were needed
```

The four new vias are harmless — spreading IN+ current is fine — so there is
nothing to undo. But the thermal item is still open.

## Still the same two options

1. **A B+ island on Inner2 under Q2, stitched with 6–9 vias through the tab.**
   Inner2 is already poured and already carries routing (2391 draws), so it is a
   matter of carving the island rather than finding a layer.
2. **Commit to the firmware retry limit instead** — Q3/U_SHDN exists for it,
   the always-on MCU survives to run it, and capping at 3 retries bounds the
   exposure at 3 × 54 ms rather than indefinitely.

Either closes it. Option 2 costs no board area and was always the primary
recommendation; option 1 is belt and braces.

---

# Gerber revision 3 — Q2 thermal CLOSED

```
vias 101 → 121;  20 of them inside Q2's tab pad (8.40 × 10.57 mm)

B+ copper containing the tab:
   TOP   214.6 mm²    unchanged
   IN2   366.2 mm²    new island, bbox 7.9–22.2 × 13.8–39.5
   BOT   156.2 mm²    new island, bbox 8.6–20.6 × 26.2–39.2
                      ----------
   total 737.0 mm²  =  1.14 in²
```

**And Inner1's ground plane is untouched at 3516 mm²** — the islands were carved
on Inner2 and Bottom, so no slot was cut in the main ground plane. That was the
part that needed care and it was done right.

## Thermal estimate

```
via array   20 × 0.3 mm through 1.6 mm FR4, 25 µm plating
            157 °C/W each  →  7.84 °C/W in parallel
RθJC        1.15 °C/W
spreading   1.14 in² over three layers

estimated RθJA ≈ 25–30 °C/W        (was 40–50)
requirement    ≤ 33 °C/W

Tj = 85 + 2.74 × 28 = 162 °C   against a 175 °C limit   ✓
```

**The finding is closed on copper alone** — the firmware retry limit is now
belt-and-braces rather than load-bearing, though it remains worth having for
diagnostics and for bounding the fault.

## Via tenting is right

**Bottom soldermask has zero openings over the tab area**, so the 20 vias are
tented. That matters: untented via-in-pad wicks solder through during reflow and
starves the joint, which would have undermined the thermal path just built.

## One build note: the tab paste aperture is a single opening

```
top paste over the tab:  1 aperture, ~100 % coverage of 88.8 mm²
```

Standard default, and the solder volume is fine — a 0.12 mm stencil gives
roughly a 0.06 mm bondline. The risk is **voiding**: one large aperture gives
flux volatiles nowhere to escape, and voids under the tab would partly undo the
1.14 in² of copper.

Usual practice for a pad this size is a **windowpane pattern** — an array of
smaller apertures at 50–80 % total coverage. Worth asking the assembler for, or
editing in the stencil file. **Not a board change**, and not needed at all if
the part is hand-soldered with a preform or drag-soldered.

---

# ⚠ BLOCKING — the shunt datasheet describes a jumper, not a 10 mΩ resistor

`FRM252WJR010TN` was flagged earlier only for its `J` tolerance code. The
datasheet raises something worse.

## The series is sub-milliohm by definition

Four independent statements in the same document:

```
Title            "FRM-Jumper Series — Zero milli-ohm (Jumper) Metal alloy Chip Resistor"
                 "FRM-0mΩ系列合金电阻"

Electrical       Type    Power   Max Loading Current   Resistance (mΩ)
characteristics  2512    2 W          100.0 A              < 0.20

Every performance spec (overload, soldering heat, thermal shock, …):
                 "0603: ≤0.3 mΩ   Others: ≤0.2 mΩ"

Part-number key  "R000 = Below 0.2 mΩ"
```

**There is also no TCR specification anywhere in the datasheet** — which makes
sense for a jumper and is disqualifying for a current-sense element.

## What the part number decodes to

```
F    R          M       25     2W    J       R010    T          N
FOJAN Resistor  Metal   2512   2 W   ±5 %    ?       7" reel    NiCu
```

**2 W and a NiCu alloy element are both good news** — better than the 1 W
thick-film worry from the earlier review. But `J = ±5 %` is confirmed, and
`R010` sits in a series whose own key only defines `R000` as "below 0.2 mΩ".

## If it is a jumper, the LTC4364 loses its current limit entirely

```
current limit   45 mV / 0.2 mΩ   =  225 A        → never trips
inrush          1236 µF charged with no limit    → uncontrolled every key-on
overcurrent     the fault timer never starts     → no shutdown, no FLT#
INA238          0.33 A × 0.2 mΩ = 66 µV = 13 LSB → battery current unreadable
```

The LTC4364's entire overcurrent function, the inrush control, the fault timer
and the battery-current measurement all rest on this one resistor being 10 mΩ.

## Resolve before ordering

Either this datasheet is for the wrong series, or the part is not 10 mΩ. The
LCSC listing (C7420034) and the BOM both say 10 mΩ, so the conflict is real and
cheap to settle:

- **Measure one with a 4-wire meter** — 10 mΩ and 0.2 mΩ are not close.
- Or **switch to a part whose own datasheet states the value**, which also
  fixes the tolerance and TCR questions in one move.

### Replacement specification

| | |
|---|---|
| Value | **10 mΩ** |
| Tolerance | **1 %** — it sets the current-limit trip point directly |
| TCR | **≤ 50 ppm/°C** — it also sets the INA238's accuracy |
| Power | ≥ 1 W (203 mW at the limit; the 2512 footprint is already there) |
| Construction | **metal element**, 4-terminal preferred |

Vishay WSL2512, Susumu KRL2512, Bourns CRE/CRF and Panasonic ERJ-M1W are all
stocked classes that meet this and drop into the existing 2512 land.

---

# Shunt resolved — FPM series is the right part

`FPM253WJR010TM` replaces `FRM252WJR010TN`. The FPM datasheet is a genuine
current-sense part and answers every question the FRM one raised.

| | FRM (jumper series) | **FPM** |
|---|---|---|
| Series purpose | "Zero milli-ohm (Jumper)" | **"Low Resistance High Power Alloy Resistor"**, current detection |
| 2512 resistance range | < 0.2 mΩ | **1–100 mΩ** — 10 mΩ is in range ✓ |
| **T.C.R.** | **not specified** | **±50 ppm/°C** |
| Tolerances offered | ±5 % only | **±0.5 %, ±1 %, ±2 %, ±5 %** |
| Alloy | NiCu | **CuMn (manganin)** — the classic shunt alloy |
| Power at 70 °C | 2 W | **3 W** |
| Rated / overload current | — | **38 A / 86 A** |
| Operating temperature | — | **−55 °C to +170 °C** |
| Qualification | — | **AEC-Q200 compliant** |
| Inductance | — | **low inductance** stated |

**AEC-Q200 matters beyond this part**: it makes the shunt one of the few
automotive-qualified items in the rail chain, alongside the LTC4364 and the
MAX25239.

The datasheet also has a **"Resistance measurement point"** section, which is
exactly the Kelvin-probe guidance the layout item needs.

## One change: `J` → `F`

```
FPM253W J R010TM   ←  ±5 %   (chosen)
FPM253W F R010TM   ←  ±1 %   (available, and the datasheet's own example
                              part number is FPM253W F R005TM)
```

The tolerance table lists ±0.5 %, ±1 %, ±2 % and ±5 % for this size and value,
so the 1 % part is a stocked option rather than a special.

### What ±5 % actually costs

```
current limit   4.5 A ± 5 %  =  4.28 – 4.73 A          tolerable on its own
INA238          ±5 % gain error on every current reading
TCR drift       ±50 ppm/°C × 165 °C  =  ±0.83 %        not calibratable

±1 % part  →  ~1.8 % worst case
±5 % part  →  ~5.8 % worst case
```

**±5 % is recoverable in firmware** — the INA238 has a `SHUNT_CAL` register
exactly for this, so a per-board calibration removes the initial error and
leaves only the 0.83 % drift. But that is a production step per board, and the
1 % part costs pennies more.

**Take the F variant if it is stocked.** If only the J is available, fit it and
calibrate `SHUNT_CAL` at bring-up — the part is otherwise entirely right, which
is the thing that was in doubt.

---

# Output caps resolved — HGC1206R7226K160NSPJ

Decoded from the manufacturer's ordering key:

```
HGC | 1206 | R7 | 226 | K | 160 | N | S | P | J
      3216   X7R  22µF ±10% 16V  Cu/Ni/Sn  tape  1.6mm  7"
```

**X7R, −55 to +125 °C** — which was the thing to protect. Moving to 16 V in
0805 would have meant X5R at +85 °C, and this avoids that by going up a case
size instead.

## It fixes both variables

| | Old | **New** |
|---|---|---|
| Case | 0805 | **1206** — thicker/more dielectric layers, lower field |
| Rating | 10 V (50 % bias at 5 V) | **16 V** (31 % bias) |
| Dielectric | +125 °C class | **X7R, +125 °C** ✓ |
| Estimated effective, 4 × 22 µF | 36–44 µF | **57–66 µF** |

The design assumption was **66 µF**, so this lands on it rather than 40 % short.
Crossover returns to about 51 kHz and f<sub>ZRHP</sub>/5 as designed.

**±10 % tolerance is irrelevant here** — the loop moves ~7° of phase margin
across a 2× capacitance range, so a ±10 % part is noise against DC bias.

## Three things to know

### Height goes from ~0.9 mm to 1.6 mm

Thickness code **P = 1.6 mm**, against roughly 0.85–1.0 mm for a 22 µF 0805.
Check it against the enclosure and anything that stacks over that area.

### Standard termination on a 1206, in a vehicle

The part is **`N` = Cu/Ni/Sn**. The same series offers **`C` = Cu/Resin/Ni/Sn**,
a soft termination.

**1206 is more flex-crack prone than 0805** simply because it is longer, and
this board lives somewhere that vibrates. The datasheet's bending test is the
standard 1 mm deflection for 5 s; soft-termination parts tolerate substantially
more. Either take the `C` variant, or keep these four away from board edges,
mounting holes and connector insertion zones when re-placing them.

### The datasheet has no DC bias curve

It is a generic approval sheet covering 0201–1210 and 4–63 V, with no per-part
bias data — so **the 57–66 µF figure above is a rule of thumb, not a
specification.**

That matters more than usual here because **the loop cannot be measured in
circuit** — FB is tied to VCC for the fixed 5 V option, so there is no injection
point. Worth asking the supplier for the bias curve, or measuring one part at
5 V bias on an LCR meter that supports it.

Also not AEC-Q200 — consistent with the TLV62085 and the MAX6070 variant, and a
deliberate trade rather than an oversight.

### And it is a re-layout of that area

1206 is 3.2 × 1.6 mm against 0805's 2.0 × 1.25 mm, so the four output caps need
re-placing and re-routing. Keep them tight to the MAX25239's OUT pins (12, 13)
— the output loop is part of what the compensation assumes.

## Add 100 nF 0402 at the OUT pins — not 4.7 or 10 µF

Worth adding, because moving to 1206 created a gap that 0805 did not have.

### The 1206 bank is inductive at the switching frequency

```
22 µF nominal → ~15 µF effective at 5 V bias
1206 ESL      ≈ 1.2 nH        (0805 ≈ 0.7 nH, 0402 ≈ 0.5 nH)

SRF = 1/(2π√(1.2 nH × 15 µF)) = 1.19 MHz
```

**That is below the 2.1 MHz fundamental.** Above SRF a capacitor is an inductor,
so the output bank is inductive exactly where the converter switches — 15.8 mΩ
per part, about 4 mΩ for four.

For *ripple* that barely matters: 0.34 A rms × 4 mΩ = 1.4 mV. What it does
matter for is the **nanosecond edges**, where `V = L·di/dt` and 0.3 nH of bank
ESL against a 2 A transition in 10 ns is a **60 mV spike**.

The input side does not have this problem — C24/C25 are 4.7 µF 0603, whose SRF
lands around 4.3 MHz, comfortably above 2.1 MHz. **The asymmetry is the whole
argument.**

### Why not 4.7 µF or 10 µF — anti-resonance

A small capacitor in parallel with a large one resonates against the large one's
ESL, and impedance *peaks* at that frequency:

```
f = 1/(2π√(L_bank × C_small))       L_bank ≈ 0.3 nH (four 1206s in parallel)

C_small = 10 µF  (≈3.5 µF biased)   →  4.9 MHz
C_small = 4.7 µF (≈2 µF biased)     →  6.5 MHz     ← 3rd harmonic is 6.3 MHz
C_small = 100 nF                    →   29 MHz     ← clear of the comb
```

**4.7 µF lands the impedance peak essentially on the third harmonic.** 100 nF
puts it an octave and a half above anything the converter produces strongly.

The small part also has to be the one with low ESL to be worth fitting — a
0402's 0.5 nH against the 1206's 1.2 nH is the point, and a 10 µF 0402 is a
dense part with worse ESL and heavy bias derating anyway.

### What to fit

**One 100 nF 0402 at each OUT pin (12 and 13)**, each with its own ground via,
kept in the tightest loop available. Two beats one — it halves the loop area
rather than the capacitance.

**This is a refinement, not a correction.** The datasheet's own application
circuit is 4 × 22 µF with nothing smaller, and everything downstream of this
rail either does not care (the TLV62085 is a switcher) or has its own ferrite
and local decoupling (the ADC daughterboard). Do not let it hold up the board.

### Placement checked — the pour makes the distances acceptable

The output caps could not all sit close to the MAX25239, but **+5V is routed as
a 38 mm² top-layer pour**, not as traces — and every one of them is inside it:

```
U10 pin 12, pin 13, C9, C10, C11, C12, C13, C14   all in one 38 mm² TOP region
                                                   over the Inner1 ground plane
```

That is the difference between acceptable and not. A thin trace over a plane is
roughly 0.7 nH/mm; a ~3 mm wide pour is closer to 0.1–0.2 nH/mm. Across the
12 mm span this is **~1–3 nH instead of ~8–9 nH.**

| | Distance from nearest OUT pin | |
|---|---|---|
| **C9**, 0603 HF | **1.83 mm** | ✓ this is the one that catches the ns edges |
| C10, 0603 HF | 4.08 mm | contributes less at HF, harmless |
| C11–C14, 1206 bulk | 7.5 – 11.9 mm | ~2–3 nH on the pour → ~8 mΩ for four at 2.1 MHz → 2.7 mV |

**C9 at 1.83 mm is doing the job the small cap was added for.** On a pour that
is a few tenths of a nanohenry, which is the same order as the 0603's own ESL —
so nothing is being wasted by the distance.

0603 rather than 0402 costs about 0.1–0.2 nH of ESL. Immaterial next to the
spreading inductance either way.

**TLV62085 input decoupling is also well placed** — C18 (0402) at 1.59 mm and
C22 at 2.17 mm from U9 pin 7. Note the 5 V reaches it through the inner and
bottom layers rather than the top pour, which is fine given that local
decoupling.

**Nothing to change.** The compromise forced by the tight placement was absorbed
by routing +5V as copper rather than track, which is the right trade.

---

# Closeout — L1, L2 and the TVS

## L2 — CYA0650-2R2M, confirmed with margin

```
                     spec          needed
inductance     2.20 µH ±20 %       2.2 µH        ✓
Isat                 10.0 A        ≥ 4.3 A       ✓  2.3×
Irms (heat)           9.5 A        3.6 A peak    ✓
DCR            11.2 mΩ typ / 12.5 max   →  130 mW at the 3.4 A boost corner
dimensions     7.2 × 6.6 × 5.0 mm   footprint IND-SMD_L7.2-W6.6  ✓ matches
core           metal dust — soft saturation
```

**±20 % tolerance is fine.** At the 1.76 µH end ripple rises 25 % (0.69 → 0.86 A);
at 2.64 µH the RHP zero falls from 255 to 213 kHz, making the 51 kHz crossover
f<sub>ZRHP</sub>/4.2 rather than /5 — a couple of degrees of phase margin.

Note the BOM calls it `CYA0650-2.2UH` where the datasheet calls it
`CYA0650-2R2M`; same part, distributor naming.

**5.0 mm height** is the second-tallest item after the 560 µF cans at 10 mm.

## L1 — RETRACTED, 500 nH is a TI-recommended value

My concern about 94 % ripple was a rule of thumb applied where the datasheet has
an explicit answer. TI's own recommended-inductor table for the TLV62085:

| Inductance | Current | Size | Part |
|---|---|---|---|
| **0.47 µH** | 6.6 A | 4 × 4 × 1.5 | Coilcraft XFL4015-471 |
| **0.47 µH** | 4.7 A | 3.2 × 2.5 × 1.2 | TOKO DFE322512-R47N |
| 1 µH | 5.1 A | 4 × 4 × 2 | Coilcraft XFL4020-102 |

**Two of the three recommendations are 0.47 µH**, and `CR4015-R50N` is 500 nH in
the same 4 × 4 package as the first entry. The ripple really is ~0.94 A pk-pk —
`3.3 × (1 − 3.3/5)/(500 nH × 2.4 MHz)` — but **high ripple is normal for
DCS-Control**, which is a fixed-on-time architecture rather than fixed-frequency
PWM. TI designed the part around it.

`I_L,MAX = 1 + 0.94/2 = 1.47 A`, so **[verify]** the CR4015-R50N's Isat is
comfortably above that — a 4 × 4 mm 500 nH part is typically 5–10 A.

The rest of the TLV62085 section also matches TI's guidance: 22 µF typical
output (C15/C16 are 2 × 22 µF) and 10 µF input (C21/C22).

## TVS — one SMDJ43A

Closed. 3000 W is enough on its own, and a single part removes the sharing
assumption that made two of them less than 2× anyway.

---

# Everything is closed

No board or BOM changes outstanding. Two things remain that are not board
changes:

- **Windowpane paste aperture on Q2's tab** — a stencil edit or an instruction
  to the assembler, to avoid voiding under the thermal path.
- **The 1206 DC-bias figure is an estimate**, since the loop cannot be measured
  in circuit with FB tied to VCC. If ripple or transient response looks wrong at
  bring-up, start there.

---

# PGND, D1, and the tie that was never confirmed

`schematic-review-power.md` §8 said *"D1/D2 return to PGND, everything else to
GND. Correct instinct. **Confirm the two are joined at exactly one point**, and
that the TVS return is the shortest, widest path to the input connector."* It was
filed as severity **low** and never closed. Measured off
`FlyingProbeTesting.json` and the copper, here is what is actually there.

## PGND is a two-node net

| Net | Pins |
|---|--:|
| **GND** | **118** |
| **PGND** | **2** — `D1_2` and `CN1_2`, each listed twice |

**That is the entire net: D1's cathode to the input connector's ground pin.**
Nothing else is on it.

## And CN1 has only two pins, so PGND is not just a surge path

```
  CN1_1   B+     (12.19, 6.22)
  CN1_2   PGND   (17.27, 6.22)
```

**There is no third pin.** GND never reaches CN1, which means **PGND is the
board's only return to the vehicle** — every milliamp the board draws goes out
through it, not merely the TVS surge. GND touches the outside world only through
the four mounting pads (U2–U5, at the board corners) and the two headers.

So the mental model of *"PGND for surge, GND for everything else"* is not what
this board does. **PGND is the trunk and GND hangs off it.**

> **The join is still unconfirmed, and the netlist cannot confirm it.** PGND and
> GND are distinct nets with distinct names, so they are joined in *copper*
> somewhere, not through a pin. That copper join is what §8 asked about.

## Where the tie belongs: at `CN1_2`, not at D1

Both choices are "one point". They are not equivalent:

| Tie at | What GND rides on |
|---|---|
| **`CN1_2`** ✅ | the vehicle ground entry. Surge current enters at `CN1_1`, crosses D1, and leaves at `CN1_2` — GND sits at the *end* of that path and never carries any of it |
| `D1_2` ❌ | the far end of the PGND run. Every volt the run develops appears across GND |

**Tie at the connector.**

## ⚠ D1 is 17.7 mm from the connector

```
  CN1_1  (12.19,  6.22)  ──────┐
                               │   loop 17.7 x 7.4 mm
  D1_1   (11.05, 23.88) ──[D1]─┤   area ~130 mm², perimeter ~50 mm
  D1_2   (18.42, 23.88)        │   L ~ 20 nH over a plane, ~50 nH if traces
                               │
  CN1_2  (17.27,  6.22)  ──────┘
```

A TVS clamps to its own V<sub>clamp</sub> **plus whatever its loop develops**, so
that inductance is part of the protection:

| Transient | di/dt | L·di/dt at 20 nH | at 50 nH |
|---|--:|--:|--:|
| Load dump, 10/1000 µs | 4 A/µs | **0.1 V** | 0.2 V |
| ISO 7637-2 **pulse 3a/3b**, 5 ns | 4000 A/µs | **80 V** | 201 V |
| IEC 61000-4-2 **ESD**, 1 ns | 30 000 A/µs | **602 V** | 1506 V |

**The slow surge does not care about the loop. The fast ones are nothing but
loop.** So D1 is doing its advertised job against load dump — which is what it
was chosen for — and much less than advertised against fast transients.

That matters here specifically because **Q1 is a 100 V part**
(`IRF540NS`, per §Q1). A pulse-3b edge arriving as an inductive spike rather
than a clamped level is exactly the case the 100 V rating has to cover.

## ⚠ There is no capacitor at the input at all

`B+` touches **six** things: `CN1`, `D1`, `Q1`, and the divider resistors `R2`,
`R6`, `R7`. The nearest component of any kind to CN1 is R13 at **8 mm**.

**A TVS is a slow device dressed as a fast one.** Its companion is a small
ceramic right at the entry, which handles the nanosecond edge while the TVS
handles the energy. There isn't one.

## What to do

| | | |
|---|---|---|
| **1** | **Tie PGND to GND at `CN1_2`**, one point, and confirm in CAD that it is only one | v1, layout check |
| **2** | **Add a ceramic across CN1** — 100 nF X7R ≥ 100 V, plus 1 nF C0G if there is room, as close to the pins as the footprint allows | **v1, and it needs no respin if there is pad space** |
| **3** | **Move D1 to the connector** — target < 20 mm² instead of 130 | v2 |
| **4** | **Do not split the Inner1 plane.** 3516 mm² solid is right; a split forces return current to detour and costs more than it saves | v2 |
| **5** | **Decide about the four mounting pads on GND** — that is a chassis bond at four points, and four parallel paths through the enclosure is a loop if the enclosure is bonded elsewhere | [`enclosure.md`](enclosure.md) |

## ✅ And one thing that is already right: there is only one TVS

The BOM asks for **2 × SMDJ43A, designators `D1,D2`**. **`D2` is not on the
board** — the placement list has `D1`, `D3` and `D4` and no `D2`.

So §7's *"one is 3000 W and enough; paralleled TVS do not share"* is **already
satisfied in copper**, and this document's own line *"D1, D2 are still two
SMDJ43A"* was reading the BOM rather than the placement. **Correct the BOM to
quantity 1** — as it stands you would order a part with nowhere to go.

---

# BOM revision 2 — checked against the placement, 2026-09-18

Cross-checked designator by designator against `FlyingProbeTesting.json`.

| | |
|---|---|
| BOM designators | **71** |
| Real placements on the board | **71** |
| In the BOM but not placed | **none** |
| Placed but not in the BOM | **none** |

**A clean match both ways**, which the previous BOM was not.

## ✅ What this revision fixes

| | |
|---|---|
| **`D2` removed** | It has no footprint. The old BOM asked for 2 × SMDJ43A and you would have had nowhere to put the second |
| **`D4` added** — `ESD5Z5.0T1G` | It was **on the board and missing from the BOM** — you would have been one part short at assembly |
| **Phantom `C1206` designator gone** | The old rows for C11–C14 were **column-shifted** — manufacturer in the part field, value in the footprint field — which leaked the footprint string `C1206` into the designator column as a 72nd "part" |
| **C11–C14 now name a real part** | `HGC1206R7226K160NSPJ`, whose datasheet is already in [`Datasheets/`](Datasheets/) |
| **`R1` footprint** | `R2512` → `RES-SMD_L6.4-W3.2-R2512`. **Rename only** — same 2512 |

## ✅ Q1/Q2 — the old BOM had them backwards, and the board proves it

The netlist is authoritative about what is on the copper:

| Ref | Pads on the board | Footprint |
|---|---|---|
| **Q1** | 3 pads **+ an 8.40 × 10.57 mm tab** | **TO-263-2 (D2Pak)** |
| **Q2** | 9 pads, 0.40 × 0.65 fine pitch + a 2.45 × 2.00 centre pad | **DFN-8** |

| | Q1 | Q2 | |
|---|---|---|---|
| **New BOM** | `IRF540NSTRLPBF` / TO-263-2 | `YJQ40G10A` / DFN-8 | ✅ **matches** |
| Old BOM | `YJQ40G10A` / DFN-8 | `IRF540NSTRLPBF` / TO-263-2 | ❌ backwards |

So [`schematic-review-power.md`](schematic-review-power.md) summary item 6 —
*"Q1 → IRF540NS (D2Pak); keep YJQ40G10A for Q2"* — **was already implemented in
the layout**, and only the BOM had lagged. It has now caught up.

> ⚠ **And that corrects this document.** The *"Gerber revision 3 — Q2 thermal
> CLOSED"* section above analyses *"**Q2**'s tab pad (8.40 × 10.57 mm)"*. **That
> tab is `Q1_4`.** The thermal work — 20 vias, 737 mm² of copper, RθJA ≈ 25–30 °C/W
> — is all correct and all about **Q1**. The designator was taken from the old,
> wrong BOM.

## ⚠ Two changes worth confirming

**`R1`: `FRM252WJR010TN` → `FPM253WFR010TM`.** This is the current-sense shunt
feeding both the INA238 and the LTC4364's current limit, so it is not a
like-for-like swap to wave through:

- **Different series** — FRM252 → FPM253.
- **Different tolerance code** — `…W**J**R010TN` → `…W**F**R010TM`. J is 5 %,
  **F is 1 %**, which is an improvement for current sensing.
- **[CONFIRM]** power rating and TCR. [`Datasheets/`](Datasheets/) holds
  `FPM253WJR010TM` and `FRM252WJR010TN` — **the `F` variant now specified is not
  on file.**

**`Q4`: `BS170FTA` → `BSS123`.** Same SOT-23-3 footprint, and now identical to
Q3 — one fewer line item. BSS123's V<sub>GS(th)</sub> is ≈ 1.3 V against BS170's
up to 3 V, so this is the better part if Q4 is driven from **3.3 V** logic.
**[CONFIRM]** that is what drives it.

## ⚠ And a number that does not match: the shunt is 10 mΩ, not 8

[`schematic-review-power.md`](schematic-review-power.md) §7 reasons from
*"At 8 mΩ…"*; the BOM says **`R010` — 10 mΩ**, and so does this document
elsewhere (*"the LTC4364's 10 mΩ shunt"*).

**The conclusion survives, the arithmetic does not:**

| R1 | ADCRANGE=1 (±40.96 mV) | ADCRANGE=0 (±163.84 mV) |
|---|---|---|
| 8 mΩ *(assumed)* | ±5.12 A — saturates under the 5.6 A limit | ±20.48 A |
| **10 mΩ *(actual)*** | **±4.10 A — saturates harder** | **±16.38 A** ✓ |

**`ADCRANGE=0` is still the right answer**, and at the real 10 mΩ the case for it
is stronger, not weaker.
