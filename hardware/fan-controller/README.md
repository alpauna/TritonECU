# Enclosure fan controller — ATtiny

A self-contained thermostat for the [PSU enclosure](../psu-enclosure) fan. One
12 V input, one fan output, sensor on the board, and an OLED on a tail showing
the exhaust temperature. Replaces the ESP32 bench rig in
[`../psu-enclosure/fan-controller`](../psu-enclosure/fan-controller), which
proved the control law and the driver but wants a whole dev board and a USB
cable to do it.

## Schematic

```
        +12V o---+-------------------------------+----------------o fan +
                 |                               |
              [U1 MCP1703A-5002]              (FAN, 40x40x10, ~100 mA)
              12V -> 5V, SOT-89                  |
                 |  Iq = 2 uA                    |
        +5V o----+----+----+                     |
                 |    |    |                     |
              [C1] [R1 10k NTC 0805]             |
              1uF    |                           |
                 |   +---- PA3/AIN3 (NTC sense)  |
                 |   |                           |
                 |  [R2 10k 1% 0805]             |
                 |   |                           |
        GND o----+---+------+--------------------|----------------o fan -
                            |                    |               (via Q1)
                            |              +-----+
                  [ATtiny1614 - 16K]        |
                            |              C
                   PA7 o--[R3 470R]--B  [Q1 SS8050]
                            |              E
                        [R4 1k]            |
                            |             GND
                          +5V
                   PA6 o--[R5 2k2]--[LED1]--GND      status

         I2C tail to the front panel:  SDA/SCL/5V/GND -> SSD1306 0.96"
         SW1 (momentary, to GND)      wakes the display
```

`R4` pulls the base high, so a floating MCU pin runs the fan. See **Fail-safe**.

## The sensor is on the board, which decides two things

**The board lives in the exhaust, at END B.** The sensor's position *is* the
board's position. Intake air is room air and says nothing about the supply;
this has to sit where air has already crossed the heatsink.

**The board's own heat biases its own sensor.** An LDO dropping 7 V plus a
transistor plus an MCU is 50–70 mW on a small board, which is several °C of
local rise measured by the part whose job is measuring °C. Two answers, and the
second matters more than the first:

- **A routed thermal slot**, most of the way around `R1`, leaving a narrow neck.
  Free at fab, and it cuts the conduction path so the sensor sees air rather
  than copper. Put `U1` and `Q1` at the far end of the board from it.
- **Sleep.** Not for power — for *measurement*. The MCU wakes on the watchdog,
  converts, decides, and goes back down, awake maybe 1 ms in 1000. A board that
  does not dissipate has no self-heating to isolate. That is why `U1` is a 2 µA
  LDO and not a 78L05, whose 5 mA quiescent alone would be 35 mW of permanent
  error sat next to the sensor.

## Why an NTC and not a DHT22 or a DS18B20

Because **the ATtiny never needs to know what a degree is.** A bang-bang
thermostat only has to know which side of a line it is on, so the thresholds
live in ADC counts and the Beta equation is done here, once, at design time:

| T (°C) | R_ntc | ADC (10-bit) |
|---|---|---|
| 30 | 8037 | 567 |
| **32** | 7379 | **589** ← OFF |
| 35 | 6506 | 620 |
| **38** | 5749 | **650** ← ON |
| 50 | 3588 | 753 |

61 counts of hysteresis, and 10.1 counts/°C — one LSB is 0.10 °C, far finer
than the sensor is accurate. No float, no `log()`, no lookup table: two integer
comparisons on an 8-bit part.

**It is ratiometric, and that is not an accident.** The divider is fed from VCC
and the ADC references VCC, so a sagging rail moves both ends and cancels
exactly. Use VCC as the reference, **not** the internal 1.1 V bandgap — against
a bandgap, every millivolt of rail droop becomes a temperature error.

A 10 k 0805 NTC is about two cents, has almost no thermal mass, and needs no
2 s conversion floor like the DHT22.

## The display pushes the part up, and sits somewhere else

**The sensor wants the exhaust; the display wants your eye line.** Those are not
the same place. The board stays at END B with `R1` in the airstream, and the
OLED goes on a **4-wire I2C tail** to the front panel next to the DC-DC's
screen. 200 mm at 100 kHz is untroubled.

That split is not just ergonomics. At ~15 mA the OLED dissipates more than
everything else on this board combined, and sat next to the thermistor it would
undo the entire sleep argument. On a tail, its heat goes to the panel.

**2 KB is not enough for a display.** An ATtiny202 has 2 KB of flash and any
SSD1306 driver with a font spends most of it before your code exists. So the
display forces the part up to an **ATtiny1614** — 16 KB, 2 KB RAM, same UPDI
toolchain, SOIC-14. Without a display the 202 is the right part and this BOM
would not need changing.

> Keeping the 202 is possible if the display is a **TM1637 4-digit** module
> instead: two wires, no font, a driver in a few hundred bytes. Less pleasant to
> read, much smaller to drive.

### The display converts. The control law does not.

Thresholds stay in raw ADC counts. Only the display turns counts into degrees,
through a 16-entry LUT at 5 °C spacing with integer interpolation:

```
  0 C -> 234      35 C -> 620      70 C -> 870
```

**32 bytes of flash, 0.09 °C worst-case interpolation error** — an order of
magnitude below what the thermistor is accurate to, and still no float and no
`log()`. Keeping the conversion on the display side means a presentation bug
cannot reach the thermostat.

### Blank it

The display times out after a few minutes and wakes on the button. An OLED left
showing a static number burns its pixels in, and an always-on 15 mA is 75 mW
that has to leave the box somehow.

## Fail-safe

Same reasoning as the ESP32 version: this box's airflow depends entirely on this
fan and it holds a warm supply and a mains connection, so *off* is the expensive
way to be wrong.

- `R4` pulls the base high, so a floating pin runs the fan — covering reset,
  boot, and a watchdog trip
- Boot drives the fan on before anything else, and exercises it for 3 s
- **An open NTC is the dangerous fault and is caught explicitly.** Open the top
  leg and the divider reads ~0 counts, which looks like *very cold* and would
  switch the fan off forever. A short reads ~1023, which looks like very hot and
  fails safe by luck. Only the first one needs catching, and it is.
- Brown-out fuse at 4.3 V, so a sagging rail stops the part rather than letting
  it run the comparison on a bad conversion

What this still **cannot** cover is losing 12 V while the supply runs hot. That
wants a **KSD9700 60 °C normally-open** across `Q1`, which closes when hot
whatever the firmware is doing, including when it is unpowered.

## Tune the thresholds before you build this

650/589 come from the Beta equation, not from the box. Run the ESP32 rig in the
assembled enclosure first, watch what the exhaust actually idles at under load,
and set these from that. If idle sits at 35 °C the fan will never stop, and the
thresholds should move rather than the box run hot.

That is the trade for the small board: no serial, no telemetry. `LED1` gives
heartbeat, fan state and sensor fault, which is enough to *diagnose* but not
enough to *tune*.

## Status LED

Flashed briefly at each wake, so it is a heartbeat rather than a load — always
low duty, negligible dissipation next to the sensor.

| pattern | meaning |
|---|---|
| one flash / s | alive, fan off |
| two flashes / s | alive, fan running |
| three fast flashes | sensor fault, fan forced on |
| dark | not running — check 5 V |
