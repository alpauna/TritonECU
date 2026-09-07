#pragma once
// STM32 storage backend — SD card on SPI4, Port E. See Board.h for pins.
//
// The ESP32 build uses fs::FS via SD_MMC; this one uses SdFat. The two APIs
// differ enough that Config has a per-platform implementation rather than a
// shared one behind a shim -- which is honest about the difference instead of
// hiding it behind a lowest-common-denominator wrapper.

#include <Arduino.h>
#include <SdFat.h>

namespace storage {

bool begin();
bool mounted();
const char* backend();
uint64_t cardSizeBytes();
uint64_t usedBytes();
void report();

// The filesystem object, for Config and later the logger.
SdFat& fs();

}  // namespace storage
