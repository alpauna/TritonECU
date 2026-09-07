#include "PinSelfTest.h"

#include <Arduino.h>
#include <string.h>
#include <math.h>

#include "Ad7606c.h"

namespace pintest {
namespace {

// Every GPIO on the 2x20 header, in silkscreen order down each side.
//
// GPIO24/25 are deliberately excluded: they are the USB 2.0 HS D-/D+ pair, and
// driving them serves no purpose here.
constexpr uint8_t kHeaderPins[] = {
    // left side, top to bottom
    52, 51, 31, 30, 29, 28, 50, 49, 5, 4, 3, 2, 8, 7,
    // right side, top to bottom
    20, 21, 22, 23, 26, 27, 32, 33, 46, 47, 48,
};
constexpr size_t kNumPins = sizeof(kHeaderPins) / sizeof(kHeaderPins[0]);

void allInputsPulledDown() {
    for (size_t i = 0; i < kNumPins; i++) pinMode(kHeaderPins[i], INPUT_PULLDOWN);
}

}  // namespace

uint32_t run() {
    uint32_t faults = 0;
    bool tiedHigh[kNumPins] = {false};
    bool tiedLow[kNumPins]  = {false};

    Serial.println();
    Serial.println("--- header pin self-test -------------------------------");
    Serial.printf("Testing %u header GPIOs. Nothing should be connected.\n",
                  (unsigned)kNumPins);

    // Pass 1 — characterise each pin on its own. A pin that an internal
    // pull-up cannot lift, or an internal pull-down cannot drop, has something
    // external on it. That is not automatically a fault: the carrier board has
    // I2C pull-ups on GPIO7/8, and they are supposed to be there.
    for (size_t i = 0; i < kNumPins; i++) {
        const uint8_t p = kHeaderPins[i];
        pinMode(p, INPUT_PULLUP);
        delayMicroseconds(50);
        const bool highWithPullup = digitalRead(p) == HIGH;
        pinMode(p, INPUT_PULLDOWN);
        delayMicroseconds(50);
        const bool lowWithPulldown = digitalRead(p) == LOW;

        if (!highWithPullup && lowWithPulldown) {
            tiedLow[i] = true;
            Serial.printf("  FAULT GPIO%-2u : held LOW — shorted to GND\n", p);
            faults++;
        } else if (highWithPullup && !lowWithPulldown) {
            tiedHigh[i] = true;
            Serial.printf("  note  GPIO%-2u : held HIGH by an external pull-up\n", p);
        } else if (!highWithPullup && !lowWithPulldown) {
            Serial.printf("  FAULT GPIO%-2u : follows neither pull — driven by something\n", p);
            faults++;
        }
    }

    // Pass 2 — bridges. Drive one pin high, everything else pulled down.
    //
    // Pins already known to sit high on their own are skipped as victims: they
    // read HIGH no matter what is driven, and counting that as a bridge
    // produced one false positive per driver on the first run of this test.
    for (size_t i = 0; i < kNumPins; i++) {
        const uint8_t driver = kHeaderPins[i];
        if (tiedLow[i]) continue;

        allInputsPulledDown();
        pinMode(driver, OUTPUT);
        digitalWrite(driver, HIGH);
        delayMicroseconds(50);

        for (size_t j = 0; j < kNumPins; j++) {
            if (i == j || tiedHigh[j] || tiedLow[j]) continue;
            const uint8_t victim = kHeaderPins[j];
            if (digitalRead(victim) == HIGH) {
                Serial.printf("  FAULT GPIO%-2u -> GPIO%-2u : bridged\n", driver, victim);
                faults++;
            }
        }
        pinMode(driver, INPUT);
    }

    allInputsPulledDown();

    if (faults == 0) {
        Serial.printf("  PASS — %u header pins, no shorts and no bridges.\n",
                      (unsigned)kNumPins);
    } else {
        Serial.printf("  %lu fault(s) — anything already wired to the header\n"
                      "  will also read as a fault.\n", (unsigned long)faults);
    }
    Serial.println("--------------------------------------------------------");
    Serial.println();
    return faults;
}

}  // namespace pintest

