# POWER board bring-up diagnostic

Standalone Nucleo F767ZI program. Answers one question the slow instruments
cannot: **which rail let go first.**

## The question

The board drops out above ~24 V. Measurement has cleared all three of the
LTC4364's supervisor inputs:

| path | measured | threshold |
|---|---|---|
| UV | 6.78 V | 1.25 V — 5× over |
| OV | 0.70 V | 1.25 V — would need 43.2 V |
| FB clamp | clamps at 28.2 V | *above* the dropout |

So either the protector is faulting on **current limit**, or the MAX25239 is
misbehaving as its on-time hits the floor and the protector is merely reacting:

```
22.92 V in -> MAX25239 on-time 103.9 ns
23.92 V in ->                   99.6 ns   <- where it stops
```

**From outside, those look identical** — VIN disappears either way. They differ
only in order, by microseconds:

```
3.3_ENOUT falls first, then 5_GOOD   -> protector faulted, starved the buck
5_GOOD falls first, then 3.3_ENOUT   -> buck failed, protector reacted
```

## Result — 2026-09-26: no fault. The board clamps as designed.

```
>>> EDGE  3.3_ENOUT  FALL
>>> EDGE      3.611 us  5_GOOD  FALL
dropped out at 26.74 V, peak current 25 mA
```

**The protector turned off first; the buck followed 3.6 µs later** — just its
output caps coasting before PGOOD let go. So the MAX25239 is innocent and the
min-on-time hypothesis is dead. The current-limit path is dead too: 25 mA peak
against a 5 A limit.

| | |
|---|---|
| dropped out at | **26.74 V** |
| FB clamp, by design | 26.99 V (R3 105k / R8 5.1k) |
| the sheet's own note | *"VIN is max 27 volts"* |

That is the LTC4364 clamping at its FB-set voltage, running the 594 ms timer and
shutting down. **Working as drawn.**

The earlier "drops out above 24 V" was an artifact of the bench setup: the
Nucleo was powered *from the board*, and the FB node was being probed at 3 %
margin. Both are now understood — see the git history.

### Current limit measured: 4.96 / 5.16 A against 5.00 designed

Deliberate shorts, with the INA238 at 50 µs conversions and peak-hold running in
the sampling loop rather than the print loop:

```
design      10 mOhm x 50 mV threshold  =  5.000 A
measured    4.962 A   and   5.157 A       within 1-3%
```

That validates two things which could not be separated any other way: `Rsns`
really is 10 mΩ, and the LTC4364's threshold really is 50 mV. Either being off
would have moved this.

**The first attempt measured nothing, and the instrument was at fault.** An
`INPUT_PULLDOWN` on the status pins fought the board's own 10 kΩ pull-ups,
making an 8 kΩ node at 2.6 V that picked up 10,508 spurious edges in four
minutes — and printing them at ~3 ms a line starved the INA238 poll, so the
peak-hold never ran. The event happened; the diagnostic was busy.

**A diagnostic that prints without a budget can starve the thing it is
diagnosing, and that failure looks exactly like "the event did not happen."**
The edge drain is bounded to four per pass now, with drops counted and flagged.

### A 5 V short hiccups locally — it does not reach the protector

Repeated dead shorts on the 5 V rail:

```
GAP 7.01 s   GAP 5.00 s   GAP 2.00 s    rails down, INA238 unpowered
0 peaks over 200 mA                     input side never saw it
recovered every time
```

**Input current stayed under 200 mA** — under 5 W at 24 V — so the LTC4364 never
knew. The MAX25239 absorbed it and hiccupped. That is the behaviour you want on
a vehicle: a harness short on 5 V costs a hiccup, **not** the minutes-long
protector cooldown a short on VIN produces.

**A DMM in the short read 2.7 A.** That is the *average*, not the limit — the
buck bursts to its 8.2 A limit and backs off, and a meter shows the mean, which
implies roughly a **33 % duty cycle**. Three things confirm hiccup rather than
regulation:

| evidence | why it rules out regulation |
|---|---|
| rails collapsed | a buck holding 5 V would not drop the 3.3 V rail |
| input < 200 mA | delivering 5 V × 2.7 A would draw **625 mA** at 24 V |
| the DMM averages | it cannot show a burst |

The power balance agrees: ~0.4–0.7 W reaches the short against up to 4.8 W going
in, the rest being switching and inrush loss.

**2.7 A is nevertheless the number worth keeping.** 8.2 A is what the silicon
does; 2.7 A sustained is what a real harness short pulls, and that is what sizes
fuses and traces.

Two limits of this particular measurement:

- **The gap includes hold time.** 2–7 s is contact duration plus recovery, not
  the buck's hiccup period, which is tens of milliseconds underneath.
