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
