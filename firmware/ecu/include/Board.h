#pragma once
// Pin map for the Waveshare ESP32-P4-WIFI6 carrier.
//
// Only 27 GPIOs reach the 2x20 header; the rest are committed on-board:
//   GPIO 9-13   I2S audio codec + microphone
//   GPIO 14-19  SDIO link to the ESP32-C6 (Wi-Fi/BLE transport)
//   GPIO 35-38  boot strapping and UART0 to the CH343
//   GPIO 39-45  SD card on SDMMC slot 0 (45 = card power)
//   GPIO 53,54  speaker amp enable, C6 reset
//
// Two consequences drive everything below:
//   1. The C6 link occupies GPIO16-19, which are ADC1 channels 0-3. Only ADC1
//      CH4-7 (GPIO20-23) survive.
//   2. GPIO24/25 are the USB 2.0 HS D-/D+ pair and are left alone.
//
// See docs/f150-1999-target.md for the full budget. Pins are assigned as
// milestones land, not up front — an unassigned pin here is a pin no code
// touches yet.

#include <stdint.h>

#if defined(ECU_BOARD_NUCLEO_F767ZI)

// ---------------------------------------------------------------------------
// STM32F767ZI Nucleo-144 — the truck ECU target.
//
// Chosen over the ESP32-P4 because rusEFI's Proteus ECU runs on this exact
// part, the board was already on the bench, and ~114 I/O against 37 needed
// removes the pin budget as a design constraint entirely.
//
// Room to grow, which was an explicit goal: 2 MB flash, 512 KB RAM, three CAN
// controllers, Ethernet, and more timer compare channels than this engine can
// use. Nothing here is sized to just barely fit.
// ---------------------------------------------------------------------------

namespace board {

constexpr const char* kName = "STM32F767ZI Nucleo-144";

// Nucleo-144 fixed hardware.
constexpr uint8_t kLedGreen = PB0;
constexpr uint8_t kLedBlue  = PB7;
constexpr uint8_t kLedRed   = PB14;
constexpr uint8_t kButton   = PC13;

// --- Console UART -----------------------------------------------------------
// The ST-Link's own VCP proved unreliable on this board: it drops characters
// even on a five-second heartbeat with no host traffic, at both 115200 and
// 57600. That is an ST-Link firmware/hardware issue, not something the
// application can fix.
//
// USART2 on PD5/PD6 is free (USART3 on PD8/PD9 is the ST-Link's) and takes an
// ordinary USB-UART adapter. Output goes to BOTH ports, so whichever is
// connected works and nothing needs reconfiguring.
namespace console {
constexpr uint8_t kTx = PD5;   // USART2_TX -> adapter RX
constexpr uint8_t kRx = PD6;   // USART2_RX <- adapter TX
constexpr uint32_t kBaud = 115200;
}  // namespace console

// --- SD card, SPI4 on Port E ------------------------------------------------
// Port E carries no fixed function on the Nucleo-144 -- no Ethernet, no
// ST-Link, no USB, no LEDs -- so it is the safest block to take. It also
// leaves the Arduino-header SPI alone, which matters because PA7 is
// RMII_CRS_DV on this board and the conventional SPI1 trio is already broken
// by Ethernet.
//
// SPI rather than SDMMC: four signals instead of six, and the card carries
// only config and logs, so bandwidth is not the constraint. If high-rate
// logging later needs it, SDMMC1 is available on PC8-PC12 + PD2.
namespace sd {
constexpr uint8_t kSck  = PE2;   // SPI4_SCK
constexpr uint8_t kMiso = PE5;   // SPI4_MISO
constexpr uint8_t kMosi = PE6;   // SPI4_MOSI
constexpr uint8_t kCs   = PE4;   // software-driven chip select
}  // namespace sd

// --- AD7606 analog front end, SPI2 -----------------------------------------
// Its own bus, separate from the SD card on SPI4. The ADC is sampled at engine
// rate and must never wait behind a card write.
//
// Avoids PB0/PB7/PB14 (LEDs) and PB13 (Ethernet RMII_TXD1).
namespace adc {
constexpr uint8_t kSck      = PB10;  // SPI2_SCK
constexpr uint8_t kMiso     = PC2;   // SPI2_MISO  <- AD7606 DOUTA
constexpr uint8_t kMosi     = PC3;   // SPI2_MOSI  (unused in hardware mode)
constexpr uint8_t kCs       = PB12;
constexpr uint8_t kConvst   = PB11;
constexpr uint8_t kBusy     = PB1;
constexpr uint8_t kReset    = PB2;
constexpr uint8_t kFrstdata = PB15;
constexpr uint8_t kOs0      = PB3;
constexpr uint8_t kOs1      = PB4;
constexpr uint8_t kOs2      = PB5;
constexpr uint8_t kRange    = PB6;
}  // namespace adc

// --- Pins committed by the Nucleo-144 itself --------------------------------
// Do not assign these. [CONFIRM] against UM1974 before finalising a carrier;
// this list is from the board family rather than the document.
//   Ethernet RMII : PA1 PA2 PA7 PB13 PC1 PC4 PC5 PG11 PG13
//   ST-Link VCP   : PD8 (TX) PD9 (RX)
//   USB OTG FS    : PA8 PA9 PA10 PA11 PA12
//   LEDs          : PB0 PB7 PB14
//   User button   : PC13
//   Oscillators   : PC14 PC15 (LSE), PH0 PH1 (HSE)

}  // namespace board

#else

namespace board {

constexpr const char* kName = "Waveshare ESP32-P4-WIFI6";

// --- Committed by the carrier board -----------------------------------------
constexpr uint8_t kI2cSda = 7;   // header silkscreen SDA
constexpr uint8_t kI2cScl = 8;   // header silkscreen SCL

// --- Free header GPIOs, in header order -------------------------------------
// 2 3 4 5 | 20 21 22 23 | 26 27 28 29 30 31 32 33 | 46 47 48 | 49 50 51 52
// (24/25 reserved: USB D-/D+)
//
// ADC-capable among these:
//   ADC1 CH4-7 : 20 21 22 23   <- the only ADC1 channels available
//   ADC2 CH0-3 : 49 50 51 52   <- usable here; the P4 has no on-die radio
constexpr uint8_t kAdc1Pins[] = {20, 21, 22, 23};
constexpr uint8_t kAdc2Pins[] = {49, 50, 51, 52};

// --- AD7606 external ADC (bench wiring, M2) ---------------------------------
// See docs/adc-wiring.md. Grouped so each side of the header is one run.
// In the final ECU, reset/frstdata/os0/os1/os2/range move to the MCP23S17
// expander chain — they are static, and do not deserve native pins.
namespace adc {
constexpr int8_t kSck      = 27;
constexpr int8_t kMiso     = 33;   // AD7606 DOUTA
constexpr int8_t kCs       = 46;
constexpr int8_t kConvst   = 26;
constexpr int8_t kBusy     = 28;
constexpr int8_t kReset    = 29;
constexpr int8_t kFrstdata = 30;
constexpr int8_t kOs0      = 31;
constexpr int8_t kOs1      = 47;
constexpr int8_t kOs2      = 48;
constexpr int8_t kRange    = 2;
}  // namespace adc

}  // namespace board

#endif  // board select
