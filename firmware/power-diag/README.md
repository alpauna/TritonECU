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
