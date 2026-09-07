#include "Storage.h"

#include <SD_MMC.h>

namespace storage {
namespace {

bool g_mounted = false;
bool g_oneBit = false;

}  // namespace

bool begin() {
    // Never pass format_if_mount_failed. An unmountable card is far more often
    // the wrong filesystem than a broken one, and formatting it would destroy
    // whatever is on it. Report and continue instead.
    if (SD_MMC.begin("/sdcard", false)) {
        g_mounted = true;
        g_oneBit = false;
        return true;
    }
    Serial.println("[SD] 4-bit mount failed, retrying in 1-bit mode");
    if (SD_MMC.begin("/sdcard", true)) {
        g_mounted = true;
        g_oneBit = true;
        return true;
    }
    g_mounted = false;
    return false;
}

bool mounted() { return g_mounted; }

const char* backend() {
    if (!g_mounted) return "not mounted";
    return g_oneBit ? "SDMMC 1-bit" : "SDMMC 4-bit";
}

uint64_t cardSizeBytes() { return g_mounted ? SD_MMC.cardSize() : 0; }
uint64_t usedBytes()     { return g_mounted ? SD_MMC.usedBytes() : 0; }

void report() {
    if (!g_mounted) {
        // The IDF log above this line distinguishes the two cases:
        //   sdmmc_init_ocr / send_op_cond timeout -> no card responding
        //   mount_to_vfs failed                   -> card present, filesystem
        //                                            unreadable (usually exFAT;
        //                                            FATFS needs FAT16/FAT32)
        Serial.println("  storage      : unavailable — no card, or a filesystem");
        Serial.println("                 FATFS cannot read. Cards over 32 GB ship");
        Serial.println("                 as exFAT; reformat as FAT32.");
        return;
    }
    const char* type = "unknown";
    switch (SD_MMC.cardType()) {
        case CARD_MMC:  type = "MMC";   break;
        case CARD_SD:   type = "SDSC";  break;
        case CARD_SDHC: type = "SDHC";  break;
        default: break;
    }
    Serial.printf("  storage      : %s, %s, %.2f GB (%.2f GB used)\n",
                  backend(), type,
                  cardSizeBytes() / (1024.0 * 1024.0 * 1024.0),
                  usedBytes() / (1024.0 * 1024.0 * 1024.0));
}

}  // namespace storage
