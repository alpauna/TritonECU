# Watching output current as a pre-failure signal

A motor that draws more current for the same work is wearing out. A fuel pump
whose steady-state current climbs has bearing drag, brush wear, or a partial
short, and it usually does that for weeks before it strands anyone. The same
measurement catches the blunter faults instantly — a blown fuse, a relay that
did not close, a locked rotor.

Nothing in the repo measures current today. `SensorManager::readCoilHealth()` is
a *digital* readback — expander shadow versus actual — which catches a stuck pin
but says nothing about what the load is drawing.

## The detector needs no new code

This is the useful part. Two `SensorDescriptor` slots pointed at the **same**
current channel, with different EMA weights, plus the `OP_DELTA` rule that
already exists:

| Slot | `emaAlpha` | τ at the 10 ms update | Role |
|---|--:|--:|---|
| `PUMP_I` | 0.03 | 0.33 s | tracks what the pump is doing now |
| `PUMP_I_BASE` | 0.0003 | 33 s | holds where it has been sitting |

```
FaultRule: op = OP_DELTA, sensorSlot = PUMP_I, sensorSlotB = PUMP_I_BASE
           thresholdA = 1.25        // 25% of a 5 A nominal pump
           debounceMs = 2000
           requireRunning = true
```

`OP_DELTA` already computes `|A − B| > threshold`. A fast average against a slow
one *is* a step detector, and because both slots share a calibration, the delta
comes out in amps. Slow drift — a warming pump, a rising battery voltage — moves
both averages together and produces nothing. A step moves only the fast one.

Reading one channel twice per update costs one extra I²C or SPI transaction.

**What this does not catch:** the slow trend, because the baseline follows it.
That needs the 33 s average logged to SD and compared across weeks, not a rule.
Both are worth having and they are different mechanisms.

## Four fault classes, in order of how actionable they are

| Class | Signature | Response |
|---|---|---|
| **Open circuit** | Commanded on, current ≈ 0 | Blown fuse, relay not closed, broken wire, dead pump. Immediate, unambiguous, and the one that strands you. Needs no baseline at all — a simple `OP_LT` while the output is commanded |
| **Locked rotor / short** | Far above nominal, immediately | Cut the relay. Protects the wiring, not just the diagnosis |
| **Sudden jump** | 15–25 % above the 33 s baseline, sustained | The pre-failure warning. `OP_DELTA` as above |
| **Slow trend** | Baseline creeping over weeks | Log it; no rule can see it |

The first two are worth building even if the trend work never happens — and they
answer a question the ECU cannot currently ask at all: **did the output actually
do what it was told?** That is the same question `readCoilHealth()` answers
digitally for the coils, and current answers it for everything else.

## Sensing hardware

The fuel pump is switched by a **relay** on MCP23017 P0, so no pump current flows
through the ECU today. Something has to be inserted:

| Part | ~Cost | Notes |
|---|--:|---|
| **INA226** (I²C) | $1 | 16-bit, gives **current *and* bus voltage**, averages internally, has an alert pin. Costs no ADC channel — and the I²C bus already carries the MCP23017 and ADS1115. Best fit |
| INA180 / INA181 | $0.50 | Analog out, so it costs an ADC channel — a muxed one would do ([`analog-mux-scan.md`](analog-mux-scan.md)) |
| ACS724 hall | $1–2 | Isolated, no shunt in the path, but 100 mV/A and drifts with temperature. Easiest retrofit if the pump feed does not pass the ECU |

**Shunt, for the INA226 route:**

| | 5 A | 8 A |
|---|--:|--:|
| 5 mΩ | 25 mV, 0.12 W | 40 mV, 0.32 W |
| **10 mΩ** | **50 mV, 0.25 W** | **80 mV, 0.64 W** |
| 20 mΩ | 100 mV, 0.50 W | 160 mV, 1.28 W |

10 mΩ is the sweet spot: comfortably inside the INA226's ±81.92 mV range at 8 A,
and a 1 W part runs cool. 20 mΩ gives better resolution and clips above ~8 A.

## Normalising, so the warning means something

A DC motor's current moves with supply voltage, so raw amps are not comparable
between a 12.4 V key-on and a 14.4 V fast idle. Three options, in order:

1. **Use the fast-vs-slow delta** — immune to slow voltage drift by construction,
   which is most of the problem and needs nothing extra.
2. **Compute power** if the sensor is an INA226, which measures bus voltage
   anyway. Watts are comparable across voltages; amps are not.
3. **Gate the rule** with `gateRpmMin`/`gateRpmMax` so it only evaluates at a
   stable operating point, which the rule engine already supports.

## Worth logging per start

The same shape as the crank-sag metric: **inrush peak and time-to-steady on every
pump prime**, plus the steady-state average. A pump on the way out shows a rising
inrush and a longer settle long before its running current moves — and it costs
two floats per start.

## Candidates beyond the fuel pump

Everything the ECU switches and currently cannot verify: injectors (peak/hold, so
open and shorted coils become visible), ignition coils (dwell current, which is
the real measure of a failing coil), the alternator field, the CJ125 heaters, and
the transmission solenoids — where
[`dash-indicators.md`](dash-indicators.md) already lists "solenoid circuit open or
shorted" as a fault the O/D lamp should flash for, with nothing able to detect it.
