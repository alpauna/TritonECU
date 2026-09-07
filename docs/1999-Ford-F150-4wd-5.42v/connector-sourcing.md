# Sourcing the EEC-V 104-pin connector

For a plug-and-play ECU the board needs the **PCB-mount header** — the male
half the PCM presents to the harness. Note this is the opposite half from what
is usually sold.

## The problem

The board-mount header is a **controlled Ford part**. Buying it new through
Ford Component Sales requires manufacturer approval, which is not realistic for
a one-off. What is widely sold on eBay and in forums as a "Ford 104 Pin EEC-V
PCM Connector Assembly" is the **harness-side** connector plus dress cover —
useful for building a jumper harness, not for mounting on a PCB.

## Options, roughly in order of practicality

**1. Salvage a scrap EEC-V PCM.** Cut the header off a dead junkyard PCM and
transplant it. This is what most builders do, it is cheap, and the part is
guaranteed correct for the truck. Downsides: desoldering a 104-pin header from
a potted automotive board is tedious, and the pins may need cleaning up before
they will take a new board.

**2. Buy the harness-side connector and build a jumper.** Fit a generic
high-density header on the ECU board and make a short adapter loom to the OEM
connector. This gives up true plug-and-play but removes the sourcing problem
entirely, keeps the ECU board layout free, and makes the ECU usable on other
vehicles later. **Recommended if the goal is a working truck rather than an OEM
appearance.**

**3. rusEFI community PCB designs.** rusEFI has open-source breakout boards for
Ford EEC connectors — the EEC-IV 60-pin board is documented, and there is forum
work on the EEC-V 104-pin. Worth checking their repos for footprints before
drawing one from scratch; a verified footprint for a 104-pin connector is worth
a lot.

**4. Copy what the MS3Pro PNP does.** DIYAutoTune built exactly this product
for exactly this truck. Their PNP unit mates to the OEM connector, so they
solved the sourcing problem. Whether they will say how is another matter, but
the physical part is identifiable from a unit or from photos.

## Before ordering anything

Resolve the **pin numbering** question first. The MegaSquirt sheet numbers
1–104 flat; the Ford power-pin sheet uses connector-relative numbering (A-13,
A-20, B-17, C-17). Those are two different schemes and they have not been
reconciled. Ordering or drawing a footprint against the wrong one produces a
board that plugs in and does the wrong thing on every pin.

**[CONFIRM]** how the 104 pins divide across connectors A, B and C, and which
numbering the schematics use, before committing to a footprint.
