# POWER sheets review — 2026-09-13

Review of `Schematics/TritonECU_Power_2026-09-13.zip` (POWER1, POWER2), V1.0.
Supersedes [`schematic-review-power.md`](schematic-review-power.md), which
reviewed the 2026-09-08 single sheet.

## Corrections from the previous review that landed

| | |
|---|---|
| R1 2.2 kΩ → **220 Ω**, C1 100 nF → **470 nF** | ✓ |
| D3 (CMZ5945B zener) **deleted** | ✓ |
| OV/UV divider → **249 kΩ / 86.6 kΩ / 10 kΩ** (43.2 V / 4.47 V) | ✓ |
| Q2 → **IRF540NSTRLPBF** (D2Pak), Q1 stays **YJQ40G10A** | ✓ exactly as specified |
| PPTCs **removed**, external 5 A fuse noted | ✓ |
| TVS → **SMDJ43A** | ✓ (see §5 on quantity) |
| SPS strapped to **VCC** via R21, not to 5 V | ✓ the pin that kills the part |
| SYNC **10 kΩ to GND** plus M_SYNC to the header | ✓ |
| PGOOD → **3.3 V** on both converters (5_GOOD, 3.3_GOOD) | ✓ |
| Output bank **4 × 22 µF** | ✓ |
| MCU shutdown via BSS123 pulling SHDN# low | ✓ the retry-latch path |

## 1. BLOCKING — U11 is the 400 kHz variant

```
U11 = MAX25239AFFB/VY+
```

From the ordering table:

| Part | I<sub>LIM</sub> | Fixed V<sub>OUT</sub> | Adj | **f<sub>SW</sub>** |
|---|---|---|---|---|
| MAX25239AFF**A**/VY+ | 8.2 A | 5 V | <6.5 V | **2100 kHz** |
| MAX25239AFF**B**/VY+ | 8.2 A | 5 V | <6.5 V | **400 kHz** |

**The B suffix is 400 kHz.** Two independent consequences, either one blocking:

**It puts harmonics straight into the AM band** — the single reason the switching
frequency was pushed up in the first place:

```
400 kHz × 3 = 1.20 MHz     AM band = 530–1710 kHz
400 kHz × 4 = 1.60 MHz     both inside it
```

**And L2 = 2.2 µH is the 2.1 MHz value.** At 400 kHz the same inductor gives:

```
ΔIL = Vout(Vin − Vout)/(fsw · L · Vin)

at 2.1 MHz, 13.8 V in    0.69 A pk-pk    ← what 2.2 µH was chosen for
at  400 kHz, 13.8 V in   3.62 A pk-pk
at  400 kHz,   27 V in   4.63 A pk-pk
```

**Change U11 to MAX25239AFFA/VY+.** The 400 kHz part would need ~4.7 µH — the
datasheet's own 400 kHz application value — and would still be in the AM band.
Everything else on the sheet (L2, the output bank, the compensation) is already
sized for 2.1 MHz.

## 2. BLOCKING — R19 is 78.7 Ω, should be 78.7 kΩ

```
R19 = 78.7 Ω        drawn
Rc  = 78.7 kΩ       calculated
```

A factor of **1000**. With 78.7 Ω the error amplifier has essentially no gain at
crossover and the zero sits at `1/(2π·78.7·2.2 nF)` = **919 kHz** instead of
919 Hz — above the intended crossover rather than a decade below the power-stage
pole.

C22 = 2.2 nF is correct. C23 = 3.3 pF is the low-stray option discussed for
C<sub>p</sub> and is fine.

## 3. BLOCKING — ENOUT sits at V<sub>IN</sub> and reaches the MCU header

R3 pulls ENOUT to **VIN**, which is correct and necessary: ENOUT must enable the
MAX25239 before any downstream rail exists, so it cannot be pulled to 3.3 V or
5 V. That part is right.

**But ENOUT is also on U8 pin 8**, alongside SCL, SDA, U_SHDN, M_SYNC and the
three GOOD signals — a header that is otherwise entirely 3.3 V logic. During a
clamped overvoltage that pin carries **27 V into the MCU.**

Fix, in order of preference:

1. **Remove ENOUT from U8.** It has a job on this board — driving the MAX25239's
   EN — and the MCU does not need it.
