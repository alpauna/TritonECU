#include "Ad7606c.h"
#include "Console.h"

#include <SPI.h>

#include "Board.h"

namespace ad7606c {
namespace {

// Timing from the AD7606C-16 datasheet, Table 3 (Reset Functionality): RESET
// must be held high >= 3.2 us, then >= 274 us must elapse before the first
// CONVST. Padded, as in the Teensy driver — none of this is timing-critical.
constexpr uint32_t kResetPulseUs  = 10;
constexpr uint32_t kResetSettleUs = 400;

// SPI clock is a runtime value, not a constant: bring-up starts slow over
// Dupont leads and steps up once the wiring has proven itself. The Teensy build
// ran 1 MHz through Phase 1 and only moved to 8 MHz after bench validation.
// The part itself will take 63.5 MHz; the wiring is the limit, not the silicon.
uint32_t g_spiHz = 1000000;
// NOTE: this default is inherited from the ESP32-P4 and is NOT established for
// the STM32. The Teensy needed MODE0 and the P4 needed MODE2 for the same ADC,
// so the mode is a property of the host/ADC pairing. Sweep it against a known
// signal before trusting any reading -- a wrong CPHA reads exactly 2x high
// while looking perfectly stable.
//
// SPI_MODE2, established empirically on 2026-09-06 against two known signals:
// a +/-1.22 V scope output on V1 and a 0-2 V 1 kHz Hantek square on V8. Modes
// 0, 1 and 3 all read exactly 2x high; MODE2 read both correctly.
//
// Note this differs from the Teensy build, which validated SPI_MODE0 against
// the same part. Same ADC, different host SPI peripheral — so the mode is a
// property of the pairing, not of the AD7606, and must be re-established on any
// new host rather than carried over.
uint8_t  g_spiMode = SPI_MODE2;

// BUSY should fall within ~10 us even at the slowest oversampling ratio. A
// generous ceiling here still catches a genuinely stuck part quickly.
constexpr uint32_t kBusyTimeoutUs = 10000;

Pins  g_pins{};
Range g_range = Range::kBipolar10V;
bool  g_ready = false;

SPISettings g_spi(g_spiHz, MSBFIRST, SPI_MODE2);

// Dedicated SPI2 instance. Unlike the ESP32 core, STM32duino takes the pins
// when the object is constructed rather than in begin().
SPIClass g_spiBus(board::adc::kMosi, board::adc::kMiso, board::adc::kSck);

void applyRange() {
    digitalWrite(g_pins.range, g_range == Range::kBipolar10V ? HIGH : LOW);
}

void applyOversampling(Oversampling os) {
    const uint8_t v = static_cast<uint8_t>(os);
    digitalWrite(g_pins.os0, (v & 0x1) ? HIGH : LOW);
    digitalWrite(g_pins.os1, (v & 0x2) ? HIGH : LOW);
    digitalWrite(g_pins.os2, (v & 0x4) ? HIGH : LOW);
}

void pulseConvst() {
    digitalWrite(g_pins.convst, LOW);
    delayMicroseconds(1);   // t_LP_CNV min is 10 ns; generous margin
    digitalWrite(g_pins.convst, HIGH);
}

bool waitBusyLow() {
    const uint32_t start = micros();
    while (digitalRead(g_pins.busy) == HIGH) {
        if (micros() - start > kBusyTimeoutUs) return false;
    }
    return true;
}

// Probe that the part is really there.
//
// Waiting for BUSY to fall is not evidence of anything: with nothing connected
// the pin floats low and the wait returns immediately, MISO floats high, and
// every channel reads 0xFFFF — which looks like a plausible -0.0003 V. This
// was observed on the bench, so the check below exists because the obvious one
// failed.
//
// Instead, require BUSY to actually RISE after CONVST. To make that impossible
// to miss, probe at x64 oversampling, where conversion takes ~255 us rather
// than the ~3 us of a normal conversion. The caller's real oversampling
// setting is applied afterwards.
bool probeBusyRises() {
    applyOversampling(Oversampling::kX64);
    delayMicroseconds(10);

    pulseConvst();

    const uint32_t start = micros();
    bool sawHigh = false;
    while (micros() - start < 1000) {          // 1 ms >> the ~255 us expected
        if (digitalRead(g_pins.busy) == HIGH) { sawHigh = true; break; }
    }
    if (!sawHigh) return false;
    return waitBusyLow();
}

// A bus with nothing driving it reads all-ones or all-zeros on every channel.
// Real inputs, even grounded ones, disagree in the low bits from noise alone.
bool looksLikeFloatingBus(const int16_t raw[kChannels]) {
    for (uint8_t i = 1; i < kChannels; i++) {
        if (raw[i] != raw[0]) return false;    // channels differ — real data
    }
    return raw[0] == static_cast<int16_t>(0xFFFF) || raw[0] == 0;
}

}  // namespace

bool begin(const Pins& pins, Range range, Oversampling os, uint32_t spiHz) {
    g_pins  = pins;
    g_range = range;
    g_spiHz = spiHz;
    g_spi   = SPISettings(g_spiHz, MSBFIRST, g_spiMode);

    pinMode(g_pins.cs, OUTPUT);      digitalWrite(g_pins.cs, HIGH);
    pinMode(g_pins.convst, OUTPUT);  digitalWrite(g_pins.convst, HIGH);
    pinMode(g_pins.reset, OUTPUT);   digitalWrite(g_pins.reset, LOW);
    pinMode(g_pins.range, OUTPUT);
    pinMode(g_pins.os0, OUTPUT);
    pinMode(g_pins.os1, OUTPUT);
    pinMode(g_pins.os2, OUTPUT);
    pinMode(g_pins.busy, INPUT);
    if (g_pins.frstdata >= 0) pinMode(g_pins.frstdata, INPUT);

    applyRange();
    applyOversampling(os);

    g_spiBus.begin();

    // Full reset.
    digitalWrite(g_pins.reset, HIGH);
    delayMicroseconds(kResetPulseUs);
    digitalWrite(g_pins.reset, LOW);
    delayMicroseconds(kResetSettleUs);

    g_ready = true;

    // Catching BUSY's rising edge is inherently racy: if the OS pins are
    // strapped on the module rather than driven, a conversion takes ~3 us and a
    // digitalRead poll can miss the whole pulse. Observed on the bench, where
    // begin() reported "BUSY never went high" and a diagnostic run moments
    // later saw it go high.
    //
    // So a missed edge is no longer fatal on its own. The data check below is
    // the real evidence, and it does not depend on winning a race.
    const bool sawBusyRise = probeBusyRises();

    // Restore the caller's oversampling now the probe is done.
    applyOversampling(os);
    delayMicroseconds(10);

    int16_t sample[kChannels];
    if (!read(sample)) {
        g_ready = false;
        console::println("[ADC] conversion did not complete — BUSY stayed high. "
                       "Check RESET, CONVST and BUSY wiring.");
        return false;
    }
    if (!sawBusyRise) {
        console::println("[ADC] note: BUSY rising edge not caught — normal when "
                       "OS is strapped on the module and conversions are ~3 us");
    }
    if (looksLikeFloatingBus(sample)) {
        g_ready = false;
        console::printf("[ADC] all 8 channels read identical 0x%04X — DOUTA is "
                      "floating, not driven\n", (uint16_t)sample[0]);
        return false;
    }
    return true;
}

bool read(int16_t raw[kChannels]) {
    if (!g_ready) return false;

    pulseConvst();
    if (!waitBusyLow()) return false;

    g_spiBus.beginTransaction(g_spi);
    digitalWrite(g_pins.cs, LOW);
    for (uint8_t i = 0; i < kChannels; i++) {
        raw[i] = static_cast<int16_t>(g_spiBus.transfer16(0x0000));
    }
    digitalWrite(g_pins.cs, HIGH);
    g_spiBus.endTransaction();
    return true;
}

float voltsPerCount() {
    // 16-bit two's complement across the full bipolar span.
    return (g_range == Range::kBipolar10V ? 20.0f : 10.0f) / 65536.0f;
}

bool readVolts(float volts[kChannels]) {
    int16_t raw[kChannels];
    if (!read(raw)) return false;
    const float scale = voltsPerCount();
    for (uint8_t i = 0; i < kChannels; i++) volts[i] = raw[i] * scale;
    return true;
}

void setSpiHz(uint32_t hz) {
    g_spiHz = hz;
    g_spi   = SPISettings(g_spiHz, MSBFIRST, g_spiMode);
}

void setSpiMode(uint8_t mode) {
    g_spiMode = mode;
    g_spi     = SPISettings(g_spiHz, MSBFIRST, g_spiMode);
}

uint8_t spiMode() { return g_spiMode; }

uint32_t spiHz() { return g_spiHz; }

Range range() { return g_range; }

void setRange(Range r) {
    g_range = r;
    if (g_ready) applyRange();
}

}  // namespace ad7606c
