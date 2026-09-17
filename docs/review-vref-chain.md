# VREF chain review — pre-schematic

Review of the VREF output chain as specified in
[`vref-supply.md`](vref-supply.md), **before it is drawn**. Nothing is committed
to copper yet, which is the cheapest moment for this.

```
LTC4364 rail ─► NCV8772C ─► TPS2H160B ─┬─► LM74700 + DMN6040 ─► TVS ─► PPTC ─► A-20
   14 V nom      5.00 V     dual switch │      ideal diode      SMAJ   NSHT050    │
   27–30 V clamp                        └─► (ch2, identical) ────────────────► C-20
```

---

## 1. IMPORTANT — the PPTC's 16 V rating is exceeded by a compound fault

`MF-NSHT050KX` is a **16 V** part. Once tripped it holds off the difference
between the shorted-to circuit and the TVS clamp:

| Shorted-to circuit | Tripped PTC holds off | |
|---|--:|---|
| 14 V, normal running | 7.2 V | ✅ inside 16 V |
| 27 V | 20.2 V | ❌ **exceeds** |
| 35 V, load dump on that circuit | 28.2 V | ❌ **exceeds** |

A VREF wire shorted to a truck circuit **while that circuit sees a load dump**
overstresses the PPTC. It is a compound event, but not an exotic one — a chafed
loom does not care what else is happening.

Note the clamp does not rescue it: once the PTC trips its resistance rises to
kΩ, current falls, and the far-side node is held at the TVS clamp while the
near side sits at the fault voltage. The full difference lands across the PTC
and stays there.

**The trade is unpleasant**, which is why it is flagged rather than fixed:

| Part | V<sub>max</sub> | I<sub>hold</sub> | |
|---|--:|--:|---|
| NSHT035 | **30 V** | 0.35 A | only 1.4× the switch's 250 mA limit — derates into nuisance-trip territory |
| **NSHT050** | 16 V | **0.50 A** | 2× the limit, but the rating above |

Options, none free:

1. **Accept it** as a compound-event risk and record it. The PTC is a backstop
   for a switch that has failed short — already a second fault.
2. **NSHT035** and resolve the derating question first — it is already a
   `[CONFIRM]` in `vref-supply.md`. If 0.35 A holds above 250 mA at worst-case
   ambient, this becomes free.
3. **Drop the PPTC.** With the ideal diode blocking reverse and the switch
   limiting forward, its only remaining job is switch-fails-short.

**Recommendation: resolve the NSHT035 derating question, because it may make
option 2 free.** That measurement now decides two things instead of one.

---

## 2. ~~IMPORTANT~~ FIXED — the feed divider will exceed the ADC input

The per-feed short-to-battery divider feeds an STM32 internal ADC. At a
plausible 100 kΩ / 27 kΩ:

| Feed at | ADC sees | |
|---|--:|---|
| 5 V, healthy | 1.06 V | ok |
| 14 V, short to battery | 2.98 V | ok — this is what it is for |
| **27 V**, short during a load dump | **5.74 V** | ❌ **over V<sub>DDA</sub> + 0.3** |

Same defect as the `CS` pin, and it needs the same treatment: **series resistor
plus a Schottky to V<sub>DDA</sub>**, or a larger divider ratio. A larger ratio
costs resolution in the 5 V region where the useful measurement is, so the
clamp is the better answer.

**This was missed because the divider was specified for the 14 V case only.**

> **Fixed 2026-09-17.** Divider is now **100 kΩ / 12.4 kΩ**, scaled so our own
> 27 V clamp lands at 2.98 V rather than so 14 V lands mid-scale, plus a
> **Schottky to V<sub>DDA</sub>**. No series resistor is needed — the 100 kΩ top
> leg is the series element, passing under 1 mA even with the feed at 100 V.
> Source impedance is 11 kΩ, so the ADC wants a long sampling time and a 10 nF
> cap at the node.

---

## 3. ~~The startup window must gate readings, not just faults~~ FIXED

