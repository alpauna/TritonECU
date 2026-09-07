// ESP-ECU — STM32F767ZI Nucleo-144.
//
// M0: board bring-up. Reports what silicon it is actually running on, because
// the same questions matter here as they did on the P4 — clock, flash size and
// revision all decide what the firmware can assume.
//
// The engine-critical modules (CrankDecoder, EnginePosition, SparkScheduler)
// are <stdint.h>-only and shared verbatim with the ESP32 build. Only the
// platform layer differs.

#include <Arduino.h>

#include "Board.h"
#include "Version.h"

namespace {

// STM32F7 system memory registers. Values are burned in at manufacture.
constexpr uint32_t kFlashSizeReg = 0x1FF0F442;   // 16-bit, in kilobytes
constexpr uint32_t kUidReg       = 0x1FF0F420;   // 96-bit unique device ID

uint32_t g_heartbeats = 0;
uint32_t g_lastBeatMs = 0;

const char* resetReasonName() {
    // RCC_CSR latches the cause of the last reset until explicitly cleared.
    const uint32_t csr = RCC->CSR;
    if (csr & RCC_CSR_LPWRRSTF) return "low-power";
    if (csr & RCC_CSR_WWDGRSTF) return "window watchdog";
    if (csr & RCC_CSR_IWDGRSTF) return "independent watchdog";
    if (csr & RCC_CSR_SFTRSTF)  return "software";
    if (csr & RCC_CSR_PORRSTF)  return "power-on";
    if (csr & RCC_CSR_PINRSTF)  return "pin / NRST";
    if (csr & RCC_CSR_BORRSTF)  return "brown-out";
    return "unknown";
}

// The ST-Link's VCP drops the occasional byte on a long burst at 115200 --
// observed on the bench, cosmetic on a console but not something to build
// datalogging on. A short pause between lines is enough to avoid it.
void slowPrint(const char* line) {
    Serial.println(line);
    delayMicroseconds(500);
}

void reportIdentity() {
    const uint16_t flashKb = *reinterpret_cast<const uint16_t*>(kFlashSizeReg);
    const uint32_t* uid    = reinterpret_cast<const uint32_t*>(kUidReg);

    // DBGMCU_IDCODE: [11:0] device ID, [31:16] revision.
    const uint32_t idcode = DBGMCU->IDCODE;
    const uint16_t devId  = idcode & 0x0FFF;
    const uint16_t revId  = idcode >> 16;

    Serial.println();
    Serial.println("=======================================================");
    Serial.printf("  ESP-ECU %s\n", ECU_VERSION);
    Serial.printf("  built %s\n", ECU_BUILD_DATE);
    Serial.printf("  target %s\n", ECU_TARGET_VEHICLE);
    Serial.println("=======================================================");
    Serial.printf("  board        : %s\n", board::kName);
    Serial.printf("  device ID    : 0x%03X  rev 0x%04X\n", devId, revId);
    Serial.printf("  CPU          : %lu MHz\n", (unsigned long)(SystemCoreClock / 1000000UL));
    Serial.printf("  flash        : %u KB\n", flashKb);
    Serial.printf("  unique ID    : %08lX-%08lX-%08lX\n",
                  (unsigned long)uid[0], (unsigned long)uid[1], (unsigned long)uid[2]);
    Serial.printf("  last reset   : %s\n", resetReasonName());
    Serial.println("=======================================================");

    // 0x451 is the STM32F76x/F77x family. Anything else means the board file
    // and the silicon disagree, which is worth knowing before trusting a pin.
    if (devId != 0x451) {
        Serial.printf("  WARNING: device ID 0x%03X is not STM32F76x/F77x (0x451)\n", devId);
    }
    Serial.println();

    // Latch cleared so the next boot reports its own cause, not this one's.
    RCC->CSR |= RCC_CSR_RMVF;
}

}  // namespace

void setup() {
    Serial.begin(115200);
    // On an ST-Link VCP the port exists whether or not a host is listening, so
    // there is nothing to wait for -- just settle before the first write.
    delay(200);

    pinMode(board::kLedGreen, OUTPUT);
    pinMode(board::kLedBlue, OUTPUT);
    pinMode(board::kLedRed, OUTPUT);
    digitalWrite(board::kLedGreen, LOW);
    digitalWrite(board::kLedBlue, LOW);
    digitalWrite(board::kLedRed, LOW);

    reportIdentity();
    Serial.println("M0: board bring-up. Heartbeat every 5 s. Send 'i' to repeat this.");
    g_lastBeatMs = millis();
}

void loop() {
    // The ST-Link's VCP and SWD share one USB device, so resetting the target
    // over SWD disconnects the serial port -- which makes the boot banner
    // awkward to catch. Reprinting on demand sidesteps that entirely, and is
    // worth having on a bench regardless.
    while (Serial.available()) {
        const int c = Serial.read();
        if (c == 'i' || c == 'I') reportIdentity();
    }

    const uint32_t now = millis();
    if (now - g_lastBeatMs >= 1000) {
        g_lastBeatMs += 1000;
        g_heartbeats++;
        digitalWrite(board::kLedGreen, g_heartbeats & 1);

        if (g_heartbeats % 5 == 0) {
            Serial.printf("[%6lu s] alive\n", (unsigned long)g_heartbeats);
        }
    }
}
