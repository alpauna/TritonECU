# Oil pressure board — reconstruction of V 1.0

**AMPED Oil Pressure V 1.0**, alshowto.com. JLC panel `5363411A_Y1`, date code
**230106** — the boards were made January 2023. The design files are gone, so
this is being rebuilt from the physical boards.

Purpose: replace the truck's oil pressure *switch* with a real pressure sender,
show the reading on an LCD, **and keep the original dash lamp working** — lamp on
below 12 psi, the stock default.

> **Status: partial.** Everything below is marked ⬤ confirmed or ○ inferred.
> Nothing here has been verified by continuity yet.

## Identified so far

| Ref | Part | How |
|---|---|---|
| ⬤ U1 | **ATtiny85-20SU**, SOIC-8, lot 2233 (week 33, 2022) | Top marking: ATMEL / TINY85 / 20U |
| ⬤ Q1 | **KIA2803A** — N-ch MOSFET, 30 V, 150 A, 2.2 mΩ, TO-263 | Datasheet read |
| ⬤ R1 | **10 MΩ**, gate pull-down for Q1 | Marking `01F` (EIA-96), confirmed by the builder |
| ⬤ R2 | **1.2 kΩ**, gate series to Q1 | Marking `122`; role by elimination once R3 was placed |
| ⬤ R3 | **1.2 kΩ**, series into the ADC from `Sensor` | Builder |
| ⬤ D1 | **A TVS on the 12 V input — value not recorded.** Removed from the board | Builder |
| ⬤ D2 | **A 5 V clamp protecting the ADC node**, on the R3 / `Sensor` side. Removed from the board | Builder |
| ⬤ Sender | **100 PSI, 0.5–4.5 V ratiometric transducer** (what it was tested with) | Builder |
| ○ U2 | A 78xx regulator, DPAK | Marking legibly starts `78…`, rest degraded |
| ⬤ C1, C3 | **7.9 µF in-circuit** — almost certainly 10 µF MLCCs; regulator input and output | Meter |
| ⬤ C2 | **100 nF** — the ADC filter at the `Sensor` node | Meter |

> ⚠ **D1 and D2 are off the board as it sits.** It currently has *no* input
> transient protection and *no* ADC clamp. Fine on a bench supply; do not put it
> back in a vehicle in this state.

## Connectors, from the silkscreen

| Ref | Type | Pins |
|---|---|---|
| ⬤ **J1** | 2×3 | `12+`, `Sensor`, `GND` / `Dash`, `5v` (one unlabelled) — the vehicle harness |
| ⬤ **J2** | 2×3 | `GND`, `5v` marked — the footprint and labels say **AVR ISP** |
| ○ **J3** | 1×4 | Almost certainly the I²C LCD: GND / VCC / SDA / SCL |

`5v` appearing on the *vehicle* connector means the sender is powered from the
board — so a **3-wire ratiometric sender** (0.5–4.5 V), not a resistive one.

## Reconstruction

```
   J1 12+ ──┬──[ D1 TVS ]── GND
            └── U2 (78xx) IN     OUT ──┬── 5V ── U1 VCC, J2, J3, and J1 5v
               C1 ──┴── GND          C3 ──┴── GND        (the sender's supply)

   J1 Sensor ──[ R3 1k2 ]──┬── U1 ADC (PB3 or PB4)
                           ├──[ D2 5V clamp ]── GND
                           └──[ C2 ? ]── GND

   U1 PB? ──[ R2 1k2 ]──┬── GATE  Q1 KIA2803A ── DRAIN ── J1 Dash
                R1 10M ──┴── GND                 SOURCE ── GND

   U1 PB0/PB2 (USI) ── J3 SDA/SCL
```

## The sender path, in numbers

100 PSI over 0.5–4.5 V, read against V<sub>CC</sub> as the ADC reference:

| PSI | Volts | ADC count |
|--:|--:|--:|
| 0 | 0.50 | 102 |
| **12** (the lamp threshold) | **0.98** | **201** |
| 50 | 2.50 | 512 |
| 100 | 4.50 | 921 |

