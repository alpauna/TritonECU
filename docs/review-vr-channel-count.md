# ⚠ The VR channel count is one short — TSS was never counted

> ## ✅ DECIDED — **build for the 4R100, run the 4R70W as the test bed**
>
> Design to the superset, validate on what is in the truck. Both questions below
> are resolved in favour of fitting them:
>
> | | |
> |---|---|
> | **Third MAX9926** | ✅ **add it** — TSS plus the first genuine spare |
> | **CCS solenoid channel** | ✅ **add it** — NCV8405A 13 → 14, on **pin 20** |
>
> Cost: **2 GPIOs of 34 spare, one QSOP-16, one SOT-223.** Pin 20 and the two
> free `74HCT541 #2` channels were already there.

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

~~Decide before layout.~~ **Decided: fit it.**

## ⭐ And the MegaSquirt sheet is rehabilitated

That sheet has been the project's cautionary tale — it listed a coast clutch
solenoid on **pin 20** that does not exist on a 4R70W, and
[`output-drivers.md`](output-drivers.md) records the reason: **it was developed
on a 4R100.**

**Building for the 4R100 makes it the right reference again.** Its pin 20 CSS
entry is not an error; it is the 4R100 pinout, and it is now the pin this design
uses for exactly that purpose. The sheet goes from *the thing that misled us* to
*the 4R100 mapping we are building to* — with the caveat unchanged: **every entry
still wants a Ford source behind it.**

## To extract from the 4R100 manual when it is read

The [4R100 rebuild manual](https://www.powerstrokearmy.com/threads/4r100-rebuild-manual-for-the-diy.20642/)
noted in the README should settle these:

| | Why |
|---|---|
| **Solenoid resistances** | The 4R70W's are 20–30 Ω (SSA/SSB), 10–16 Ω (TCC), **2.48–5.66 Ω** (EPC). **If the 4R100's differ, the driver sizing moves** — and TCC is already at 79 % of its minimum-pad limit |
| **Coast clutch solenoid resistance** | A new channel with no number behind it |
| **Range sensor encoding** | Whether it is the same 4-bit digital TR |
| **Anything the 4R70W does not have** | Beyond CCS. The assumption is nothing else; assumptions are what this document exists to catch |
