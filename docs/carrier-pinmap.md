# Carrier pin map — STM32F767ZIT6 on the MCU module

**Decided 2026-10-17.** Every carrier function on a port pin, and through
[`mcu_pinout.py`](Schematics/KiCad/TritonECU-MCU/mcu_pinout.py) on a module
header pad. The source of truth is
[`carrier_pinmap.py`](Schematics/KiCad/TritonECU-Main/carrier_pinmap.py); this
table is its output (`python3 carrier_pinmap.py --md`). Firmware's `Board.h`
and the carrier schematic follow it.

**101 signals on 105 usable pins, 4 spare** (PA10, PC12, PG11, PG12). PG10 became `ADC_REF_EN` with the ADC sheet.

## The budget was short, not long

[`pin-budget.md`](pin-budget.md) said **83 of ~114, 29 spare**. Counted against
every design document, the carrier needs **115**, and the module has **105**
usable port pins (110, less SWDIO, SWCLK and SWO on the STDC14 and the ST-Link
VCP on PD8/PD9). The 83 left out:

| Missed | Pins |
|---|--:|
| Internal ADC inputs ([`adc-front-end.md`](adc-front-end.md)'s 16 plus knock, less TR3A, already counted as an input) | 16 |
| SD card, SDMMC 4-bit | 6 |
| USB FS + VBUS sense | 3 |
| Standby wake pins: key-on and CAN | 2 |
| Console UART | 2 |
| Power board: it brings out nine signals (I²C, `M_SYNC`, `U_SHDN`, `3.3_ENOUT`, `5_GOOD`, `3_GOOD`, `FLT`, `VIN_ALERT`), not seven | 2 |
| 74HCT541 #1 `OE1`, the firmware "ignition armed" enable ([`Schematics/schematic-ecu-v1.txt`](Schematics/schematic-ecu-v1.txt) §5) | 1 |
| **Total** | **32** — 83 + 32 = 115 |

Trimmed with the user, **with no loss of function**:

| Trim | Saves |
|---|--:|
| Console UART dropped: the STLINK-V3's VCP on the module's STDC14 (USART3) is the console | 2 |
| ADS8588H OS0–2 and RANGE strapped (0 Ω options keep them changeable); FRSTDATA not wired | 5 |
| SD card on SDMMC2 **1-bit** — config and logs only | 3 |
| Power board `3_GOOD` not wired: if 3.3 V fails the MCU cannot read it | 1 |
| TPS2H160B `DIAG_EN` tied high | 1 |
| The 8 slow diagnostics (6 drain senses, supply senses 1138 and 391) behind a **74HC4051**, as in [`analog-mux-scan.md`](analog-mux-scan.md): 8 ADC pins become 1 + 3 selects | 4 |
| **Total** | **16** |

The VREF short-to-battery sense keeps its own ADC pin: the 4051 has eight inputs.

## Constraints the checker enforces

* **Timers.** Coils on TIM4 and TIM8 (all eight on header C), injectors on
  TIM1, TIM3 and TIM12, each with its own output-compare channel, so every edge
  is hardware-timed. CKP, CMP, the ADS8588H `CONVST` and J1850 RX share **TIM2**,
  the 32-bit timebase, so a crank tooth, an ADC conversion and an SCP bit are
  stamped on one clock. A timer is either free-running (scheduling, capture) or
  fixed-period PWM, never both: EPC, TCC and IAC each have their own PWM timer,
  EVAP and EGR share TIM9's period. VSS out is a compare toggle on TIM5. **TIM14
  stays free** for the firmware's watchdog guard tick.
* **ADC pins are the scarce resource**, not GPIO. Nearly every timer pin that is
  not also an ADC input is used. The external ADC moved from the bench's SPI2
  to **SPI3** (PC10/PC11), and the SD card from SPI4 to **SDMMC2** (Port D/G),
  to free the timer and ADC pins those buses sat on. All ten analog inputs are
  on header A; knock is on ADC1 (PC3) for the 200 kSPS path.
* **EXTI lines: all 16 are used**, one per pin number across all ports. The
  three slow VR channels (OSS, TSS, transfer case) are EXTI plus a timestamp, as
  the wiring view always had them. **Any new interrupt input needs a line freed
  first** — the six spare pins are all on lines already taken.
* **Standby wakes only on a WKUP pin** (PA0, PA2, PC1, PC13 on this package), not
  on an ordinary EXTI. Key-on is **PC13 / WKUP4**. The CAN transceiver's `RXD`
  goes to **CAN1_RX (PD0) and to PA0 / WKUP1** — one net, two pins — so bus
  activity can wake a sleeping ECU. [`can-bus.md`](can-bus.md) said "any
  EXTI-capable pin", which would never wake it from Standby.
* **J1850 TX_P and TX_N share Port G**, so one BSRR write switches both.

## Firmware consequences

The Nucleo bench keeps its current wiring until the carrier exists. When
`Board.h` moves to this map:

* ADS8588H: SPI2 → **SPI3**; `OS0–2`, `RANGE`, `FRSTDATA` go away.
* SD: SPI4 → **SDMMC2 1-bit** (PD6 CK, PD7 CMD, PG9 D0).
* Console: USART2 PD5/PD6 → the ST-Link VCP, USART3 PD8/PD9.
* Watchdog kick: PF13 → **PD10**.
* HO2S heaters are software PWM (ramp, stagger), not timer outputs.

## Pin table, by module header

| pad | pin | net | function | group | note |
|---|---|---|---|---|---|
| A4 | PE2 | **ENOUT** | GPIO | power | 3.3_ENOUT, LTC4364 enable |
| A5 | PE3 | **M_SYNC** | GPIO | power | MAX25239 SYNC; 10k pull-down on the power board |
| A6 | PE4 | **FLT** | GPIO | power |  |
| A7 | PE5 | **EVAP** | TIM9_CH1 | pwm | purge, pin 56; shares TIM9 period with EGR |
| A8 | PE6 | **EGR** | TIM9_CH2 | pwm | EVR, pin 47 |
| A10 | PC13 | **IGN_WAKE** | WKUP4 | power | key-on sense, conditioned; also key-off detect |
| A11 | PF0 | **I2C_SDA** | I2C2_SDA | power | power board, INA238, baro |
| A12 | PF1 | **I2C_SCL** | I2C2_SCL | power |  |
| A13 | PF2 | **U_SHDN** | GPIO | power |  |
| A14 | PF3 | **DPFE** | ADC | analog |  |
| A15 | PF4 | **TFT** | ADC | analog | tft-sensor.md |
| A16 | PF5 | **VIN_ALERT** | GPIO | power |  |
| A19 | PF6 | **O2_DN1** | ADC | analog | HO2S #12, buffered |
| A20 | PF7 | **O2_DN2** | ADC | analog | HO2S #22, buffered |
| A21 | PF8 | **IAC** | TIM13_CH1 | pwm | pin 83, own timer |
| A22 | PF9 | **VREF_FAULT** | GPIO | vref |  |
| A23 | PF10 | **FP_MON** | ADC | analog | fuel pump monitor |
| A25 | PC0 | **TR3A** | ADC | analog | three-state, 4R100 270R; 4r100-deltas.md |
| A26 | PC1 | **VREF_CS** | ADC | analog | TPS2H160B current sense, via 4.7k + Schottky |
| A27 | PC2 | **VREF_STB** | ADC | analog | VREF feed short-to-battery divider |
| A28 | PC3 | **KNOCK** | ADC1 | analog | 200 kSPS on ADC1, adc-front-end.md |
| A31 | PA0 | **CAN_RX_WAKE** | WKUP1 | can | SAME NET as CAN_RX: Standby wakes only on a WKUP pin |
| A32 | PA1 | **J1850_RX** | TIM2_CH2 | j1850 | capture on the TIM2 timebase |
| A33 | PA2 | **MUX_OUT** | ADC | analog | 74HC4051 COM: drain sense x6 (HO2S x4, EVAP, vent), supply sense 1138, 391 |
| B2 | PA3 | **VSS_OUT** | TIM5_CH4 | pwm | pin 68 open drain via NCV8405A #13; frequency by compare toggle |
| B5 | PA4 | **O2_BIAS** | DAC_OUT1 | analog | DAC -> 1k -> 455 mV bias node, o2-input-stage.md |
| B6 | PA5 | **TACH** | GPIO | test | software square wave |
| B7 | PA6 | **SPEED** | GPIO | test | software square wave |
| B8 | PA7 | **MUX_S2** | GPIO | analog | 74HC4051 select |
| B9 | PC4 | **VREF_IN2** | GPIO | vref |  |
| B10 | PC5 | **VREF_SEL** | GPIO | vref |  |
| B11 | PB0 | **MUX_S0** | GPIO | analog | 74HC4051 select |
| B12 | PB1 | **MUX_S1** | GPIO | analog | 74HC4051 select |
| B13 | PB2 | **VREF_EN** | GPIO | vref |  |
| B14 | PF11 | **TR1** | GPIO | input | pin 34 |
| B15 | PF12 | **TR2** | GPIO | input | pin 49 |
| B18 | PF13 | **VREF_IN1** | GPIO | vref |  |
| B19 | PF14 | **TR4** | GPIO | input | pin 50 |
| B20 | PF15 | **BRAKE** | GPIO | input |  |
| B21 | PG0 | **ACC** | GPIO | relay | A/C clutch |
| B22 | PG1 | **5_GOOD** | GPIO | power |  |
| B23 | PE7 | **FPUMP** | GPIO | relay |  |
| B24 | PE8 | **4X4L** | GPIO | input | 4x4 low. [CONFIRM] no PCM pin found for it in either pinout source |
| B25 | PE9 | **INJ1** | TIM1_CH1 | injection |  |
| B28 | PE10 | **ACP** | GPIO | input | A/C pressure |
| B29 | PE11 | **INJ2** | TIM1_CH2 | injection |  |
| B30 | PE12 | **FAN1** | GPIO | relay |  |
| B31 | PE13 | **INJ3** | TIM1_CH3 | injection |  |
| B32 | PE14 | **INJ4** | TIM1_CH4 | injection |  |
| B33 | PE15 | **FAN2** | GPIO | relay |  |
| B34 | PB10 | **CMP** | TIM2_CH3 | vr | cam; capture on TIM2 |
| B35 | PB11 | **ADC_CONVST** | TIM2_CH4 | adc | CONVSTA+B; compare output on the crank timebase |
| C2 | PB12 | **SSB** | GPIO | solenoid | pin 11 (5.4L; 1 is the 4.6L pin) |
| C3 | PB13 | **CCS** | GPIO | pwm | coast clutch, pin 20, #2 ch7 |
| C4 | PB14 | **INJ7** | TIM12_CH1 | injection |  |
| C5 | PB15 | **INJ8** | TIM12_CH2 | injection |  |
| C6 | PD8 | — | reserved | module | USART3 TX, ST-Link VCP (STDC14) |
| C7 | PD9 | — | reserved | module | USART3 RX, ST-Link VCP (STDC14) |
| C8 | PD10 | **WDI** | GPIO | ignition | TPS3823A-33 kick; its RESET drives OE2 of #1 and OE of #3. NO pull resistor |
| C9 | PD11 | **COIL_ARM** | GPIO | ignition | 74HCT541 #1 OE1: engine position known, ignition armed |
| C10 | PD12 | **COIL1** | TIM4_CH1 | ignition |  |
| C11 | PD13 | **COIL2** | TIM4_CH2 | ignition |  |
| C14 | PD14 | **COIL3** | TIM4_CH3 | ignition |  |
| C15 | PD15 | **COIL4** | TIM4_CH4 | ignition |  |
| C16 | PG2 | **HTR11** | GPIO | solenoid | HO2S #11 heater, software PWM (ramp, stagger) |
| C17 | PG3 | **HTR21** | GPIO | solenoid | HO2S #21 heater |
| C18 | PG4 | **HTR12** | GPIO | solenoid | HO2S #12 heater |
| C19 | PG5 | **HTR22** | GPIO | solenoid | HO2S #22 heater |
| C20 | PG6 | **VENT** | GPIO | solenoid | canister vent, pin 67 |
| C21 | PG7 | **IMCC** | GPIO | solenoid | pin 46 |
| C22 | PG8 | **SSA** | GPIO | solenoid | pin 6 (5.4L; 27 is the 4.6L pin) |
| C25 | PC6 | **COIL5** | TIM8_CH1 | ignition |  |
| C26 | PC7 | **COIL6** | TIM8_CH2 | ignition |  |
| C27 | PC8 | **COIL7** | TIM8_CH3 | ignition |  |
| C28 | PC9 | **COIL8** | TIM8_CH4 | ignition |  |
| C29 | PA8 | **PWM_OE** | GPIO | pwm | 74HCT541 #2 OE, software-releasable |
| C30 | PA9 | **USB_VBUS** | USB_OTG_FS_USB_OTG_FS | usb | via divider |
| C31 | PA10 | *spare* | | | |
| C32 | PA11 | **USB_DM** | USB_OTG_FS_USB_OTG_FS | usb | tuning path |
| C33 | PA12 | **USB_DP** | USB_OTG_FS_USB_OTG_FS | usb |  |
| C34 | PA13 | — | reserved | module | SWDIO (STDC14) |
| D2 | PA14 | — | reserved | module | SWCLK (STDC14) |
| D3 | PA15 | **CKP** | TIM2_CH1 | vr | 36-1 crank; capture on the 32-bit TIM2 timebase |
| D4 | PC10 | **ADC_SCK** | SPI3_SCLK | adc |  |
| D5 | PC11 | **ADC_MISO** | SPI3_MISO | adc | DOUTA |
| D6 | PC12 | *spare* | | | |
| D7 | PD0 | **CAN_RX** | CAN1_CAN_RD | can |  |
| D8 | PD1 | **CAN_TX** | CAN1_CAN_TD | can |  |
| D9 | PD2 | **ADC_CS** | GPIO | adc | software chip select |
| D10 | PD3 | **ADC_BUSY** | GPIO | adc | falling edge = data ready |
| D11 | PD4 | **ADC_RESET** | GPIO | adc | active high; OS0-2, RANGE strapped, FRSTDATA not wired |
| D12 | PD5 | **CAN_STB** | GPIO | can | not strapped: standby is what reaches 20 uA |
| D15 | PD6 | **SD_CK** | SDMMC2_SD_CK | storage | 1-bit |
| D16 | PD7 | **SD_CMD** | SDMMC2_SD_CMD | storage |  |
| D17 | PG9 | **SD_D0** | SDMMC2_SD_DATA0 | storage |  |
| D18 | PG10 | **ADC_REF_EN** | GPIO | adc | MAX6070AAUT25 EN, 10k pulldown: gated off in Standby, always-on-domain.md |
| D19 | PG11 | *spare* | | | |
| D20 | PG12 | *spare* | | | |
| D21 | PG13 | **J1850_TXP** | GPIO | j1850 | same port as TXN: one BSRR write |
| D22 | PG14 | **J1850_TXN** | GPIO | j1850 |  |
| D25 | PG15 | **J1850_NSLEEP** | GPIO | j1850 |  |
| D26 | PB3 | — | reserved | module | SWO (STDC14) |
| D27 | PB4 | **INJ5** | TIM3_CH1 | injection |  |
| D28 | PB5 | **INJ6** | TIM3_CH2 | injection |  |
| D29 | PB6 | **OSS** | GPIO | vr | output shaft; EXTI + timestamp |
| D30 | PB7 | **TSS** | GPIO | vr | turbine shaft, pin 59; EXTI + timestamp |
| D32 | PB8 | **EPC** | TIM10_CH1 | pwm | NCV8408B, pin 81, >= 200 Hz, own timer |
| D33 | PB9 | **TCC** | TIM11_CH1 | pwm | pin 54, own timer |
| D34 | PE0 | **TC_SPEED** | GPIO | vr | transfer case, pin 7; EXTI + timestamp |
| D35 | PE1 | **TCS** | GPIO | input | O/D cancel switch, pin 29; polled, all EXTI lines are taken |
