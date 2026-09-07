// ESP-ECU rebuild — M0: board bring-up.
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

#include "Board.h"
#include "Version.h"

namespace {

std::atomic<uint32_t> g_heartbeats{0};
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

    Serial.println("M0: board bring-up. Heartbeat every 5 s.");
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
    }
    delay(50);
}
