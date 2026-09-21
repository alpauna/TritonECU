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

### New evidence, 2026-09-21 — `InstramentCluster-Interactive.png`

A colourised cluster sheet, and it lands on the EVTM's side:

- The **MALFUNCTION INDICATOR sits inside the cluster**, fed by the *theft
  indicator micro cluster*, alongside LOW OIL/HIGH COOLANT, LOW FUEL, 4×4
  HIGH/LOW, DOOR AJAR and the rest. No discrete wire reaches it.
- The cluster's only link toward the PCM is **C237 pins 1 and 2** —
  `TAN/ORG` and `PNK/LT BLU`, labelled *computer data lines system*. Those are
  circuits 914 and 915: **SCP**.
- **No `PNK/LT GRN` appears anywhere on the sheet.** The Chilton drawing's MIL
  wire has no counterpart here.

That is now two EVTM-family sources against one Chilton composite. The Chilton
set spans 1997–2003 and several models, and early clusters were more discretely
wired — which would explain its drawing being true of *a* truck but not this one.

**Still settle it the way pin 12 was settled**, because paper lost to metal once
already today: back-probe and watch which pin swings when the lamp lights. If
nothing swings, it is SCP.

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

## RESOLVED BY THE TRUCK — pin 79 is Ignition Coil 8

| Source | Said pin 79 is |
|---|---|
| EVTM `4R70W-Transmission.png`, at the pin row | Transmission Control Indicator Lamp, `911 WH/LG` — **wrong** |
| `eec-v-pinout.md` line 108 and its coil summary | **Ignition Coil 8**, IGNH, `WHT/RED` — **right** |
| **The truck** (`Pin79-Question.png`, 2026-09-21) | **white/RED**, in the cavity confirmed by the **moulded number on the back of the 104-pin connector**, cross-checked against pinout placement |

The truck is the arbiter and it is unambiguous: **PCM pin 79 drives ignition
coil 8.** Nothing else may ever be wired there.

### Why this one is worth remembering

The two sources **agree everywhere else they overlap** — 29 (TCS), 92 (BPP), 36
and 88 (MAF), 39 (IAT), 89 (TP). That rules out a numbering-convention mismatch,
which would have made them disagree everywhere. The EVTM sheet simply has a bad
pin callout at this one place, and the "wrong variant" explanation is closed too:
[`transmission.md`](1999-Ford-F150-4wd-5.42v/transmission.md) confirms the truck
is 4R70W 4×4, which is the sheet in question.

### The trust order needs a row above the EVTM

This file previously said "prefer the EVTM for anything with a pin or circuit
number". That was right against *derived notes* and wrong as a general rule:

1. **The truck.** A moulded cavity number and a meter.
2. The EVTM.
3. Derived notes (`eec-v-pinout.md`, `dash-modules.md`, `schematic-findings.md`).

Both of this file's own earlier conclusions about pin 79 were wrong in turn —
first pin 12 by counting sources, then pin 79 by trusting the EVTM over the
derived note that happened to be right. Paper lost to metal.

### And the indicator lamp is C174 pin 12 — also confirmed on the truck

`eec-v-pinout.md` had it right: **pin 12, `WHT/LT GRN`** — which is `911 WH/LG`
under a different transcription. Confirmed at the connector, 2026-09-21.

So on this one circuit the derived note was right **twice** and the EVTM sheet
wrong once:

| | `eec-v-pinout.md` | `4R70W-Transmission.png` | **The truck** |
|---|---|---|---|
| Indicator lamp (TCIL) | pin **12** ✅ | pin 79 ❌ | **pin 12** |
| Ignition coil 8 | pin **79** ✅ | — | **pin 79** |
| O/D switch (TCS) | pin 29 ✅ | pin 29 ✅ | pin 29 |

**This does not demote the EVTM generally.** Those sheets have been right about
everything else they were asked — the oil pressure switch polarity, the cluster's
indicator set, the DTR and OSS pins, the 820 Ω, the flash-for-faults behaviour.
What is established is narrower and more useful: **`4R70W-Transmission.png` has a
bad pin callout at the TCIL**, and a source being authoritative in general does
not make it right in a particular. That is what the trust order above is for, and
why the truck sits at the top of it.

## Colour is not unique — a trap this harness sets twice

`InstramentCluster-Interactive.png` makes something explicit that has already
cost time here: **the same colour appears on unrelated circuits.**

| Colour | Is circuit | At | And also |
|---|---|---|---|
| `WHT/RED` | **31**, engine oil pressure switch | cluster **C236 pin 20** | **Ignition coil 8** at PCM pin 79 |
| `WHT/LT GRN` | **1215**, PATS transceiver TX | cluster **C237 pin 15** | **911**, the TCIL, at PCM pin 12 |

Both pairs were live hazards in this project: `WHT/RED` is what confirmed pin 79
is a coil, and `WHT/LT GRN` is the colour we were hunting for the indicator lamp.
A wire identified by colour alone could have been either member of either pair.

**So: cavity number first, then trace, and treat colour as corroboration only.**

There is a third coincidence of the same kind, harmless but worth knowing: an
**820 Ω** resistor exists *inside the cluster* on pin B19, and a different 820 Ω
sits inside the TCS switch assembly feeding the O/D lamp. Same value, unrelated
parts.

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
