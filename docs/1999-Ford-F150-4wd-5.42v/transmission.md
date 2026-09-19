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

**Confirmed by the owner:** TSS is fitted only on the 4R100. This truck has
none.

## DTR is confirmed digital

C182 is the **Digital** Transmission Range sensor — the name is explicit, and it
matches the MegaSquirt pinout showing four separate "Trans Pos Sensor" inputs
(pins 34, 49, 64, 50 — ✅ all four confirmed against DTR connector C182; pin 64
is **TR3A**, and it also carries 12 V while cranking because the DTR is the
neutral safety switch — [`schematic-findings.md`](schematic-findings.md) §21).
It is a 4-bit gear-position code on digital lines,
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

**Resolved:** the transfer case has its own **shift relay module (C221)** in the
dash, fed by the 4WD mode switch (C230). It is a self-contained subsystem and
the replacement ECU does not have to actuate it — see `dash-modules.md`. The
ECU may still want to *know* the range, since low range should change shift
points and line pressure.

## Outputs at C183 (from the EEC-V pinout)

| Function | ECU pin | Wire |
|---|---|---|
| SS1 — shift solenoid 1 | 6 | ORG/YEL |
| SS2 — shift solenoid 2 | 11 | VIO/ORG |
| CSS — coast clutch solenoid | 20 | BRN/ORG |
| TCC — torque converter clutch (PWM) | 54 | VIO/YEL |
| EPC — electronic pressure control (PWM) | 81 | WHT/YEL — needs a flyback diode to 12 V |
| TFT — transmission fluid temperature | 37 | ORG/BLK |

---

# ✅ C183 — the transmission connector, and it settles the solenoid count

`4R70W-Solenoid-Temp-Connector.png`. **This is the definitive sheet**, and it was
the hard one to find in the service documentation.

| Pin | Circuit | Function | PCM pin |
|--:|---|---|--:|
| 1 | — | **NOT USED** | |
| 2 | `359 GY/RD` | Signal return | **91** (SIGRTN) |
| 3 | `480 VT/YE` | **Torque converter clutch solenoid** | **54** |
| 4 | `1138 VT/WH` | **Vehicle power** | — *(not from us)* |
| 5 | `923 OG/BK` | **Transmission fluid temperature (TFT)** | **37** |
| 6 | `925 WH/YE` | **Electronic pressure control solenoid** | **81** |
| 7 | `237 OG/YE` | **Shift solenoid A** | **27** |
| 8 | `315 VT/OG` | **Shift solenoid B** | **1** |
| 9, 10 | — | **NOT USED** | |

## Four solenoids, and three unused cavities

**Pins 1, 9 and 10 are empty.** A fifth solenoid would have somewhere to go and
does not. That is **independent confirmation** that the 4R70W has exactly
**TCC, EPC, SSA and SSB** — and that CSS is a 4R100 part, as
[`../output-drivers.md`](../output-drivers.md) records.

Every circuit matches what was already assembled from Ford's 4R70W diagram, so
nothing moves. **What changes is the standard of proof**: this is a connector
sheet listing every cavity, not an inference from which wires happened to appear.

## ⭐ And it validates the freewheel decision precisely

**Pin 4 is `1138 VT/WH` — "Vehicle Power" — *at the transmission*.** That is the
common supply for all four solenoids.

[`../output-drivers.md`](../output-drivers.md) brought `1138` into the ECU on
**pin 82** so the PWM freewheel diodes for TCC and EPC return to it rather than
to VPWR. This sheet shows why that was right: **the return lands on the
solenoids' own feed rail**, so the recirculation loop is the solenoid and its
diode — not a path out through the connector, across the Battery Junction Box
and back.

## The transmission interface, complete

With C183 settled, every wire between the ECU and the transmission is now
enumerated:

| | Where | |
|---|---|---|
| TCC, EPC, SSA, SSB | **C183** | four drives out |
| TFT | **C183** | one analog in |
| Signal return | **C183** pin 2 | shared SIGRTN |
| TR1 / TR2 / TR3A / TR4 | **C182** (DTR) | four digital in — [`schematic-findings.md`](schematic-findings.md) §21 |
| TSS — turbine shaft speed | C192, `970 DG/WH` | PCM pin 59, VR |
| OSS — output shaft speed | separate | PCM pin 84, VR |

**Nothing over a bus, and nothing left unaccounted for.**
