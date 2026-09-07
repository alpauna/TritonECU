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
#include <stdarg.h>

#include "Board.h"
#include "Config.h"
#include "StorageStm32.h"
#include "Version.h"

// Console on USART2 (PD5/PD6) alongside the ST-Link VCP. Everything is written
// to both, so an external USB-UART adapter can be plugged in without changing
// anything -- and the ST-Link's flaky VCP stops being the only option.
HardwareSerial ExtSerial(board::console::kRx, board::console::kTx);

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

// The ST-Link's VCP drops bytes on a long burst at 115200. Steady output is
// clean; a fifteen-line banner arrives with gaps. Draining the UART and
// Write to both consoles. printf-style, because every call site uses it.
void cprintf(const char* fmt, ...) {
    char buf[160];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    Serial.print(buf);        // NOT cprintf -- that would recurse
    ExtSerial.print(buf);
}

void cprintln(const char* line = "") {
    Serial.println(line);
    ExtSerial.println(line);
}

void settle() {
    Serial.flush();
    ExtSerial.flush();
    delay(3);
}

// ST-Link VCP baud. Kept low because that port drops characters regardless --
// see Board.h. The USART2 console is the one to trust.
constexpr uint32_t kConsoleBaud = 57600;

void reportIdentity() {
    const uint16_t flashKb = *reinterpret_cast<const uint16_t*>(kFlashSizeReg);
    const uint32_t* uid    = reinterpret_cast<const uint32_t*>(kUidReg);

    // DBGMCU_IDCODE: [11:0] device ID, [31:16] revision.
    const uint32_t idcode = DBGMCU->IDCODE;
    const uint16_t devId  = idcode & 0x0FFF;
    const uint16_t revId  = idcode >> 16;

    cprintln();
    settle();
    cprintln("=======================================================");
    settle();
    cprintf("  ESP-ECU %s\n", ECU_VERSION);
    settle();
    cprintf("  built %s\n", ECU_BUILD_DATE);
    settle();
    cprintf("  target %s\n", ECU_TARGET_VEHICLE);
    settle();
    cprintln("=======================================================");
    settle();
    cprintf("  board        : %s\n", board::kName);
    settle();
    cprintf("  device ID    : 0x%03X  rev 0x%04X\n", devId, revId);
    settle();
    cprintf("  CPU          : %lu MHz\n", (unsigned long)(SystemCoreClock / 1000000UL));
    settle();
    cprintf("  flash        : %u KB\n", flashKb);
    settle();
    cprintf("  unique ID    : %08lX-%08lX-%08lX\n",
                  (unsigned long)uid[0], (unsigned long)uid[1], (unsigned long)uid[2]);
    cprintf("  last reset   : %s\n", resetReasonName());
    settle();
    storage::report();
    config::report();
    cprintln("=======================================================");
    settle();

    // 0x451 is the STM32F76x/F77x family. Anything else means the board file
    // and the silicon disagree, which is worth knowing before trusting a pin.
    if (devId != 0x451) {
        cprintf("  WARNING: device ID 0x%03X is not STM32F76x/F77x (0x451)\n", devId);
        settle();
    }
    cprintln();
    settle();

    // Latch cleared so the next boot reports its own cause, not this one's.
    RCC->CSR |= RCC_CSR_RMVF;
}

}  // namespace

void setup() {
    Serial.begin(kConsoleBaud);
    ExtSerial.begin(board::console::kBaud);
    // On an ST-Link VCP the port exists whether or not a host is listening, so
    // there is nothing to wait for -- just settle before the first write.
    delay(200);

    pinMode(board::kLedGreen, OUTPUT);
    pinMode(board::kLedBlue, OUTPUT);
    pinMode(board::kLedRed, OUTPUT);
    digitalWrite(board::kLedGreen, LOW);
    digitalWrite(board::kLedBlue, LOW);
    digitalWrite(board::kLedRed, LOW);

    if (!storage::begin()) {
        cprintln("[SD] mount failed — continuing on built-in defaults");
    }
    config::load();
    config::data.bootCount++;
    if (storage::mounted() && !config::save()) {
        cprintln("[cfg] could not persist boot count");
    }

    reportIdentity();
    cprintln("M0/M1: board, storage, config. Heartbeat every 5 s. Send 'i' for identity, 's' to remount the card.");
    g_lastBeatMs = millis();
}

void loop() {
    // The ST-Link's VCP and SWD share one USB device, so resetting the target
    // over SWD disconnects the serial port -- which makes the boot banner
    // awkward to catch. Reprinting on demand sidesteps that entirely, and is
    // worth having on a bench regardless.
    while (Serial.available() || ExtSerial.available()) {
        const int c = Serial.available() ? Serial.read() : ExtSerial.read();
        if (c == 'i' || c == 'I') {
            reportIdentity();
        } else if (c == 's' || c == 'S') {
            // Remount without a power cycle -- useful because resetting over
            // SWD drops the VCP, so a fresh boot is awkward to observe.
            // Remount and report only. Deliberately does NOT touch bootCount:
            // that counts boots, and an earlier version incremented it here,
            // which quietly inflated it every time the command ran.
            cprintln("[SD] remounting...");
            settle();
            if (storage::begin()) config::load();
            storage::report();
            settle();
            config::report();
        }
    }

    const uint32_t now = millis();
    if (now - g_lastBeatMs >= 1000) {
        g_lastBeatMs += 1000;
        g_heartbeats++;
        digitalWrite(board::kLedGreen, g_heartbeats & 1);

        if (g_heartbeats % 5 == 0) {
            cprintf("[%6lu s] alive\n", (unsigned long)g_heartbeats);
        }
    }
}
