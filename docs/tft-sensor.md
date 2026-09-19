# TFT — transmission fluid temperature

**Closed from Ford's own service manual. No bench measurement needed.**

Source: `1999-Ford-F150-4wd-5.42v/4R70W_Ford_Transmission_Service_Manual[Helms].pdf`,
*Resistance/Continuity Tests — Transmission Fluid Temperature (TFT) Sensor*.

Wiring: **C183 pin 5**, circuit `923 OG/BK` → **PCM pin 37**, returning on
C183 pin 2 (`359 GY/RD`, SIGRTN). It is an **NTC thermistor** — physically a
glass axial bead on the inner pan harness, easily mistaken for a diode.

## Ford's table

| °C | °F | Resistance |
|---|---|---|
| −40 … −20 | −40 … −4 | 967 k – 284 k |
| −19 … −1 | −3 … 31 | 284 k – 100 k |
| **0 … 20** | 32 … 68 | **100 k – 37 k** |
| 21 … 40 | 69 … 104 | 37 k – 16 k |
| 41 … 70 | 105 … 158 | 16 k – 5 k |
| 71 … 90 | 159 … 194 | 5 k – 2.7 k |
| **91 … 110** | 195 … 230 | **2.7 k – 1.5 k** |
| 111 … 130 | 231 … 266 | 1.5 k – 0.8 k |
| 131 … 150 | 267 … 302 | 0.8 k – 0.54 k |

## A single β fits it — **β = 3987 K**, R₀ = 100 kΩ at 0 °C

`R(T) = 100 kΩ · exp(β(1/T − 1/273.15))`, T in kelvin.

| °C | Ford | β model | Error |
|--:|--:|--:|--:|
| 40 | 16.00 k | 15.50 k | −3.2 % |
| 70 | 5.00 k | 5.09 k | +1.8 % |
| 90 | 2.70 k | 2.68 k | −0.6 % |
| 110 | 1.50 k | 1.51 k | +0.9 % |
| 150 | 0.54 k | 0.57 k | +4.8 % |

**Within a few percent across 190 °C.** No Steinhart–Hart, no lookup table, and
Ford's own figures are band edges rather than points — so the residuals are
mostly the table's own granularity.

## ⭐ Pull up from **3.3 V**, not VREF — and that is not a style choice

TFT lands on the **STM32 internal ADC**, which is a **3.3 V** input.

> **A 5 V VREF pull-up reaches 4.99 V at −40 °C and 4.90 V at 0 °C. That is over
> the ADC's input range.** CHT and IAT can sit on VREF because they read on the
> ±10 V ADS8588H; TFT cannot.

Pulling up from 3.3 V also **removes it from the VREF load budget entirely** —
see the correction in [`vref-supply.md`](vref-supply.md).

### Value: **2.2 kΩ**

| °C | R<sub>th</sub> | V | Resolution |
|--:|--:|--:|--:|
| 0 | 100 k | 3.229 V | — |
| 40 | 15.5 k | 2.890 V | 11 LSB/°C |
| 70 | 5.09 k | 2.304 V | 24 LSB/°C |
| **90** | 2.69 k | **1.814 V** | **30 LSB/°C** |
| 110 | 1.51 k | 1.345 V | 29 LSB/°C |
| 150 | 0.57 k | 0.675 V | 18 LSB/°C |

**24 mV/°C where it matters** — 30 ADC counts per degree through the 90–110 °C
band that governs lockup and line pressure — and still 11 counts/°C down at
0–40 °C, where the only job is *"too cold, inhibit lockup."*

1.5 kΩ and 3.3 kΩ both work; 2.2 kΩ sits nearest the middle of the operating
band and loses least at the ends.

### Self-heating is not a concern

| °C | I | P in the bead |
|--:|--:|--:|
| 0 | 32 µA | 0.10 mW |
| 90 | 676 µA | **1.23 mW** |
| 150 | 1.19 mA | 0.81 mW |

A glass bead in fluid has a dissipation constant of a few mW/°C, so ~1 mW is
well under a degree.

> **Note the shape**: dissipation *peaks in the middle* of the range, not at
> either end — at high temperature the resistance is low but so is the voltage
> across it. Worth knowing before someone "checks the worst case" at 150 °C and
> finds the wrong number.
