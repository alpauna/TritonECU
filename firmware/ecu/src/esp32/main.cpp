// ESP-ECU rebuild — M0 board bring-up, M1 storage and config.
//
// Proves the toolchain, the upload path and the board identity, and nothing
// else. It reports what silicon it is actually running on, because two things
// in this project depend on it: the chip revision selects the PlatformIO board
// variant (v1.3 here is pre-rev300, so 360 MHz, not 400), and the PSRAM/flash
// sizes decide what the partition table can look like.
//
// The heartbeat is deliberately driven from esp_timer rather than a delay() in
// loop(), so that the timebase everything downstream will use is exercised
// from the very first milestone.

#include <Arduino.h>

#include <atomic>
#include <esp_chip_info.h>
#include <esp_flash.h>
#include <esp_heap_caps.h>
#include <esp_system.h>
#include <esp_timer.h>

#include "Ad7606c.h"
#include "Board.h"
#include "Config.h"
#include "PinSelfTest.h"
#include "Storage.h"
#include "Version.h"

namespace {

std::atomic<uint32_t> g_heartbeats{0};
bool g_adcReady = false;
esp_timer_handle_t g_heartbeatTimer = nullptr;

// Fires from the esp_timer task, not an ISR context we own — safe to keep
// trivial work here, but it stays trivial on purpose.
void onHeartbeat(void*) { g_heartbeats.fetch_add(1, std::memory_order_relaxed); }

const char* resetReasonName(esp_reset_reason_t r) {
    switch (r) {
        case ESP_RST_POWERON:   return "power-on";
        case ESP_RST_EXT:       return "external";
        case ESP_RST_SW:        return "software";
        case ESP_RST_PANIC:     return "panic";
        case ESP_RST_INT_WDT:   return "interrupt watchdog";
        case ESP_RST_TASK_WDT:  return "task watchdog";
        case ESP_RST_WDT:       return "other watchdog";
        case ESP_RST_DEEPSLEEP: return "deep sleep wake";
        case ESP_RST_BROWNOUT:  return "brownout";
        case ESP_RST_SDIO:      return "SDIO";
        default:                return "unknown";
    }
}

void reportIdentity() {
    esp_chip_info_t chip;
    esp_chip_info(&chip);

    uint32_t flashBytes = 0;
    esp_flash_get_size(nullptr, &flashBytes);

    const size_t psramTotal = heap_caps_get_total_size(MALLOC_CAP_SPIRAM);
    const size_t heapTotal  = heap_caps_get_total_size(MALLOC_CAP_INTERNAL);

    Serial.println();
    Serial.println("=======================================================");
    Serial.printf("  ESP-ECU %s\n", ECU_VERSION);
    Serial.printf("  built %s\n", ECU_BUILD_DATE);
    Serial.printf("  target %s\n", ECU_TARGET_VEHICLE);
    Serial.println("=======================================================");
    Serial.printf("  carrier      : %s\n", board::kName);
    Serial.printf("  silicon      : ESP32-P4 rev v%d.%d, %d core(s)\n",
                  chip.revision / 100, chip.revision % 100, chip.cores);
    Serial.printf("  CPU          : %lu MHz\n", (unsigned long)(getCpuFrequencyMhz()));
    Serial.printf("  flash        : %.1f MB\n", flashBytes / (1024.0 * 1024.0));
    Serial.printf("  PSRAM        : %.1f MB\n", psramTotal / (1024.0 * 1024.0));
    Serial.printf("  internal RAM : %u KB total, %u KB free\n",
                  (unsigned)(heapTotal / 1024),
                  (unsigned)(heap_caps_get_free_size(MALLOC_CAP_INTERNAL) / 1024));
    Serial.printf("  last reset   : %s\n", resetReasonName(esp_reset_reason()));
    storage::report();
    config::report();
    Serial.println("=======================================================");

    // A rev300+ part runs at 400 MHz and needs the esp32-p4_r3 board. Say so
    // rather than silently running the wrong variant.
    if (chip.revision >= 300) {
        Serial.println("  NOTE: rev300+ silicon — switch board to esp32-p4_r3");
    }
    if (psramTotal == 0) {
        Serial.println("  WARNING: no PSRAM detected — check BOARD_HAS_PSRAM");
    }
    Serial.println();
}

}  // namespace

