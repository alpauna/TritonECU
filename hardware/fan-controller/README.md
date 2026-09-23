# Enclosure fan controller — ATtiny

A thermostat for the [PSU enclosure](../psu-enclosure) fan. Sensor on the board
on a thermally isolated tongue, setpoint on a pot, and an OLED on a tail showing
the exhaust temperature.

**Built.** `Schematic/` carries the EasyEDA schematic, gerbers and BOM as
fabricated: **54.86 × 16.13 mm**, 3 × M2. Read [As built](#as-built) before
ordering — one net needs changing. Replaces the ESP32 bench rig in
[`../psu-enclosure/fan-controller`](../psu-enclosure/fan-controller), which
proved the control law and the driver but wants a whole dev board and a USB
cable to do it.

## Schematic

Logic runs on **5 V**, fed in on `H2`. The fan's 12 V never touches this board —
`Q1` only switches its low side out through `H1`.

```
   +5V o--+--[C2 10u]--[C1 100n]--+-- U1 VDD (ATTINY1614-SSN, SOIC-14)
          |                       |
       [R6 6k8]           [R3 NTC 10k B3950]      <- on the isolated tongue
          |                       |
        o 3 RV1 10k               +-- PA3  (pin 13)
        o 1 --+-- PA4 (pin 2)     |
        o 2 --+              [R4 10k 1%]
              |                   |
          [R7 20k]               GND
              |
             GND

   PA7 (pin 5) --[R1 220R]--+-- gate  Q1 AO3400A
                            |
                         [R2 10k]  ** see As built - this must go to +5V **
                            |
                           GND

   H1  1 Load (drain)   2 Flyback   3 GND      D1 1N4148W: drain -> Flyback pin
   H2  GND  +5V  Status(PA6)  Wake(PA2)  UPDI(PA0)  SCL(PB0)  SDA(PB1)
```

`PA5`, `PA1`, `PB2`, `PB3` are deliberately unconnected. `PA5` is the one worth
keeping free — a fan tach input if a 3-wire fan is ever fitted.

### The flyback is opt-in, which is the right call

`D1` is fitted, but its cathode lands on `H1` pin 2 rather than on a supply. Wire
that pin to +12 V and the diode sits across the fan; leave it and it does nothing.

For this fan it does nothing worth having. A 2-wire brushless fan commutates its
windings internally behind its own input capacitor, so switching the supply does
not break inductive current the way a relay coil does. What is left is roughly
0.5 µH of lead inductance at 100 mA — about **2.5 nJ** — turned off over
microseconds by `R1`, into a 30 V part on a 12 V rail. Connect pin 2 if the load
ever becomes a relay, a solenoid or a brushed motor.

## The FET

`Q1` is an **AO3400A**: 30 V, 5.7 A, `Rds(on)` ~30 mΩ specified down to 2.5 V.
At 100 mA it drops 3 mV.

**Do not substitute a 2N7002.** It characterises `Rds(on)` at 10 V and 5 V and
**nothing below**, and `Id` falls from 115 mA to 75 mA at 100 °C — against a
~100 mA fan, in a box that is hot precisely when the fan is needed. `L2N7002LT1G`
is the same part; the leading `L` is Leshan Radio, the manufacturer, not a
logic-level suffix. See [`../2N7002 Driver`](../2N7002%20Driver/README.md).

## As built

The fabricated board differs from the sketch above it in three ways. Two are
improvements; one is a fault.

### ⚠ R2 is a pulldown. It must be a pull-up.

`R2` 10 kΩ runs from the gate to **GND**, so a floating `PA7` — during reset,
during boot, after a watchdog trip — holds the gate low and **stops the fan**.
That is backwards. This box's airflow depends entirely on this fan and it holds a
warm supply and a mains connection, so a floating pin must *run* it.

**Fix: R2's lower end goes to +5 V, not GND.** One net in EasyEDA. On a board
already made, lift that end and wire it to the +5 V pour.

Until then, `setup()` driving the fan on still covers a clean start, but nothing
covers a hang or the reset window, and the KSD9700 stops being a backstop and
becomes the only defence.

### ⚠ `Status` has no series resistor

`PA6` goes raw to `H2` pin 3 and there is no pad for one. An LED straight onto it
kills the pin or the LED. Put it in the tail or the LED module, and note it on
the silkscreen.

### ✅ No LDO — and that is better

The board takes 5 V in rather than regulating 12 V down. The LDO would have been
the largest heat source on a board whose entire problem is self-heating beside
its own sensor, so removing it makes the sleep argument stronger rather than
weaker. The enclosure already has a fixed 5 V rail.

### ✅ AO3400A rather than the SS8050

An SS8050 NPN was the earlier plan, because a BJT is current-driven and the
gate-threshold question disappears. But that was the better answer to a *3.3 V
gate*, not the better part: the BJT needs continuous base current and drops
~0.15 V where the AO3400A drops 0.003 V. `R1` is now a gate resistor rather than
base drive, which is fine — it damps the edge and nothing here switches fast.

### ✅ The thermal tongue is real

Verified in the gerbers rather than assumed:

```
slot 1   x 18.50..19.16   y 0.40..4.54     0.66 x 4.14 mm
tongue         1.64 mm wide, NTC 0805 at x 19.94, y 1.29 / 3.29
slot 2   x 20.80..21.46   y 0.40..4.54
```

Nothing else sits on it — the next components are at y ≥ 6.1, past the slot ends.

One floor that no isolation removes: the NTC dissipates about **0.6 mW**, which
on an 0805 is 0.15–0.3 °C of self-heating. That is inside the thermistor's own
tolerance and not worth chasing, but it is the accuracy limit.

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
  does not dissipate has no self-heating to isolate. The as-built board goes
  further and drops the regulator entirely, taking 5 V in, which removes what
  would have been the largest standing heat source of the lot.

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

## Setpoint pot — compared against the sensor, not converted

`RV1` on PA4 sets the trip temperature. **It is not mapped into degrees and it
is not calibrated.** The pot is simply another divider on the same ADC against
the same reference, so the firmware compares the two readings directly and the
fan trips wherever they cross:

```
    ntc >= pot          -> fan on
    ntc <= pot - HYST   -> fan off
```

No conversion, no constants, no LUT anywhere in the control path. And the
comparison is immune to the supply in a way a mapped setpoint would not be:
**both** dividers are ratiometric off VCC, so a sagging rail moves the sensor
and the setpoint together and the crossing does not shift.

### Wire it as a rheostat, and mind which end the wiper goes to

Specified part: **ALPS RK09K11300DR** — 9 mm vertical, 10 kΩ, taper `1B`
(linear), 280° travel, 3 × Ø1 mm pins on a 10.6 × 7 pattern.

```
   +5V --[R8 6k8]--o 3
                     RV1 10k        terminal 2 is the WIPER (datasheet p.315)
                   o 1 --+-- PA4    tie it to terminal 1, the ADC side
                   o 2 --+
                         |
        GND --[R9 20k]---+
```

Span is **556–763 counts, about 29–51 °C**, and clockwise **raises** the
setpoint. That falls out of feeding R8 into terminal 3 rather than 1: ALPS
increase R(1→2) clockwise, so R(3→2) *decreases* clockwise, the node rises, and
the knob reads the way a knob should.

### ±20 %, and why it does not matter

The pot is ±20 %, so the bottom of the span moves — 26.4 °C on a +20 % part,
31.9 °C on a −20 % one. The **top does not move at all**: at 0 Ω the pot
contributes nothing to the divider, so 51.4 °C is tolerance-free.

**For setting it, this is irrelevant.** You turn the knob watching the display,
not reading the dial — which is the dividend from putting the setpoint through
the same LUT as the measurement. A ±20 % part just shifts where in the travel a
given temperature lands.

It matters in exactly one place: the fault window has to clear 527, not 556.

**A rheostat beats a 3-terminal divider here, and the reason is the failure
mode.** If the wiper contact goes open, the track is still intact, so the
resistance goes to full scale and the node lands at 556 counts — the lowest
setpoint, fan earliest. It degrades *toward cooling by construction*, with
nothing to detect and no firmware involved. A 3-terminal pot would leave the
node floating and the reading anyone's guess.

**Tie the wiper to terminal 3, the ADC side.** On terminal 1 an open wiper
disconnects the node from the supply, it is pulled to ground through R9, reads
0 counts, and is caught by the fault window as a fallback to the compiled
default. Safe — but by detection rather than by construction, which is weaker.

It also spends the whole knob on settings worth having. A divider across the
same resistors would have reached 62 °C, and a third of the travel would have
been setpoints nobody would choose for this box.

**R8 and R9 still earn their place**, because the wiring cannot catch a broken
*lead*: R8 open pulls the node to ground, R9 open pulls it to the rail, and a
missing pot leaves it grounded through R9. All three land near 0 or 1023, so the
window sits at **450–850** — wide enough for a +20 % pot at full travel, and
still nowhere near a real fault. On that fault the firmware falls back to the compiled default rather
than to fan-on — a known-good threshold beats a fan that runs forever — and the
display flags that the pot is being ignored.

### One pot, not two

There is deliberately no second pot for the release point.

**Two independent pots can be set to a state that cannot work** — nothing stops
OFF being placed above ON, and a quarter turn gives you a fan that trips and
immediately releases, or never releases at all.

**And the hysteresis width is a property of the plant, not a preference.** The
thing being controlled is a box of air with a long time constant; a narrow band
only cycles the fan without moving the average temperature. A knob for it is a
control whose sole available use is to make the system worse. It stays fixed at
61 counts, which rides across the range as:

| setpoint | releases at | band |
|---|---|---|
| 30 °C | 24.5 | 5.5 |
| 38 °C | 32.0 | 6.0 |
| 45 °C | 38.3 | 6.7 |
| 60 °C | 50.7 | 9.3 |

A fixed count band widens in degrees as it gets hotter, because the NTC's
counts-per-degree falls. That is the right direction to drift: a higher setpoint
means a hotter box, where you want the fan to run on longer rather than trip
in and out.

**PA5 stays free** — a tach input if a 3-wire fan is ever fitted.

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
