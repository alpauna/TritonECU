# PSU enclosure fan controller

ESP32 reads the exhaust air with a DHT22 and switches the 40 mm intake fan
through the low-side FET on the [`2N7002 Driver`](../../2N7002%20Driver) board.

## Wiring

```
GPIO4  --[220R]--+-- gate (SOT-23 pin 1)
                 |
              [10k] -- 3V3        fail-safe: floating gate = fan RUNS

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

## Change the FET before you build this

The driver BOM ships a **2N7002**, and it is the wrong part for a 3.3 V gate.
`Vgs(th)` runs 1.0–2.5 V and `Rds(on)` is specified at `Vgs = 10 V`, so at 3.3 V
you may have 0.8 V of overdrive in a region no datasheet guarantees. At the
fan's ~100 mA that is somewhere between 100 mW and 350 mW in a SOT-23 rated for
200–350 — it works on the bench and dies on a warm day.

**AO3400A** or **SI2302**: same SOT-23 footprint, same G/S/D pinout, `Rds(on)`
specified down to 2.5 V. AO3400A at 100 mA drops 3 mV and burns 0.3 mW.

**The BOM also has no flyback diode.** Switching a fan low-side puts a spike on
the drain at turn-off. A 60 V 2N7002 shrugs it off; a 20 V SI2302 may not. Add a
diode across the fan, **cathode to +12 V** — the enclosure BOM already carries
1N5819.

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
