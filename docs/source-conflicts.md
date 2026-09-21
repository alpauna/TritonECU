# Where the sources disagree

Two kinds of document describe this truck's electrics, and they do not always
agree. When they conflict, this file records it rather than letting whichever was
read most recently win.

| Source | What it is | Trust for |
|---|---|---|
| `1999-Ford-F150-4wd-5.42v/*.png` | Ford **EVTM** sheets — circuit numbers (911, 224, 31), connector IDs (C236, C251), module pin numbers | Year-specific detail |
| `1997-2003 Ford Electrical_000332.pdf` | **Chilton-style** chassis wiring, 22 pages, no text layer | Orientation, wire colours, module-level topology |
| `ford-f150_1997-2004.zip` | Chilton HTML rip, **missing chapters 4 and 5** | Little — the chapters with the PCM pin charts are absent |

The Chilton set is a **composite across 1997–2003 and several models**. Ford
changed cluster architecture during that span — early clusters were more
discretely wired, later ones multiplexed — so a Chilton page can be perfectly
accurate for a 1997 truck and wrong for this one.

## Conflict 1 — is the MIL a discrete PCM output?

**This one has teeth**, because [`v1-scope.md`](v1-scope.md) and
[`output-drivers.md`](output-drivers.md) both depend on the answer.

| Source | Says |
|---|---|
| `schematic-findings.md` §10–11, from the EVTM cluster sheets | The cluster's only PCM connection is **SCP**. The MIL is driven by the cluster's own micro. "Lighting the check-engine lamp is an SCP message, not an output" — and a TBD62083AFNG channel was freed on that basis |
| Chilton p. 12-38, *Instrument panel warning system — pick-up models* | **MALFUNCTION INDICATOR LAMP → PNK/LT GRN → POWERTRAIN CONTROL MODULE.** A discrete wire, drawn unambiguously |

**Why it matters now:** the ECU drives a CEL on expander pin 202 with the new
three-tier logic. If the MIL is SCP-only on this truck, **that pin lights
nothing** and the tiers need an SCP message instead. If it is discrete, the wire
is already there and the work is done.

**Test:** at the cluster connector, look for a **PNK/LT GRN** wire and check
continuity to the PCM. Colour is the discriminator — the trans-control indicator
on PCM pin 12 is **WHT/LT GRN**, a different circuit that is easy to confuse with
it.

## Resolved — the O/D indicator is PCM pin 79

`eec-v-pinout.md` and `dash-modules.md` both said pin **12**;
`schematic-findings.md` said **79** and doubted itself. `4R70W-Transmission.png`
draws the circuit end to end: `911 WH/LG` from the Transmission Control Indicator
Lamp through C251 and C158 to **PCM pin 79**, with an **820 Ω** series resistor
inside the switch assembly and 12 V (start or run) arriving via `640 RD/YE` and
splice **S225**. The switch is separately on pin **29** via `224 TN/WH`.

`eec-v-pinout.md` has the right wire colour and the wrong pin — a transcription
error, most likely from a generic EEC-V table. **This is the rule below working:
the EVTM outranks derived notes, and counting sources is not weighing them.**

## Conflict 2 — what is on PCM pin 79? ⚠ **highest stakes so far**

| Source | Says pin 79 is |
|---|---|
| EVTM `4R70W-Transmission.png`, read at the pin row | **Transmission Control Indicator Lamp**, `911 WH/LG`, a low-side sink |
| `eec-v-pinout.md` line 108, and its coil summary | **Ignition Coil 8**, IGNH, `WHT/RED` |
| **The truck**, photographed at the connector | a **white/RED** wire — which matches coil 8, not the lamp |

Both cannot be true of the same connector, and **this is the dangerous kind of
disagreement**: a replacement ECU that drives a coil output onto a lamp circuit,
or sinks a lamp driver onto a coil primary, destroys something on the first key
cycle.

`eec-v-pinout.md` has already been wrong once here — it placed the trans
indicator on pin 12 when the EVTM shows 79 — and its coil list (`26, 104, 52, 53,
27, 1, 78, 79`) is internally consistent with that error, which is how such
things survive. The EVTM is Ford's own and is drawn for this truck's
transmission. It is the stronger source, but the cost of being wrong is high
enough to warrant measuring.

### Truck observation, 2026-09-21

`Pin79-Question.png`, photographed at the PCM connector: the wire in question is
**white with a RED stripe** (builder's reading, on a faded 25-year-old harness —
the photo itself is flash-washed and every pale wire in it measures hue ≈ 39°, so
the colour call is the builder's, not the camera's).

**`WHT/RED` is coil 8.** If that cavity is genuinely 79, then `eec-v-pinout.md`
is right and the EVTM's pin callout is wrong for this truck — and the wrong-sheet
escape is closed: [`transmission.md`](1999-Ford-F150-4wd-5.42v/transmission.md)
confirms this truck is **4R70W, 4×4**, which is the sheet that shows 911 WH/LG
at 79.

**Still open: how the cavity was identified as 79.** Counted against the moulded
numbers, or inferred? That is the whole question now.

**The test that needs no colour and no counting — follow the wire.** Coil 8's
wire runs *out to a coil on the engine*. The indicator wire runs *into the cabin*
to C251 on the column. Twelve inches of tracing separates them absolutely, on a
harness where every pale wire has faded toward tan.

⛔ **Until that is done, nothing gets wired to pin 79.** If it is coil 8, a lamp
sink there meets a coil primary.

## Conflict 3 — who drives the 4×4 LOW RANGE indicator?

| Source | Says |
|---|---|
| EVTM `InstramentCluster3.png`, in its own callout | *"LOW Range indicator is controlled by the PCM. When the switch is activated in LOW Range, a ground is given to the LOW indicator."* |
| Chilton p. 12-38 | 4×4 LOW RANGE → **BRN/YEL → GENERIC ELECTRONIC MODULE (GEM)** |

Lower stakes — the ECU does not drive this lamp either way — but it bears on
whether PCM pin 14 (`784 LB/BK`, 4×4 low **input** from the GEM) is the whole
GEM↔PCM interface, which [`gem-module.md`](1999-Ford-F150-4wd-5.42v/gem-module.md)
claims. If the PCM also *drives* the indicator, there is a second wire.

## What the PDF did settle

Not everything it touched was a conflict:

- **No O/D OFF indicator appears in the cluster** on p. 12-38 either — the same
  absence found across three EVTM cluster sheets. That corroborates the lamp
  living at **C251**, in the switch pod. See
  [`dash-indicators.md`](dash-indicators.md).
- **The engine oil pressure switch feeds the cluster's oil pressure gauge**,
  matching the EVTM and the polarity already confirmed on the bench.

## Rule of thumb

**Prefer the EVTM for anything with a pin or circuit number. Prefer the Chilton
for "what is connected to what" when the EVTM sheet for that system is missing.
When they disagree on architecture, measure the truck.**
