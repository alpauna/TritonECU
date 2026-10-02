/* PSU enclosure fan controller — ATtiny1614.
 *
 * NTC on the board in the END B exhaust, fan through an AO3400A low-side switch,
 * OLED on a tail to the front panel. See ../README.md for why the sensor and
 * the display live in different places.
 *
 * THE CONTROL LAW NEVER LEAVES ADC COUNTS. A thermostat only has to know which
 * side of a line it is on, so the Beta equation was solved once at design time
 * and the thresholds are integers. No float, no log(), no lookup on the path
 * that decides anything. Only the DISPLAY converts to degrees, which means a
 * presentation bug cannot reach the fan. v2's speed steps are counts too.
 *
 * IT IS RATIOMETRIC. The divider is fed from VCC and the ADC references VCC, so
 * rail droop moves both ends and cancels. Do NOT switch this to the internal
 * bandgap: against a fixed reference every millivolt of droop becomes degrees.
 *
 * EVERY FAILURE PATH ENDS WITH THE FAN RUNNING. R2 pulls the gate high so a
 * floating pin runs it; boot drives it on before anything else; the watchdog
 * resets on a hang, and reset floats the pin. The one fault that needs catching
 * in software is an OPEN NTC — see ADC_OPEN.
 *
 * FAN_HW_V2 adds the 3/4-wire fan: 25 kHz PWM through Q2, tach on PA5, fan
 * type detected at boot, and a status line on serial once a pass. Without it
 * this builds the v1 board exactly - v1 has no pads for any of that.
 *
 * The v2 board is an ATtiny1616 (VQFN-20): PWM on PB5, USART0 on its default
 * PB2 (TX) / PB3 (RX). The bench build is a v1 board's ATtiny1614, which has
 * no PB5, so there PWM stays on PB2 and TX moves to PA1. The MCU decides which;
 * nothing else differs. See README, v2.
 */

#include <Arduino.h>
#include <avr/wdt.h>
#include <Tiny4kOLED.h>

static const uint8_t PIN_NTC  = PIN_PA3;   // AIN3, divider midpoint
static const uint8_t PIN_FAN  = PIN_PA7;   // -> R1 220R -> Q1 AO3400A gate
static const uint8_t PIN_LED  = PIN_PA6;   // status, ACTIVE LOW: +5V -> R -> LED -> PA6
static const uint8_t PIN_WAKE = PIN_PA2;   // SW1 to GND, wakes the display
static const uint8_t PIN_SET  = PIN_PA4;   // RV1 wiper, setpoint
#ifdef FAN_HW_V2
#if defined(__AVR_ATtiny1616__)
/* WO2's ALTERNATE pin (PORTMUX.CTRLC TCA02), which frees PB2/PB3 for USART0 at
 * its default pins. The datasheet: TCA02 works in normal mode, unlike TCA03-05
 * which are split-mode only. */
static const uint8_t PIN_PWM  = PIN_PB5;   // TCA0 WO2 alt -> R10 220R -> Q2, INVERTED
#define PWM_ALT_PIN 1
#else
static const uint8_t PIN_PWM  = PIN_PB2;   // bench 1614: TCA0 WO2 default
#define PWM_ALT_PIN 0
#endif
static const uint8_t PIN_TACH = PIN_PA5;   // 10k series + 5V1 zener, NO pull-up
static const uint32_t BAUD    = 115200;
#endif

/* Thresholds in ADC counts, 10-bit, VCC reference. 10k NTC B=3950 as the top
 * leg, 10k 1% to ground. 10.1 counts per degree near 35 C, so the 61 counts
 * between these is 6 C of hysteresis — wide on purpose, because the plant is a
 * box of air and a narrow band only cycles the fan. */
/* THE POT IS NOT CONVERTED TO DEGREES AND NOT CALIBRATED. It is another divider
 * on the same ADC against the same reference, so the setpoint is compared
 * against the sensor directly and the fan trips where the two readings cross.
 * No mapping constants, no LUT in the control path.
 *
 * That also makes the comparison supply-immune in a way a mapped setpoint would
 * not be: BOTH dividers are ratiometric off VCC, so a sagging rail moves the
 * sensor and the setpoint together and the crossing stays put. */
