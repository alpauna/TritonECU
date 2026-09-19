# ⚠ The VR channel count is one short — TSS was never counted

Found while checking what multi-transmission support would cost.

## The gap

**EEC-V pin 59 is `TSS Speed Sensor`, DK GRN/WHT — circuit `970 DG/WH`, the
transmission's turbine shaft speed sensor.** It is on this truck: Ford's
`EngineControls2.png` draws it at C192, and `4R70W-Related-Power-Fuses and
relays.png` confirms pin 59 carries `*970 DG/WH` on the 5.4L.

**It appears in no design document.** Not in
[`v1-scope.md`](v1-scope.md), [`pin-budget.md`](pin-budget.md),
[`1999-Ford-F150-4wd-5.42v/vr-conditioning.md`](1999-Ford-F150-4wd-5.42v/vr-conditioning.md),
[`review-vr-chain.md`](review-vr-chain.md), or the schematic. **Not as an
allocation, and not as a deliberate omission.**

The four channels are spoken for:

| Ch | Signal | PCM pin |
|--:|---|--:|
| 1 | CKP | 21/22 |
| 2 | CMP | 85 |
| 3 | OSS — output shaft | 84 |
| 4 | Transfer case speed | 7 |
| — | **TSS — turbine shaft** | **59** ⚠ **no channel** |

**Five signals, four channels.**

## A naming collision helped it hide

`schematic-ecu-v1.txt` §3 labels the fourth channel **"TSS (transfer case)"**,
and `pin-budget.md` lists the four as *"CKP, CMP, OSS, **TSS**"*. In Ford's
terminology **TSS is the turbine shaft sensor** — pin 59 — while the transfer
case sensor is `1496 PK` on pin 7.

**So the design's paperwork already contains the word TSS, attached to the wrong
sensor.** Anyone auditing the count would tick it off and move on. That is
exactly how it survived a dedicated VR chain review.

> This is the **second** time this number has gone wrong.
> [`review-vr-chain.md`](review-vr-chain.md) §2 records the fourth channel being
> *"described as spare in three separate documents while `cooling-fans.md` was
> spending it on road speed."* **Nothing owned the count then either.**

## What TSS is for, and whether v1 needs it

Turbine speed against engine speed is **converter slip** — the basis for smooth
TCC apply and release, for detecting a failing converter, and for adaptive shift
control.

**Without it**, slip has to be inferred from engine RPM against OSS × gear ratio.
That works, and it is cruder: it cannot distinguish converter slip from a
slipping clutch pack.

**For a first-start, engine-focused v1 it is deferrable.** It is not deferrable
*silently* — and the ECU is meant to run the transmission, which is the half that
wants it.

## The fix costs one package

| | |
|---|---|
| **A third MAX9926** | QSOP-16, dual channel. Gives TSS **and a genuine spare** — the first this design has had |
| One GPIO | 34 spare |
| Connector pin | **59 already exists** |

**Nothing else moves.** The MAX9926's input network already suits everything from
CMP's measured 371 Ω to OSS's specified 450–750 Ω.

## And it matters more with other transmissions planned

A **4R100** also has a turbine shaft speed sensor. Any transmission worth
controlling properly reports input speed. **Designing to exactly four VR channels
makes the 4R70W the only one this board can ever run well.**

## The related, cheaper question: CSS for the 4R100

A 4R100 has **five** solenoids — SSA, SSB, **coast clutch**, TCC, EPC — against
the 4R70W's four. Accommodating it is nearly free, and every piece is already
spare:

| | |
|---|---|
| EEC-V **pin 20** | **free** — it was the 4R70W's phantom CSS |
| **74HCT541 #2** | 6 of 8 used (EVAP, EGR, TCC, EPC, IAC, VSS out) — **2 spare** |
| Driver | one more **NCV8405A**, 13 → 14 |
| GPIO | 1 of 34 spare |

**Decide before layout.** Adding a footprint now is free; adding it after is a
respin.
