# Scanning slow signals through an analog mux

**The idea:** the ADC channels are nearly all spoken for, but most of what is
left to measure changes slowly and matters only for diagnostics. Put an analog
mux in front of one ADC input and let the ECU walk it during idle time, after the
critical work of each cycle is done, looking for faults rather than controlling
anything.

It works, and it fits this ECU better than it might look — with three caveats
that decide the design.

## Where it belongs: behind the MCP3204, not the ESP32

The ESP32's own ADC is the wrong target — ADC2 is unusable with WiFi up, ADC1 is
allocated, and the native range is 3.3 V against 5 V sensors. The **MCP3204 is
0–5 V on SPI**, already in the build, and already the home for the oil sender. A
74HC4051 (8:1, ~$0.25) in front of one of its four inputs gives:

| | |
|---|--:|
| 3 direct + 8 muxed | **11 channels** |
| Two muxes, 2 direct + 16 | **18 channels** |

## The per-channel RC is what makes it work

Each muxed input gets **10 kΩ + 100 nF** — the same network already specced for
the oil sender, doing triple duty:

| Job | Number |
|---|--:|
| Anti-alias / noise filter | τ = 1 ms, corner 159 Hz |
| **Fault limiting** — channel shorted to 35 V | 3.0 mA into the mux clamp (a 4051 takes ~10) |
| **Settling after a channel switch** | **nanoseconds** |

That last one is the part people get wrong. With the cap on the **input** side of
the mux, switching channels only has to charge the ADC's ~20 pF sample capacitor
from a 100 nF reservoir: 125 Ω × 20 pF = **2.5 ns**, and the charge sharing costs
0.02 % — a 1 mV droop on 5 V, well under a count. Put a single shared cap *after*
the mux instead and every channel switch needs **7 ms** to settle, which is where
the "mux scanning is slow" reputation comes from. Charge injection is 10 pC into
100 nF = 100 µV, irrelevant.

**Scan budget** at a 1 ms dwell: 8 channels sweep in 8 ms, 16 in 16, 32 in 32.
For oil pressure, temperatures, fluid levels and switch positions, that is
hundreds of times faster than the signals move.

## The three caveats

**1. It is a shared failure path.** One channel shorted to battery does not just
lose that channel — it can take the mux and everything behind it. The 10 kΩ
series resistors are what make that survivable, so they are not optional and not
a place to economise. If any muxed signal leaves the board on a long wire to
somewhere hostile, consider a fault-protected mux (ADG5248F and friends survive
±55 V on an input) at roughly ten times the price.

**2. It is firmware, not config.** `SensorDescriptor` has `sourceType`,
`sourceDevice` and `sourceChannel`, but nothing that says "set three GPIOs, wait,
then read". It needs a new `SRC_MUX` source type, a select-line trio, and — the
awkward part — **an asynchronous read**, because the current read path is
synchronous and a scan that blocks is a scan that steals time from the 10 ms
loop. The natural shape is a small state machine: select, return, sample on the
next tick, advance.

**3. Only put non-critical signals on it.** Anything the engine control loop
depends on within a cycle — crank, cam, MAP, TPS — stays on a dedicated channel.
The mux is for the diagnostic tail: oil pressure, trans temp, fluid levels,
switch positions, rail voltages, the 5 V reference itself.

## The alternative, honestly

| | Cost | New firmware | Shared failure path |
|---|--:|---|---|
| 74HC4051 + 8 RC pairs | ~$0.35 | **Yes** — new source type + async scan | **Yes** |
| MCP3208 (8 ch) instead of MCP3204 | ~$2 | No — same driver, more channels | No |
| Second ADS1115 @ 0x49 | ~$1 | No — `_ads1115_2` already exists | No |

**Below about eight extra signals, another ADC chip is the cheaper answer once
firmware time is counted.** The mux wins when the channel count gets large, or
when the channels are genuinely a scanning diagnostic tail rather than sensors —
which is exactly the use described here, so it is worth building. Just build it
for the tail, not for the sensors.

## Worth measuring while the mux is there

The one that pays for itself: **the 5 V rail, through a divider, on its own muxed
channel.** Ratiometric sensors cancel supply error only if the ADC reference and
the sensor supply move together; measuring the rail directly lets the ECU verify
that assumption instead of trusting it, and lets it log a sagging rail during
cranking rather than silently reporting a wrong pressure.
