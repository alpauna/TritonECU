#pragma once
// Per-board default pin assignments.
//
// These are only the *defaults*. Every value is overridable from /config.txt on
// the SD card (see Config.cpp) and editable from the /pins web page, so a board
// respin does not need a firmware change. Selected by the board flag in
// platformio.ini.

#if defined(BOARD_ESP32_P4)

// ---------------------------------------------------------------------------
// Waveshare ESP32-P4-WIFI6  (ESP32-P4NRW32 + ESP32-C6-MINI-1)
//
// Only 27 GPIOs reach the 2x20 header; everything else is committed on-board:
//   GPIO 9-13   I2S audio codec (ES8311) + microphone
//   GPIO 14-19  SDIO link to the ESP32-C6 — this is the Wi-Fi/BLE transport
//   GPIO 35-38  boot strapping (35/36) and UART0 to the CH343 (37/38)
//   GPIO 39-45  SD/TF card on SDMMC slot 0 (45 = card power enable)
//   GPIO 53     speaker amplifier enable
//   GPIO 54     ESP32-C6 reset
//
// Two consequences drive the map below:
//   1. The C6 link occupies GPIO16-19, which are ADC1 channels 0-3. Only
//      ADC1 CH4-7 (GPIO20-23) survive, so the four fastest/most critical
//      analog channels go there and the slow ones go on ADC2 (GPIO49-52).
//      ADC2 is genuinely usable here, unlike on the S3 — the P4 has no on-die
//      radio to contend for it.
//   2. The SD card is on the native SDMMC controller, not SPI, so the four
//      SD SPI pins the S3 build needed are freed.
//
// GPIO24/25 are the USB 2.0 HS D-/D+ pair and are deliberately left alone.
// GPIO46-48 sit in the GPIO39-48 bank fed by on-chip LDO VO4; the Arduino
// periman enables VO4 on demand (BOARD_PERIMAN_IO_LDO_AUTO), so they are safe.
// ---------------------------------------------------------------------------

#define BOARD_PROFILE_NAME "ESP32-P4-WIFI6 Rev 1.0"

// Analog — ADC1 CH4-7, the only ADC1 channels left after the C6 link
#define DEF_PIN_O2_BANK1    20   // ADC1_CH4 — CJ125 UA bank 1
#define DEF_PIN_O2_BANK2    21   // ADC1_CH5 — CJ125 UA bank 2
#define DEF_PIN_MAP         22   // ADC1_CH6
#define DEF_PIN_TPS         23   // ADC1_CH7
// Analog — ADC2, slow-changing channels
#define DEF_PIN_CLT         49   // ADC2_CH0
#define DEF_PIN_IAT         50   // ADC2_CH1
#define DEF_PIN_VBAT        51   // ADC2_CH2 — 47k/10k divider, 5.7:1
#define DEF_PIN_OIL_PRESS   52   // ADC2_CH3

// Crank/cam triggers — ISR inputs, kept on low-numbered pins in the base bank
#define DEF_PIN_CRANK        2
#define DEF_PIN_CAM          3

// PWM outputs
#define DEF_PIN_ALTERNATOR   4   // 25 kHz field drive
#define DEF_PIN_HEATER1      5   // 100 Hz — CJ125 heater bank 1
#define DEF_PIN_HEATER2     26   // 100 Hz — CJ125 heater bank 2
#define DEF_PIN_TCC         28   // torque converter clutch
#define DEF_PIN_EPC         29   // electronic pressure control

// SPI — MCP23S17 expander chain + MCP3204 ADC
#define DEF_PIN_HSPI_SCK    27
#define DEF_PIN_HSPI_MOSI   32
#define DEF_PIN_HSPI_MISO   33
#define DEF_PIN_HSPI_CS     46   // shared CS; MCP23S17 A0-A2 select the chip
#define DEF_PIN_MCP3204_CS  31

// I2C — fixed by the board silkscreen
#define DEF_PIN_I2C_SDA      7
#define DEF_PIN_I2C_SCL      8

// Wired-OR expander interrupt
#define DEF_PIN_SHARED_INT  30

// SD card is on SDMMC slot 0, not SPI. 0xFF = unused.
#define DEF_PIN_SD_CLK    0xFF
#define DEF_PIN_SD_MISO   0xFF
#define DEF_PIN_SD_MOSI   0xFF
#define DEF_PIN_SD_CS     0xFF

// Unassigned and reachable on the header: GPIO47, GPIO48.
// Reserved for a TWAI (CAN) transceiver — the P4 has two TWAI controllers.
#define BOARD_SPARE_GPIO_A  47
#define BOARD_SPARE_GPIO_B  48

#elif defined(BOARD_ESP32_S3_WROOM)

// ---------------------------------------------------------------------------
// Freenove ESP32-S3-WROOM — the original board. SD card on SPI.
// ---------------------------------------------------------------------------

#define BOARD_PROFILE_NAME "ESP32-S3 Rev 1.0"

#define DEF_PIN_O2_BANK1     3
#define DEF_PIN_O2_BANK2     4
#define DEF_PIN_MAP          5
#define DEF_PIN_TPS          6
#define DEF_PIN_CLT          7
#define DEF_PIN_IAT          8
#define DEF_PIN_VBAT         9
#define DEF_PIN_OIL_PRESS    0   // 0 = not set

#define DEF_PIN_CRANK        1
#define DEF_PIN_CAM          2

#define DEF_PIN_ALTERNATOR  41
#define DEF_PIN_HEATER1     19
#define DEF_PIN_HEATER2     20
#define DEF_PIN_TCC         45
#define DEF_PIN_EPC         46

#define DEF_PIN_HSPI_SCK    10
#define DEF_PIN_HSPI_MOSI   11
#define DEF_PIN_HSPI_MISO   12
#define DEF_PIN_HSPI_CS     13
#define DEF_PIN_MCP3204_CS  15

#define DEF_PIN_I2C_SDA      0
#define DEF_PIN_I2C_SCL     42

#define DEF_PIN_SHARED_INT  0xFF

#define DEF_PIN_SD_CLK      47
#define DEF_PIN_SD_MISO     48
#define DEF_PIN_SD_MOSI     38
#define DEF_PIN_SD_CS       39

#else
#error "No board selected — define BOARD_ESP32_P4 or BOARD_ESP32_S3_WROOM in platformio.ini"
#endif

// ---------------------------------------------------------------------------
// Expander pin numbering — identical on both boards.
// 200+ addresses MCP23S17 chips: 200 + (chip * 16) + port pin.
// ---------------------------------------------------------------------------
#define DEF_PIN_FUEL_PUMP   200   // MCP23S17 #0 P0
#define DEF_PIN_TACH_OUT    201   // MCP23S17 #0 P1
#define DEF_PIN_CEL         202   // MCP23S17 #0 P2
#define DEF_PIN_CJ125_SS1   208   // MCP23S17 #0 P8
#define DEF_PIN_CJ125_SS2   209   // MCP23S17 #0 P9
#define DEF_PIN_SS_A        216   // MCP23S17 #1 P0
#define DEF_PIN_SS_B        217   // MCP23S17 #1 P1
#define DEF_PIN_SS_C        218   // MCP23S17 #1 P2 — 4R100 only
#define DEF_PIN_SS_D        219   // MCP23S17 #1 P3 — 4R100 only
#define DEF_COIL_PIN_BASE   264   // MCP23S17 #4 P0..P7
#define DEF_INJ_PIN_BASE    280   // MCP23S17 #5 P0..P7