static const uint16_t ADC_DEFAULT = 650;   // 38 C, used only if the pot is faulty
static const uint16_t HYST        =  61;   // counts. See README for the degrees
                                           // this rides across the range.

/* RV1 is wired as a RHEOSTAT - wiper tied to the terminal on the ADC side - in
 * the top leg, between 6k8 and 20k. That pins the node to 556..763 counts,
 * about 29..51 C.
 *
 * WHY A RHEOSTAT AND NOT A 3-TERMINAL DIVIDER. If the wiper contact fails, the
 * track is still intact, so the resistance goes to FULL scale and the node
 * lands at 556 - the lowest setpoint, fan earliest. It degrades toward cooling
 * by construction, with nothing to detect. A 3-terminal pot would leave the
 * node floating and the reading anyone's guess.
 *
 * It also spends the whole knob on settings worth having: a divider would have
 * reached 62 C, and nobody wants a 62 C setpoint in this box.
 *
 * The window below still catches LEAD faults, which the wiring cannot: R8 open
 * pulls the node to ground (0), R9 open pulls it to the rail (1023), and a
 * missing pot leaves it grounded through R9. */
/* WIDENED for the pot's +/-20% tolerance (ALPS RK09K11300DR). Only the LOW end
 * of the span moves - at 0 ohm the pot contributes nothing to the divider, so
 * 763 is tolerance-free - but a +20% part reads 527 at full travel, and the old
 * 506 left 21 counts of margin. That would have flagged a good pot as broken.
 * A fault still reads ~0 or ~1023, so this window catches them by a mile. */
static const uint16_t POT_MIN = 450;
static const uint16_t POT_MAX = 850;

/* AN OPEN NTC IS THE DANGEROUS FAULT. Open the top leg and the divider reads
 * near zero, which looks like VERY COLD and would hold the fan off forever. A
 * short reads near full scale, looks like very hot, and fails safe by accident.
 * Only the first needs catching, and 0 C is 234 counts, so nothing legitimate
 * lives below 150. */
static const uint16_t ADC_OPEN  = 150;
static const uint16_t ADC_SHORT = 1000;

static const uint32_t DISPLAY_TIMEOUT_MS = 180000UL;   // blank after 3 min
static const uint16_t SELFTEST_MS        = 3000;

/* v2 speed steps, ABOVE the setpoint. 30 % at the setpoint, +10 % per STEP
 * counts, 100 % at setpoint + 7 steps. STEP = 10 counts is ~1.0 C at 38 C and
 * ~1.2 C at 50 C. Each step goes UP at its boundary and DOWN only STEP_HYST
 * below it: ADC noise is a count or two, and without the dead band a reading on
 * a boundary flips the fan between two speeds every pass. */
static const uint8_t  STEP        = 10;    // counts per speed step
static const uint8_t  STEP_HYST   = 4;     // counts
static const uint8_t  TOP_LEVEL   = 7;     // 30 % + 7 x 10 % = 100 %
static const uint8_t  DUTY_FLOOR  = 30;    // %; most fans do not start below
static const uint8_t  DUTY_STEP   = 10;    // %

/* 5 MHz / (PER + 1) = 25.000 kHz, Intel's 21-28 kHz window. analogWrite()'s
 * PER = 255 misses it at every clock - see README. */
static const uint8_t  PWM_PER     = 199;
static const uint16_t KICK_MS     = 300;   // 100 % on every stopped -> running
static const uint16_t STALL_MS    = 2000;  // running, no tach pulse this long
static const uint8_t  TACH_MIN    = 3;     // pulses/s; below this, no tach

/* Counts -> centi-degrees, display only. 16 knots at 5 C, linear between.
 * 32 bytes of flash for 0.09 C worst-case error, which is an order of magnitude
 * under what the thermistor is accurate to. */
static const uint16_t LUT[16] PROGMEM = {
    234, 285, 339, 396, 454, 512, 567, 620,
    669, 713, 753, 788, 819, 846, 870, 890
};

