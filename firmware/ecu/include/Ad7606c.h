#pragma once
// AD7606C-16 — 8-channel, 16-bit, simultaneous-sampling SAR ADC.
//
// Ported from the bench-validated Teensy 4.1 driver in
// ~/Claude/LxScanner/firmware-teensy/src/main.cpp, which was checked against a
// known +/-1.24 V reference on 2026-08-27/28. The conversion sequence
// (CONVST pulse, BUSY wait, 8x 16-bit SPI read) and SPI_MODE0 are carried over
// unchanged because they were verified on hardware; only the surrounding
// structure differs — this samples on demand for the ECU rather than streaming
// frames over USB.
//
// Why this part rather than the P4's own ADC:
//   * True differential bipolar inputs. The MAF has a dedicated signal return
//     (circuit 968) separate from the ground its supply current flows in, so it
//     is only measurable correctly as a difference. The P4's single-ended ADC
//     cannot use that return at all.
//   * +/-10 V / +/-5 V ranges take 0-5 V sensors directly, no scaling op-amps.
//   * On-chip clamps to +/-16.5 V — real protection against a harness fault.
//   * Simultaneous sampling: every sensor captured at the same instant.
// See docs/1999-Ford-F150-4wd-5.42v/oem-connectors.md.
//
// Hardware mode: range and oversampling are set by pins, not registers, so
// MOSI is not required. RANGE is one setting shared across all 8 channels.

#include <Arduino.h>

namespace ad7606c {

constexpr uint8_t kChannels = 8;

enum class Range : uint8_t { kBipolar5V = 0, kBipolar10V = 1 };

// Hardware oversampling ratio, set on OS0..OS2. Higher ratios trade conversion
// time for noise: each step halves the noise floor's bandwidth.
enum class Oversampling : uint8_t {
    kNone = 0, kX2 = 1, kX4 = 2, kX8 = 3, kX16 = 4, kX32 = 5, kX64 = 6,
};

struct Pins {
    int8_t sck;
    int8_t miso;      // AD7606C DOUTA
    int8_t cs;        // software-driven, not hardware SPI CS
    int8_t convst;    // also drives WR on the usual breakouts
    int8_t busy;
    int8_t reset;
    int8_t range;
    int8_t os0, os1, os2;
    int8_t frstdata = -1;  // optional; -1 if not wired
};

bool begin(const Pins& pins, Range range = Range::kBipolar10V,
           Oversampling os = Oversampling::kX16);

// Triggers a conversion and reads all 8 channels. Returns false on BUSY
// timeout, which is a real signal — miswiring, no RESET, or a dead part —
// rather than something to retry blindly.
bool read(int16_t raw[kChannels]);

// Same, converted to volts using the configured range.
bool readVolts(float volts[kChannels]);

// Volts per LSB for the configured range.
float voltsPerCount();

Range range();
void setRange(Range r);   // takes effect on the next conversion

}  // namespace ad7606c