namespace pintest {

// Is this pin driven by something, or floating?
// A pin the chip is driving holds its level against both internal pulls.
static const char* probePin(uint8_t p) {
    pinMode(p, INPUT_PULLUP);
    delayMicroseconds(100);
    const bool hiWithPu = digitalRead(p) == HIGH;
    pinMode(p, INPUT_PULLDOWN);
    delayMicroseconds(100);
    const bool loWithPd = digitalRead(p) == LOW;
    pinMode(p, INPUT);

    if (hiWithPu && loWithPd)   return "FLOATING (nothing driving it)";
    if (hiWithPu && !loWithPd)  return "driven HIGH";
    if (!hiWithPu && loWithPd)  return "driven LOW";
    return "indeterminate";
}

void adcDiagnose(uint8_t busy, uint8_t douta, uint8_t convst, uint8_t reset,
                 uint8_t cs) {
    Serial.println();
    Serial.println("--- AD7606 connection diagnosis ------------------------");

    // Release everything and see what the module holds on its own. A line the
    // module pulls is a line our wire may not actually be reaching.
    pinMode(cs, INPUT); pinMode(convst, INPUT); pinMode(reset, INPUT);
    delay(1);

    // BUSY is an ADC output, so probing it is meaningful. CONVST, RESET and CS
    // are ADC *inputs* — the chip never drives them, so "floating" there says
    // nothing about whether the wire is connected. Only the module's own pulls
    // would show, and a driven HIGH on RESET would be a real finding.
    Serial.printf("  BUSY   (GPIO%-2u) : %s   [ADC output — meaningful]\n",
                  busy, probePin(busy));
    Serial.printf("  CONVST (GPIO%-2u) : %s   [ADC input — uninformative]\n",
                  convst, probePin(convst));
    Serial.printf("  RESET  (GPIO%-2u) : %s   [ADC input — HIGH would be bad]\n",
                  reset, probePin(reset));
    Serial.printf("  CS     (GPIO%-2u) : %s   [ADC input — uninformative]\n",
                  cs, probePin(cs));

    // DOUTA is three-stated until CS goes low, so "floating" with CS high is
    // correct behaviour, not a fault. The useful test is whether it starts
    // being driven when CS is asserted — that proves the serial interface is
    // alive and the part is in serial mode.
    pinMode(cs, OUTPUT); digitalWrite(cs, HIGH);
    delayMicroseconds(100);
    Serial.printf("  DOUTA, CS high  : %s (floating is correct here)\n",
                  probePin(douta));
    digitalWrite(cs, LOW);
    delayMicroseconds(100);
    const char* doutaCsLow = probePin(douta);
    Serial.printf("  DOUTA, CS low   : %s\n", doutaCsLow);
    digitalWrite(cs, HIGH);

    // With RESET released and no conversion running, BUSY should be driven LOW
    // by the part. FLOATING means the wire, the chip's power, or the chip
    // itself is not there.
    pinMode(reset, OUTPUT);  digitalWrite(reset, LOW);
    pinMode(convst, OUTPUT); digitalWrite(convst, HIGH);
    delay(1);

    pinMode(busy, INPUT);
    Serial.printf("  BUSY idle level : %s\n", digitalRead(busy) ? "HIGH" : "LOW");

    // Sample BUSY as fast as possible across a CONVST pulse. At 360 MHz this
    // catches a ~3 us conversion comfortably.
    digitalWrite(convst, LOW);
    delayMicroseconds(1);
    bool sawHigh = false;
    digitalWrite(convst, HIGH);
    for (uint32_t i = 0; i < 20000; i++) {
        if (digitalRead(busy) == HIGH) { sawHigh = true; break; }
    }
    Serial.printf("  BUSY after CONVST: %s\n",
                  sawHigh ? "went HIGH — the part is converting"
                          : "never moved");

    Serial.println();
    if (strcmp(doutaCsLow, "FLOATING (nothing driving it)") != 0) {
        Serial.println("  DOUTA responds to CS. That single result proves the");
        Serial.println("  part is powered, grounded, in SERIAL mode, and that");
        Serial.println("  the CS and DOUTA wires are both good.");
        Serial.println("  So the fault is isolated to the CONVST path:");
        Serial.println("   1. CONVSTA and CONVSTB must be SHORTED TOGETHER.");
        Serial.println("      If the module breaks out both and only one is");
        Serial.println("      wired, BUSY never moves. Most likely cause.");
        Serial.println("   2. The CONVST wire is off, loose, or on a different");
        Serial.println("      pin than GPIO26.");
        Serial.println("   3. RESET held HIGH would also do it — but a part in");
        Serial.println("      reset would not have answered CS, so this is");
        Serial.println("      unlikely here.");
        Serial.println("--------------------------------------------------------");
        Serial.println();
        return;
    }
    Serial.println("  BUSY driven means the part is powered and alive.");
    Serial.println("  BUSY not moving after CONVST means no conversion starts:");
    Serial.println("   1. CONVSTA and CONVSTB must be SHORTED TOGETHER. If the");
    Serial.println("      module breaks out both and only one is wired, nothing");
    Serial.println("      ever converts. Most likely cause of this symptom.");
    Serial.println("   2. RESET is ACTIVE HIGH. If the module pulls it up and");
    Serial.println("      our wire is not landing, the part sits in reset");
    Serial.println("      forever — check the RESET line above reads driven LOW");
    Serial.println("      or floating, not driven HIGH.");
    Serial.println("   3. STBY must be HIGH — low is standby.");
    Serial.println("   4. Check the CONVST wire is on the pin it thinks it is.");
    Serial.println();
    Serial.println("  If DOUTA stays floating with CS LOW, the part is not in");
    Serial.println("  serial mode: PAR/SER/BYTE SEL must be HIGH and");
    Serial.println("  DB15/BYTE SEL must be LOW.");
    Serial.println("--------------------------------------------------------");
    Serial.println();
}

}  // namespace pintest

