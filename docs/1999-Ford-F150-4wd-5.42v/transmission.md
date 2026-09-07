# 4R70W transmission — sensors and connectors

Sources: `Transmission-Componet-Locations-1.png`, `Transmission-Componet-Locations-2.png`

The sheets cover three transmissions (4R70W, 4R100, M5R2 manual) in both 4x2 and
4x4. This truck is **4R70W, 4x4**, so only that combination applies — and the
differences between them matter.

## Connectors on the 4R70W 4x4

| Ref | Component |
|---|---|
| C183 | 4R70W transmission — main connector (solenoids) |
| C182 | **Digital transmission range (DTR) sensor** |
| C187 | **Output shaft speed (OSS) sensor** |
| C189 | 4x4 low and high indicator switch |
| C199 | **Transfer case speed sensor** |
| C201 | Transfer case assembly (electronic shift) |
| C260 | Transfer case assembly (mechanical shift) |
| C184, C185 | HO2S #12 and #22 pass-through (downstream sensors) |

## CORRECTION: the 4R70W has no turbine shaft speed sensor

Earlier documents recorded, from a forum source, that *"the TSS was put in the
later 4R70W around 1999"* and listed TSS as a required input.

The factory sheets show otherwise. **C192, turbine shaft speed (TSS), appears
only on the 4R100** — on both the 4x2 and 4x4 drawings. The 4R70W drawings show
C187 (OSS) and C182 (DTR) and no TSS at all.

The MegaSquirt pinout does list a TSS pin (59). That is consistent: the PCM
connector is shared across applications, so the pin exists for 4R100 trucks and
is simply unused on this one.

Consequences:

- **One fewer VR conditioning channel.** The VR count drops from three (CKP,
  OSS, TSS) to two (CKP, OSS), plus CMP if it turns out to be VR. A single
  dual-channel MAX9926 covers CKP and OSS.
- **No direct turbine speed means no direct converter-slip measurement.** Slip
  has to be inferred from engine rpm against OSS and the current gear ratio.
  That is workable for lockup control and shift scheduling, but it is an
  estimate rather than a measurement, and it is only valid once the gear is
  known with confidence.

**[CONFIRM ON TRUCK]** by looking for a sensor at the C192 location. It is
cheap to check and it changes the transmission control strategy.

## DTR is confirmed digital

C182 is the **Digital** Transmission Range sensor — the name is explicit, and it
matches the MegaSquirt pinout showing four separate "Trans Pos Sensor" inputs
(pins 34, 49, 50, 64). It is a 4-bit gear-position code on four digital lines,
not an analog ladder.

Four expander inputs, no ADC channel. Decode the pattern to PRNDL.

## 4x4 adds two things the 4x2 build would not need

1. **Transfer case speed sensor (C199).** On a 4x4 this sits downstream of the
   transfer case. **[CONFIRM]** which of C199 and C187 actually feeds the
   speedometer and cruise control on this truck — they measure different shafts
   and will disagree in low range.
2. **4x4 low/high indicator switch (C189).** Range state. It matters for
   transmission control: shift points and line pressure should not be the same
   in low range as in high.

**[CONFIRM]** whether the transfer case is the electronic-shift type (C201) or
mechanical (C260). If electronic, something has to drive it — and on this truck
that something is currently the GEM, not the PCM, so it may not be the
replacement ECU's problem at all.

## Outputs at C183 (from the EEC-V pinout)

| Function | ECU pin | Wire |
|---|---|---|
| SS1 — shift solenoid 1 | 6 | ORG/YEL |
| SS2 — shift solenoid 2 | 11 | VIO/ORG |
| CSS — coast clutch solenoid | 20 | BRN/ORG |
| TCC — torque converter clutch (PWM) | 54 | VIO/YEL |
| EPC — electronic pressure control (PWM) | 81 | WHT/YEL — needs a flyback diode to 12 V |
| TFT — transmission fluid temperature | 37 | ORG/BLK |
