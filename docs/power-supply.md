# Power supply

## Current budget first — it decides the topology

| Load | 5 V rail draw |
|---|---|
| ESP32-P4 at 400 MHz + 32 MB PSRAM (via its 3.3 V regulator) | ~350–500 mA |
| ESP32-C6 module, peak TX | ~300 mA |
| SD card, peak | ~100 mA |
| AD7606 (110 mW) | ~25 mA |
| MAX9926 ×2 | ~20 mA |
| 74HCT541, MCP23S17 chain | ~20 mA |
| Sensor pull-ups | ~50 mA |
| **VREF** | **~25 mA** |
| **Total, realistic peak** | **~1.5 A** |

**Not 3 A.** That matters, because it removes the only argument for
interleaving.

Note this table is the *5 V-equivalent* load. Once the P4, C6 and SD card are
fed by a 3.3 V buck rather than directly, the actual draw on the SEPIC falls
further — see the rail tree below.

## Two-phase: no

The earlier SEPIC study established what a second phase actually buys — and it
was never efficiency. The two designs came within half a point at every
operating point. What it buys is **fault current halved per component**, output
ripple halved, and low-line losses spread across two packages.

All three matter at 3 A. **None of them matter at 1.5 A.**

What a second phase costs is the thing being optimised for here:

- Twice the inductors, switches and diodes — the parts that actually fail.
- Current sharing that the LM3481 datasheet does not specify, so it has to be
  designed and then trusted.
- A clock generator and phase relationship to get right.

**In a vibration and thermal-cycling environment, part count is the enemy of
reliability.** A second phase roughly doubles the switching component count to
solve problems this load does not have. Single phase is the more reliable
choice here, not the compromise.

## Topology: a SEPIC or buck-boost is genuinely justified

Not because of the upper end — a buck handles load dump fine — but because of
**cranking**.

The ECU must keep running while the starter is turning, since that is exactly
when it is controlling fuel and spark. A tired battery on a cold morning can
pull the rail at the ECU down to **6 V or below** after harness drop. A 5 V
buck runs out of duty cycle there and the ECU browns out at the worst possible
moment.

So the input range that matters is roughly **6 V to 40 V**, and it has to hold
5 V across all of it. That is a SEPIC or a four-switch buck-boost.

## Controller: LM5155-Q1 — decided

| | |
|---|---|
| Input range | **3.5 V – 45 V**, 50 V transient |
| Qualification | **AEC-Q100 Grade 1, −40 to +125 °C** |
| Topologies | boost, SEPIC, flyback |
| Max duty | 93 % |
| Switching frequency | 100 kHz – 2.2 MHz, programmable |

The **3.5 V minimum is the headline for this application** — it covers the
worst cranking sag with enormous margin, which is the whole reason a SEPIC was
chosen over a buck.

It is a **controller with an external switch**, not an integrated converter, so
output current is set by the FET, inductors, diode and thermal design rather
than by the IC.

## 4 A: yes, and here is what changes

Achievable, and the existing 3–30 V design already handles comparable switch
stress — at 3 V in and 3 A out it drew 5.9 A of input current, which is harder
than 4 A out from 6 V.

At the worst realistic corner, **6 V in, 4 A out**:

```
D    = Vout / (Vin + Vout) = 5 / 11        = 45 %
Iin  = Pout / (η · Vin)    = 20 / (0.85·6) = 3.9 A
```

In a SEPIC the switch and diode both carry **IL1 + IL2**, so:

| | |
|---|---|
| IL1 (input inductor), average | ~3.9 A |
| IL2 (output inductor), average | 4.0 A |
| **Switch and diode peak** | **~10 A** with ripple |

What that costs:

- **Magnetics get large.** Two inductors rated for ~10 A saturation.
- **Thermal.** 20 W out at 85 % is **3.5 W dissipated**, needing real copper
  pour. Helped considerably by the ECU living in the cabin rather than the
  engine bay.
- **The input path must carry 3.9 A at low line** — the P-FET, the resettable
  fuse and the TVS all sized for that, not for the 1.5 A the rail actually
  delivers.
- **Light-load efficiency suffers.** Against the ~1.5 A budget, a 4 A design
  runs at 37 % load for its whole life.