2. If the MCU should see it, add a divider or a small open-drain level shift to
   3.3 V, sized so the MAX25239's EN still sees its logic threshold.

Worth a check across every header pin: **U8 is otherwise safe** (VIN-ALERT,
5_GOOD, 3.3_GOOD are pulled to 3.3 V; M_SYNC and U_SHDN are MCU-driven).

## 4. HIGH — C7 is 1.5 µF, should be 2.2 µF

Sized for the 400 ms ISO 7637 load dump, which has to survive X7R tolerance:

```
capacitance tolerance ±10 %, X7R tempco ±15 %  →  worst case ≈ −23 %

1.5 µF → 405 ms nominal → 312 ms worst case      short of 400 ms ✗
2.2 µF → 594 ms nominal → 457 ms worst case      ✓
```

Specify **X7R or C0G, 16 V, 0805** — the TMR pin charges at 5 µA, and tantalum
leakage is specified in microamps, the same order as the charging current.

## 5. Items to confirm

### R<sub>SNS</sub> is 8 mΩ, giving a 5.6 A limit

Not the 11 mΩ / 4.1 A discussed, but **acceptable as drawn** — the IRF540NS
absorbs it:

```
short:  14 V × 5.6 A = 78 W  for tOC = 54 ms (with C7 = 2.2 µF) = 4.2 J
        Zθ(54 ms) ≈ 0.35 °C/W  →  ΔTj ≈ 27 °C
```

The consequence is that the supply is sized for more output than the 2 A decided
in [`power-supply.md`](power-supply.md). Leave it or change it deliberately; do
not change it by accident.

### FB is tied to M_VCC — the fixed 5 V option

Valid, and it gives ±2 % with no divider current. **But it removes the
loop-injection point**, which matters more here than it did in the abstract:
with §2 outstanding, the compensation network cannot be verified in circuit
without cutting into the board.

Either accept that the loop goes unmeasured, or move to adjustable mode
(53.6 kΩ / 10.2 kΩ for 5.004 V, 78 µA) and keep a 10–20 Ω injection resistor in
the divider.

### TLV62085 feedback divider is 672 kΩ

R17 = 510 kΩ, R18 = 162 kΩ → 3.32 V ✓, but only **4.9 µA** of divider current.
That is deliberate for the sleep budget and defensible, with two things to check
against the TI datasheet:

- **FB leakage** against 4.9 µA — at 50 nA it is a 1 % output error.
- **Whether a feedforward capacitor across R17 is required.** High-value
  dividers usually need one for loop stability, and a high-impedance FB node
  beside a 2.4 MHz switcher is also a noise-pickup risk.

### L1 = 500 nH on the TLV62085

At 2.4 MHz, 5 V → 3.3 V that gives **0.94 A pk-pk** — about 94 % ripple at a 1 A
load. Check TI's recommended value; 1 µH would halve it.

### Two SMDJ43A in parallel

Breakdown-voltage tolerance means the lower-V<sub>br</sub> device takes most of
the surge and fails first, so two do not give 2× capability. **One SMDJ43A is
3000 W and is enough** — that is why the part was chosen over the SMCJ. Harmless
to keep, but it is not buying what it appears to.

### PGND pins

The symbol shows PGND1 on pin 5 and PGND2 on pin 9. The datasheet assigns
**PGND1 = 5, 6** and **PGND2 = 9, 10**. Confirm all four are connected.

## Summary

| # | Change | Severity |
|---|---|---|
| 1 | **U11 → MAX25239AFF*A*/VY+** (2100 kHz) | **blocking** |
| 2 | **R19 → 78.7 kΩ** | **blocking** |
| 3 | **Remove ENOUT from U8**, or level-shift it | **blocking** |
| 4 | C7 → 2.2 µF X7R/C0G 16 V | high |
| 5 | Confirm R<sub>SNS</sub> 8 mΩ is intentional (5.6 A limit) | medium |
| 6 | Fixed FB loses the loop-injection point | medium |
| 7 | TLV62085: check FB leakage vs 4.9 µA, and feedforward cap | medium |
| 8 | TLV62085: check L1 = 500 nH against TI's recommendation | medium |
| 9 | One SMDJ43A is enough | low |
| 10 | Confirm PGND pins 6 and 10 connected | low |
