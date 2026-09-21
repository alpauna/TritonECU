# Cranking, rail sag, and not crying wolf at startup

Three things have to be true at once during a start: the ECU should **watch** the
rail sag, it should **not raise faults** for conditions that are normal while
cranking, and slow sensors should get time to become meaningful before anyone
believes them.

The machinery for the second one exists. The first and third do not, and the
existing gate has a defect that has to be fixed before either can be built on it.

## The defect: masked reads as zero

`SensorManager::update()` gates every descriptor on engine run state:

```c
if (!(d.activeStates & curState)) {
    d.value = 0.0f;
    d.inError = false;
    d.inWarning = false;
    continue;
}
```

Two problems:

1. **`0.0` is a value, not an absence.** A masked oil pressure sensor reads zero
   — which is exactly the number that means *danger*. The dashboard, `/state`,
   MQTT, the logger and any `OutputRule` sourcing that slot all see a plausible,
   alarming, false reading. Nothing downstream can tell "masked" from "failing".
2. **The read is skipped entirely**, so nothing is captured during cranking —
   the one window where rail sag, pressure rise time and low-voltage sensor
   behaviour are visible.

**The fix is to separate reading from believing.** Always read, filter and
publish. Gate only the *validation* — `errorMin`/`errorMax`, `warnMin`/`warnMax`,
fault bits and actions. A descriptor needs a `masked` flag alongside `inError`
and `inWarning` so consumers know the value is live but unvalidated.

## Three different questions, three different masks

They get conflated, and they should not be:

| Question | During crank | Settle after start |
|---|---|---|
| **Indicate** — what the driver sees | Follow the real value. A stock oil lamp *is* lit while cranking, and should be | No delay |
| **Validate** — set a fault bit, log it | Suppressed for sensors the crank genuinely disturbs | Held off for `settleMs` |
| **Act** — limp, shutdown, cut fuel | Suppressed | Held off, plus the normal `debounceMs` |

The oil pressure indicator should read LOW while cranking because it *is* low.
What must not happen is a latched fault, a log entry and a limp-mode entry every
time the engine starts.

## The settle window

`activeStates` is state-based; what is missing is **time**-based. Add a
per-descriptor `settleMs`, counted from the **CRANKING → RUNNING transition**,
not from boot, and reset whenever the engine stalls:

| Sensor | `settleMs` | Why |
|---|--:|---|
| Oil pressure | **3000** | Pressure takes a second or two to come up. Indicate immediately, believe it after three |
| Fuel pressure (if added) | 2000 | Pump prime |
| O2 / CJ125 | — | Already gated by `isReady()`; heater state is a better signal than a timer |
| CLT / IAT / TFT | 0 | Slow, but valid the moment the rail is stable — mask during crank, not after |
| Crank / cam / MAP / TPS | 0 | Critical. Never masked, never delayed |

## Rail monitoring — and which sensors sag actually breaks

Put the 5 V rail on its own channel through a divider (see
[`analog-mux-scan.md`](analog-mux-scan.md)). Then the sag is data rather than an
assumption — but **which sensors it corrupts depends on which ADC they sit on**:

| Path | Reference | A sagging 5 V rail… |
|---|---|---|
| **MCP3204 with VREF tied to the 5 V rail** | ratiometric | **cancels.** Sensor and reference move together; the reading stays true |
| **ADS1115** | its own internal reference | **does not cancel.** It measures absolute volts, so a ratiometric sensor read through it drifts with the rail |
| ESP32 native ADC | internal | does not cancel |

So the same transducer is trustworthy through one ADC and wrong through another,
during exactly the window where things are already hard. That decides which ADC a
5 V ratiometric sensor belongs on, and it is worth stating plainly because the
symptom — a reading that is wrong only while cranking — is miserable to chase.

### State-dependent thresholds

Rather than disabling the rail monitor during cranking, move its limits:

| State | Warn below | Error below | Notes |
|---|--:|--:|---|
| RUNNING | 4.75 V | 4.50 V | The regulator should be comfortable |
| **CRANKING** | 4.25 V | 4.00 V | Sag is expected here; only flag what is genuinely bad |
| OFF | — | — | Not interesting |

This keeps the monitor alive through the interesting window instead of blinding
it, which is the whole point.

### Log the sag depth

Record the **minimum rail voltage seen during each crank event**, with the crank
duration. It costs one float and it is the most useful battery-health metric the
truck can produce: a battery on the way out shows up as crank sag getting deeper
over weeks, long before it fails to start. The same applies to the battery
voltage input itself.

## What this needs, in order

1. **Fix the mask semantics** — read always, gate validation, add `masked`.
   Everything else depends on it.
2. **Add `settleMs`** to `SensorDescriptor`, timed from the RUNNING transition
   and reset on stall.
3. **Add the rail sensor** and state-dependent thresholds.
4. **Log crank sag depth and duration** per start.
