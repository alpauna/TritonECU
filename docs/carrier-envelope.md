# Carrier board envelope — keeping the EEC-V footprint

**Goal: the replacement drops in where the OEM PCM came out.** The 104-pin
connector is the one part that genuinely cannot be bought, so it drives the
outline rather than the other way round — see
[`1999-Ford-F150-4wd-5.42v/connector-sourcing.md`](1999-Ford-F150-4wd-5.42v/connector-sourcing.md).

**Donor PCM envelope: 158 W × 174 L × 31 H mm.**

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
