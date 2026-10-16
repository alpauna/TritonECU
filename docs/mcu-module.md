# MCU module — STM32F767ZIT6 on a 44 × 44 mm daughterboard

**Decided 2026-10-16.** The Nucleo-144 takes about 70 × 133 mm of the
158 × 174 carrier, roughly a third of the usable area. It is replaced by a
small module carrying only the MCU and its essential parts. That leaves room on
the carrier for the drivers, the analog front end and the CAN/J1850
interfaces. The module stacks the same way as the power board, on **10 mm M3
standoffs**.

This keeps what the Nucleo stage was for ([`carrier-board.md`](carrier-board.md)):
the MCU section is a separate, swappable board, so a carrier respin never
touches it and a damaged MCU is a module swap. Ethernet was already dropped,
and USB is the tuning path, so the module needs **no PHY, magnetics or RJ45**.

## What is on the module

| Item | Detail |
|---|---|
| MCU | STM32F767ZIT6, LQFP144 (same silicon as the Nucleo's F767ZI) |
| HSE | **8 MHz crystal** on PH0/PH1 |
| LSE | 32.768 kHz crystal on PC14/PC15 for the RTC (Standby + RTC, [`always-on-domain.md`](always-on-domain.md)) |
| Decoupling | 100 nF per VDD pin, bulk 4.7 µF; VCAP_1/VCAP_2 2.2 µF each |
| VDDA / VREF+ | ferrite from VDD, 1 µF + 100 nF; VREF+ tied to VDDA |
| PDR_ON | tied to VDD (internal supervisor on) |
| BOOT0 | 10 k pull-down, also on header D |
| NRST | 100 nF on the module; the carrier's TPS3823 drives it via header A |
| SWD | a Tag-Connect TC2030 footprint on the module, and PA13/PA14 + NRST on the headers so the carrier can have its own SWD header too |
| Regulator | **none.** +3.3 V comes from the power board's TLV62085 through the carrier |

## Interconnect

Four **2×18, 1.27 mm** through-hole headers, one on each side of the QFP, give
a **10 mm mated height** to match the standoffs. Each header carries the pins of
the QFP side it faces, in package order, so the module escape is a straight
fan-out with no crossings. **All 110 port pins are broken out**, everything
except the four crystal pins. The carrier's pin assignment
([`pin-budget.md`](pin-budget.md), 83 of ~114) therefore stays free; nothing is
fixed by the module.

The source of truth is
[`Schematics/KiCad/TritonECU-MCU/mcu_pinout.py`](Schematics/KiCad/TritonECU-MCU/mcu_pinout.py).
The carrier footprint `TritonECU-Main:MCUModule_F767_Mate` (DB3) is generated
from it by `TritonECU-Main/gen_floorplan.py`. Running the script checks that
every port pin appears exactly once.

Each header has 36 pins. Odd numbers are the inner row (nearer the QFP), and
pin 1 is at the start of each side in package order:

| Header | Side | Package pins |
|---|---|---|
| A | left | 1–36, top → bottom (pin 1 corner) |
| B | bottom | 37–72, left → right |
| C | right | 73–108, bottom → top |
| D | top | 109–144, right → left |

## Firmware consequence

The Nucleo's HSE comes from the ST-LINK's 8 MHz MCO, in **bypass** mode. The
module has a real crystal. The PLL settings stay identical because the
frequency is the same 8 MHz, but `SystemClock_Config` must switch
`RCC_HSE_BYPASS` to `RCC_HSE_ON`. Firmware that runs on the Nucleo will fall
back to HSI, or fail to start HSE, until that change is made.

## Open

- **Header parts:** a 1.27 mm header/socket pair with 10 mm mated height
  (Samtec FTSH/SFM-family or equivalent) — **TBD**. The footprint uses the
  standard 0.65 mm drill / 1.0 mm pad.
- Module schematic and PCB (4-layer): `TritonECU-MCU/` project, not started.
- USB: PA11/PA12 come out on header C. The connector, ESD protection and VBUS
  sense live on the carrier.

## Pinout

| pad | net | pad | net |
|---|---|---|---|
| A1 | GND | A2 | GND |
| A3 | GND | A4 | PE2 |
| A5 | PE3 | A6 | PE4 |
| A7 | PE5 | A8 | PE6 |
| A9 | VBAT | A10 | PC13 |
| A11 | PF0 | A12 | PF1 |
| A13 | PF2 | A14 | PF3 |
| A15 | PF4 | A16 | PF5 |
| A17 | GND | A18 | +3.3V |
| A19 | PF6 | A20 | PF7 |
| A21 | PF8 | A22 | PF9 |
| A23 | PF10 | A24 | NRST |
| A25 | PC0 | A26 | PC1 |
| A27 | PC2 | A28 | PC3 |
| A29 | +3.3V | A30 | GND |
| A31 | PA0 | A32 | PA1 |
| A33 | PA2 | A34 | GND |
| A35 | GND | A36 | GND |
| B1 | GND | B2 | PA3 |
| B3 | GND | B4 | +3.3V |
| B5 | PA4 | B6 | PA5 |
| B7 | PA6 | B8 | PA7 |
| B9 | PC4 | B10 | PC5 |
| B11 | PB0 | B12 | PB1 |
| B13 | PB2 | B14 | PF11 |
| B15 | PF12 | B16 | GND |
| B17 | +3.3V | B18 | PF13 |
| B19 | PF14 | B20 | PF15 |
| B21 | PG0 | B22 | PG1 |
| B23 | PE7 | B24 | PE8 |
| B25 | PE9 | B26 | GND |
| B27 | +3.3V | B28 | PE10 |
| B29 | PE11 | B30 | PE12 |
| B31 | PE13 | B32 | PE14 |
| B33 | PE15 | B34 | PB10 |
| B35 | PB11 | B36 | +3.3V |
| C1 | GND | C2 | PB12 |
| C3 | PB13 | C4 | PB14 |
| C5 | PB15 | C6 | PD8 |
| C7 | PD9 | C8 | PD10 |
| C9 | PD11 | C10 | PD12 |
| C11 | PD13 | C12 | GND |
| C13 | +3.3V | C14 | PD14 |
| C15 | PD15 | C16 | PG2 |
| C17 | PG3 | C18 | PG4 |
| C19 | PG5 | C20 | PG6 |
| C21 | PG7 | C22 | PG8 |
| C23 | GND | C24 | +3.3V |
| C25 | PC6 | C26 | PC7 |
| C27 | PC8 | C28 | PC9 |
| C29 | PA8 | C30 | PA9 |
| C31 | PA10 | C32 | PA11 |
| C33 | PA12 | C34 | PA13 |
| C35 | GND | C36 | +3.3V |
| D1 | GND | D2 | PA14 |
| D3 | PA15 | D4 | PC10 |
| D5 | PC11 | D6 | PC12 |
| D7 | PD0 | D8 | PD1 |
| D9 | PD2 | D10 | PD3 |
| D11 | PD4 | D12 | PD5 |
| D13 | GND | D14 | +3.3V |
| D15 | PD6 | D16 | PD7 |
| D17 | PG9 | D18 | PG10 |
| D19 | PG11 | D20 | PG12 |
| D21 | PG13 | D22 | PG14 |
| D23 | GND | D24 | +3.3V |
| D25 | PG15 | D26 | PB3 |
| D27 | PB4 | D28 | PB5 |
| D29 | PB6 | D30 | PB7 |
| D31 | BOOT0 | D32 | PB8 |
| D33 | PB9 | D34 | PE0 |
| D35 | PE1 | D36 | +3.3V |

110 port pins, 19 GND, 12 +3.3V, plus NRST, VBAT, BOOT0
