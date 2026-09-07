# Harness-facing protection

Every wire leaving the box is an antenna and a fault path. On a 27-year-old
truck with unknown harness history, that is worth taking seriously — but the
right protection differs by pin type, and two obvious moves are actively
harmful.

## Do not put a PTC in series with a coil or injector output

Tempting, and wrong.

The driver is a **low-side switch**: it sits in the load's current path. A PTC
in series is therefore in the **coil primary circuit**, and its resistance
directly reduces the current the coil reaches in a given dwell. A PTC with even
50 mΩ of cold resistance costs real dwell current at 6–10 A, and PTC resistance
**rises with temperature** — so the ignition gets progressively weaker as the
ECU warms up. That is a maddening fault to chase.

They are also far too slow to protect a semiconductor. Seconds, against a
failure that happens in microseconds.

**Use the driver's own protection instead.** The ZXMS6005DGQ has over-current
and over-temperature shutdown built in. The ISL9V3040 is protected by its
clamp, and the firmware's dwell limit governs its current.

PTCs belong on **VREF** and on **low-current signal outputs**, where their
resistance is irrelevant and the fault current is small enough for them to
matter.

## Do not add a TVS below the driver's own clamp

The clamp voltages were chosen deliberately (see
[`output-drivers.md`](output-drivers.md)):

| Output | Clamp | A TVS below it would |
|---|---|---|
| Coil, ISL9V3040 | **400 V** | steal spark energy — the flyback *is* the spark |
| Injector, ZXMS6005DGQ | **60–70 V** | slow the pintle close and over-fuel at idle |

Any external TVS on these pins must sit **above** the driver's clamp, at which
point it is protecting against the driver failing rather than against the
harness — a reasonable thing to want, but not the same job, and a 400 V TVS on
each coil output is a lot of board for an unlikely mode.

## What the outputs actually need: negative-transient protection

The threat the self-protecting drivers do *not* cover is **negative** voltage.
ISO 7637-2 pulse 1 — an inductive load switching off elsewhere in the harness —
is **−100 V for 2 ms**, and it appears on any wire in the loom. Reversed battery
during a jump start does something similar but sustained.

A low-side driver pulled negative forward-biases its body diode (or, on the
IGBT, its emitter-collector path — the ISL9V3040 specifies only 30 V
emitter-to-collector breakdown). Current then flows from the board's ground out
into the harness, through a path never designed to carry it.

**Fit a Schottky from ground (anode) to each output (cathode).**

- Conducts only when the output is dragged below ground, taking the current a
  body diode would otherwise carry.
- **Invisible in normal operation** — the output swings 0 V to +12 V, and up to
  the clamp on turn-off, so the Schottky is reverse-biased throughout.
- Does not touch the flyback clamp, so spark energy and injector close time are
  unaffected.

That single part is the one genuinely useful addition per output.

## By pin type

| Pin type | Protection |
|---|---|
| **Coil outputs** | IGBT internal 400 V clamp + Schottky to ground |
| **Injector outputs** | IntelliFET 60–70 V clamp, over-current and over-temp + Schottky to ground |
| **Relay / solenoid outputs** (fuel pump, EVAP, EGR, IMCC, fan, A/C) | flyback diode across the load + TVS to ground; PTC acceptable, currents are low |
| **VREF** | per-feed electronic current limit ~150 mA with fault flag, PTC as backstop — see [`vref-supply.md`](vref-supply.md) |
| **Analog sensor inputs** | series resistance + clamp. The AD7606's own ±16.5 V clamps do most of this |
| **VR inputs** | 2 × 5 kΩ series per leg into the MAX9926's internal ESD clamps — see the VR document |
| **Digital switch inputs** (brake, A/C, TR, 4x4) | series resistor + TVS + pull-up; they see battery-level signals |
| **Tach / VSS outputs** | series resistor + TVS; these drive the cluster and leave the box |
| **J1850 bus** | already has its own protection network in the transceiver design |

## Grounding, which matters more than any of it

From the EEC-V pinout: the OEM PCM presents **three separate signal returns**
(A-17, B-17, C-17) plus **four power grounds** (A-24 to A-27) plus a case
ground, meeting only inside the module.

Reproduce that. Injector and coil return currents are large and pulsed, and if
they share copper with the sensor returns they will appear as sensor noise —
which is exactly the error the MAF's dedicated return exists to avoid. Star
point inside the box, and nowhere else.
