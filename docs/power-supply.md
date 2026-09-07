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

## Controller: consider LM5155-Q1 over LM3481

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

## What actually determines reliability here

Topology is not the risk. The input stage is:

1. **Reverse polarity** — a P-channel MOSFET in the feed, not a series
   Schottky. Same protection without the permanent voltage drop and heat.
2. **Load dump** — a '99 truck has no centralised clamping to rely on. A TVS
   sized for the energy, ahead of everything.
3. **Cold-crank ride-through** — bulk capacitance sized so the SEPIC has
   something to work with while the rail collapses.
4. **Thermal design at the top of the input range.** The worst case for a
   switcher is not cranking; it is 14 V continuous in a hot engine bay, forever.

An ordinary single-phase SEPIC with those four handled will outlast an elegant
two-phase one without them.