enum FanType : uint8_t { FAN_2W, FAN_3W, FAN_4W };

static bool     fanOn    = false;   // Q1 on
static FanType  fanType  = FAN_2W;  // detected at boot on v2; always 2W on v1
static uint8_t  level    = 0;       // speed step, 4-wire only
static bool     stall    = false;   // commanded running, tach silent
static uint16_t rpm      = 0;
static bool     fault    = false;   // NTC open or shorted
static bool     potFault = false;   // wiper open or lead broken
static uint16_t lastAdc  = 0;
static uint16_t setpoint = ADC_DEFAULT;

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

#ifdef FAN_HW_V2
static volatile uint16_t tachPulses = 0;
static void onTach() { tachPulses++; }
static uint32_t lastTachMs = 0;
static uint32_t lastPassMs = 0;   // RPM window, one loop pass

static uint16_t takePulses() {
    noInterrupts();
    uint16_t n = tachPulses;
    tachPulses = 0;
    interrupts();
    return n;
}

/* Q2 INVERTS: PB2 high pulls the fan's PWM line low. So the fan's duty is the
 * time PB2 is LOW, and 100 % is the compare output switched off with PB2 held
 * low - Q2 off, the line released. That is also the reset state (Q2's gate
 * pull-down), and the state whenever the fan is stopped: with Q1 off the fan's
 * ground floats, and Q2 on would hand it a ground path through its PWM pin. */
static void pwmDuty(uint8_t pct) {
    if (pct >= 100) {
        TCA0.SINGLE.CTRLB &= ~TCA_SINGLE_CMP2EN_bm;
        digitalWrite(PIN_PWM, LOW);
    } else {
        TCA0.SINGLE.CMP2BUF = (uint16_t)(PWM_PER + 1) * (100 - pct) / 100;
        TCA0.SINGLE.CTRLB |= TCA_SINGLE_CMP2EN_bm;
    }
}

static void pwmBegin() {
    pinMode(PIN_PWM, OUTPUT);
    digitalWrite(PIN_PWM, LOW);               // released: fan full speed
    takeOverTCA0();                           // stops and hard-resets TCA0;
                                              // millis() is on TCD0, untouched
#if PWM_ALT_PIN
    PORTMUX.CTRLC |= PORTMUX_TCA02_bm;        // WO2 -> PB5
#endif
    TCA0.SINGLE.CTRLB = TCA_SINGLE_WGMODE_SINGLESLOPE_gc;
    TCA0.SINGLE.PER   = PWM_PER;
    TCA0.SINGLE.CMP2  = 0;
    TCA0.SINGLE.CTRLA = TCA_SINGLE_CLKSEL_DIV1_gc | TCA_SINGLE_ENABLE_bm;
}
/* Serial is OUT only in this firmware: one status line per pass, for tuning
 * and bring-up. RX is wired on the v2 board but unread. Its internal pull-up
 * holds the line idle when nothing is plugged into H3, rather than letting it
 * float and clock noise into the receiver. R13/R14 (1k) on the board limit
 * back-powering from a connected adapter while the board is off.
 *
 * Bench 1614: TX on PA1 (USART0 alternate). Its RX would be PA2 - the wake
 * button - so the receiver is switched off and PA2 handed back. */
static void serialBegin() {
#if PWM_ALT_PIN
    Serial.begin(BAUD);
    PORTB.PIN3CTRL |= PORT_PULLUPEN_bm;       // RX idle-high when unplugged
#else
    Serial.swap(1);                           // TX PA1, RX PA2
    Serial.begin(BAUD);
    USART0.CTRLB &= ~USART_RXEN_bm;           // PA2 is the wake button
#endif
}
#else
static void pwmDuty(uint8_t) {}
#endif

/* Starting releases PWM first, so the fan comes up at 100 % - which IS the
 * kick a 4-wire fan needs to start from below its floor. Stopping releases
 * PWM before Q1 opens, for the floating-ground reason above. */
