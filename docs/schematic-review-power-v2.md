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

## 1. ~~BLOCKING~~ RESOLVED 2026-09-13 — U11 was the 400 kHz variant

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

**Fixed: U11 is now MAX25239AFFA/VY+.** ✓ The 400 kHz part would need ~4.7 µH — the
datasheet's own 400 kHz application value — and would still be in the AM band.
Everything else on the sheet (L2, the output bank, the compensation) is already
sized for 2.1 MHz.

## 2. ~~BLOCKING~~ RESOLVED 2026-09-13 — R19 was 78.7 Ω

```
R19 = 78.7 Ω        drawn
Rc  = 78.7 kΩ       calculated
```

**Fixed: R19 is now 78.7 kΩ.** ✓ It was a factor of **1000** out. With 78.7 Ω the error amplifier has essentially no gain at
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

**POWER2 revised 2026-09-13; POWER1 is unchanged from the reviewed version.**

| # | Sheet | Change | Status |
|---|---|---|---|
| 1 | POWER2 | U11 → MAX25239AFF*A*/VY+ (2100 kHz) | **✓ fixed** |
| 2 | POWER2 | R19 → 78.7 kΩ | **✓ fixed** |
| 3 | **POWER1** | **Remove ENOUT from U8**, or level-shift it | **open — blocking** |
| 4 | **POWER1** | C7 → 2.2 µF X7R/C0G 16 V | **open — high** |
| 5 | Confirm R<sub>SNS</sub> 8 mΩ is intentional (5.6 A limit) | medium |
| 6 | Fixed FB loses the loop-injection point | medium |
| 7 | TLV62085: check FB leakage vs 4.9 µA, and feedforward cap | medium |
| 8 | TLV62085: check L1 = 500 nH against TI's recommendation | medium |
| 9 | One SMDJ43A is enough | low |
| 10 | Confirm PGND pins 6 and 10 connected | low |

---

# Before the BOM and layout

## R<sub>SNS</sub> = 11 mΩ — what moves and what does not

```
ILIM(min) = 45 mV / 11 mΩ = 4.09 A        (was 5.6 A at 8 mΩ)
inrush    = 1236 µF × 12 V / 4.09 A = 3.63 ms
tOC       = 2.2 µF × 1.35 V / 55 µA = 54 ms        15× margin ✓
```

**C7 stays at 2.2 µF** — the timer was sized by the 400 ms load dump, not by
inrush, and 54 ms still clears 3.63 ms by 15×. Q1's worst case improves:
`14 V × 4.09 A = 57 W` for 54 ms = 3.1 J, ΔTj ≈ 20 °C on the IRF540NS.

### Specify the shunt properly — and power is not what sizes it

```
running, 13.8 V, 0.33 A          1.2 mW
cold crank, real load, 0.9 A     8.9 mW
2 A out at the 4.4 V floor       113 mW    ← realistic worst case, and transient
at the 4.09 A current limit      184 mW    ← absolute ceiling, 54 ms before shutdown
auto-retry average (4.3 % duty)    8 mW
```

**1 W is ~5× the absolute peak and ~800× the continuous figure — keep it
anyway.** The power rating is not the binding spec here. Three other things are:

| | Why |
|---|---|
| **Tolerance 1 %** | it sets the current limit *directly* |
| **TCR ≤ 100 ppm/°C**, prefer ≤ 50 | it sets the INA238's battery-current accuracy too |
| **Kelvin routability** | 2512 leaves room to bring both sense pairs off the inner pad edges; 4-terminal parts start at 2512 |

TCR is the one worth spending on. A thick-film 1206 at 200 ppm/°C drifts
**3.3 %** over −40 to +125 °C, and that error lands in the reported battery
current as well as the trip point. A metal-element 2512 at 15–50 ppm/°C drifts
0.25–0.8 %.

Self-heating favours the larger part slightly as well: at the 184 mW ceiling a
2512 rises 5–9 °C against 15–22 °C for a 1206, which with the TCR above is a
further 0.07 % versus 0.2 %. Small, but it points the same way.

**So the 1 W part is already the right choice, for reasons other than its
wattage.**

### DECIDED 2026-09-13: 10 mΩ, 1 W, 2512

11 mΩ is E96 and the selection in good tolerance and TCR is thinner. The
datasheet's own worked example picks **10 mΩ** for a 4 A target:

