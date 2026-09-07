#include "StorageStm32.h"

#include <SPI.h>
#include <SdFat.h>

#include "Board.h"
#include "Console.h"

namespace storage {
namespace {

// SPI4 on Port E. STM32duino builds an SPIClass from the pin triple and picks
// the peripheral itself.
SPIClass g_spi(board::sd::kMosi, board::sd::kMiso, board::sd::kSck);

// Start conservatively. Flying leads to an SD module are not a controlled
// impedance environment, and a card that enumerates at 4 MHz but corrupts at
// 25 MHz is a miserable fault to chase. Raise it once the card is on a PCB.
constexpr uint32_t kSpiHz = 4000000;

SdFat  g_sd;
bool   g_mounted = false;

}  // namespace

SdFat& fs() { return g_sd; }

bool begin() {
    // SdSpiConfig: chip select, options, clock, and the SPI port to use.
    const SdSpiConfig cfg(board::sd::kCs, SHARED_SPI, SD_SCK_MHZ(kSpiHz / 1000000), &g_spi);

    if (g_sd.begin(cfg)) {
        g_mounted = true;
        return true;
    }

    // SdFat distinguishes "no card responded" from "card is there but the
    // filesystem is not readable", which is exactly the distinction that
    // wasted time on the ESP32 build.
    if (g_sd.card()->errorCode()) {
        console::printf("[SD] card did not initialise (err 0x%02X, data 0x%02X)\n",
                      g_sd.card()->errorCode(), g_sd.card()->errorData());
        console::println("     Check wiring, CS pin, and that the module is 3.3 V.");
    } else if (g_sd.card()->sectorCount() == 0) {
        console::println("[SD] card initialised but reports zero sectors");
    } else {
        console::println("[SD] card is present but the filesystem is unreadable.");
        console::println("     FAT16/FAT32 only -- cards over 32 GB ship as exFAT.");
    }
    g_mounted = false;
    return false;
}

bool mounted() { return g_mounted; }

const char* backend() { return g_mounted ? "SPI (SPI4, Port E)" : "not mounted"; }

uint64_t cardSizeBytes() {
    return g_mounted ? (uint64_t)g_sd.card()->sectorCount() * 512ULL : 0;
}

uint64_t usedBytes() { return 0; }   // not cheap to compute on FAT; not needed yet

void report() {
    if (!g_mounted) {
        console::println("  storage      : unavailable — see the [SD] lines above");
        return;
    }
    const char* type = "unknown";
    switch (g_sd.card()->type()) {
        case SD_CARD_TYPE_SD1:  type = "SD1";  break;
        case SD_CARD_TYPE_SD2:  type = "SD2";  break;
        case SD_CARD_TYPE_SDHC: type = "SDHC"; break;
        default: break;
    }
    console::printf("  storage      : %s, %s, %.2f GB, FAT%d\n",
                  backend(), type,
                  cardSizeBytes() / (1024.0 * 1024.0 * 1024.0),
                  (int)g_sd.vol()->fatType());
}

}  // namespace storage