**0.122 PSI per count** — resolution is nowhere near the limiting factor. R3's
1.2 kΩ source impedance is well inside the AVR ADC's 10 kΩ guidance.

**Ratiometric is doing more work than it looks.** The transducer is fed from the
same 5 V that is the ADC reference, so regulator error cancels in the ratio —
*including while the 78xx is in dropout during cranking*, since the sensor and
the reference sag together. The reading stays honest right down to the MCU's
brown-out threshold. That is the single best decision in this design.

**D2's headroom was the flaw in that path — and it was seen on the bench.** The
clamp got in the way and **skewed the high-pressure readings**, which is why it
is off the board. The arithmetic says the same thing: the signal legitimately
reaches 4.50 V and the clamp sits at 5 V.

| | |
|---|--:|
| Signal maximum | 4.50 V |
| A 5.1 V ±5 % zener, worst case | **4.85 V** |
| Margin | **0.35 V**, into a soft knee |

10 µA of leakage at full scale costs 12 mV across R3 — 0.3 PSI, reading *low* at
high pressure, and climbing with temperature.

### Replacing it

The pin is bare now, which is fine on a bench transducer and not fine in a
vehicle, where the sender wire can find battery. Options, against a 35 V fault:

| Clamp | R3 | Error at full scale | 35 V fault current | |
|---|--:|--:|--:|---|
| 5.1 V zener | 1k2 | **12 mV — 0.30 PSI** | 24.9 mA | what was fitted, and what skewed the readings |
| 5.6 V zener | 1k2 | 1.2 mV — 0.03 PSI | 24.5 mA | knee moved clear, but there is still a knee |
| **BAT54S to the rails** | **10k** | **0.5 mV — 0.01 PSI** | **3.0 mA** | Schottky reverse-biased 0.5 V at full scale; no knee to sit on |
| **Internal clamps only** | **47k** | **0** | **0.63 mA** | no part at all — R3 alone limits pin injection |

⚠ **Rail clamping has a catch worth knowing**: a fault pushes current *into* the
5 V rail, and a 78xx cannot sink. At R3 = 1k2 that is 25 mA, which would drag
the rail up and take the ATtiny with it. At 10k it is 3 mA, comfortably absorbed
by the ATtiny's own ~5 mA draw. **So the clamp and the resistor have to be
chosen together** — fitting a BAT54S while leaving R3 at 1.2 kΩ would be worse
than no clamp at all.

Either of the bottom two rows wants **C2 = 100 nF** at the pin: the cap feeds the
ADC's sample-and-hold, so the 10 kΩ guidance on source impedance stops applying
and a 10k or 47k series resistor is fine. τ is 1–4.7 ms, which for oil pressure
is instant.

## Still to establish

1. **The regulator's full marking** — which 78xx, and its absolute maximum,
   which is what sets D1's clamping ceiling.
2. **C1's voltage rating** — the value is now known, the rating is not, and on
   the input side that is the number that matters.
3. **Reverse polarity** — a TVS does not protect against it. Is there a series
   diode anywhere, or was the harness simply trusted?