- **Zero edges is expected, not a miss.** When the board's 3.3 V dies its status
  pull-ups die with it, and the Nucleo's high-impedance inputs then hold their
  last level on pin capacitance — no threshold crossing, no interrupt. For
  rail-collapse tests **the gap is the instrument and the edges are not.**

### A 3.3 V short is contained too — and the on-board indicators lie about it

Dead short on 3.3 V: **1849 mA** sustained, audible, no input peak above 200 mA,
no INA238 gap. Retry cadence measured from the edge timing:

```
13 intervals, mean 9.32 ms  ->  107 Hz
```

That is the buzz. The 2 MHz switching is inaudible; what you hear is the
TLV62085 retrying a hundred times a second.

**The 5 V rail sagged 5.13 → 5.06 V. 1.4 %.** Fully contained.

### The indicators cannot measure this fault, and that is structural

All three status signals — `5_GOOD`, `3.3_GOOD`, `3.3_ENOUT` — have their
pull-ups on the **3.3 V rail being shorted.** So the trace showed 18 `5_GOOD`
edges and 30 `3.3_ENOUT` edges during a fault that touched neither:

```
5.06 V sits 6.5-10% ABOVE any plausible PGOOD threshold (92-95% of 5 V)
```

`5_GOOD` had no business deasserting. Those edges were the pull-up losing
supply. Only a meter on the rail itself could tell the difference.

**This is the third time the same shape appeared in one session:**

| | instrument fed by the thing it measured |
|---|---|
| 1 | Nucleo powered from the board — died mid-capture |
| 2 | status pull-ups on the board's rail — a dead board read `111` |
| 3 | `5_GOOD`'s pull-up on the shorted rail — 18 phantom edges |

Each time it produced *confident, plausible, wrong* data rather than an obvious
failure. **When measuring a rail, the observer must not be powered by it.**

### Two things the trace taught that outlive this fault

**`5_GOOD` rises again 18.3 ms later with ENOUT still low and VBUS at 2.86 V.**
That is not recovery. PGOOD is open-drain with a pull-up, so a converter that
has lost its own bias *releases* the pin and the pull-up takes it high.
**5_GOOD high does not mean good when the part is unpowered** — firmware must
not trust it during startup or brownout.

**The first delta printed is meaningless.** It is measured from `prev_cyc = 0`,
so it reads as time since boot. Only deltas after the first event count.

## Reverse polarity: no measurable current, and the test was valid

Run with **D1 (SMDJ43A) out of the path**, **13.5 V driven into the GND plane**
with the return on **B+**, supply limited to **0.2 A**, and the Nucleo
**disconnected** — its shared ground is invalid once the input flips.

```
supply current        no deflection at all
downstream of Q1/Q2   0 V
5 V rail              0 V
3.3 V rail            0 V
```

**Why this is a real result and not an open circuit.** D1's ground sits on PGND,
a two-pin island (`D1_2`, `CN1_2`) with **no copper tie to GND** — see below. So
lifting PGND floats D1's anode and takes it out of the path, while the 118-pin
GND plane, which is what the converters and the LTC4364 actually reference, stays
fully connected. Feeding the plane directly is what keeps the circuit complete:
the return does **not** have to enter at `CN1_2`.

**Taking D1 out is what made this a measurement instead of a stress test.** The
SMDJ43A is unidirectional: in reverse it forward-conducts like a plain diode,
crowbars at ~0.8 V, and that conducting path *masks everything behind it*. You
learn the TVS works and nothing else. With it gone the only reverse path is the
UV/OV divider — roughly 350 kΩ, about **38 µA at 13.5 V** — which is why the
supply never twitched.

### The destructive path does not exist on this board

The one outcome worth fearing was reverse-biasing the 1120 µF of aluminum
electrolytic. It cannot happen — **C3/C4 sit downstream of the protector**, not
at the connector. [`power-supply.md`](../../docs/power-supply.md) has the order:

```
Battery ─ fuse ─ TVS ─ LTC4364-2 ─┬─ 1000 µF ─ converter
```

The review's phrase "input electrolytics" means input *to the converter*. The
back-to-back body diodes block ahead of them, and the LTC4364-2 is specified for
reverse input to **−40 V** — 13.5 V is a third of rating.

> **D1 must be reinstalled before OV testing or anything vehicle-side.** It is
> the last-ditch clamp above the 43.2 V trip; without it a fast harness
> transient lands on Q1's 100 V `Vds` with nothing in front of it. Its 43 V
> standoff breaks down near 47.8 V, so it does not overlap the OV trip.

## What this settled: PGND and GND are joined at zero points

`schematic-review-power.md` §8 asked to *"confirm the two are joined at exactly
one point."* It was filed **low** and never closed.
[`review-power-v1-bom-gerbers.md`](../../docs/review-power-v1-bom-gerbers.md)
narrowed it to a two-node net but could not settle it from the netlist:

