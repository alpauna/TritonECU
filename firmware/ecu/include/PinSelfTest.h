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

}  // namespace pintest
