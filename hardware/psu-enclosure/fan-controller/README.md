# PSU enclosure fan controller

ESP32 reads the exhaust air with a DHT22 and switches the 40 mm intake fan
through the low-side FET on the [`2N7002 Driver`](../../2N7002%20Driver) board.

## Wiring

```
GPIO4  --+-- [470R] -- 3V3       fail-safe: floating pin = fan RUNS
         |
         +-- H1 pin 2 (In) -> R1 220R -> SS8050 base

GPIO13 ----------+-- DHT22 DATA
                 |
              [10k] -- 3V3

DHT22 VCC -> 3V3      NOT 5 V. The pull-up sets the data line's idle
                      level, and the ESP32 is not 5 V tolerant.
```

Pins 4 and 13 are interchangeable — neither is a strapping pin. Most of the
ESP32's obvious pins are not so free: **12** is the dangerous one, because a
pull-up there sets the flash rail to 1.8 V and the board will not boot at all.
**2, 5, 15** are strapping or emit a PWM burst at reset, **6–11** are the flash,
and **34–39** are input-only with no pull-ups, so they cannot drive a gate or do
the DHT22's bidirectional handshake.

## Fit an SS8050, not the 2N7002

Full reasoning in the [driver board README](../../2N7002%20Driver/README.md).
Short version: the 2N7002 characterises `Rds(on)` at 10 V and 5 V and **nothing
below 5 V**, so 3.3 V is off the end of its own curve — and `Id` falls from
115 mA to **75 mA at 100 °C**, against a ~100 mA fan, in a box that is hot
precisely when the fan is needed. `L2N7002LT1G` is the same part; the `L` is the
manufacturer, Leshan Radio, not a logic-level suffix.

An SS8050 in SOT-23 drops into the same footprint (base/emitter/collector is the
same pin order as gate/source/drain) and sidesteps the threshold problem
entirely, because a BJT is current-driven. ~0.15 V `Vce(sat)`, 15 mW, 1.5 A
rating, 1 W package.

**The pull-up is 470 Ω, not 10 k, and it lives at this end** — the driver board
has no 3.3 V rail. A BJT base needs *current*: through 10 k you would get
0.26 mA, a forced beta of 385 against an hFE that may be 85, and the fan would
turn at half speed while the transistor burned a third of a watt looking like it
worked.

No flyback diode. A 2-wire brushless fan commutates internally behind its own
input capacitor; what is left is ~2.5 nJ of lead inductance, switched slowly,
into 13 V of headroom.

## Fail-safe

The box's airflow depends entirely on this fan and it holds a warm supply and a
mains connection, so *off* is the expensive way to be wrong. Every path here
ends with the fan running: the gate pull-up covers a floating pin, `setup()`
drives it on before serial or the sensor, a crash floats the pin through reset,
and repeated sensor failures force it on rather than holding the last state.

Two cases software **cannot** cover: the ESP32 losing power while the supply
keeps running, and a true CPU hang with the pin still driven low. Both want a
**KSD9700 60 °C normally-open** thermal switch across the FET, which closes when
hot no matter what the firmware is doing — including when it is unpowered.

## Bench testing

Thresholds are build-overridable so the control law can be exercised against
room temperature without a source edit anyone might forget to revert:

```bash
PLATFORMIO_BUILD_FLAGS="-DT_ON_C_VAL=31.0f -DT_OFF_C_VAL=29.0f" pio run -t upload
```

Boot always starts the fan on, so thresholds *below* room temperature only prove
it will not switch off. Put room temperature on the other side to see a real
transition.

## Sensor placement

In the **END B exhaust**, not at the fan — intake air is room air and says
nothing about the supply. Not on the heatsink either: the DHT22 is an air sensor
with an 80 °C ceiling. Metal temperature wants a DS18B20.

It needs 2 s between reads and is ±0.5 °C, which is fine for a plant that is a
box of air, and rules out anything tighter.

## Finding the sensor again

[`../dht-scan`](../dht-scan) probes every free pin for a DHT22 and reports which
one answers. It distinguishes "wrong pin" from "not powered" — a sensor with no
VCC answers on *no* pin, which is a different finding from answering on one.
