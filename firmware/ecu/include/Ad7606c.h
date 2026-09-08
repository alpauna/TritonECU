#pragma once
// AD7606C-16 — 8-channel, 16-bit, simultaneous-sampling SAR ADC.
//
// Ported from the bench-validated Teensy 4.1 driver in
// ~/Claude/LxScanner/firmware-teensy/src/main.cpp. The conversion sequence
// (CONVST pulse, BUSY wait, 8x 16-bit SPI read) is carried over unchanged
// because it was verified on hardware; only the surrounding structure differs —
// this samples on demand for the ECU rather than streaming frames over USB.
//
// The SPI mode did NOT carry over. The Teensy validated SPI_MODE0; the ESP32-P4
// needs SPI_MODE2. Modes 0, 1 and 3 all read exactly 2x high here — the
// signature of a one-clock bit shift. Established against two known signals on
// 2026-09-06. The mode is a property of the host/ADC pairing, not of the ADC.
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

// Hardware oversampling ratio, set on OS0..OS2. Higher ratios trade throughput
// for noise, and the setting is GLOBAL across all eight channels — at x16 the
// whole part drops to ~16 kSPS, which is useless for knock.
//
// Default is kNone, with averaging done in software instead: the same sqrt(N)
// noise reduction, applied per channel at whatever depth each one deserves,
// without throttling the fast channel. The analog anti-aliasing filter (22 kHz)
// is always in circuit and is unaffected by this setting.
// See docs/adc-front-end.md.
enum class Oversampling : uint8_t {
    kNone = 0, kX2 = 1, kX4 = 2, kX8 = 3, kX16 = 4, kX32 = 5, kX64 = 6,
};

struct Pins {
    // int16_t, not int8_t: STM32duino's pin constants run past 127 (PB10 is
    // 199), while -1 still means "not wired". The ESP32's numbering happened
    // to fit in a signed byte; that was luck rather than design.
    int16_t sck;
    int16_t miso;      // AD7606C DOUTA
    int16_t cs;        // software-driven, not hardware SPI CS
    int16_t convst;    // also drives WR on the usual breakouts
    int16_t busy;
    int16_t reset;
    int16_t range;
    int16_t os0, os1, os2;
    int16_t frstdata = -1;  // optional; -1 if not wired
};

// spiHz defaults to 1 MHz — deliberately slow for bring-up over flying leads.
// The Teensy build started here too before raising to 8 MHz once the wiring had
// proven itself. Raise it only after readings have been checked against a known
// reference, not because it "seems to work".
bool begin(const Pins& pins, Range range = Range::kBipolar10V,
           Oversampling os = Oversampling::kNone,
           uint32_t spiHz = 1000000);

// Change the SPI clock at runtime, for stepping it up during bring-up.
void setSpiHz(uint32_t hz);
uint32_t spiHz();

// SPI mode. The Teensy build validated MODE0, but the ESP32 SPI peripheral does
// not necessarily sample on the same edge for the same mode number — a wrong
// CPHA shifts every bit one clock and is mathematically a 2x error. Settable so
// it can be swept against a known signal rather than assumed.
void setSpiMode(uint8_t mode);
uint8_t spiMode();

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
