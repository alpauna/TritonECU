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
| ⬤ R2 | **1.2 kΩ** | Marking `122` |
| ○ U2 | A 78xx regulator, DPAK | Marking legibly starts `78…`, rest degraded |
| ○ R3, C1, C2, C3, D1, D2 | unread | |

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
   J1 12+ ──?──[ D1/D2 ? ]──?── U2 (78xx) ──┬── 5V ── U1 VCC, J2, J3, J1 5v
                                            └── C1 / C3
   J1 Sensor ──?──[ R2 1k2 ? ]──┬── U1 ADC (PB3 or PB4)
                                └── C2 ?
   U1 PB? ──[ R2 1k2 ? ]──┬── GATE  Q1 KIA2803A ── DRAIN ── J1 Dash
                     R1 10M ──┴── GND              SOURCE ── GND
   U1 PB0/PB2 (USI) ── J3 SDA/SCL
```

R2 is drawn in both candidate roles because one continuity check has not been
done yet: **R2 to Q1's gate, or R2 to J1 `Sensor`?** Both are sensible at 1.2 kΩ
— as a gate series it gives 4.2 mA peak pin current and a 5 µs gate τ; as a
sender filter it sets a corner with C2 and limits a 12 V fault on the sender wire
to ~5.3 mA into the ATtiny's clamp diodes.

## Still to establish

1. **D1 and D2 body codes** — is there reverse-polarity protection, a TVS, or
   just a clamp? This is the biggest unknown on the board.
2. **The regulator's full marking** — which 78xx, and its absolute maximum.
3. C1, C2, C3 values and **voltage ratings**.
4. R3's value and role.
5. Continuity: U1 pins → J2 (confirms ISP and the part's orientation); U1 pin →
   Q1 gate; U1 pin → sender divider; J3 → U1; `12+` → regulator input, and what
   is in between; Q1 drain → `Dash`, source → GND.

## Audit against automotive reality

What is known so far, worst first:

| Finding | Severity | Notes |
|---|---|---|
| **The lamp path depends on the MCU.** Dead or reset ATtiny → lamp **off**, silently | **High** | Worse than the stock switch it replaced, because it fails dark. Cranking is both the moment a 7805 is least reliable and the moment you most want oil pressure. A comparator that pulls the lamp below 12 psi regardless of firmware would make the warning independent again |
| **Q1 is 30 V** on a net tied to battery through the bulb | Medium, on paper | Clamped load dump is ~35 V. *But* the bulb is ~78 Ω hot, so the FET avalanches at 30 V passing only ~64 mA — ~1.9 W in a 160 W part that is explicitly avalanche-rated. It likely clamps the dump itself. A 60 V part costs the same and retires the question |
| **R1 = 10 MΩ** gate pull-down | Low | 100 nA worst-case leakage × 10 MΩ = 1.0 V against a 0.8 V minimum threshold; and C<sub>rss</sub> 355 pF couples ~8.8 % of any drain step onto the gate, bled with τ = R × C<sub>iss</sub> = **40 ms**. 10 kΩ gives 40 µs and clears both by 1000×. In practice harmless here: real leakage at 1 V is picoamps and a lamp's drain does not slew fast. Fails toward lamp-on, which is the forgiving direction |
| **Input protection unknown** | ? | Until D1/D2 are read this is the open question. A 78xx with no TVS ahead of it is what dies first on a vehicle |
| **Cold crank** | Medium | A 78xx needs ~2 V of headroom. The rail dips to 6 V and below while cranking, so the 5 V rail — and with it the sender supply *and* the ADC reference — collapses exactly when the reading matters |

## What was right

Worth recording alongside the faults, because the re-spin keeps these:

- **Q1 is logic-level** — R<sub>DS(on)</sub> is specified at V<sub>GS</sub> = 4.5 V
  and V<sub>GS(th)</sub> is 2.0 V max, so a 5 V pin drives it fully on. No linear-region
  problem.
- **Ratiometric sender fed from the board's own 5 V.** If the ATtiny uses V<sub>CC</sub>
  as its ADC reference, regulator error cancels exactly. That is the correct
  architecture, not a lucky accident.
- ISP broken out on a proper 2×3, and a ground pour on the back.
