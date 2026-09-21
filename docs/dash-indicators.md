# Dash indicators — speaking Ford's language

Two driver-facing lamps, and the rule for both is the same: **the truck should
behave the way the person looking at it expects.** A mechanic who has seen a
hundred F-150s reads these lamps fluently. Inventing new meanings for them
throws that away for nothing.

| Lamp | Stock meaning | Driven by |
|---|---|---|
| **Oil pressure** | Below ~12 psi | `hardware/oil-pressure/` — see that doc for the driver and the watchdog |
| **O/D OFF** | **Steady:** overdrive cancelled. **Flashing:** transmission fault | This document |

## The O/D OFF lamp is the transmission's MIL

That is the part worth preserving carefully. On these trucks a **flashing O/D OFF
lamp is how Ford reports a transmission fault** — a stored DTC, a failed solenoid
circuit, a lost speed signal, limp mode. Engine faults go to the MIL; transmission
faults go here. They are two separate indicators and must not be merged.

So the lamp has three states, not two:

| State | Means |
|---|---|
| Off | Overdrive available, no faults |
| **Steady** | Overdrive cancelled — by the driver's button, or by strategy (tow/haul, overheat, warm-up) |
| **Flashing ~1 Hz** | **Transmission fault.** Takes precedence over steady |

> **To verify on the truck**, rather than trusted from memory: the exact flash
> cadence, and whether this indicator proves out at key-on.

### Where the lamp actually is — settled

**Not in the instrument cluster.** `InstramentCluster2/3/4.png` carry the low
fuel, low oil pressure / high coolant, MIL, 4×4 low and high range, fuel reset,
door ajar and anti-lock indicators — and no overdrive one. `dash-modules.md` has
it: **C251, the transmission control switch assembly, is "29 in, 12 out" — the
O/D switch *and* its indicator lamp.** The lamp is in the switch on the column.

That matters, because `schematic-findings.md` establishes the cluster's only PCM
connection is **SCP**, and the MIL is driven by the cluster's own micro with no
wire to it. Had the O/D lamp been a cluster indicator it would have been an SCP
message, there would be no wire to grab, and the watchdog design below would be
impossible. It is not — it is a **discrete ground-switched LED**, which is also
where the resistor in that circuit lives (the LED's own, per `eec-v-pinout.md`),
so the ECU sinks milliamps.

**PCM pin 12, not 79.** Two independent notes (`eec-v-pinout.md`,
`dash-modules.md`) say the indicator is pin 12; `schematic-findings.md` says 79
and flags that it appears "in no output list in this tree", which reads as its
own doubt. Going with **12 in / 29 for the switch**, and worth a continuity check
at C251 before anything is wired.

> **The cluster's house style is open-to-warn**, which is worth knowing for
> everything else on that connector: the oil pressure switch is *closed* for
> normal, and the anti-lock indicator "receives an **open** from the ABS module
> when there is a fault". The O/D lamp is the opposite — ground-switched to
> illuminate — because it is an LED in a switch pod, not a cluster input.

## What the ECU is missing today

Nothing in the repo touches this. Checked:

- **No lamp output** and **no O/D cancel switch input** anywhere in `src/` or
  `include/`.
- **`TransmissionManager` detects no faults at all.** `_limpMode` exists and
  `setLimpMode()` is public, but it is only ever called from outside — there is
  no internal detection that would ever call it.
- **`TransmissionState` exposes no fault or limp field**, so the dashboard, the
  `/state` JSON and MQTT cannot report one either.

That last point matters more than the lamp: **a lamp that flashes for faults
needs faults to exist first.** The lamp is the cheap half of this job.

## Three layers of work

### 1. The O/D cancel input

A momentary switch on the shift lever, to ground. A `CustomPin` in
`CPIN_INPUT_POLL` with an internal pull-up covers the electrical side; the state
machine is firmware:

- Each press **toggles** the cancel state.
- **It resets to "overdrive enabled" on every key cycle** — that is stock Ford
  behaviour, and a driver who expects it will be surprised by anything else.
  Deliberately *not* persisted to config.

> Verify on the truck: momentary-to-ground is the assumption. Confirm before
> wiring a pull-up to it.

### 2. The lamp driver

Electrically identical to the oil lamp: cluster feeds +12 through the bulb, the
ECU sinks it to ground through a low-side FET. Reuse that design.

**But the flash cannot be an `OutputRule`.** Rules evaluate a threshold to a
boolean — there is no cadence in them. This needs a small piece of firmware that
owns the lamp and takes a mode:

```
    LAMP_OFF
    LAMP_STEADY
    LAMP_FLASH(period_ms)
```

driven from the existing 10 ms task. Worth writing generically, because the MIL
will eventually want the same thing.

### 3. Something for it to flash about

The fault list `TransmissionManager` should detect and latch, each setting a bit
and any of them lighting the flash:

| Fault | Detect by |
|---|---|
| Solenoid circuit open or shorted | Current sense, or a flyback-clamp voltage check on each of SS A–D, TCC, EPC |
| **OSS or TSS lost** | Pulses stop while the engine is running and the trans is in gear |
| OSS/TSS implausible | Ratio outside anything the gear set can produce — the check that catches a sensor lying rather than dying |
| Excessive slip | `slipRpm` beyond threshold with TCC commanded locked |
| **Over temperature** | `overTemp` already exists in `TransmissionState` and currently lights nothing |
| MLPS invalid | Position decodes to a combination the switch cannot produce |
| Commanded gear not achieved | Target vs actual disagree for N shifts |

Each should set a fault bit, latch until cleared, and the serious ones should
call the `setLimpMode()` that is already sitting there unused.

## The ECU-is-dead signature

The heartbeat-gated watchdog in `hardware/oil-pressure/` should drive **this lamp
too**. If the ECU stops pulsing, the transmission is uncontrolled — so lighting
O/D OFF is not a guess, it is the truth.

The watchdog's output is static, so a dead ECU gives **both lamps steady**, which
is a recognisable signature and distinct from either fault on its own:

| Oil | O/D OFF | Means |
|---|---|---|
| on | off | Genuine low oil pressure, ECU alive and reporting |
| off | flashing | Transmission fault, ECU alive and reporting |
| off | steady | Driver cancelled overdrive |
| **on** | **steady** | **ECU is dead** — no heartbeat, nothing is controlling anything |

## What goes in `/state` and MQTT

`TransmissionState` gains `odCancelled`, `limpMode` and a `faultBits` mask, so
the dashboard and `ecu/fault` can say *which* fault is flashing the lamp. A
flashing lamp tells the driver something is wrong; the ECU should be able to tell
the mechanic what.
