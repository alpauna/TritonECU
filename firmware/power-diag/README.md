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

### Two things the trace taught that outlive this fault

**`5_GOOD` rises again 18.3 ms later with ENOUT still low and VBUS at 2.86 V.**
That is not recovery. PGOOD is open-drain with a pull-up, so a converter that
has lost its own bias *releases* the pin and the pull-up takes it high.
**5_GOOD high does not mean good when the part is unpowered** — firmware must
not trust it during startup or brownout.

**The first delta printed is meaningless.** It is measured from `prev_cyc = 0`,
so it reads as time since boot. Only deltas after the first event count.

## Why the M7 and not the INA238

The INA238 is on the right shunt — the same 10 mΩ the LTC4364 uses — but it
runs at **20 kSa/s at best** and averages straight over a transition that takes
microseconds. It tells you the current *trend* as VIN is swept, never the event.

The **DWT cycle counter** at 216 MHz gives **4.63 ns** per tick on GPIO edges,
four orders of magnitude finer than the thing being resolved. That is the
measurement; the INA238 is context around it.

## Wiring — POWER board U7 (2.54 2×5)

```
+3.3V ---- 3V3          SCL ------ D15 (PB8)
GND ------ GND          SDA ------ D14 (PB9)
3.3_ENOUT- D7  (PF13)
5_GOOD --- D4  (PF14)
3.3_GOOD - D2  (PF15)
```

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
