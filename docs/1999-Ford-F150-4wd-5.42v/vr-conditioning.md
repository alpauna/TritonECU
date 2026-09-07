# VR sensor conditioning

Three sensors on this truck are variable-reluctance and cannot drive a GPIO:

| Sensor | Pins | Confirmed by |
|---|---|---|
| **CKP** — crankshaft position | 21 (+, DK BLU), 22 (−, GRY) | two-wire differential coil |
| **OSS** — output shaft speed | 84 | MegaSquirt notes: *"DFIN1 via LM1850"* — the LM1815 VR amplifier |
| **TSS** — turbine shaft speed | 59 | **[CONFIRM]** — assumed VR by analogy with OSS |

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

## Channel count

Three channels needed (CKP, OSS, TSS), possibly four if CMP turns out to be VR.
Two MAX9926 packages cover four. The knock sensor is **not** one of these — it
is a piezo needing a charge amplifier and a sampled ADC channel, not edge
detection.
