# VR sensor conditioning

Three sensors on this truck are variable-reluctance and cannot drive a GPIO:

| Sensor | Pins | Confirmed by |
|---|---|---|
| **CKP** — crankshaft position | 21 (+, DK BLU), 22 (−, GRY) | two-wire differential coil |
| **OSS** — output shaft speed | 84 | MegaSquirt notes: *"DFIN1 via LM1850"* — the LM1815 VR amplifier |
| ~~TSS~~ | 59 | **Not fitted.** C192 is 4R100-only — confirmed by the owner. The PCM pin exists for other applications |

**CMP (pin 85) is unresolved** — a single wire with no matching negative, which
is equally consistent with a Hall sensor or a single-ended VR. **[CONFIRM]**
before committing a channel.

## Why it cannot be done in software

A VR sensor is a coil and a magnet. Its output amplitude is proportional to
tooth speed, which spans a very wide range:

- **Cranking (~200 rpm):** a few hundred millivolts.
- **Redline:** tens of volts, enough to need clamping.

A fixed comparator threshold cannot serve both ends. Set it high enough to
reject noise at speed and the engine will not sync while cranking — which is
precisely when sync must be established. Set it low enough to catch cranking
and it triggers on ringing at speed.

The answer is an **adaptive-threshold zero-crossing detector**: track the
signal's own peak amplitude and set the threshold as a fraction of it.

## Recommended part: MAX9926

rusEFI's VR conditioner board (`hardware/VR_Board` in
[rusefi/rusefi](https://github.com/rusefi/rusefi), GPLv3) uses the
**MAX9926UAEE+** — a dual-channel adaptive VR interface in QSOP-16. Two
channels per package covers CKP and CMP, or CKP and OSS, from one part.

The full BOM is published (`vrs_io_1.csv`), which is a working reference rather
than a datasheet application note:

| Ref | Value | Part |
|---|---|---|
| U101 | MAX9926/9927 | MAX9926UAEE+ |
| C101, C102 | 1000 pF | input coupling |
| C103 | 10 µF | bulk |
| C104 | 0.1 µF | decoupling |
| R102–R112 | 5 kΩ | input network |
| R101, R113, R114 | 10 kΩ | |
| R137, R141 | 1 kΩ | |

rusEFI's own `VR_discrete/readme.md` points at
[mck1117/vr-interface](https://github.com/mck1117/vr-interface) as "much more
proven" than their discrete attempt — worth reading before designing one.

---

## Configuration — use Mode A2

The MAX9926 has four operating modes, selected by strapping two kinds of pin.
Zero-crossing is global (one `ZERO_EN` pin); the adaptive threshold is
**per channel** (`INT_THRS1`, `INT_THRS2`), so the two channels can run
differently if ever needed.

| Mode | ZERO_EN | INT_THRS | Zero crossing | Adaptive threshold | Bias source |
|---|---|---|---|---|---|
| A1 | VCC | VCC | on | on | **external divider** |
| **A2** | **GND** | **GND** | **on** | **on** | **internal 2.5 V** |
| B | VCC | GND | on | off | external |
| C | GND | VCC | off | off | external |

**Mode A2** is the right choice here. It keeps both features that matter and
uses the internal 2.5 V reference, which eliminates the external VCC/2
resistor-divider and its 0.1 µF + 10 µF bypass on *each* BIAS pin that Mode A1
would need. Same behaviour, fewer parts, less to get wrong.

Mode B is worth remembering as a later option, not a starting point: it
disables the internal adaptive threshold and takes the threshold from `EXT`,
typically a filtered PWM from the MCU. That would allow an rpm-dependent
threshold implemented in firmware — interesting once there is real cranking
data, pointless before it.

Mode C is a plain comparator and throws away the reason for using this part.

### Strapping for Mode A2

| Pin | Name | Connect to |
|---|---|---|
| 13 | ZERO_EN | **GND** — note it is internally pulled up to VCC through 10 kΩ, so it must be actively pulled low |
| 1 | INT_THRS1 | GND |
| 8 | INT_THRS2 | GND |
| 3 | BIAS1 | **GND** — required in A2; the internal reference is used instead |
| 6 | BIAS2 | GND |
| 2 | EXT1 | leave unconnected |
| 7 | EXT2 | leave unconnected |
| 12 | DIRN | leave unconnected — quadrature direction output, not useful for CKP or OSS |

### Power and outputs

| Pin | Name | Notes |
|---|---|---|
| 14 | VCC | **5 V** |
| 11 | GND | |
| 4 | COUT1 | **open-drain** — 10 kΩ pull-up |
| 5 | COUT2 | **open-drain** — 10 kΩ pull-up |

**Pull COUT up to 3.3 V, not 5 V.** The part runs from 5 V but the output is
open-drain, so the pull-up rail alone sets the logic level. That makes it
directly compatible with the ESP32-P4 with **no level shifter** — which is why
an open-drain output was chosen by the part's designers, and it is worth not
undoing by pulling up to 5 V out of habit.

Decoupling: 10 nF, 0.1 µF and 1 µF in parallel, with the **10 nF closest** to
the VCC/GND pins. The datasheet is unusually insistent about this because the
front-end amplifier uses an internal charge pump.

### Inputs — the 10 kΩ series resistors are not optional

| Pin | Name |
|---|---|
| 16 | IN1+ |
| 15 | IN1− |
| 9 | IN2+ |
| 10 | IN2− |

**A 10 kΩ series resistor in every input leg**, per the datasheet: it limits pin
current when the sensor voltage exceeds VCC and turns on the internal ESD
diodes. A VR sensor at engine speed swings far above 5 V, so this is a
guaranteed condition on this application, not an edge case.

Add a **filter capacitor across the op-amp inputs** to limit input bandwidth —
rusEFI use 1 nF, which with 10 kΩ puts the corner near 16 kHz. Note the series
resistors also lower the input amplifier's gain, so they interact with
threshold behaviour and should not be changed casually.

**[CONFIRM]** the datasheet's own pin table describes pin 15 (IN1−) as
"Noninverting Input 1" and pin 16 (IN1+) as "Inverting Input 1" — the
descriptions look transposed relative to the names. Trust the names. Polarity
is in any case testable on the bench, and an inversion only changes which edge
the decoder should trigger on.

### How the adaptive threshold behaves

Two mechanisms, and both matter for cranking:

- The threshold is set to **1/3 of the previous cycle's peak**, recomputed
  cycle by cycle. That is what tracks the signal from a few hundred millivolts
  at cranking to tens of volts at speed without any fixed level to get wrong.
- If the input stays below the threshold for more than **85 ms**, an internal
  watchdog drops the threshold to its minimum, so recognition recovers after an
  intermittent connection. At 200 rpm cranking a 36-1 tooth arrives every
  ~8.3 ms, so normal cranking never trips it — it is there for faults.

## Channel count

**Two channels needed — CKP and OSS** — plus CMP if it turns out to be VR
rather than Hall, and possibly the transfer case speed sensor (C199) on this
4x4. A single dual-channel MAX9926 covers CKP and OSS; a second package covers
the other two if needed.

The knock sensor is **not** one of these — it is a piezo needing a charge
amplifier and a sampled ADC channel, not edge detection.