| R<sub>SNS</sub> | I<sub>LIM(min)</sub> | I<sub>LIM(typ)</sub> | Q1 short-circuit |
|---|---|---|---|
| 10 mΩ | 4.50 A | 5.00 A | 63 W |
| **11 mΩ** | **4.09 A** | **4.55 A** | **57 W** |
| 12 mΩ | 3.75 A | 4.17 A | 53 W |

All three clear the 3.2 A needed at the 4.4 V floor, and all three are
comfortable for the IRF540NS. **ADCRANGE = 0 is required at any of them** — the
narrow range saturates below the limit in every case.

**Settled on 10 mΩ**, the datasheet's own value, moved from 1206 to **2512** for
Kelvin routing. Everything downstream holds:

```
ILIM(min)          45 mV / 10 mΩ            =  4.50 A
inrush             1236 µF × 12 V / 4.50 A  =  3.3 ms   vs 54 ms timer   ✓
C7                 unchanged at 2.2 µF                                    ✓
Q1 short-circuit   14 V × 4.50 A = 63 W for 54 ms = 3.4 J → ΔTj ≈ 22 °C   ✓
shunt dissipation  10 mΩ × 4.50² = 203 mW on a 1 W 2512, ~20 % of rating  ✓
INA238 ADCRANGE=0  ±163.84 mV / 10 mΩ = ±16.4 A, 0.50 mA/LSB              ✓
```

The 1206 → 2512 move is the right call for a second reason beyond routing room:
**thick-film 1206 shunts are typically 200 ppm/°C**, which would have put 3.3 %
of drift into both the trip point and the reported battery current over the
temperature range.

| Terminals | **4-terminal (Kelvin) if available** — see layout below |

### INA238: ADCRANGE = 0

```
ADCRANGE = 1   ±40.96 mV  →  ±3.72 A at 11 mΩ    saturates BELOW the 4.09 A limit ✗
ADCRANGE = 0  ±163.84 mV  →  ±14.9 A             0.45 mA/LSB                      ✓
```

A firmware constant, not a schematic change — but it has to be right for the
FLT# disambiguation in [`always-on-domain.md`](always-on-domain.md), which
distinguishes an overcurrent fault from an overvoltage warning by reading
whether the current is at the limit.

## Three layout items that are hard to fix later

### 1. Kelvin the shunt — it is sensed twice

**Both** the LTC4364 (SENSE/OUT) and the INA238 (IN+/IN−) measure across the
same 11 mΩ. At the 4 A limit, **1 mΩ of trace error is 4 mV against a 45 mV
threshold — 9 % of the current limit**, and a direct error in the battery
current reading.

Route both sense pairs from the **inner edges of the shunt pads**, symmetric,
each pair kept together. Do not tap them off the current-carrying copper.

### 2. Copper under Q1 is a specified requirement, not a preference

From the auto-retry analysis: a persistent short averages **2.5 W** in Q1 at a
4.3 % duty cycle that cannot be tuned away, because it is fixed by the ratio of
the TMR charge and discharge currents.

```
required   RθJA ≤ (175 − 85) / 2.5 = 36 °C/W
D2Pak on minimum pad          40 °C/W   →  Tj = 185 °C  ✗
D2Pak on ~1 in² of 2 oz Cu    25–30     →  Tj ≈ 147 °C  ✓
```

### 3. The COMP node is small and high-impedance

C23 is **3.3 pF** and board stray is 2–5 pF — the same order. R20 is **78.7 kΩ**
sitting beside a 2.1 MHz switching node. Keep R20/C22/C23 tight to the pin and
away from LX1/LX2.

## BOM cautions

- **C7 must be X7R or C0G, never tantalum or electrolytic.** TMR charges at
  5 µA; tantalum leakage is specified in microamps.
- **The 560 µF input electrolytics must stay electrolytic.** Their ESR is the
  input filter's damping — a low-ESR polymer "upgrade" raises Q from 1.7 to
  about 14. See [`power-supply.md`](power-supply.md).
- **4 × 22 µF output: check DC bias derating.** The compensation assumes ~66 µF
  effective from 88 µF nominal; a 6.3 V part at 5 V bias would fall well short.
- **One SMDJ43A is enough** — two in parallel do not share.