Worth being deliberate about *why* 4 A rather than defaulting to it: 2.7×
headroom over the measured budget is generous, and the cost is size, heat and
the input-side ratings. **2.5 A would give a comfortable 1.7× margin at
noticeably smaller magnetics.** If the extra is earmarked for something
specific — a display, more sensors, powering something external — 4 A is a fine
call; if it is general headroom, 2.5 A buys most of it for less.

## Overvoltage: a surge stopper, not a crowbar

The LM3481 works and there is already a validated 3–30 V design for it in
`~/Claude/3-30-sepic-3A-DCtoDC`, which is worth reusing rather than starting
over.

But for something going in a truck, **[CONFIRM]** whether the LM3481 is
AEC-Q100 qualified — it is a long-established general-purpose part and it may
not be. The **LM5155-Q1** is a modern automotive-qualified boost/SEPIC/flyback
controller covering the same job, and qualification here is not box-ticking: it
is the difference between a part characterised to 125 °C with known behaviour
under automotive transients and one that is not.

Reusing the existing design at a lower current is otherwise sound — derating a
3 A design to 1.5 A improves margin everywhere.

## Rail tree

VREF draws from the main rail — it has to, since it must hold up through
cranking and that is the only rail that does. But it goes through its own
regulator, not a tap.

```
 12 V ─[PTC]─[P-FET]─[TVS]─[surge stopper]─► LM5155-Q1 SEPIC ──► 6.0 V main
                                                                     │
        ┌────────────────────────────────────────────────────────────┤
        │                                                            │
   Buck → 3.3 V                LDO → 5.0 V digital        LDO → 5.0 V analog
   P4, C6, SD card             74HCT541, MCP23S17         AD7606 AVDD, MAX9926 x2
   ~900 mA @ 3.3 V             ~30 mA                     ~50 mA
                                                                     │
                                                        LDO → 5.00 V VREF
                                                        ~25 mA, limited to ~150 mA
                                                        harness-facing
```

### Why this shape

- **The big load goes through a buck, not an LDO.** The P4, C6 and SD card all
  run at 3.3 V and together draw the great majority of the power. Taking them
  down with a switcher keeps the dissipation out of the box.
- **Every 5 V load is small**, so every 5 V rail can be a linear regulator.
  With 1 V of headroom from the 6 V main:

  | Rail | Current | Dissipation |
  |---|---|---|
  | 5.0 V digital | ~30 mA | 30 mW |
  | 5.0 V analog | ~50 mA | 50 mW |
  | 5.00 V VREF | ~25 mA | 25 mW |

  All negligible. Linears here are not a compromise — they are free.
- **The AD7606 and the MAX9926s get their own quiet rail**, separate from the
  74HCT541 and the expander chain. Those are digital parts switching eight
  ignition gates; keeping them off the ADC's supply is worth one extra
  regulator.
- **VREF gets its own again**, so a harness fault on VREF cannot pull down the
  ADC's supply. An LDO's PSRR also isolates VREF from the switcher's ripple —
  which matters because every sensor on VREF is ratiometric, so supply ripple
  reads as sensor movement.

### This reframes the 4 A question

Totalling what the SEPIC actually delivers at 6 V:

| | |
|---|---|
| 3.3 V buck input (900 mA at 3.3 V, ~90 % eff) | ~550 mA |
| All three 5 V linears | ~105 mA |
| **Total from the SEPIC** | **~650 mA** |

So the internal ECU load is under **1 A at 6 V, about 4 W** — not 20 W.

Sizing the SEPIC for 4 A is then a decision about **headroom for things not yet
on the board**, not about feeding the ECU. **2 A gives 3× margin** on the real
load at much smaller magnetics and less heat. If 4 A is wanted because
something external will hang off the 5 V rail, that is a good reason — but it
should be a stated load, not a default.

## Two rails, but only one switcher

Requested: a solid 5 V for internal use and a separate 5 V for VREF. Correct
instinct — sensor-supply noise and harness fault current should never reach the
logic rail or the ADC. But it does not need two switching supplies:

```
  12 V ─[protection]─► SEPIC ──► 5.0 V main, ~1.5 A ─┬─► logic, SD, ADC, drivers
                                                     │
                                                     └─► small boost ~7 V
                                                              │
                                                              └─► LDO ──► 5.00 V VREF
                                                                   ~150 mA limit
```

