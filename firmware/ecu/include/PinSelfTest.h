#pragma once
// Header solder-bridge and short detector.
//
// Checks every GPIO that reaches the 2x20 header for three faults:
//   * shorted to ground   — an internal pull-up cannot pull it high
//   * shorted to 3V3      — an internal pull-down cannot pull it low
//   * bridged to another  — driving one pin high moves another
//
// Intended to be run once after soldering the header, before anything is
// connected to it. Anything wired to the header will look like a fault, which
// is the point: it only means something on a bare board.

#include <stdint.h>

namespace pintest {

// Returns the number of faults found. Prints a report either way.
uint32_t run();

// Reports whether the AD7606's BUSY/DOUTA lines are actually driven or
// floating, and walks the likely causes when they are not.
void adcDiagnose(uint8_t busy, uint8_t douta, uint8_t convst, uint8_t reset,
                 uint8_t cs);

// Measures the achieved noise floor and noise-free resolution per channel.
// Short every input to its own VxGND first, or the numbers mean nothing.
void adcNoiseFloor(uint16_t samples = 1000);

// Determines whether the RANGE pin actually reaches the chip, separating a
// range mismatch from an SPI-mode error — both of which look like a clean 2x.
void adcRangeCheck();

// Sweeps all four SPI modes and reports each channel's envelope, to identify
// the correct mode against a known signal.
void adcSpiModeSweep(uint16_t samplesPerMode = 400);

}  // namespace pintest
