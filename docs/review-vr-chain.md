# VR input chain review — pre-schematic

Review of the crank, cam and shaft-speed conditioning as specified in
[`vr-conditioning.md`](1999-Ford-F150-4wd-5.42v/vr-conditioning.md), with Ford's
diagrams now in the tree. The **board** has already been reviewed —
[`review-vr-v1.md`](review-vr-v1.md) — so this looks at the *chain* and at what
the diagrams changed.

```
CKP (21/22, differential) ─┐
CMP (85, + sensor gnd)     ├─► 2 x 5k per leg ─► 2 x MAX9926, Mode A2 ─► STM32
OSS (84)                   │
transfer case (7)         ─┘
```

**The conditioning itself checks out** — see §4, which puts numbers on the thing
the roadmap calls the highest-risk item in the project. The findings are about
what feeds it.

---

## 1. ~~IMPORTANT — the diagram appears to show CMP with a 12 V feed~~ CLOSED — CMP is VR

The tree resolved this confidently:

> [`vr-conditioning.md`](1999-Ford-F150-4wd-5.42v/vr-conditioning.md):
> **CMP is VR — confirmed by the owner.** Pin 85 shows a lone "CMP+" with no
> [CMP−] … returns on sensor ground (pin 91, SGND)

Ford's `EngineControls6.png` shows connector **C100** with:

| Conductor | |
|---|---|
| **796 LB** | marked **`*12V`**, running to C120 / S138 |
| 795 DG | signal → PCM pin **85** |
| shield (circuit 48) | drained via S199/S101 → **567 LB/YE → PCM pin 25, 0 V** |

**A passive VR returning on sensor ground does not have a 12 V feed.** Either I
am misreading a scanned diagram, or the resolution is wrong and CMP is a powered
— Hall — sensor.

> **[CONFIRM ON TRUCK]**, and it is a two-minute measurement: **ohm the two
> sensor wires**. A VR coil reads a few hundred ohms to ~2 kΩ; a Hall sensor
> reads open. Or key-on and check whether one wire sits at 12 V.

It matters because the two need different hardware:

| If CMP is… | Needs |
|---|---|
| **VR** | a MAX9926 channel, as designed |
| **Hall** | a **digital input with level shifting**, and it **frees a MAX9926 channel** — which §2 has just spent |

The tree's own reasoning for "VR" was that the sensor connector has two pins.
**Two pins is equally consistent with a Hall sensor fed 12 V and returning its
signal**, with the ground arriving via the shield drain — which is exactly what
the diagram shows.

> ### Measured 2026-09-17: **371 Ω. CMP is VR.**
>
> Squarely inside the *"few hundred ohms to about 2 kΩ"* that
> [`eec-v-pinout.md`](1999-Ford-F150-4wd-5.42v/eec-v-pinout.md) gives for a VR
> coil; a Hall sensor would read open. **The tree's resolution was right and my
> reading of the scanned diagram was wrong** — whatever the `*12V` marking
> belongs to, it is not a feed into C100.
>
> The measurement also validates an assumption made silently in §4: the
> attenuation there treated the sensor as an ideal source. At 371 Ω the coil is
> **1.9 % of the series network**, moving attenuation from 76.5 % to 76.1 % and
> leaving the **5.1× cranking margin unchanged**.
>
> **No channel comes back** — so finding 2 stands in full.

---

## 2. The fourth MAX9926 channel is no longer spare

Two documents record it as free:

- `vr-conditioning.md`: *"two MAX9926s with the fourth channel spare"*
- `review-vr-v1.md`: *"Four channels for crank, cam and two spare"*

**It has since been allocated, in a different document.**
[`cooling-fans.md`](cooling-fans.md) §4.4 now takes road speed from the
**transfer case speed sensor** — C199, circuit 1496 PK, **PCM pin 7** — because
it sits downstream of the range box and so is correct in both ranges.

That is a fourth VR input:

| Ch | Signal |
|---|---|
| 1 | CKP (differential, pins 21/22) |
| 2 | CMP (pin 85) — *unless §1 says otherwise* |
| 3 | OSS (pin 84) |
| **4** | **transfer case speed (pin 7)** |

**Four of four. No spare**, and no headroom if a fifth VR input is ever wanted.
This is the same failure mode as the internal ADC in
[`review-analog-chain.md`](review-analog-chain.md) §1 — a resource spent in one
document while another still lists it as available.

---

## 3. The CMP cable is shielded, and nothing in the design terminates the shield

`EngineControls6.png` shows the CMP cable explicitly **shielded**, with the
shield drained through splices S199 and S101 to **567 LB/YE at PCM pin 25**,
marked 0 V.

**Neither `vr-conditioning.md` nor `review-vr-v1.md` mentions shields at all.**

That matters more here than it usually would, because the design's own argument
for the balanced 5 kΩ legs is CMRR:

> *CMRR is the whole reason for using a differential input in an engine bay*

A shield left floating, or drained to the wrong ground, gives that away — and
Ford thought this one cable worth shielding when CKP's is not.

> **[DECIDE]** where the shield drain terminates on our board. It is a
> single-point connection by nature; the question is **which** point, and it
> should not be the sensor-ground net the signal returns on.

---

## 4. Checked and clear — including the number nobody had put on it

[`roadmap.md`](roadmap.md) calls VR at cranking *"the highest-risk item in the
whole project"*, because amplitude is weakest exactly when sync must be
established. The protection resistors attenuate that signal, and **the margin
had never been computed.** It is fine:

```
MAX9926 RIN            65k min          2 x 10k series (both legs, balanced)
attenuation            76.5% through    23.5% lost, worst case
VMIN-THRESH            30 mV max        -> needs 39 mV at the connector
```

| Cranking amplitude | Margin |
|---|--:|
| 200 mV — *"a few hundred millivolts"* | **5.1×** |
| 100 mV — if the estimate is optimistic | **2.5×** |

And there is far more room than the design uses: holding 30 mV from a 200 mV
source allows series resistance up to **368 kΩ**. **We use 20 kΩ — 5 % of the
budget.**

| | |
|---|---|
| **High-rpm transients** | The pin limit is ±20 mA, so 10 kΩ per leg survives **200 V** at the connector. The series resistors are doing exactly the job they were chosen for |
| **Balanced legs** | Already specified, and for the right reason — grounding IN− directly while IN+ sees 10 kΩ would throw away the CMRR |
| **Mode A2 strapping** | Already verified against datasheet Table 1 in [`review-vr-v1.md`](review-vr-v1.md) |
| **TSS not fitted** | The diagrams *do* show TSS wiring (C192, 971 PK/BK → PCM 59) — that is the **4R100** variant. This truck's 4R70W does not have it, as recorded |

---

## Summary

| # | Finding | Action |
|---|---|---|
| 1 | ~~Diagram shows CMP with a `*12V` feed~~ | **CLOSED** — measured **371 Ω**, CMP is VR. My misread of the scan |
| 2 | The "fourth channel spare" was spent by the fan road-speed decision | correct both documents; **no spare** |
| 3 | CMP cable is shielded; no shield termination is specified | **[DECIDE]** the drain point, and not onto sensor ground |

Findings 1 and 2 interacted: if CMP had been Hall it would have handed back
exactly the channel finding 2 spent. **It is not — measured 371 Ω — so the
MAX9926 allocation is full at four, with no spare.** Findings 2 and 3 remain.
