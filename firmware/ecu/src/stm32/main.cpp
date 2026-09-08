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
#include "Ad7606c.h"
#include "Console.h"
#include "Config.h"
#include "StorageStm32.h"
#include "Version.h"

namespace {

// STM32F7 system memory registers. Values are burned in at manufacture.
constexpr uint32_t kFlashSizeReg = 0x1FF0F442;   // 16-bit, in kilobytes
constexpr uint32_t kUidReg       = 0x1FF0F420;   // 96-bit unique device ID

uint32_t g_heartbeats = 0;
bool g_adcReady = false;
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



void reportIdentity() {
    const uint16_t flashKb = *reinterpret_cast<const uint16_t*>(kFlashSizeReg);
    const uint32_t* uid    = reinterpret_cast<const uint32_t*>(kUidReg);

    // DBGMCU_IDCODE: [11:0] device ID, [31:16] revision.
    const uint32_t idcode = DBGMCU->IDCODE;
    const uint16_t devId  = idcode & 0x0FFF;
    const uint16_t revId  = idcode >> 16;

    console::println();
    console::settle();
    console::println("=======================================================");
    console::settle();
    console::printf("  ESP-ECU %s\n", ECU_VERSION);
    console::settle();
    console::printf("  built %s\n", ECU_BUILD_DATE);
    console::settle();
    console::printf("  target %s\n", ECU_TARGET_VEHICLE);
    console::settle();
    console::println("=======================================================");
    console::settle();
    console::printf("  board        : %s\n", board::kName);
    console::settle();
    console::printf("  device ID    : 0x%03X  rev 0x%04X\n", devId, revId);
    console::settle();
    console::printf("  CPU          : %lu MHz\n", (unsigned long)(SystemCoreClock / 1000000UL));
    console::settle();
    console::printf("  flash        : %u KB\n", flashKb);
    console::settle();
    console::printf("  unique ID    : %08lX-%08lX-%08lX\n",
                  (unsigned long)uid[0], (unsigned long)uid[1], (unsigned long)uid[2]);
    console::printf("  last reset   : %s\n", resetReasonName());
    console::settle();
    if (g_adcReady) {
        console::printf("  ADC          : AD7606 responding, +/-10 V, OS off, SPI %lu kHz\n",
                        (unsigned long)(ad7606c::spiHz() / 1000));
    } else {
        console::printf("  ADC          : AD7606 not responding\n");
    }
    console::settle();
    storage::report();
    config::report();
    console::println("=======================================================");
    console::settle();

    // 0x451 is the STM32F76x/F77x family. Anything else means the board file
    // and the silicon disagree, which is worth knowing before trusting a pin.
    if (devId != 0x451) {
        console::printf("  WARNING: device ID 0x%03X is not STM32F76x/F77x (0x451)\n", devId);
        console::settle();
    }
    console::println();
    console::settle();

    // Latch cleared so the next boot reports its own cause, not this one's.
    RCC->CSR |= RCC_CSR_RMVF;
}

}  // namespace

void setup() {
    console::begin();

    pinMode(board::kLedGreen, OUTPUT);
    pinMode(board::kLedBlue, OUTPUT);
    pinMode(board::kLedRed, OUTPUT);
    digitalWrite(board::kLedGreen, LOW);
    digitalWrite(board::kLedBlue, LOW);
    digitalWrite(board::kLedRed, LOW);

    if (!storage::begin()) {
        console::println("[SD] mount failed — continuing on built-in defaults");
    }
    config::load();
    config::data.bootCount++;
    if (storage::mounted() && !config::save()) {
        console::println("[cfg] could not persist boot count");
    }

    const ad7606c::Pins adcPins{
        .sck = board::adc::kSck,       .miso = board::adc::kMiso,
        .cs = board::adc::kCs,         .convst = board::adc::kConvst,
        .busy = board::adc::kBusy,     .reset = board::adc::kReset,
        .range = board::adc::kRange,
        .os0 = board::adc::kOs0,       .os1 = board::adc::kOs1,
        .os2 = board::adc::kOs2,       .frstdata = board::adc::kFrstdata,
    };
    g_adcReady = ad7606c::begin(adcPins);

    reportIdentity();
    console::println("M0/M1: board, storage, config. Heartbeat every 5 s. Send 'i' for identity, 's' to remount the card.");
    g_lastBeatMs = millis();
}

void loop() {
    // The ST-Link's VCP and SWD share one USB device, so resetting the target
    // over SWD disconnects the serial port -- which makes the boot banner
    // awkward to catch. Reprinting on demand sidesteps that entirely, and is
    // worth having on a bench regardless.
    for (int c = console::read(); c >= 0; c = console::read()) {
        if (c == 'i' || c == 'I') {
            const ad7606c::Pins adcPins{
        .sck = board::adc::kSck,       .miso = board::adc::kMiso,
        .cs = board::adc::kCs,         .convst = board::adc::kConvst,
        .busy = board::adc::kBusy,     .reset = board::adc::kReset,
        .range = board::adc::kRange,
        .os0 = board::adc::kOs0,       .os1 = board::adc::kOs1,
        .os2 = board::adc::kOs2,       .frstdata = board::adc::kFrstdata,
    };
    g_adcReady = ad7606c::begin(adcPins);

    reportIdentity();
        } else if (c == 's' || c == 'S') {
            // Remount without a power cycle -- useful because resetting over
            // SWD drops the VCP, so a fresh boot is awkward to observe.
            // Remount and report only. Deliberately does NOT touch bootCount:
            // that counts boots, and an earlier version incremented it here,
            // which quietly inflated it every time the command ran.
            console::println("[SD] remounting...");
            console::settle();
            if (storage::begin()) config::load();
            storage::report();
            console::settle();
            config::report();
        }
    }

    const uint32_t now = millis();
    if (now - g_lastBeatMs >= 1000) {
        g_lastBeatMs += 1000;
        g_heartbeats++;
        digitalWrite(board::kLedGreen, g_heartbeats & 1);

        if (g_heartbeats % 5 == 0) {
            console::printf("[%6lu s] alive\n", (unsigned long)g_heartbeats);
            if (g_adcReady) {
                float v[ad7606c::kChannels];
                if (ad7606c::readVolts(v)) {
                    console::settle();
                    console::printf("   V1-V8:");
                    for (uint8_t i = 0; i < ad7606c::kChannels; i++) {
                        console::printf(" %+7.4f", v[i]);
                    }
                    console::printf(" V\n");
                }
            }
        }
    }
}
