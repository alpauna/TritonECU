#include "Ad7606c.h"

#include <SPI.h>

namespace ad7606c {
namespace {

// Timing from the AD7606C-16 datasheet, Table 3 (Reset Functionality): RESET
// must be held high >= 3.2 us, then >= 274 us must elapse before the first
// CONVST. Padded, as in the Teensy driver — none of this is timing-critical.
constexpr uint32_t kResetPulseUs  = 10;
constexpr uint32_t kResetSettleUs = 400;

// 8 MHz, as raised and proven on the Teensy bench setup. Well under the
// datasheet's 63.5 MHz ceiling; this is a cautious value for flying-wire
// wiring, not a limit of the part. Re-validate against a known reference
// before raising it.
constexpr uint32_t kSpiHz = 8000000;

// BUSY should fall within ~10 us even at the slowest oversampling ratio. A
// generous ceiling here still catches a genuinely stuck part quickly.
constexpr uint32_t kBusyTimeoutUs = 10000;

Pins  g_pins{};
Range g_range = Range::kBipolar10V;
bool  g_ready = false;

SPISettings g_spi(kSpiHz, MSBFIRST, SPI_MODE0);

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

}  // namespace

bool begin(const Pins& pins, Range range, Oversampling os) {
    g_pins  = pins;
    g_range = range;

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

    SPI.begin(g_pins.sck, g_pins.miso, -1, -1);   // no MOSI in hardware mode

    // Full reset.
    digitalWrite(g_pins.reset, HIGH);
    delayMicroseconds(kResetPulseUs);
    digitalWrite(g_pins.reset, LOW);
    delayMicroseconds(kResetSettleUs);

    // A conversion that completes is the only evidence the part is alive and
    // wired: BUSY has to rise and fall on its own.
    int16_t discard[kChannels];
    g_ready = true;
    if (!read(discard)) {
        g_ready = false;
        Serial.println("[ADC] AD7606C did not complete a conversion — check "
                       "wiring, RESET and BUSY");
        return false;
    }
    return true;
}

bool read(int16_t raw[kChannels]) {
    if (!g_ready) return false;

    pulseConvst();
    if (!waitBusyLow()) return false;

    SPI.beginTransaction(g_spi);
    digitalWrite(g_pins.cs, LOW);
    for (uint8_t i = 0; i < kChannels; i++) {
        raw[i] = static_cast<int16_t>(SPI.transfer16(0x0000));
    }
    digitalWrite(g_pins.cs, HIGH);
    SPI.endTransaction();
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

Range range() { return g_range; }

void setRange(Range r) {
    g_range = r;
    if (g_ready) applyRange();
}

}  // namespace ad7606c
