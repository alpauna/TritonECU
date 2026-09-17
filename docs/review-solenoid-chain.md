# Solenoid and heater chain review — pre-schematic

Review of the twelve NCV8405A / NCV8408B channels as specified in
[`output-drivers.md`](output-drivers.md), **before they are drawn**. Same
discipline as [`review-vref-chain.md`](review-vref-chain.md), and it includes a
check for the two patterns from
[`review-protection-sweep.md`](review-protection-sweep.md).

```
gate drive ─► NCV8405A / NCV8408B ─► drain ─► load ─► 12 V (VPWR)
                                       ├─► drain-sense divider ─► ?
                                       └─► freewheel diode (PWM loads) ─► 12 V ?
```

---

## 1. ~~IMPORTANT — EVAP and EGR are PWM loads assigned to a port expander~~ FIXED

[`pin-budget.md`](pin-budget.md) lists them among the outputs that live "on the
expander and costing nothing extra":

> fuel pump relay, **EVAP purge, EGR regulator**, IMCC, cooling fan, A/C clutch…

But [`sensors-to-run.md`](1999-Ford-F150-4wd-5.42v/sensors-to-run.md) has both
as **`1 PWM`**, and `output-drivers.md` now requires PWM loads to recirculate
through a freewheel diode precisely *because* they are switched continuously.

**An SPI port expander cannot generate PWM.** Every edge is an SPI transaction —
microseconds of latency, no hardware timing, and jitter from whatever else
shares the bus. Bit-banging a duty cycle through a shift register is not duty
control.

This is a **classification error that predates the driver work**: the outputs
were split into "fast" and "slow" by *current and criticality*, and PWM loads
landed on the slow side because they are neither fast nor critical. They are
still PWM.

**Fix:** EVAP purge and EGR regulator need **native timer pins**, like TCC and
EPC. The pin budget absorbs it — 37 assigned against ~114.

> **[CONFIRM]** whether IMCC is on/off or PWM. It is already flagged in
> `sensors-to-run.md` and it decides which side of this line it falls on.

> **Fixed 2026-09-17.** `output-drivers.md` now classifies every channel by
> **drive type**, and PWM loads take native timer pins: EVAP, EGR, TCC, EPC.
> The expander keeps the heaters, the on/off shift solenoids and IMCC.

---

## 2. ~~IMPORTANT — the gate drive rail is unspecified~~ FIXED

Every dissipation number in `output-drivers.md` — including the
**3.69 A** limit that selected the NCV8408B for EPC — uses R<sub>DS(on)</sub>
**at V<sub>GS</sub> = 5 V**. That is the only condition either datasheet
characterises apart from 10 V on the NCV8405A.

**Neither part specifies R<sub>DS(on)</sub> at 3.3 V.** Both have
V<sub>GS(th)</sub> up to 2.0–2.2 V, so at 3.3 V they conduct but are nowhere near
fully enhanced, and the figure is simply not guaranteed.

| Channel | Driven from | Gate voltage |
|---|---|---|
| Heaters, on/off solenoids | MCP23S17 chain | **rail unspecified** in the tree |
| **TCC, EPC** | **native STM32 timer pins** | **3.3 V — certain** |

So the two channels where dissipation actually matters are the two guaranteed to
have the weakest gate drive.

**The board already has the precedent and the answer.** The ignition stage uses
a **74HCT541 buffer at 5 V** for exactly this reason. A second buffer covers the
native-pin channels — and after finding 1 that is four of them, not two.

> Also note the **2.2 kΩ series gate resistor** proposed for the NCV8408B's
> latched-fault flag forms a divider with its **25.5 kΩ internal gate
> resistance**: 5 V becomes 4.6 V at the gate. Small, but it stacks with this.

> **Fixed 2026-09-17.** A **second 74HCT541 at 5 V** buffers the four native PWM
> channels, with both `OE` pulled up so they are high-impedance at power-on —
> the same part, the same argument and the same interlock as the ignition stage.
> And the **MCP23S17 chain running at 5 V is now a requirement**, not a free
> choice, since the expander-driven channels have no buffer.

---

## 3. ~~IMPORTANT — the drain-sense divider cannot work into a logic input~~ FIXED

`output-drivers.md` specifies drain sensing as "a divider into an expander
input", with the constraint stated but no values. There are no values that work:

```
needs 12.0 V (engine off)  ->  ABOVE VIH = 4.0 V   ratio >= 0.333
needs 14.4 V (charging)    ->  BELOW the 5 V rail  ratio <= 0.347
```

A **4 % window**, before resistor tolerance, V<sub>IH</sub> tolerance or supply
variation. It is not realisable.

The cause is that a logic input forces the threshold into hardware, where the
normal supply range (12–14.4 V) is wider than the gap between "high" and "the
rail".

**Fix: sense into an STM32 internal ADC and put the threshold in software.**