```
GND    118 pins
PGND     2 pins  --  D1_2 and CN1_2, that is the entire net
```

**Confirmed on hardware 2026-09-26: they are not tied in copper at all.** The
answer is zero points, not one.

**D1's own loop is fine** — arguably textbook. Surge current enters at `CN1_1`,
crosses D1, and leaves at `CN1_2` to vehicle ground without ever touching the
board's GND plane. That is exactly what the review said to aim for.

**The isolation itself is intentional and correct.** PGND's whole job is to carry
clamp current when D1 fires, and routing that anywhere near a reference corrupts
every reading on the board during the one event most worth surviving. Keeping it
away from sensitive signal grounds is the design, not an oversight.

**What is missing is a DC return for GND.** CN1 has only two pins, so with no tie
the board's ground reference reaches the outside world *only* through the four
mounting standoffs (U2–U5) and the two headers. Consequences:

| | |
|---|---|
| **The board cannot be powered through CN1 alone** | B+ and PGND give it no return |
| **All return current would flow through the standoffs** | into the enclosure, if they are even bonded to vehicle ground |
| **On the bench, the return has been coming from whatever else was attached** | the Nucleo's ground wire through U7 |

That last row is the **fourth instance** of the session's recurring shape, and
the sharpest: not the instrument drawing power from the board, but the instrument
**supplying the board's return path**.

### The fix does not compromise the isolation

A tie at `CN1_2` puts **no** surge current on GND, which is exactly why the v1
review chose it over `D1_2`:

| tie at | what GND rides on |
|---|---|
| **`CN1_2`** ✅ | the vehicle ground entry. Surge has already *left* the board by the time it gets there |
| `D1_2` ❌ | the far end of the run — the whole 17.7 mm of IR and L·di/dt appears across GND |

Same "one point", opposite outcome. With a 2-pin `WJ2EDGRC-5.08` and no third pin
for signal ground, and with a chassis return through the standoffs being a poor
reference once engine currents share the loop, the `CN1_2` tie is the only option
actually on the table.

**Make it a component, not copper: a 0 Ω 0805 link or a net-tie at `CN1_2`.**

- The single point is enforced by construction and cannot silently become two
  when a plane is re-poured.
- It is an inspectable decision rather than geometry a reviewer must measure off
  the gerbers — which is what left this open across two board revisions.
- **Lifting it becomes a one-component operation** — the exact isolation
  performed on 2026-09-26, by design instead of by rework.

## Why the M7 and not the INA238

The INA238 is on the right shunt — the same 10 mΩ the LTC4364 uses — but it
runs at **20 kSa/s at best** and averages straight over a transition that takes
microseconds. It tells you the current *trend* as VIN is swept, never the event.

The **DWT cycle counter** at 216 MHz gives **4.63 ns** per tick on GPIO edges,
four orders of magnitude finer than the thing being resolved. That is the
measurement; the INA238 is context around it.

## Wiring — POWER board U7 (2.54 2×5)

```
GND ------ GND          SCL ------ D15 (PB8)
3.3_ENOUT- D7  (PF13)   SDA ------ D14 (PB9)
5_GOOD --- D4  (PF14)
3.3_GOOD - D2  (PF15)

+3.3V ---- do NOT connect      <- Nucleo runs on USB power
```

**GND is the only power-domain connection.** Tying the board's 3.3 V to the
Nucleo's `3V3` pin is the first of the three observer mistakes above, and it is
worse once the Nucleo is on USB: two regulators on one node with no ORing, the
higher one sourcing into the lower, and during a 3.3 V short test the Nucleo's
LDO feeding the short.

Nothing else needs it:

- The three status signals are pulled up by the **board's own 10k** resistors to
  the **board's** 3.3 V. The Nucleo reads them as inputs and needs only a common
  return. When that rail collapses the pull-ups collapse with it and the pins
  read low — **that is the measurement**, and it is where the 18 phantom
  `5_GOOD` edges came from.
- SCL/SDA are open-drain: the STM32 only ever pulls them *low*, and the INA238's
  pull-ups are on the board. No back-feed, no reference needed.

D2/D4/D7 sit on EXTI 15/14/13 — **different lines, so all three can interrupt at
once**. STM32 shares an EXTI line across ports by *pin number*, so pins that look
unrelated collide when their numbers match. That is the constraint that chose
these three.

## Reading the output

Edges print with the delta from the previous event. **The first line after a
quiet period names the rail that failed**; everything after it is the cascade.

`ADCRANGE = 0` deliberately: ±163.84 mV full scale, 5 µV/LSB → **500 µA/LSB and
±16.384 A** on a 10 mΩ shunt. Range 1 resolves four times finer but clips at
4.1 A — below the 5 A limit this is trying to watch approach.