4. Continuity: U1 pins → J2 (confirms ISP and the part's orientation); U1 pin →
   Q1 gate; U1 pin → sender divider; J3 → U1; `12+` → regulator input, and what
   is in between; Q1 drain → `Dash`, source → GND.

## The capacitors

C1 and C3 read **7.9 µF** in circuit, which is what a 10 µF MLCC measures on a
typical meter once tolerance, test conditions and ageing are accounted for. C2
is **100 nF**, sitting at the ADC node — which happens to be exactly what the
replacement clamp options want, so that part of the re-spin is already fitted.

With C2 at 100 nF the sender filter is:

| R3 | τ | Corner |
|--:|--:|--:|
| 1k2 (as built) | 0.12 ms | 1326 Hz |
| 10k | 1.0 ms | 159 Hz |
| 47k | 4.7 ms | 34 Hz |

All three are instant against oil pressure. The higher two also do useful noise
rejection in an engine bay, which the 1.3 kHz corner does not.

### Two things the value does not tell us

**C1's voltage rating matters more than its value.** A 10 µF X5R 0805 rated 16 V
loses 60–80 % of its capacitance at 12 V bias, so C1 may be **2–4 µF in service**
even though it measures 7.9 at zero bias on the bench. On a 12 V automotive net
the part wants a **50 V** rating — for the derating as much as for the survival.

**There is no cold-crank ride-through, and capacitance cannot buy it.** At a
30 mA load with 3 V of allowed droop, 10 µF holds the input up for **1 ms**:

| Dip | Capacitance needed |
|--:|--:|
| 10 ms | 100 µF |
| 100 ms | 1 000 µF |
| 400 ms | 4 000 µF |

A 7805 needs ~7 V in, and cranking dips last tens to hundreds of milliseconds, so
this is not a capacitor problem. The two real answers are a **wide-input buck**
that keeps regulating down to 6 V, or **accept the reset and stop letting the
lamp depend on the MCU** — which is the High finding below, reached from a
different direction.

## Audit against automotive reality

What is known so far, worst first:

| Finding | Severity | Notes |
|---|---|---|
| **The lamp path depends on the MCU.** Dead or reset ATtiny → lamp **off**, silently | **High** | Worse than the stock switch it replaced, because it fails dark. Cranking is both the moment a 7805 is least reliable and the moment you most want oil pressure. A comparator that pulls the lamp below 12 psi regardless of firmware would make the warning independent again |
| **Q1 is 30 V** on a net tied to battery through the bulb | Medium, on paper | Clamped load dump is ~35 V. *But* the bulb is ~78 Ω hot, so the FET avalanches at 30 V passing only ~64 mA — ~1.9 W in a 160 W part that is explicitly avalanche-rated. It likely clamps the dump itself. A 60 V part costs the same and retires the question |
| **R1 = 10 MΩ** gate pull-down | Low | 100 nA worst-case leakage × 10 MΩ = 1.0 V against a 0.8 V minimum threshold; and C<sub>rss</sub> 355 pF couples ~8.8 % of any drain step onto the gate, bled with τ = R × C<sub>iss</sub> = **40 ms**. 10 kΩ gives 40 µs and clears both by 1000×. In practice harmless here: real leakage at 1 V is picoamps and a lamp's drain does not slew fast. Fails toward lamp-on, which is the forgiving direction |
| **D1's TVS value was never recorded** | Medium | There *was* a TVS, which is the right instinct. But the window is narrow and easy to miss: it must stand off **> 16 V** (charging system plus margin) and clamp **< 35 V** (a 78xx's absolute maximum). SMAJ/SMBJ **18A** clamps at 29.2 V ✓ and **20A** at 32.4 V ✓, while a **24A** clamps at 43 V ✗ — above the regulator's abs max, so it would protect nothing. If the original was a 24 V part it was decorative |
| **Cold crank** | Medium | A 78xx needs ~2 V of headroom and the rail dips to 6 V and below while cranking. C1 gives **1 ms** of ride-through where the dip is 10–400 ms, and no practical capacitor closes that gap — see above. The *reading* survives, because ratiometric sensing cancels a sagging rail; the **MCU** does not, and with it goes the lamp |

## What was right

Worth recording alongside the faults, because the re-spin keeps these:

- **Q1 is logic-level** — R<sub>DS(on)</sub> is specified at V<sub>GS</sub> = 4.5 V
  and V<sub>GS(th)</sub> is 2.0 V max, so a 5 V pin drives it fully on. No linear-region
  problem.
- **Ratiometric sender fed from the board's own 5 V.** If the ATtiny uses V<sub>CC</sub>
  as its ADC reference, regulator error cancels exactly. That is the correct
  architecture, not a lucky accident.
- ISP broken out on a proper 2×3, and a ground pour on the back.