| Drain | ADC sees |
|---|--:|
| 0.2 V, on | 0.02 V |
| 12.0 V, off | 1.13 V |
| 14.4 V, off charging | 1.36 V |
| 35 V, load dump | 3.30 V |

Ratio 0.094 — e.g. **100 kΩ / 10.5 kΩ**. Scaled so a load dump lands at full
scale rather than so 12 V does, which is the
[sweep's Pattern A](review-protection-sweep.md) applied deliberately this time.
**No clamp needed** below 35 V, and the analogue value is a richer diagnostic
than a bit.

Cost: an internal ADC channel per sensed output. **Not all twelve need it** —
the OBD requirement is the four heaters, and EPC and TCC have the gate-current
flag instead.

> **Fixed 2026-09-17.** Specified as **100 kΩ / 10.5 kΩ into an STM32 internal
> ADC**, scaled so a load dump lands at full scale rather than so 12 V does —
> the sweep's Pattern A applied deliberately this time. No clamp needed below
> 35 V. One correction to the note above: the gate-current flag is an
> **NCV8408B** feature, so it covers **EPC only**; TCC is on an NCV8405A and
> needs a PWM-synchronised drain sample like the other PWM channels.

---

## 4. ~~The freewheel diode has no 12 V node inside the ECU~~ FIXED

A freewheel diode goes *across the load*. **We only have one end of the load.**
The solenoid is fed 12 V from the EEC relay out in the harness; only its low
side reaches the ECU, at the driver's drain.

The practical answer is to return the diode to the ECU's own **VPWR** (A-32,
A-33) and let recirculation flow back through the harness. That works only if
the solenoid feed and VPWR come from the same relay — electrically the same
node, separated by harness resistance and inductance.

> **Answered from Ford's diagrams**, and the answer is worse than hoped — but it
> opens a better option. See
> [`schematic-findings.md`](1999-Ford-F150-4wd-5.42v/schematic-findings.md) §5.
>
> The transmission solenoids share **1138 VT/WH** (BJB fuse 24, off the PCM power
> relay); EGR, EVAP and IMCC share **391 RD/YE**. **The PCM's own VPWR is 361 RD**
> — a third branch. **Neither 1138 nor 391 reaches the PCM at all**, so a diode
> returned to VPWR would recirculate out through the connector, across the
> Battery Junction Box and over two fuses.
>
> **28 EEC-V pins are unused.** Bring **1138 and 391 into the ECU** as two
> dedicated freewheel returns — two wires for a local, tight loop serving all
> five PWM solenoids.
>
> **Fixed 2026-09-17: pin 82 for 1138** (adjacent to EPC on 81) **and pin 48 for
> 391** (between EGR on 47 and EVAP on 56). Both also get a divider into an
> internal ADC, which gives EPC's open-loop compensation the *real* solenoid
> supply rather than V<sub>BAT</sub>, and turns a blown BJB fuse 24 into one DTC
> instead of four simultaneous solenoid failures.

The loop area also matters: recirculation current runs out of the ECU, through
the harness, and back. That is a large loop switching at PWM rates — worth
keeping in mind for emissions.

---

## 5. Checked and clear

| | |
|---|---|
| **HO2S heater inrush** | PTC elements draw several amps cold against ~1.5 A hot. The drivers limit at 6–11 A, which is a soft start rather than a fault. Already recorded as a caution, and firmware must not read it as one |
| **Heater ground return** | 4 heaters × ~1.5 A is comparable to the injector and coil currents `harness-protection.md` already routes to PGND. Same treatment, not SIGRTN |
| **E<sub>AS</sub> on the PWM channels** | NCV8408B's 185 mJ is lower than the NCV8405A's 275 mJ, but with freewheel diodes the clamp should never engage. Only matters if a diode opens |
| **Sweep Pattern A** (clamp energy in a load dump) | already applied to this chain — it is what produced the per-load clamp strategy |
| **Sweep Pattern B** (backstop that cannot trip) | no PTCs or fuses on these channels; protection is the drivers' own current limits, which act by construction |

---

## Summary

| # | Finding | Action |
|---|---|---|
| 1 | ~~EVAP and EGR are PWM but assigned to an SPI expander~~ | **FIXED** — native timer pins; channels now classified by drive type |
| 2 | ~~Gate rail unspecified; thermal budget assumed 5 V~~ | **FIXED** — second 74HCT541 at 5 V; expander chain at 5 V now required |
| 3 | ~~Drain-sense divider into a logic input has a 4 % window~~ | **FIXED** — 100 k / 10.5 k into an internal ADC |
| 4 | ~~Freewheel diode has no in-ECU 12 V node~~ | **FIXED** — 1138 on pin 82, 391 on pin 48, both sensed |

Findings 1 and 2 share a root: **outputs were classified by speed and current,
and PWM is neither.** EVAP and EGR landed on a port expander, and the two
channels that most need gate drive got the weakest. Classifying by *drive type*
— which [`output-drivers.md`](output-drivers.md) only started doing when fixing
the clamp-versus-freewheel error — catches both.