namespace pintest {

// Measures the real noise floor, in this wiring, with these leads.
//
// This is what actually closes M2. Datasheet ENOB is a lab number; what
// matters is how many bits survive a Dupont harness. Short every input to its
// own VxGND and run this: the spread across samples is the noise floor, and
// log2(fullscale / peak-to-peak noise) is the noise-free resolution actually
// available.
void adcNoiseFloor(uint16_t samples) {
    float vmin[8], vmax[8], sum[8], sumsq[8];
    for (uint8_t c = 0; c < 8; c++) {
        vmin[c] = 1e9f; vmax[c] = -1e9f; sum[c] = 0.0f; sumsq[c] = 0.0f;
    }

    uint16_t taken = 0;
    for (uint16_t i = 0; i < samples; i++) {
        float v[8];
        if (!ad7606c::readVolts(v)) continue;
        for (uint8_t c = 0; c < 8; c++) {
            if (v[c] < vmin[c]) vmin[c] = v[c];
            if (v[c] > vmax[c]) vmax[c] = v[c];
            sum[c]   += v[c];
            sumsq[c] += v[c] * v[c];
        }
        taken++;
    }
    if (taken == 0) { Serial.println("  no samples — ADC not responding"); return; }

    const float lsb   = ad7606c::voltsPerCount();
    const float range = lsb * 65536.0f;

    Serial.println();
    Serial.printf("--- ADC noise floor, %u samples, SPI %lu kHz ------------\n",
                  taken, (unsigned long)(ad7606c::spiHz() / 1000));
    Serial.println("  ch      mean      p-p noise    p-p LSBs   noise-free bits");
    for (uint8_t c = 0; c < 8; c++) {
        const float mean = sum[c] / taken;
        const float pp   = vmax[c] - vmin[c];
        const float lsbs = pp / lsb;
        // Noise-free resolution: how many bits are larger than the noise.
        const float bits = (lsbs > 1.0f) ? (log(range / pp) / log(2.0f)) : 16.0f;
        Serial.printf("  V%u  %+9.4f V  %8.5f V  %8.1f   %6.1f\n",
                      c + 1, mean, pp, lsbs, bits);
    }
    Serial.println("  Inputs must be shorted to their own VxGND for this to mean");
    Serial.println("  anything. Datasheet says ~13.7 ENOB; expect less on leads.");
    Serial.println("--------------------------------------------------------");
    Serial.println();
}

}  // namespace pintest