void setup() {
    Serial.begin(115200);
    // The CH343 enumerates independently of the P4, so a short settle keeps the
    // identity banner from being cut in half on the host side.
    const int64_t deadline = esp_timer_get_time() + 1500 * 1000;
    while (!Serial && esp_timer_get_time() < deadline) { /* wait */ }

    // Storage and config before the banner, so the banner can report them.
    if (!storage::begin()) {
        Serial.println("[SD] mount failed — continuing on built-in defaults");
    }
    config::load();
    config::data.bootCount++;
    if (storage::mounted() && !config::save()) {
        Serial.println("[cfg] could not persist boot count");
    }

    reportIdentity();

    const esp_timer_create_args_t args = {
        .callback = &onHeartbeat,
        .arg = nullptr,
        .dispatch_method = ESP_TIMER_TASK,
        .name = "heartbeat",
        .skip_unhandled_events = true,
    };
    ESP_ERROR_CHECK(esp_timer_create(&args, &g_heartbeatTimer));
    ESP_ERROR_CHECK(esp_timer_start_periodic(g_heartbeatTimer, 1000 * 1000));  // 1 Hz

#ifdef ECU_PIN_SELFTEST
    pintest::run();
#endif

    // M2 — external ADC. Absence is not fatal: the board is useful without it
    // and this milestone is still being wired.
    const ad7606c::Pins adcPins{
        .sck = board::adc::kSck,       .miso = board::adc::kMiso,
        .cs = board::adc::kCs,         .convst = board::adc::kConvst,
        .busy = board::adc::kBusy,     .reset = board::adc::kReset,
        .range = board::adc::kRange,
        .os0 = board::adc::kOs0,       .os1 = board::adc::kOs1,
        .os2 = board::adc::kOs2,       .frstdata = board::adc::kFrstdata,
    };
    g_adcReady = ad7606c::begin(adcPins);
    if (!g_adcReady) {
        pintest::adcDiagnose(board::adc::kBusy, board::adc::kMiso,
                             board::adc::kConvst, board::adc::kReset,
                             board::adc::kCs);
    }
    if (g_adcReady) {
        Serial.printf("  ADC          : AD7606 responding, +/-10 V, OS off, "
                      "SPI %lu kHz\n", (unsigned long)(ad7606c::spiHz() / 1000));
    } else {
        Serial.println("  ADC          : AD7606 not responding — see docs/adc-wiring.md");
    }

#ifdef ECU_ADC_SPI_SWEEP
    if (g_adcReady) pintest::adcSpiModeSweep(400);
#endif

#ifdef ECU_ADC_RANGE_CHECK
    if (g_adcReady) pintest::adcRangeCheck();
#endif

#ifdef ECU_ADC_NOISE_FLOOR
    if (g_adcReady) pintest::adcNoiseFloor(1000);
#endif

    Serial.println("M0/M1 up. Heartbeat every 5 s.");
}

void loop() {
    static uint32_t reported = 0;
    const uint32_t beats = g_heartbeats.load(std::memory_order_relaxed);

    if (beats >= reported + 5) {
        reported = beats;
        Serial.printf("[%6lu s] alive — free internal %u KB, free PSRAM %u KB\n",
                      (unsigned long)beats,
                      (unsigned)(heap_caps_get_free_size(MALLOC_CAP_INTERNAL) / 1024),
                      (unsigned)(heap_caps_get_free_size(MALLOC_CAP_SPIRAM) / 1024));

        if (g_adcReady) {
            float v[ad7606c::kChannels];
            if (ad7606c::readVolts(v)) {
                Serial.print("           ADC V1-V8:");
                for (uint8_t i = 0; i < ad7606c::kChannels; i++) {
                    Serial.printf(" %+7.4f", v[i]);
                }
                Serial.println(" V");
            } else {
                Serial.println("           ADC read failed (BUSY timeout)");
            }
        }
    }
    delay(50);
}
