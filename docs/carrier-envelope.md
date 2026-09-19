# Carrier board envelope — keeping the EEC-V footprint

**Goal: the replacement drops in where the OEM PCM came out.** The 104-pin
connector is the one part that genuinely cannot be bought, so it drives the
outline rather than the other way round — see
[`1999-Ford-F150-4wd-5.42v/connector-sourcing.md`](1999-Ford-F150-4wd-5.42v/connector-sourcing.md).

**Donor PCM envelope: 158 W × 174 L × 31 H mm.**

> **The donor's *case bottom* is reused, not reproduced** — and it is now a
> **requirement**: its metal flange wraps the 104-pin socket on all four sides
> and takes the mating force, which the PCB therefore does not.
>
> **And the upper shell should be metal too** — recreated rather than printed.
> See [§ Why the lid wants to be metal](#-why-the-lid-wants-to-be-metal-and-it-is-not-mainly-the-flange). That
> reframes these constraints: **X–Y is fixed because the bottom is fixed, and
> height is adjustable because only the lid changes.** See
> [`DonorECU/README.md`](DonorECU/README.md).

> ## ✅ DECIDED: 158 × 174 fixed · target 35 mm · **hard ceiling 46.5 mm**
>
> **X–Y stays exactly as it is** so the replacement mounts where the OEM PCM did.
> **Z is adjustable up to 150 % of the original 31 mm**, which retires the RJ45
> problem below and changes the layout strategy — see
> [§ Height, now that it is free](#-height-now-that-it-is-free).

## Area is not the problem

| | | |
|---|--:|--:|
| **Envelope** | **158 × 174** | **27 492 mm²** |
| Nucleo-144 | 70 × 133 | 9 310 mm² — 34 % |
| EEC-V pin field + body keepout | ~110 × 20 | 2 200 mm² |
| Power board V2, as a daughterboard | 76.6 × 46.7 | 3 579 mm² |
| VR board V1, as a daughterboard | ~60 × 40 | 2 400 mm² |
| **Subtotal** | | **17 489 mm² — 64 %** |
| **Left** for 8 IGBTs, 8 injector FETs, 13 × NCV8405A, ADS8588H, 3 × 74HCT541, TBD62083, SCP, VREF chain and routing | | **10 003 mm²** |

And that subtotal is pessimistic, because the power and VR boards **stack**
rather than sitting beside things.

## ⚠ Height is the problem, and it is one component

31 mm outside is about **28 mm internal** after case walls.

| Stack | Sum |
|---|--:|
| Power board V2: carrier 1.6 + header 11 + board 1.6 + **560 µF can 10.5** | **24.7 mm** |
| Nucleo-144: carrier 1.6 + header 11 + board 1.6 + **RJ45 13.5** | **27.7 mm** |
| Nucleo-144 without the RJ45 (USB micro-B, 5.5) | 19.7 mm |

**The Ethernet jack is the binding constraint.** At 27.7 mm of 28 it *fits* —
with essentially zero margin, which is not a design.

There is an irony worth naming: [`v1-scope.md`](v1-scope.md) chose the Nucleo
partly because *"ST-Link, USB console and **Ethernet** all come for free."* **In
a 31 mm case, Ethernet is the most expensive thing on the board.** And Wi-Fi was
dropped deliberately, so Ethernet is the only remote path there is.

~~Three levers~~ — **none of them needed. Height is free, so take it.**
The RJ45 still has to reach a **wall opening** to be usable, which constrains
where the Nucleo sits, but that is orientation rather than height.

## ✅ Height, now that it is free

**The cheap move is to stop stacking boards on boards.** One level only:
daughterboards sit *beside* each other on the carrier, never above. Height is
then the **tallest single stack**, not the sum:

| | |
|---|--:|
| **Nucleo-144 + RJ45** | **27.7 mm** |
| Power board V2 + 560 µF can | 24.7 mm |
| VR board V1 | 18.2 mm |
| *Power board stacked **on** the Nucleo* | *37.3 mm — don't* |

### And it all fits side by side

| | |
|---|--:|
| Four big blocks (Nucleo, connector, power, VR) | 17 489 mm² |
| 8 × ISL9V3040 D2Pak | 1 200 mm² |
| 8 × injector DPAK | 640 mm² |
| 13 × NCV8405A SOT-223 | 650 mm² |
| ADS8588H, 3 × 74HCT541, TBD62083, SCP, VREF chain | 1 100 mm² |
| **Components** | **21 079 mm² — 77 %** |
| **Left for routing and clearance** | **6 413 mm² — 23 %** |

**Comfortable**, with nothing stacked above anything else. That is worth more
than the millimetres it costs: better thermals, and every board stays reachable
for service.

### Recommended: 35 mm outside

| Outside | Internal | Margin over the RJ45 | |
|--:|--:|--:|---|
| 31 mm | 28 | **+0.3 mm** | zero — not a design |
| 33 mm | 30 | +2.3 mm | |
| **35 mm** | **32** | **+4.3 mm** | ✅ |
| 38 mm | 35 | +7.3 mm | buys nothing more |

**4 mm of margin** absorbs header tolerance, a taller capacitor if one gets
substituted, and conformal coat. Past ~38 mm it stops helping and starts
mattering wherever the box mounts.

> **[CONFIRM] the clearance at the mounting location before fixing 35 mm.**
> Growing 4 mm in Z is free on paper and not free in a vehicle.

### The ceiling: 46.5 mm — and what it quietly buys back

**150 % of the original 31 mm.** The target sits 11.5 mm inside it, and that gap
is a *reserve* rather than slack:

| Configuration | Internal | Outside | vs ceiling |
|---|--:|--:|--:|
| **One level — the plan** | 27.7 | **30.7** | +15.8 |
| One level, power board alone | 24.7 | 27.7 | +18.8 |
| **Two levels: power board *on* the Nucleo** | 37.3 | **40.3** | **+6.2** |

**The ceiling makes two-level stacking legal.** At 31 mm it was ruled out at
37.3 mm internal; at 46.5 it lands at 40.3 outside with 6.2 mm to spare.

That matters because **X–Y is the thing being held constant.** If the driver
section ever needs area back, the power board can go *above* the Nucleo instead
of beside it and **3 579 mm² returns** — without touching 158 × 174.

**Keep it in reserve, do not design to it.** One level is better thermally and
every board stays reachable for service.

## The measurement that actually decides the layout

**158 × 174 × 31 is the case, not the board.** The PCB inside is smaller, and it
is the *PCB* outline that has to be matched for the donor's mounting to carry
over.

> **[MEASURE] off the donor PCM:**
> - **PCB outline**, and where its mounting holes sit
> - **where the connector's pin field sits relative to that outline** — this is
>   the datum everything else is placed from
> - **internal clear height** above the PCB, board face to lid
> - **how the board is retained**, and whether the case is potted

## Two things to decide early, because they move everything

**Is the OEM case reused, or is the enclosure printed to the same envelope?**
[`enclosure.md`](enclosure.md) already places the ECU **in the cabin behind the
glovebox** with the connector face through the firewall — which is *not* where
the OEM PCM lived. If the enclosure is printed anyway, 31 mm is a **target**, not
a constraint, and lever 2 is free.

**Thermal.** Eight IGBTs and thirteen low-side drivers in a sealed 158 × 174 × 31
box is a real load, and the cabin location is the thing that makes it tractable.
Worth its own pass against [`output-drivers.md`](output-drivers.md) before the
layout fixes where the heat sources sit.

---

# ⭐ Edge cooling — the OEM's thermal strategy, and it is a placement rule

**The donor's MOSFETs were double-sided-taped to the case at the board's outer
edges.** The case is the heatsink; the board edge is the path to it.

This is the single most constraining thing known about the layout, and it was
free — it comes off the donor rather than out of a datasheet.

## It also answers the divot

Heat leaves at the **edges**, to the side rails. So the centre pan is almost
certainly **clearance, recessed away from the board** — not a thermal boss. The
`[MEASURE]` on its sign still stands, but the expectation has flipped.

## Is there enough perimeter? Yes, comfortably

| | |
|---|--:|
| Perimeter of 158 × 174 | 664 mm |
| Less the connector edge (pin field + body) | −110 mm |
| **Usable edge** | **554 mm** |

| Devices wanting the edge | | |
|---|--:|--:|
| 8 × ISL9V3040, D2Pak | 8 × 10.5 | 84.0 mm |
| 8 × injector FETs, DPAK | 8 × 6.5 | 52.0 mm |
| 13 × NCV8405A, SOT-223 | 13 × 7.0 | 91.0 mm |
| Q1, on the power board | 1 × 10.5 | 10.5 mm |
| **Bodies** | | **237.5 mm** |
| **With 4 mm between parts** | | **357.5 mm of 554** |

**196 mm to spare.** Edge is not scarce — but it has stopped being a free choice
and become a **placement rule**.

## Does it matter? The box sheds ~17 W, but only if the heat reaches it

| | |
|---|--:|
| 8 × ISL9V3040, conduction + switching | 8.0 W |
| 13 × NCV8405A (four are O2 heaters) | 4.5 W |
| Q1 buck-boost pass | 2.7 W |
| Logic, ADC, buffers, VREF | 2.0 W |
| **Total** | **17.2 W** |

At 35 mm tall the case has ~782 cm² of surface. Natural convection at
~10 W/m²K gives **0.78 W/K → a 22 °C rise**, so a 40 °C cabin puts the case at
about **62 °C**. Comfortable.

**The case can shed it. The question is whether the heat reaches the case.** On
FR4 alone a SOT-223 is ~130 °C/W on a minimum pad — 0.35 W is a 46 °C rise by
itself, before any neighbour contributes. **Edge coupling is what makes the
budget work**, not a refinement on top of it.

## Thermal tape is worse than it looks, and Ford used it anyway

| Interface | D2Pak tab | SOT-223 tab |
|---|--:|--:|
| **3M 8810-class tape**, 0.25 mm, 0.6 W/mK | **4.4 °C/W** | **9.2 °C/W** |
| Silicone gap pad, 0.5 mm, 3 W/mK | 1.8 °C/W | 3.7 °C/W |
| Thin gap pad, 0.25 mm, 6 W/mK | 0.4 °C/W | 0.9 °C/W |

Tape is **5–10× worse than a gap pad** — and it was the right call, because even
4–5 °C/W on a D2Pak beats 60–130 °C/W into still air, and tape needs **no
fastener, no clamp bar and no assembly torque**.

**Keep the approach.** Reach for a gap pad where a specific part runs hot. Do not
treat the tape as a compromise: it is the reason the OEM board worked.

### ⚠ The tape is also the insulator — and the IGBT tabs sit at 400 V

A D2Pak tab is the **collector**. On the ISL9V3040 that node is **self-clamped at
400 V** during every spark event ([`output-drivers.md`](output-drivers.md)), so
each of the eight tabs swings to 400 V, 8 times per two crank revolutions, a few
millimetres from a **grounded metal case**.

Bolting a live tab to a grounded case normally costs an insulating pad *and* a
shoulder washer *and* a torque spec. **Double-sided thermal tape is the
insulator**, so one part does both jobs and the fastener disappears entirely.
That — not the thermal number — is why the OEM did it this way.

Two things follow that a gap pad would not have forced:

| | |
|---|---|
| **[CONFIRM] the tape's dielectric withstand** against 400 V repetitive, not just its bulk rating. Thermal tapes are usually specified in kV, so this should pass — but it must be *checked*, because it is now a safety-of-operation item rather than a thermal one |
| **Creepage at the board edge.** The tab is at 400 V and the rail is at chassis. Mind the edge clearance and any conformal-coat holiday along that line |

It also buys something a bolted joint does not: **compliance**. Tape accommodates
board flex and CTE mismatch, where a rigid fastener would put that stress
straight into the tab's solder joint — in a vehicle, under vibration, for years.

## ⚠ The tension this creates with daughterboards

**A stacked daughterboard cannot reach the case edge.** Q1 on the power board
dissipates 2.7 W and would sit in mid-air, coupled to nothing.

| Option | |
|---|---|
| **Put the power stage on the carrier** rather than on a daughterboard | its D2Pak reaches the edge like everything else. Costs the modularity |
| **Bring a thermal path up to it** | a metal bracket or an L-shaped pad from the rail. Ugly, but it keeps the module |
| **Accept 2.7 W on board copper alone** | [`review-power-v1-bom-gerbers.md`](review-power-v1-bom-gerbers.md) measured RθJA ≈ 25–30 °C/W with 737 mm² of copper and 20 vias — **that is ~81 °C of rise, which is already the design** |

**The third is what the power board already does**, and it was reviewed as
adequate. Worth re-checking once the box's internal air is known to sit near
62 °C rather than at ambient.

---

# ⭐ Why the lid wants to be metal — and it is not mainly the flange

Recreating the upper shell in metal rather than printing it. **Three independent
reasons, and the usual one is the weakest.**

## 1. The flange is probably split between the halves

The base carries the lip that seats into the connector. But the socket is
**supported on all four sides**, and a clamshell cannot do that from one half —
**the lid closes the capture.** If so, reusing the base alone is not sufficient:
a printed lid would be the weak side of a joint that takes 104-way insertion
force.

> **[MEASURE] how far the base's side wall rises relative to the board plane.**
> That is what decides how the capture divides between the halves — and, below,
> which half the heat goes into.

## 2. ⭐ Edge cooling assumed the case. A plastic lid halves it.

This is the one that was never stated. [§ Edge cooling](#-edge-cooling--the-oems-thermal-strategy-and-it-is-a-placement-rule)
computed **554 mm of usable perimeter** against **357 mm of devices** — a
comfortable margin — **on the assumption that the case takes the heat.**

**A printed lid takes none of it.** Whether that matters turns on the same
measurement as above: if the base's rails rise past the board plane, devices
couple to the base and nothing changes. If the board sits high and the walls
beside it are lid, **the perimeter available for edge cooling roughly halves** —
and 357 mm of devices against ~277 mm of usable edge does not fit.

**A metal lid removes the question entirely.** The 17.2 W budget keeps its whole
perimeter regardless of where the split falls.

## 3. Shielding, which the design already asked for

[`enclosure.md`](enclosure.md) records *"no wireless, so no antenna window — the
housing **may be metal**, which helps both shielding and the thermal path."*
Eight IGBTs switching a **400 V** collector node and thirteen low-side drivers
chopping inductive loads is not a quiet box. **A metal base with a plastic lid is
a shield with the top missing.**

## And it returns the height freedom

The 35 mm target existed because the donor case is 31 mm and the Nucleo's RJ45
needs 27.7 mm. **A fabricated lid can be any height** — folded sheet aluminium
does not care. The **46.5 mm ceiling** stays the constraint; the OEM's 31 mm
stops being one.

## ✅ DECIDED: folded 5052-H32 aluminium, bent not drawn

**Folded 5052-H32 aluminium**, five faces, screw pattern matching the base's
flange, mating to the same gasket land the OEM lid used. Bent on the 10-ton
press with a shop-made V-block and punch bar — **no die.**

### A 10-ton press is four times what bending needs, and a quarter of what drawing needs

`F/mm = K·t²·UTS / V`, air bend, K = 1.33, V = 8t:

| Material | t | Longest bend (174 mm) |
|---|--:|--:|
| **5052-H32 alu** | 1.5 mm | **1.01 t** |
| 5052-H32 alu | 2.0 mm | 1.34 t |
| 6061-T6 alu | 1.5 mm | 1.37 t |
| Mild steel | 2.0 mm | 2.18 t |

**Under two tonnes for any of them.** Now the same box **drawn** in one hit —
`F ≈ perimeter × t × UTS`, plus ~30 % blank-holder:

| Material | t | Draw + holder |
|---|--:|--:|
| 5052-H32 alu | 1.5 mm | **30 t** |
| 5052-H32 alu | 2.0 mm | 40 t |
| Mild steel | 2.0 mm | **65 t** |

**23–50 tonnes.** A 10-ton press will not draw this box, and a die capable of it
is a serious piece of tooling in its own right.

> ### ⭐ Which means no die is needed at all
>
> **Bending needs a V-block and a punch bar, one edge at a time.** That is a
> shop-made fixture, not tooling. The press is already oversized for it.

### The real design problems are not force

| | |
|---|---|
| **Corners** | A five-sided box from one blank needs the corners notched, then **welded, riveted or overlapped with sealant**. This is a sealed enclosure behind a firewall penetration — an open corner is not an option |
| **Bend allowance** | The flat pattern must account for stretch. K ≈ 0.4 for aluminium; get it wrong and the box is the wrong size in both axes |
| **Material** | **5052-H32**, not 6061-T6. 6061 cracks at tight bend radii; 5052 is the sheet-metal alloy and bends without complaint |
| ⚠ **The connector-end flange** | If the lid carries part of the four-sided capture, **that feature is not a simple bend** — it is the one part that might genuinely want a form die. Settle it with the side-wall measurement above before committing to a flat pattern |

> **Worth pricing the alternative:** a laser-cut and folded one-off in 5052 from a
> sheet-metal shop is typically modest money, and they will hold the bend
> allowance for you. Making it yourself is a fair choice — just make it for the
> right reason, not because 10 tons sounded marginal. It is not.
