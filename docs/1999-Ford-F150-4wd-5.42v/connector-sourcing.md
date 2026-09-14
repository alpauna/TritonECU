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

---

# Sensor-side connectors — CKP and CMP

**Ordered: Motorcraft `3U2Z145411SMA`** — "Camshaft Crankshaft Position Sensor
Connector", supplied as a pigtail.

**One part number covering both sensors is itself a useful fact.** It means CKP
and CMP use the same 2-cavity connector, which confirms what
[`vr-conditioning.md`](vr-conditioning.md) records: **both are two-wire VR
sensors.**

## "Single-ended" CMP does not mean one wire

[`eec-v-pinout.md`](eec-v-pinout.md) shows pin 85 as a lone "CMP+" (DK GRN) with
no matching CMP−, which is what made CMP look single-ended. It is not — the
sensor still has two wires. The second one lands on the PCM's **shared sensor
ground** instead of a dedicated CMP− pin.

That is a compromise the factory made to save a PCM pin, and **there is no
reason to inherit it.**

| | Factory | **TritonECU** |
|---|---|---|
| CKP+ (DK BLU) | pin 21 | **VR1+** |
| CKP− (GRY) | pin 22 | **VR1−** |
| CMP signal (DK GRN) | pin 85 | **VR2+** |
| CMP return | tied to shared SGND | **VR2−** — its own leg |

**Route the CMP return wire to VR2−, not to board ground.** The MAX9926's
differential input then does its job on *both* channels, and the CMP channel
stops sharing an IR-drop path with every other sensor return. It costs nothing —
the wire is already in the harness, it just terminates somewhere better.

There is no conflict if that wire also reaches ground elsewhere: VR2− sits behind
5 kΩ into a high-impedance differential input.

## Quantity

**Order three**, not one:

| | |
|---|---|
| CKP, vehicle | 1 |
| CMP, vehicle | 1 |
| **Bench rig** | **1** — so the rig's sensor plugs in rather than being cut into |

The third is the one that is easy to forget and annoying to be without: with a
pigtail on the rig, the same VR board harness moves between bench and truck
unmodified, and nothing gets spliced twice.

## Identify the cavities before crimping

The pigtail arrives with short untagged tails. **Which cavity is which is not
guessable** — check continuity against the sensor, or against the vehicle
harness colours recorded in [`eec-v-pinout.md`](eec-v-pinout.md):

```
CKP+  DK BLU      CKP−  GRY       CMP  DK GRN
```

Polarity is worth getting right but is not fatal if swapped: the MAX9926 is
differential and Mode A2 triggers on the zero crossing, so an inversion moves
which edge the decoder should use rather than breaking detection. Easier to fix
in the harness than in firmware, though — so confirm it on the rig, where the
shaft position is known.

---

# Repinning the 104-pin connector

Terminals ordered, so cavities can be changed or added.

## There are four spare cavities already

[`eec-v-pinout.md`](eec-v-pinout.md) records these as **"Not used"** on this
application — they belong to the 4-sensor HO2S configuration a two-bank truck
does not have:

| Cavity | Factory function on other applications |
|---|---|
| **35** | RR HO2S signal |
| **61** | LR HO2S signal |
| **95** | RR HO2S heater |
| **96** | LR HO2S heater |

**⚠ Verify each is physically empty before counting on it.** That table was built
partly from a MegaSquirt pinout reference, and "not used on this application" in
a document is not the same as "no terminal in this connector". Trim levels
differ. Look in the cavity.

## First use: give CMP its own return

The change recommended above — **CMP return to VR2− instead of shared SGND** —
needs no new wire. The wire already runs from the sensor to the connector; it
just lands in a shared sensor-ground cavity.

**Pull that terminal and move it to one of the spares.** Same wire, same length,
different hole. That is the entire job, and it converts CMP from a compromised
single-ended channel into a proper differential pair.

## The crimp tool matters more than the terminals

This is the part that is easy to get wrong and expensive to diagnose.

**A generic crimper produces a joint that passes a tug test and fails months
later**, under vibration and thermal cycling. On a crank or cam sensor that
presents as an **intermittent no-start that comes and goes with temperature** —
the single worst fault class to chase, because it is absent whenever you are
looking for it.

Get the correct die for Ford micro terminals, and:

- **Match the wire gauge to the terminal's barrel.** Undersized wire in an
  oversized barrel crimps to a joint that is mechanically loose however good the
  tool is.
- **Get the terminal removal pick as well**, not just the terminals. Levering a
  terminal out with a screwdriver deforms the lock tang, and it will not retain
  afterwards — the terminal backs out under vibration, which looks exactly like
  a broken wire.

## Crimp, do not solder

Soldering a harness joint creates a stiffness discontinuity: the wire goes from
flexible to rigid at the edge of the solder wick, and that is where it
work-hardens and cracks. A properly crimped terminal has no such transition.

This is why automotive harnesses are crimped everywhere and soldered almost
nowhere, and a rig that will live on an engine is not the place to break with it.

## Record every repin

A modified harness that matches no factory diagram is a trap for whoever works
on it next, including the person who modified it.

**Log changes in [`eec-v-pinout.md`](eec-v-pinout.md)** — cavity moved from, moved
to, wire colour, and why. The wire colours are already in that table, which makes
it the natural place: a future reader can then diff what is in the truck against
what Ford shipped.
