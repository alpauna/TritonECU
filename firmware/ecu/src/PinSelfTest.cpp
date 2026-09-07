#include "PinSelfTest.h"

#include <Arduino.h>
#include <string.h>

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
