#include "EcuStorage.h"
#include "BoardPins.h"
#include <SPI.h>

#if defined(ECU_SD_USE_SDMMC)

// ESP32-P4-WIFI6: TF slot is on SDMMC slot 0 with IOMUX pins fixed in silicon
// (CLK/CMD/D0-D3 on GPIO39-44) and card power switched by GPIO45. The variant
// header declares all of that, so begin() needs no pin setup here.
bool ecuStorageBegin(uint8_t /*csPin*/) {
    // 4-bit bus. Falls back to 1-bit if the wide bus fails to train, which is
    // the usual symptom of a marginal card or a long adapter cable.
    if (SD_MMC.begin("/sdcard", false)) {
        return true;
    }
    Serial.println("SD (SDMMC 4-bit) failed, retrying in 1-bit mode...");
    if (SD_MMC.begin("/sdcard", true)) {
        Serial.println("SD mounted in 1-bit mode — check card and wiring.");
        return true;
    }
    return false;
}

const char* ecuStorageBackend() { return "SDMMC slot 0 (4-bit)"; }

#else

// ESP32-S3: card hangs off the shared VSPI bus.
bool ecuStorageBegin(uint8_t csPin) {
    return SD.begin(csPin, SPI, SD_SPI_SPEED * 1000000UL);
}

const char* ecuStorageBackend() { return "SPI"; }

#endif