`vref-supply.md` specifies 20 ms of blanking after a channel enable, to stop
inrush being read as a short. The LM74700 datasheet notes that **at startup
current flows through the FET's body diode** until the charge pump establishes
gate drive.

So for that interval VREF sits at roughly **5 V − V<sub>SD</sub> ≈ 4.3 V**, not
5.00 V. Any ratiometric reading taken then is wrong by ~14 %.

**The blanking window must therefore suppress sensor validity too, not only
fault handling.** As written it covers the fault path only.

> **Fixed 2026-09-17, and a timer turned out to be the wrong tool.** Validity is
> now gated on the **measured VREF** instead:
>
> ```
> sensor readings valid  <=>  VREF sense within 4.75 - 5.25 V
> ```
>
> VREF is already on the precision ADC as the ratiometric divisor, so this costs
> nothing and is strictly better than a window — it catches the body-diode
> plateau, and equally a brownout, a sagging regulator, or a channel that came
> up into a fault. None of those would trip a timer. The 20 ms blanking stays,
> for fault handling only.

---

## 4. Which ground do the TVS and dividers return to?

Not specified, and it matters. `vref-supply.md` §"On isolated" is explicit that
VREF returns via **SIGRTN**, with separation of supply and a shared ground at
the star point.

- The **divider** must reference the same ground the ADC references, or the
  measurement carries the offset between them.
- The **TVS** wants the lowest-impedance path for transient energy, which argues
  for power ground — but a SIGRTN-to-power-ground offset then appears across it,
  and this truck has **three separate SIGRTN pins** (A-17, B-17, C-17).

**[DECIDE]** before layout. This is the kind of thing that is free to get right
on a schematic and expensive afterwards.

---

## 5. Checked and correct

Recorded because a review that only lists problems does not say what was
examined.

| | |
|---|---|
| **Negative transient vs the LM74700's −5 V CATHODE-to-ANODE minimum** | Looked like a violation: a bidirectional TVS clamps the feed at −6.67 V, which against a 5 V ANODE is −11.7 V. It is not. The FET body diode conducts ANODE→CATHODE and pins the differential near −0.8 V, and the switch's 250 mA limit sits between the 5 V rail and ANODE — bounding the current and letting ANODE sag with CATHODE |
| **Body diode current in that event** | ≤ ~250 mA, set by the switch's limit, against the DMN6040's 2.1 A continuous rating |
| **Logic pins while the rail is gated off** | `IN1`, `IN2`, `DIAG_EN`, `SEL` have **100–230 kΩ internal pulldowns**, so leaving GPIOs high-impedance is safe. Driving them low is belt-and-braces, not a requirement |
| **LM74700 quiescent current** | Derived from ANODE, which is the switch output — so its 80 µA flows only when a channel is on, and never against the always-on budget |
| **Feed node when a channel is off** | Floats; the divider is the only discharge path, τ ≈ 130 ms against ~1 µF of sensor capacitance. This is a feature: with the channel disabled, a divider still reading 14 V proves the short is in the harness rather than inside the box |
| **TVS during normal startup** | Feed ramps 0→5 V against a 6.0 V standoff; never conducts |
| **FET V<sub>DS</sub> in a short to battery** | TVS clamp minus rail ≈ 2 V, against a 60 V part |

---

## Summary

| # | Finding | Action |
|---|---|---|
| 1 | PPTC 16 V rating exceeded by short-to-battery during a load dump | resolve the NSHT035 derating `[CONFIRM]` — it may make the 30 V part free |
| 2 | ~~Feed divider presents 5.7 V to the ADC at 27 V~~ | **FIXED** — 100 k / 12.4 k + Schottky |
| 3 | ~~Startup blanking covers faults but not reading validity~~ | **FIXED** — validity gated on measured VREF, not a timer |
| 4 | TVS and divider ground return unspecified | `[DECIDE]` before layout |

Two of the four are the same class of error — **a protection element specified
against the nominal fault and not against the fault coinciding with a load
dump.** Worth checking the rest of the board for the same pattern.