static void fanSet(bool on) {
    if (on == fanOn) return;
    pwmDuty(100);
    digitalWrite(PIN_FAN, on ? HIGH : LOW);
    fanOn = on;
    level = 0;
#ifdef FAN_HW_V2
    if (on) {
        if (fanType == FAN_4W) delay(KICK_MS);
        lastTachMs = millis();                // the stall clock starts now
        (void)takePulses();
    }
#endif
}

/* IS THE OLED THERE? oled.begin() on a bus with no display HANGS: the pull-ups
 * live on the OLED module, so without it SDA and SCL float, the TWI sees a bus
 * that never goes idle, and waits forever. That froze a board in setup() with
 * the fan on and the watchdog not yet armed.
 *
 * So check the lines first: pull each low for a moment, release it, and see
 * whether something pulls it back up. Floating, it stays where it was put. Only
 * then ask the bus whether 0x3C answers. No display means run headless - the
 * staging README's second board, which was always meant to have none. */
static const uint8_t PIN_SCL = PIN_PB0;
static const uint8_t PIN_SDA = PIN_PB1;
static bool hasOled = false;

static bool lineHasPullup(uint8_t pin) {
    pinMode(pin, OUTPUT);
    digitalWrite(pin, LOW);
    delayMicroseconds(10);
    pinMode(pin, INPUT);              // no internal pull-up - we want the module's
    delayMicroseconds(100);           // 10k x ~100 pF is 1 us; this is plenty
    return digitalRead(pin) == HIGH;
}

static bool oledPresent() {
    if (!lineHasPullup(PIN_SCL) || !lineHasPullup(PIN_SDA)) return false;
    Wire.begin();
    Wire.beginTransmission(SSD1306);
    return Wire.endTransmission() == 0;
}

/* Speed step for a reading `above` counts over the setpoint. */
static uint8_t levelFor(int16_t above) {
    if (above <= 0) return 0;
    uint16_t l = (uint16_t)above / STEP;
    return l > TOP_LEVEL ? TOP_LEVEL : (uint8_t)l;
}

/* The wake button is LATCHED, not polled. Polling it once per pass only saw a
 * press held at that instant, so a tap during the 1 s wait was lost. A falling
 * edge sets this flag and cuts the wait short. Contact bounce can set it again
 * and cost one extra pass, which is harmless. */
static volatile bool wakeTapped = false;
static void onWake() { wakeTapped = true; }

static uint16_t readAvg(uint8_t pin) {
    (void)analogRead(pin);                // discard the first, settles the mux
    uint32_t sum = 0;
    for (uint8_t i = 0; i < 8; i++) sum += analogRead(pin);
    return (uint16_t)(sum / 8);
}

static void flash(uint8_t n) {
    for (uint8_t i = 0; i < n; i++) {
        digitalWrite(PIN_LED, LOW); delay(10);    // active low - lit
        digitalWrite(PIN_LED, HIGH);
        if (i + 1 < n) delay(120);
    }
}

void setup() {
    /* Fan first, before the display, before the ADC, before anything that can
     * block. If this dies later in setup() it dies with air moving. */
    pinMode(PIN_FAN, OUTPUT);
    digitalWrite(PIN_FAN, HIGH);
    fanOn = true;

    /* WATCHDOG NEXT, before anything else that can block. It used to be armed
     * at the end of setup(), so a hang inside setup() was permanent - fan on,
     * board dead, no reset coming. Armed here, any hang resets within 8 s.
     * The self-test is 3 s (5 s on v2), well inside it.
     *
     * tinyAVR 0/1-series has the NEW watchdog, not the classic AVR one, so
     * wdt_enable(WDTO_8S) does not exist here - the period goes straight into
     * WDT.CTRLA behind the configuration-change protection. 8K cycles of the
     * 1.024 kHz OSCULP32K divider is 8 s, which is long against a 1 s loop and
     * short against a box heating up.
     *
     * The reset it causes IS part of the fail-safe: a reset floats PA7, and
     * R2 is a pull-up (see README, As built), so a floating PA7 runs the fan.
     * wdt_reset() is just the WDR instruction and works on any AVR. */
    _PROTECTED_WRITE(WDT.CTRLA, WDT_PERIOD_8KCLK_gc);

    digitalWrite(PIN_LED, HIGH);   // dark before the pin becomes an output
    pinMode(PIN_LED, OUTPUT);
#ifdef FAN_HW_V2
    serialBegin();                 // before the wake pin: the bench build's
                                   // USART would otherwise claim PA2 after it
#endif
    pinMode(PIN_WAKE, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_WAKE), onWake, FALLING);