namespace pintest {

// Is the RANGE pin actually reaching the chip?
//
// Both a wrong SPI mode and a wrong RANGE assumption produce a clean 2x error,
// so they cannot be told apart from a single reading. This separates them.
//
// Toggling RANGE changes the chip's full-scale span. The driver's volts-per-
// count changes with it, so if the pin IS connected, a fixed DC input reads the
// SAME voltage in both settings — the two changes cancel. If the pin is NOT
// connected, the chip stays in whatever the module straps and only the
// software scaling changes, so the reported voltage moves by exactly 2x.
void adcRangeCheck() {
    float v10[8], v5[8];

    ad7606c::setRange(ad7606c::Range::kBipolar10V);
    delay(50);
    if (!ad7606c::readVolts(v10)) { Serial.println("  read failed"); return; }
    delay(10);
    if (!ad7606c::readVolts(v10)) { Serial.println("  read failed"); return; }

    ad7606c::setRange(ad7606c::Range::kBipolar5V);
    delay(50);
    if (!ad7606c::readVolts(v5)) { Serial.println("  read failed"); return; }
    delay(10);
    if (!ad7606c::readVolts(v5)) { Serial.println("  read failed"); return; }

    Serial.println();
    Serial.println("--- RANGE pin connectivity check -----------------------");
    Serial.println("  ch    as +/-10V     as +/-5V     ratio");
    uint8_t sameCount = 0, halfCount = 0;
    for (uint8_t c = 0; c < 8; c++) {
        const float ratio = (fabs(v5[c]) > 0.02f) ? (v10[c] / v5[c]) : 0.0f;
        Serial.printf("  V%u  %+9.4f V  %+9.4f V   %5.2f\n", c + 1, v10[c], v5[c], ratio);
        if (ratio > 1.8f && ratio < 2.2f) halfCount++;
        else if (ratio > 0.9f && ratio < 1.1f) sameCount++;
    }
    Serial.println();
    if (halfCount >= 4) {
        Serial.println("  RANGE IS NOT CONNECTED (or is strapped on the module).");
        Serial.println("  Readings scale with the software setting alone, so the");
        Serial.println("  chip never changed range. Set the driver to match the");
        Serial.println("  module's strap — the Teensy build used +/-5V.");
    } else if (sameCount >= 4) {
        Serial.println("  RANGE is connected and working: the same input reads the");
        Serial.println("  same voltage in both settings, as it should. Any 2x error");
        Serial.println("  elsewhere is therefore the SPI mode, not the range.");
    } else {
        Serial.println("  Inconclusive — inputs are moving. Retry with a steady DC");
        Serial.println("  input, or with all inputs shorted to their VxGND.");
    }
    Serial.println("--------------------------------------------------------");
    Serial.println();
    ad7606c::setRange(ad7606c::Range::kBipolar10V);
}

}  // namespace pintest

namespace pintest {

// Sweeps all four SPI modes against whatever is connected.
//
// A wrong CPHA shifts every sampled bit by one clock edge, which is
// mathematically a 2x error — smooth, stable and repeatable, but wrong. That is
// indistinguishable from a range mismatch on a single reading, so this sweeps
// the modes and reports the envelope of a moving signal.
//
// With a known +/-1.24 V square wave on V1, the correct mode is the one whose
// min/max straddle +/-1.24 V rather than +/-2.4 V.
void adcSpiModeSweep(uint16_t samplesPerMode) {
    const uint8_t modes[4] = {SPI_MODE0, SPI_MODE1, SPI_MODE2, SPI_MODE3};
    const uint8_t saved = ad7606c::spiMode();

    Serial.println();
    Serial.println("--- SPI mode sweep -------------------------------------");
    Serial.printf("  %u samples per mode. Correct mode = the one whose envelope\n",
                  samplesPerMode);
    Serial.println("  matches the true signal amplitude, not twice it.");
    Serial.println();

    for (uint8_t m = 0; m < 4; m++) {
        ad7606c::setSpiMode(modes[m]);
        delay(20);

        float lo[8], hi[8];
        for (uint8_t c = 0; c < 8; c++) { lo[c] = 1e9f; hi[c] = -1e9f; }
        uint16_t n = 0;
        for (uint16_t i = 0; i < samplesPerMode; i++) {
            float v[8];
            if (!ad7606c::readVolts(v)) continue;
            for (uint8_t c = 0; c < 8; c++) {
                if (v[c] < lo[c]) lo[c] = v[c];
                if (v[c] > hi[c]) hi[c] = v[c];
            }
            n++;
            delayMicroseconds(37);   // deliberately not a 1 kHz submultiple
        }
        Serial.printf("  MODE%u (%u reads)\n", m, n);
        for (uint8_t c = 0; c < 8; c++) {
            Serial.printf("    V%u  min %+8.4f  max %+8.4f  p-p %7.4f V\n",
                          c + 1, lo[c], hi[c], hi[c] - lo[c]);
        }
        Serial.println();
    }

    ad7606c::setSpiMode(saved);
    Serial.println("--------------------------------------------------------");
    Serial.println();
}

}  // namespace pintest
