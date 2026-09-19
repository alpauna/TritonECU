# Protection sweep — the two VREF patterns, applied board-wide

[`review-vref-chain.md`](review-vref-chain.md) closed four findings, two of
which shared a cause and a third of which was its own lesson. This sweeps the
rest of the board for the same three shapes.

| | Pattern |
|---|---|
| **A** | protection sized against the **nominal** fault, not against that fault **coinciding with a load dump** |
| **B** | a backstop carried without the arithmetic on whether the current that would actually flow can **reach its threshold** |
| **C** | a policy row naming a part that has since been **superseded** |

---

## A1. ~~Clamp energy rises 4× on the NCV8405A during a load dump~~ FIXED

A low-side driver's clamp absorbs more than the inductor's stored energy —
the supply keeps pushing current during the decay. Total clamp energy is

```
E = 0.5 L I^2  x  Vclamp / (Vclamp - Vsupply)
```

so it rises sharply as the supply approaches the clamp. **Only one of the three
output stages is close enough for it to matter:**

| Driver | V<sub>clamp</sub> | at 14 V | at 35 V | rise |
|---|--:|--:|--:|--:|
| ISL9V3040, ignition | 400 V | 1.04× | 1.10× | 1.1× |
| ZXMS6005DGQ, injector | 60 V | 1.30× | 2.40× | 1.8× |
| **NCV8405A, solenoid** | **42 V** | 1.50× | **6.00×** | **4.0×** |

Against a 1 A / 50 mH solenoid:

| Supply | Clamp energy | Margin on E<sub>AS</sub> = 275 mJ |
|---|--:|--:|
| 14 V, normal | 38 mJ | **7.3×** |
| 35 V, load dump | 150 mJ | **1.8×** |

**The margin is still positive, so this is not a blocking finding** — but it
collapses from comfortable to thin, and **the solenoid inductance it rests on is
unmeasured.** At 100 mH rather than 50 mH the margin is 0.9× and the part is
outside its rating.

> **[MEASURE]** the inductance and hold current of the 4R70W shift solenoids,
> EVAP purge, EGR regulator and IMCC. This is the number the NCV8405A choice
> actually depends on, and nothing in the tree records it.
>
> **Fixed 2026-09-17, and fixing it exposed a larger error.** The loads were
> never classified by drive type. Once they are, most of them cannot clamp at
> all: the **4 HO2S heaters are resistive** and store nothing, and the **PWM
> loads should recirculate through a freewheel diode**, not avalanche. Only the
> **3 on/off shift solenoids** remain exposed — and at a Ford solenoid's real
> ~0.5 A rather than the 1 A assumed here, the load-dump margin is **7.3×**, not
> 1.8×.
>
> The larger error: `output-drivers.md` claimed the NCV8405A's integrated clamp
> satisfied the OEM's *"EPC needs a flyback diode to 12 V"* note. It does not —
> a clamp and a freewheel diode do opposite things, and on a PWM solenoid the
> clamp's fast decay *creates* the ripple it then dissipates, every cycle.
> Corrected, with a per-load clamp strategy table.
>
> Also surfaced: **EPC and TCC have no driver assigned at all.** `v1-scope.md`
> calls them "native PWM", which allocates pins rather than drivers, and the
> NCV8405A channel budget covers neither.

Note the ignition and injection stages are immune for a structural reason worth
keeping: **their clamps sit far above any credible supply excursion.** That is
not luck — 400 V and 60–70 V were chosen for what the load needs, and the
headroom came free. The 42 V part had no such margin to spare.

---

## B1. "PTC acceptable, currents are low" is the VREF error, written as policy

[`harness-protection.md`](harness-protection.md) says of the relay and solenoid
outputs:

> flyback diode across the load + TVS to ground; **PTC acceptable, currents are
> low**

That is the same unexamined assumption that put a PPTC on VREF for three
revisions — *a PTC is a reasonable thing to add here* — without asking whether
the fault current can reach its trip threshold. On VREF it could not, because
the regulator upstream limited below it.

The two chosen drivers behave **differently**, and the policy row covers both:

| Driver | Current in a shorted-load fault | Can a small PTC trip? |
|---|---|---|
| **NCV8405A** | self-limits at **6–11 A** | yes — well above any small PPTC's I<sub>trip</sub> |
| **TBD62083AFNG** | **no current limit at all** — a plain DMOS array; a shorted coil draws whatever the supply gives until thermal shutdown | yes, and here the PTC is the *only* current-based protection |

So the conclusion happens to hold — but for opposite reasons on the two parts,
and the row states it as though one answer covers both. **Rewrite it per driver
rather than per pin type.**

---

## C1. Two policy rows name superseded parts

| Row | Says | Should say |
|---|---|---|
| Relay / solenoid outputs | "flyback diode across the load" | **TBD62083AFNG** and **NCV8405A** both have **integrated clamps** — the external diode is redundant, which was the point of choosing them |
| Analog sensor inputs | "the **AD7606's** own ±16.5 V clamps" | production part is **ADS8588H** with a 9 kV input clamp; the AD7606 is the *bench* part |

Neither is dangerous, but a protection policy that names the wrong part is how
the wrong part gets fitted.

---

## Checked and clear

| | |
|---|---|
| **Input fuse vs the LTC4364's current limit** | Looked like Pattern B exactly: the limiter allows **4.50–5.00 A** and the fuse is **5 A**, which it would never blow. It is not the same error. The fuse's fault case is a **failed pass FET or a harness short upstream of the sense resistor** — precisely where the limiter is bypassed and current is unbounded. And no nuisance-blow risk either: at current limit the LTC4364 shuts down in **54 ms**, far too brief to clear a 5 A fuse |
| **ISL9V3040, ZXMS6005DGQ clamp energy** | rises during a load dump as above, but 1.1× and 1.8× against margins of orders of magnitude |
| **TBD62083AFNG with COMMON on permanent B+** | B+ reaches ~35 V in a load dump; V<sub>OUT</sub> and V<sub>COM</sub> are both rated **50 V** |
| **VREF chain** | swept in [`review-vref-chain.md`](review-vref-chain.md); all four findings closed |

---

## Summary

| # | Finding | Action |
|---|---|---|
| A1 | ~~NCV8405A clamp energy ×4 in a load dump~~ | **FIXED** — loads classified; only 3 on/off solenoids can clamp, margin 7.3×. Exposed a clamp-vs-freewheel error and an unassigned driver |
| B1 | "PTC acceptable" stated per pin type, but the two drivers differ | rewrite `harness-protection.md` per driver |
| C1 | Two policy rows name superseded parts | correct to TBD62083A / NCV8405A and ADS8588H |

**The sweep's own result is worth stating: the pattern did not recur widely.**
Pattern A appears once and is bounded; Pattern B appears once, as policy text
rather than as a fitted part. The ignition and injection stages were immune by
construction, because their clamp voltages were set by what the load needs
rather than by what the fault demands — which left headroom that a 42 V part
never had.
