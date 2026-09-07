#pragma once
// Storage abstraction — the card is on SPI on the ESP32-S3 board and on the
// native SDMMC controller on the ESP32-P4-WIFI6, which has a TF slot wired to
// SDMMC slot 0. Both back ends expose the same fs::FS interface, so only
// mounting differs; everything else in the codebase uses ECU_SD.

#include <Arduino.h>

#if defined(ECU_SD_USE_SDMMC)
  #include <SD_MMC.h>
  #define ECU_SD SD_MMC
#else
  #include <SD.h>
  #define ECU_SD SD
#endif

// Mount the card. csPin/spi are only meaningful on the SPI back end and are
// ignored when the card is on SDMMC.
bool ecuStorageBegin(uint8_t csPin);

// Human-readable description of the active back end, for logs and /heap.
const char* ecuStorageBackend();
