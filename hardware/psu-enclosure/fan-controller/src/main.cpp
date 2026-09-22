/* PSU enclosure fan controller.
 *
 * Reads the exhaust air with a DHT22 and switches the 40 mm intake fan through
 * a low-side N-FET. See ../README.md for why the fan is not a load for the
 * adjustable rail, and ../../2N7002 Driver/ for the gate drive itself.
 *
 * EVERY FAILURE PATH ENDS WITH THE FAN RUNNING. This box's airflow depends
 * entirely on this fan, and it holds a warm supply and a mains connection, so
 * "off" is the expensive way to be wrong:
 *
 *   the base carries an external 470R pull-up, so a floating pin means ON
 *   setup() drives it ON first, before serial, before the sensor
 *   a crash or reset floats the pin on the way through, so the pull-up covers
 *     the reset window as well as the boot
 *   repeated sensor failures force ON rather than holding the last state
 *
 * What software CANNOT cover is the ESP32 losing power while the supply keeps
 * running, or a genuine CPU hang with the pin still driven low. Both need the
 * KSD9700 60 C normally-open thermal switch across the FET. That part is not
 * belt-and-braces; it covers the cases this file structurally cannot.
 */

#include <Arduino.h>
#include "DHT22.h"
#include <driver/gpio.h>

/* 4 and 13 are interchangeable here - neither is a strapping pin, neither
 * glitches at boot, both drive and both take a pull-up - which is worth knowing
 * because this assignment got swapped twice: once in firmware to match the
 * wiring, and simultaneously in the wiring to match the firmware. Landed back
 * where it started. If it ever moves again, ../dht-scan finds the sensor by
 * probing every free pin rather than by asking. */
static const uint8_t PIN_FAN = 4;    // -> 470R pull-up to 3V3, then H1-2 -> R1 -> base
static const uint8_t PIN_DHT = 13;   // 10k pull-up to 3V3

/* Hysteresis on the EXHAUST air, which is air that has already crossed the
 * heatsink. Six degrees is deliberately wide: the plant is a box of air with a
 * long time constant, and a narrow band just cycles the fan without changing
 * the average temperature. */
/* Overridable at build time so the control law can be exercised against room
 * temperature on the bench. Proving the thresholds actually switch beats
 * trusting two lines of comparison, and a bench test should not need a source
 * edit that someone can forget to undo:
 *   pio run -t upload --project-option "build_flags=-DT_ON_C_VAL=27.0f -DT_OFF_C_VAL=25.0f"
 */
#ifndef T_ON_C_VAL
#define T_ON_C_VAL  38.0f
#endif
#ifndef T_OFF_C_VAL
#define T_OFF_C_VAL 32.0f
#endif
static const float T_ON_C  = T_ON_C_VAL;
static const float T_OFF_C = T_OFF_C_VAL;

static const uint32_t SAMPLE_MS  = 2500;   // datasheet floor is 2 s
static const uint8_t  FAIL_LIMIT = 4;      // bad reads before forcing ON
static const uint32_t SELFTEST_MS = 3000;

static DHT22   dht(PIN_DHT);
static bool    fanOn = false;
static uint8_t fails = 0;

static void fanSet(bool on, const char* why) {
    if (on != fanOn) Serial.printf("  FAN %-3s  (%s)\n", on ? "ON" : "OFF", why);
    fanOn = on;
    digitalWrite(PIN_FAN, on ? HIGH : LOW);
}

void setup() {
    // Fan first. Before serial, before the sensor, before anything that could
    // block or throw. If this sketch dies later in setup(), it dies with air
    // moving.
    pinMode(PIN_FAN, OUTPUT);
    digitalWrite(PIN_FAN, HIGH);
    fanOn = true;
#ifdef FAN_TEST
    // Read back the pad rather than the output register, so the bench test can
    // tell "not commanded" from "commanded and held down" without a meter.
    gpio_set_direction((gpio_num_t)PIN_FAN, GPIO_MODE_INPUT_OUTPUT);
#endif

    Serial.begin(115200);
    delay(300);
    Serial.println("\n\n=== PSU enclosure fan controller ===");
    Serial.printf("fan gate GPIO%u (HIGH = run), DHT22 GPIO%u\n", PIN_FAN, PIN_DHT);
    Serial.printf("hysteresis: ON above %.1f C, OFF below %.1f C\n", T_ON_C, T_OFF_C);

    /* Exercise the fan at boot. A controller that has never once proven the fan
     * turns is a controller that finds out about a seized bearing during the
     * thermal event it was installed to prevent. */
    Serial.printf("self-test: fan running %lu ms - confirm it spins\n",
                  (unsigned long)SELFTEST_MS);
    dht.begin();
    delay(SELFTEST_MS);
    Serial.println("self-test done, entering control\n");
}

#ifdef FAN_TEST
/* Bench mode: square wave on the output, sensor ignored. Separates "the
 * firmware is not commanding it" from "the hardware is not following", which
 * are the only two possibilities and want different fixes.
 *
 *   PLATFORMIO_BUILD_FLAGS=-DFAN_TEST pio run -t upload
 */
void loop() {
    static uint32_t last = 0;
    static bool on = true;
    if (millis() - last < 2000) return;
    last = millis();

    /* Hold HIGH solid for the first 20 s. A meter probe touched once onto a
     * 50/50 square wave reads 0 V half the time by luck, and that reading is
     * indistinguishable from a pin that cannot drive. */
    if (millis() < 20000) on = true; else on = !on;

    digitalWrite(PIN_FAN, on ? HIGH : LOW);
    delayMicroseconds(50);

    /* GPIO_MODE_INPUT_OUTPUT (set in setup) means digitalRead returns the PAD,
     * not the output register - so this is what the pin actually is, not what
     * we asked for. Driven HIGH but reading LOW means something external is
     * holding it down, and no amount of firmware will fix that. */
    int pad = digitalRead(PIN_FAN);
    bool disagree = (pad != (on ? HIGH : LOW));

    Serial.printf("[%6lus] GPIO%u driven %-4s  pad reads %-4s  %s\n",
                  millis()/1000, PIN_FAN, on ? "HIGH" : "LOW",
                  pad ? "HIGH" : "LOW",
                  disagree ? "*** DISAGREES - pin is loaded or shorted ***"
                           : (on ? "ok, fan should be RUNNING" : "ok, stopped"));
}
#else
void loop() {
    static uint32_t last = 0;
    if (millis() - last < SAMPLE_MS) return;
    last = millis();

    float t = NAN, h = NAN;
    DHT22::Result r = dht.read(t, h);

    if (r != DHT22::OK) {
        if (fails < 255) fails++;
        Serial.printf("[%6lus] read failed: %s  (%u/%u)\n",
                      millis()/1000, DHT22::strerror(r), fails, FAIL_LIMIT);
        if (fails >= FAIL_LIMIT)
            fanSet(true, "sensor unreadable - failing to cooling");
        return;
    }
    fails = 0;

    Serial.printf("[%6lus] %5.1f C  %5.1f %%RH   fan %s\n",
                  millis()/1000, t, h, fanOn ? "ON" : "off");

    if (!fanOn && t >= T_ON_C)  fanSet(true,  "above the on threshold");
    if ( fanOn && t <= T_OFF_C) fanSet(false, "below the off threshold");
}
#endif
