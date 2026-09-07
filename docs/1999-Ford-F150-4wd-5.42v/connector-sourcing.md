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

**3. rusEFI's footprint — verified, and the best starting point.** rusEFI has
a complete 104-pin EEC-V footprint and two boards using it, GPLv3, in
[rusefi/rusefi](https://github.com/rusefi/rusefi):

- `hardware/Breakout_104pin_EEC-V-Connector/` — breakout board
- `hardware/EEC-V-Blank-Board/` — blank board carrying just the connector
- footprint `rusefi_lib:eecv`, symbol `eecv_EEC-V` (104 pins)

Geometry extracted from `eecv.kicad_pcb`:

| Property | Value |
|---|---|
| Pads | 104 through-hole, round |
| Arrangement | **4 rows × 26** |
| Pitch within a row (X) | **3.4 mm** |
| Row-to-row spacing (Y) | **3.0 mm** |
| Row stagger | **1.7 mm** — alternate rows offset by half the pitch |
| Drill | **1.143 mm** (0.045″) |
| Pad diameter | **1.778 mm** (0.070″) |
| Pin field | 101.4 × 9.0 mm |

Numbering runs row by row — row 1 is pins 1–26, row 2 is 27–52, row 3 is
53–78, row 4 is 79–104 — and within each row the pin numbers **decrease** as X
increases, so pin 1 sits at one end and pin 26 at the other.

Note it is a **staggered** 4-row field, not a rectangular grid. Do not
approximate it with a generic 4×26 header; the 1.7 mm offset is what makes it
mate.

**4. Copy what the MS3Pro PNP does.** DIYAutoTune built exactly this product
for exactly this truck. Their PNP unit mates to the OEM connector, so they
solved the sourcing problem. Whether they will say how is another matter, but
the physical part is identifiable from a unit or from photos.

---

## Pin numbering — resolved, with a warning

**Use flat 1–104.** Both the MegaSquirt sheet for this truck and the rusEFI
footprint number the connector 1–104 straight through, and rusEFI's 4 rows × 26
accounts for exactly 104 pins. The two agree, so that is the scheme for this
vehicle.

**The `EEC-V-Power-Pins.png` sheet does not fit this connector and should not be
used for pin assignments on this truck.** It uses connector-relative numbering
(A-13, A-20, B-17, C-17) implying three separate connectors, and its content
contradicts the truck data directly:

- It lists **A-24 through A-27 as all PWRGND**.
- On this truck, pin 25 is ground but **pin 26 is Ignition Coil 1** and pin 27
  is Ignition Coil 5.

Two grounds where four should be, with ignition outputs in their place. No
constant offset reconciles the schemes. That sheet is almost certainly a
different EEC-V variant — the three-connector style used on other applications
— rather than this truck's single 104-pin connector.

What remains valid from it is the *conceptual* content, which is what it was
used for: that the PCM sources VREF, that signal return is separate from power
ground, and that FEPS exists. The **pin numbers** in it do not apply here.

**[CONFIRM]** VREF and SIGRTN against the flat numbering instead: the
MegaSquirt sheet puts VREF at pin 90 and SGND at pin 91.
