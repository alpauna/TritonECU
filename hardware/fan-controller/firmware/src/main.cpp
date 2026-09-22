/* PSU enclosure fan controller — ATtiny1614.
 *
 * NTC on the board in the END B exhaust, fan through an SS8050 low-side switch,
 * OLED on a tail to the front panel. See ../README.md for why the sensor and
 * the display live in different places.
 *
 * THE CONTROL LAW NEVER LEAVES ADC COUNTS. A bang-bang thermostat only has to
 * know which side of a line it is on, so the Beta equation was solved once at
 * design time and the thresholds are two integers. No float, no log(), no
 * lookup on the path that decides anything. Only the DISPLAY converts to
 * degrees, which means a presentation bug cannot reach the fan.
 *
 * IT IS RATIOMETRIC. The divider is fed from VCC and the ADC references VCC, so
 * rail droop moves both ends and cancels. Do NOT switch this to the internal
 * bandgap: against a fixed reference every millivolt of droop becomes degrees.
 *
 * EVERY FAILURE PATH ENDS WITH THE FAN RUNNING. R4 pulls the base high so a
 * floating pin runs it; boot drives it on before anything else; the watchdog
 * resets on a hang, and reset floats the pin. The one fault that needs catching
 * in software is an OPEN NTC — see readSensor().
 */

#include <Arduino.h>
#include <avr/sleep.h>
#include <avr/wdt.h>
#include <Tiny4kOLED.h>

static const uint8_t PIN_NTC  = PIN_PA3;   // AIN3, divider midpoint
static const uint8_t PIN_FAN  = PIN_PA7;   // -> R3 -> SS8050 base
static const uint8_t PIN_LED  = PIN_PA6;   // status, flashed at each wake
static const uint8_t PIN_WAKE = PIN_PA2;   // SW1 to GND, wakes the display

/* Thresholds in ADC counts, 10-bit, VCC reference. 10k NTC B=3950 as the top
 * leg, 10k 1% to ground. 10.1 counts per degree near 35 C, so the 61 counts
 * between these is 6 C of hysteresis — wide on purpose, because the plant is a
 * box of air and a narrow band only cycles the fan. */
static const uint16_t ADC_ON  = 650;   // 38 C
static const uint16_t ADC_OFF = 589;   // 32 C

/* AN OPEN NTC IS THE DANGEROUS FAULT. Open the top leg and the divider reads
 * near zero, which looks like VERY COLD and would hold the fan off forever. A
 * short reads near full scale, looks like very hot, and fails safe by accident.
 * Only the first needs catching, and 0 C is 234 counts, so nothing legitimate
 * lives below 150. */
static const uint16_t ADC_OPEN  = 150;
static const uint16_t ADC_SHORT = 1000;

static const uint32_t DISPLAY_TIMEOUT_MS = 180000UL;   // blank after 3 min
static const uint16_t SELFTEST_MS        = 3000;

/* Counts -> centi-degrees, display only. 16 knots at 5 C, linear between.
 * 32 bytes of flash for 0.09 C worst-case error, which is an order of magnitude
 * under what the thermistor is accurate to. */
static const uint16_t LUT[16] PROGMEM = {
    234, 285, 339, 396, 454, 512, 567, 620,
    669, 713, 753, 788, 819, 846, 870, 890
};

static bool     fanOn   = false;
static bool     fault   = false;
static uint16_t lastAdc = 0;

static int16_t countsToCentiC(uint16_t adc) {
    uint16_t lo = pgm_read_word(&LUT[0]);
    if (adc <= lo) return 0;
    for (uint8_t i = 1; i < 16; i++) {
        uint16_t hi = pgm_read_word(&LUT[i]);
        if (adc < hi) {
            // 5 C spans (hi - lo) counts; interpolate in hundredths
            return (int16_t)((i - 1) * 500 + ((uint32_t)(adc - lo) * 500) / (hi - lo));
        }
        lo = hi;
    }
    return 7500;
}

static void fanSet(bool on) { fanOn = on; digitalWrite(PIN_FAN, on ? HIGH : LOW); }

static uint16_t readSensor() {
    (void)analogRead(PIN_NTC);            // discard the first, settles the mux
    uint32_t sum = 0;
    for (uint8_t i = 0; i < 8; i++) sum += analogRead(PIN_NTC);
    return (uint16_t)(sum / 8);
}

static void flash(uint8_t n) {
    for (uint8_t i = 0; i < n; i++) {
        digitalWrite(PIN_LED, HIGH); delay(10);
        digitalWrite(PIN_LED, LOW);
        if (i + 1 < n) delay(120);
    }
}

void setup() {
    /* Fan first, before the display, before the ADC, before anything that can
     * block. If this dies later in setup() it dies with air moving. */
    pinMode(PIN_FAN, OUTPUT);
    digitalWrite(PIN_FAN, HIGH);
    fanOn = true;

    pinMode(PIN_LED, OUTPUT);
    pinMode(PIN_WAKE, INPUT_PULLUP);

    oled.begin();
    oled.setFont(FONT8X16);
    oled.clear();
    oled.on();
    oled.setCursor(0, 0);
    oled.print(F("FAN SELFTEST"));

    delay(SELFTEST_MS);        // exercise the fan; a controller that has never
                               // proven the fan turns has not been tested
    wdt_enable(WDTO_8S);
}

void loop() {
    static uint32_t displayOnSince = 0;
    static bool     displayOn      = true;

    wdt_reset();
    lastAdc = readSensor();

    fault = (lastAdc < ADC_OPEN) || (lastAdc > ADC_SHORT);
    if (fault)                        fanSet(true);         // fail to cooling
    else if (!fanOn && lastAdc >= ADC_ON)  fanSet(true);
    else if ( fanOn && lastAdc <= ADC_OFF) fanSet(false);

    if (digitalRead(PIN_WAKE) == LOW) { displayOn = true; displayOnSince = millis(); }
    if (displayOn && (millis() - displayOnSince > DISPLAY_TIMEOUT_MS)) {
        displayOn = false;
        oled.off();     // an OLED left on a static number burns it in
    }

    if (displayOn) {
        int16_t c = countsToCentiC(lastAdc);
        oled.on();
        oled.setCursor(0, 0);
        if (fault) {
            oled.print(F("SENSOR FAULT"));
        } else {
            oled.print(c / 100); oled.print('.'); oled.print((c % 100) / 10);
            oled.print(F(" C   "));
        }
        oled.setCursor(0, 2);
        oled.print(fanOn ? F("FAN ON   ") : F("fan off  "));
    }

    flash(fault ? 3 : (fanOn ? 2 : 1));
    delay(1000);
}