#ifdef FAN_HW_V2
    pwmBegin();
    /* NO internal pull-up: with the 10k series resistor it would form a divider
     * that holds a tach LOW at up to 1.7 V, above the 1.5 V threshold. The
     * pull-up is external, on the fan's side of the series resistor. */
    pinMode(PIN_TACH, INPUT);
    attachInterrupt(digitalPinToInterrupt(PIN_TACH), onTach, FALLING);
#endif

    hasOled = oledPresent();
    if (hasOled) {
        oled.begin();
        oled.setFont(FONT8X16);
        oled.clear();
        oled.on();
        oled.setCursor(0, 0);
        oled.print(F("FAN SELFTEST"));
    }

#ifdef FAN_HW_V2
    /* Detect the fan inside the self-test. Full speed, count the last second:
     * no tach is a 2-wire fan. Then 30 %: a 4-wire fan slows, a 3-wire fan
     * ignores the PWM line. Every misdetection fails toward MORE cooling - see
     * README. A 3/4-wire fan dead at boot reads as 2-wire and loses only the
     * stall alarm. */
    delay(SELFTEST_MS - 1000);
    (void)takePulses();
    delay(1000);
    uint16_t full = takePulses();
    uint16_t slow = 0;
    if (full < TACH_MIN) {
        fanType = FAN_2W;
    } else {
        rpm = full * 30;                      // 2 pulses per revolution
        pwmDuty(DUTY_FLOOR);
        delay(1000);
        (void)takePulses();
        delay(1000);
        slow = takePulses();
        pwmDuty(100);
        fanType = ((uint32_t)slow * 10 < (uint32_t)full * 7) ? FAN_4W : FAN_3W;
    }
    lastTachMs = lastPassMs = millis();
    (void)takePulses();
    /* The detection evidence, not just the verdict: if a fan is misread, this
     * line shows by how much. */
    Serial.print(F("boot fan="));
    Serial.print(fanType == FAN_4W ? F("4W") : fanType == FAN_3W ? F("3W") : F("2W"));
    Serial.print(F(" full_rpm=")); Serial.print((uint32_t)full * 30);
    Serial.print(F(" slow_rpm=")); Serial.print((uint32_t)slow * 30);
    Serial.print(F(" oled=")); Serial.println(hasOled ? 1 : 0);
    if (hasOled) {
        oled.setCursor(0, 2);
        oled.print(fanType == FAN_4W ? F("4W ") : fanType == FAN_3W ? F("3W ") : F("2W "));
        if (fanType != FAN_2W) { oled.print(rpm); oled.print(F(" rpm")); }
    }
#else
    delay(SELFTEST_MS);        // exercise the fan; a controller that has never
                               // proven the fan turns has not been tested
#endif
}

