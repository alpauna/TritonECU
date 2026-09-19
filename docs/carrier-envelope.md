# Carrier board envelope — keeping the EEC-V footprint

**Goal: the replacement drops in where the OEM PCM came out.** The 104-pin
connector is the one part that genuinely cannot be bought, so it drives the
outline rather than the other way round — see
[`1999-Ford-F150-4wd-5.42v/connector-sourcing.md`](1999-Ford-F150-4wd-5.42v/connector-sourcing.md).

**Donor PCM envelope: 158 W × 174 L × 31 H mm.**

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

### Three levers, cheapest first

| | | Buys |
|---|---|--:|
| **1. Lower the board-to-board stack** | 8 mm instead of 11 mm headers, if the Nucleo's underside and whatever sits beneath it allow | **3 mm** |
| **2. Raise the lid locally** | A bump over the jack only. The enclosure is being **printed** ([`enclosure.md`](enclosure.md)), so this costs nothing but a feature | as much as wanted |
| **3. Put the RJ45 at a wall opening** | Its top sits at 27.7 mm, so it clears — but it must reach an opening to be *usable*, which constrains where the Nucleo can sit | orientation, not height |

**1 and 3 together are probably the answer**, with 2 held in reserve.

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
