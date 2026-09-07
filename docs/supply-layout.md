# SEPIC layout at 2.2 MHz

Moving to 2.2 MHz clears the AM band, which was the point. It does **not** make
EMI easier — it makes layout the dominant term.

Radiated emission from a switching loop scales with **loop area × di/dt ×
frequency²**. Pushing the fundamental up by 5.5× raises every harmonic with it,
and small structures radiate far more efficiently at high frequency. A loop that
was acceptable at 400 kHz is not acceptable at 2.2 MHz.

**The layout is the design here, not a detail after it.**

## The hot loop

A SEPIC's critical loop is the one that carries current with fast di/dt at the
switching transition — when the switch turns off and current commutates to the
diode:

```
  switch drain ─► Cs ─► diode ─► Cout ─► back to switch source
```

That loop's **physical enclosed area is the antenna**. Everything else in the
power stage is secondary.

There is a useful precedent: the earlier SEPIC PCB review in
`~/Claude/3-30-sepic-3A-DCtoDC/design/layout-review.md` measured hot-loop areas
directly from the Gerbers across three revisions and got the total down from
**297 mm² to 117 mm²**.

**117 mm² was good at 200 kHz. It is not good at 2.2 MHz.** Target well under
**50 mm²**, and measure it rather than eyeball it — the same numerical approach
applies and there is already a tool for it.

## Rules that follow

1. **Cs, the diode and Cout share the tightest possible triangle** with the
   switch. Place these first; everything else routes around them.
2. **Unbroken ground plane directly beneath the switching stage**, on the
   adjacent layer. A split or a via field under the hot loop increases its
   effective area even when the top-side copper looks tight.
3. **The switch node is a compromise, not an optimisation.** Big enough for the
   current, small enough not to be a plate antenna, and never a large pour.
4. **Input capacitance right at L1**, so the input loop is also small. A pi
   filter (L-C-L) at the connector keeps conducted emissions off the harness —
   which is what CISPR 25 actually measures, and what a 27-year-old truck's
   radio will hear.
5. **Feedback trace nowhere near the switch node.** Route it on the far side,
   referenced to quiet ground, and Kelvin it back to the output.
6. Fit a **snubber footprint across the diode** even if it starts unpopulated.
   Ringing at 2.2 MHz is measured on the bench, not predicted.

## The part that makes this application harder than most

**A 16-bit ADC and a 2.2 MHz switcher share this board.**

The AD7606 resolves 305 µV per count at ±10 V. A few millivolts of switching
noise coupled into an analog input is tens of counts — and it will be
*coherent*, appearing as a stable offset rather than as noise that averages
away. Worse, sensor readings are ratiometric to VREF, so noise on the reference
becomes noise on every sensor at once.

Mitigations, in order of effectiveness:

- **Physical separation.** Power stage in one corner, analog front end in
  another, with the digital section between them rather than the reverse.
- **The ground architecture already decided** — three separate signal returns
  and a single star point — does most of the work, provided the switcher's
  return current never shares copper with a sensor return.
- **Sample away from switching edges.** The ECU knows exactly where every
  ignition and injection event is, and could synchronise ADC conversions to
  avoid them. It cannot do that for the SEPIC, which free-runs — which is an
  argument for *layout* rather than firmware being the fix.
- **A shield can over the power stage**, with a footprint provided even if not
  fitted initially.

## Verify, do not assume

Two checks worth doing before the board is trusted:

1. **Measure the hot loop area from the Gerbers**, as was done for the previous
   SEPIC. It is a number, not a judgement.
2. **Near-field probe the assembled board** and compare the switcher's
   signature against the AM band and against the ADC's inputs. A cheap H-field
   probe and any spectrum analyser will show whether the layout worked long
   before the truck does.