Why this shape:

- **VREF must survive cranking too** — a TPS reading during cranking matters —
  so it has to come from the rail that already holds up, not from raw battery.
- **An LDO is the right regulator for VREF.** At 25 mA it dissipates about
  50 mW, is inherently quiet, and its PSRR isolates VREF from the switcher's
  ripple. Every sensor on VREF is ratiometric, so ripple there reads as sensor
  movement.
- **The small boost exists only to give the LDO headroom.** Roughly 7 V in for
  5.00 V out. It carries 25 mA, so it is a tiny part.
- **Two independent switchers would be worse**, not better — a second switching
  node next to the analog front end is precisely the noise this arrangement is
  trying to avoid.

Current limiting stays per-feed as described in
[`vref-supply.md`](vref-supply.md) — roughly 150 mA electronic limit with a
fault flag, PTC as backstop only.

The instinct that a crowbar must not be fast-acting in a vehicle is exactly
right — and following it to its conclusion argues for a different device.

### Why a crowbar is awkward here

**Load dump is a normal event, not a fault.** ISO 7637-2 pulse 5 on an
unclamped 12 V system reaches tens of volts and lasts up to **400 ms**. Any
crowbar slow enough to ignore short ISO pulses is still far too fast to ignore
a load dump — so it fires during exactly the event it was fitted for.

And when it fires, **the ECU dies.** The crowbar shorts the rail, the engine
stops, and with a *resettable* fuse it stays stopped for as long as the PTC
takes to cool. On a running vehicle that is a stall, not a protection.

There is also a component problem: **a crowbar and a PTC are a poor pair.** A
crowbar is normally sized against a fast fuse that clears in milliseconds. A
PTC takes **seconds**, and the SCR has to carry full short-circuit current for
all of it — which means a much larger SCR than the threshold alone suggests.

### Use a surge stopper instead

An **LT4356-class surge stopper** puts a MOSFET in series and holds it in
*linear* regulation during an overvoltage, clamping the downstream rail while
the surge passes:

- **The ECU keeps running.** The rail is limited, not shorted — no stall.
- **It rides out a 400 ms load dump by design**, which is the case a crowbar
  cannot handle gracefully.
- **No fuse event**, so no PTC cooldown.
- It has a fault timer, so a *sustained* overvoltage — a 24 V jump start left
  connected, a failed regulator — shuts the output down properly. That is the
  case a crowbar is genuinely for, and the surge stopper covers it too.
- The same series FET can provide **reverse-polarity protection**, absorbing
  the P-FET.

**[CONFIRM]** an AEC-Q100 variant and its energy rating against the intended
load-dump level.

### Resulting input chain

```
Battery ─► resettable fuse ─► reverse-polarity P-FET ─► TVS ─► surge stopper ─► LM5155-Q1 SEPIC
                                                    (fast transients)   (load dump, sustained OV)
```

Each element covers what the next cannot:

| Element | Handles |
|---|---|
| Resettable fuse | sustained overcurrent, downstream short |
| P-FET | reverse polarity, without a Schottky's permanent drop and heat |
| TVS | fast, high-energy ISO 7637 pulses — nanoseconds to microseconds |
| **Surge stopper** | **load dump (400 ms) and sustained overvoltage, without shorting the rail** |
| LM5155-Q1 | everything from 3.5 V to 45 V, which is most of the job |

The TVS stays: it catches the sub-microsecond pulses faster than any active
device can respond. The surge stopper handles the long events the TVS cannot
absorb thermally.

If a crowbar is still wanted as a genuine last resort, set it **above the
surge stopper's clamp** and pair it with a **fast fuse rather than the PTC** —
at that point it is protecting against the surge stopper itself failing short,
which is a real if unlikely mode.

## What actually determines reliability here

Topology is not the risk. Beyond the input chain above:

- **Cold-crank ride-through** — bulk capacitance sized so the SEPIC has
  something to work with while the rail collapses.
- **Thermal design at the top of the input range.** The worst case for a
  switcher is not cranking; it is 14 V continuous, forever, at whatever the
  enclosure's ambient turns out to be.

An ordinary single-phase SEPIC with those handled will outlast an elegant
two-phase one without them.
