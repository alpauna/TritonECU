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

## Conflict 2 — who drives the 4×4 LOW RANGE indicator?

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