void loop() {
    static uint32_t displayOnSince = 0;
    static bool     displayOn      = true;

    wdt_reset();
    lastAdc = readAvg(PIN_NTC);

    /* A faulty pot falls back to the compiled default, NOT to fan-on. A
     * known-good threshold beats a fan that runs forever, and the display says
     * the pot is being ignored. The NTC is the opposite case - see below. */
    uint16_t pot = readAvg(PIN_SET);
    potFault = (pot < POT_MIN) || (pot > POT_MAX);
    setpoint = potFault ? ADC_DEFAULT : pot;

    fault = (lastAdc < ADC_OPEN) || (lastAdc > ADC_SHORT);
    if (fault)                                    fanSet(true);   // fail to cooling
    else if (!fanOn && lastAdc >= setpoint)        fanSet(true);
    else if ( fanOn && lastAdc <= setpoint - HYST) fanSet(false);

#ifdef FAN_HW_V2
    /* Tach: RPM for the display, and a stall is running with no pulse for
     * STALL_MS. fanSet() restarts the clock, so spin-up is not a stall. */
    uint32_t now = millis();
    uint16_t pulses = takePulses();
    if (pulses) lastTachMs = now;
    if (now > lastPassMs) rpm = (uint32_t)pulses * 30000UL / (now - lastPassMs);
    lastPassMs = now;
    stall = fanOn && fanType != FAN_2W && (now - lastTachMs > STALL_MS);
#endif

    /* Speed, 4-wire only. Step up at a boundary, down STEP_HYST below it. In
     * the hysteresis band under the setpoint, level 0 holds the floor until
     * the off point. A sensor fault or a stall overrides to full. */
    if (fanOn && fanType == FAN_4W) {
        int16_t above = (int16_t)lastAdc - (int16_t)setpoint;
        uint8_t up    = levelFor(above);
        uint8_t down  = levelFor(above + STEP_HYST);
        if (up > level)        level = up;
        else if (down < level) level = down;
        pwmDuty((fault || stall) ? 100 : DUTY_FLOOR + DUTY_STEP * level);
    }

    if (wakeTapped || digitalRead(PIN_WAKE) == LOW) {
        wakeTapped = false;
        displayOn = true; displayOnSince = millis();
    }
    if (!hasOled) displayOn = false;              // headless: nothing to draw
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
            oled.print(F(" C  "));
            if (fanOn && fanType != FAN_2W) { oled.print(rpm); oled.print(F("rpm")); }
            oled.print(F("      "));      // clear a longer previous line
        }
        oled.setCursor(0, 2);
        if (stall)                  oled.print(F("STALL   "));
        else if (!fanOn)            oled.print(fanType == FAN_2W ? F("fan off ")
                                             : fanType == FAN_3W ? F("3W off  ")
                                                                 : F("4W off  "));
        else if (fanType == FAN_2W) oled.print(F("FAN ON  "));
        else if (fanType == FAN_3W) oled.print(F("3W ON   "));
        else {
            uint8_t d = fault ? 100 : DUTY_FLOOR + DUTY_STEP * level;
            oled.print(F("4W ")); oled.print(d); oled.print(d < 100 ? F("%  ") : F("% "));
        }
        /* Setpoint through the SAME LUT as the reading, so both carry identical
         * calibration and any error in the table cancels between them. */
        int16_t sp = countsToCentiC(setpoint);
        oled.print(F("set ")); oled.print(sp / 100);
        oled.print(potFault ? F("! ") : F("  "));
    }

#ifdef FAN_HW_V2
    /* One line per pass. Counts AND degrees: the control law runs on counts,
     * so tuning wants them; degrees are for reading. */
    Serial.print(F("adc="));    Serial.print(lastAdc);
    Serial.print(F(" t="));     { int16_t c = countsToCentiC(lastAdc);
                                  Serial.print(c / 100); Serial.print('.');
                                  Serial.print((c % 100) / 10); }
    Serial.print(F(" set="));   Serial.print(setpoint);
    Serial.print(F(" fan="));   Serial.print(fanOn ? 1 : 0);
    Serial.print(F(" duty="));  Serial.print(fanType == FAN_4W && fanOn
                                    ? ((fault || stall) ? 100 : DUTY_FLOOR + DUTY_STEP * level)
                                    : (fanOn ? 100 : 0));
    Serial.print(F(" rpm="));   Serial.print(rpm);
    Serial.print(F(" stall=")); Serial.print(stall ? 1 : 0);
    Serial.print(F(" fault=")); Serial.print(fault ? 1 : 0);
    Serial.print(F(" pot="));   Serial.println(potFault ? 1 : 0);
#endif
    flash(fault || potFault || stall ? 3 : (fanOn ? 2 : 1));
    /* The MCU does not sleep - it waits awake. Self-heating at this duty is
     * well inside what an on/off enclosure fan cares about (README). */
    for (uint8_t i = 0; i < 100 && !wakeTapped; i++) delay(10);
}
