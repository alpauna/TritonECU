// Latching relay driver — 5 V standby, mains relay ahead of the 36 V supply.
//
// The relay remembers its own state, so this firmware never "holds" anything.
// It emits a PULSE on one coil to set and on the other to reset, and spends the
// rest of its life asleep-ish waiting for a button edge.
//
// Written for an ATtiny202 (tinyAVR 0-series, UPDI). For a classic ATtiny on an
// ISP programmer — 13A, 25/45/85 — change the five pin defines below and the
// board in platformio.ini. Everything else is plain Arduino API.

// test/sim.cpp defines HOST_SIM, stubs the Arduino API and includes this file
// so the state machine can be exercised on a PC without hardware.
#ifndef HOST_SIM
#include <Arduino.h>
#endif

/* ---------------------------------------------------------------------------
   Which relay is fitted
   ---------------------------------------------------------------------------
   LATCHING 1  a latching relay: pulses, and it remembers. Zero holding current,
               but it also holds through a blackout, so setup() has to decide
               what "off" means — see below.
   LATCHING 0  an ordinary 5 V relay: the coil is HELD while on. Costs 70-90 mA
               and ~0.4 W for as long as the supply is on, and only leg A is
               populated. It is fail-safe off by construction: no power, no
               coil, no contact. Nothing in setup() to decide.

   DUAL_COIL  two coils, two low-side FETs. Asserting a leg pin pulls that coil
              to ground: HIGH = energised.
   SINGLE     one coil across the two bridge midpoints, all four FETs fitted.
              Each leg is a CMOS pair with its gates tied, so the leg pin is
              INVERTING: pin LOW = midpoint HIGH. Idle is both pins LOW, which
              puts both midpoints high and the coil sees no differential.
              Ignored when LATCHING is 0 — an ordinary relay has one coil.      */
#define LATCHING  1
#define DUAL_COIL 1

/* ---------------------------------------------------------------------------
   Pins — ATtiny202 SOIC-8: 1 VDD, 2 PA6, 3 PA7, 4 PA1, 5 PA2, 6 UPDI, 7 PA3,
   8 GND. Five usable I/O, which is exactly what this needs.
   --------------------------------------------------------------------------- */
#define PIN_LEG_A   PIN_PA6   // SET  coil  (dual) / bridge leg A (single)
#define PIN_LEG_C   PIN_PA7   // RESET coil (dual) / bridge leg C (single)
#define PIN_BUTTON  PIN_PA1   // to GND, internal pull-up
#define PIN_SENSE   PIN_PA2   // relay's spare pole through a divider, or unused
#define PIN_ECU     PIN_PA3   // pull LOW briefly to toggle from the ESP32

/* ---------------------------------------------------------------------------
   Timing — the only numbers worth tuning to the relay you actually have
   --------------------------------------------------------------------------- */
const uint16_t PULSE_MS     =   30;  // coil energised. 20-50 typical; datasheet
                                     // "set time" is usually 10-15, so this is
                                     // a comfortable 2x
const uint16_t COIL_REST_MS =  150;  // minimum between pulses. Stops a held or
                                     // chattering input hammering the coil
const uint16_t DEBOUNCE_MS  =   25;  // contact bounce is 1-5 ms; 25 is lazy and
                                     // free, since nothing else is happening
const uint16_t LONGPRESS_MS = 1000;  // long press = force OFF, whatever the
                                     // current state

/* Set SENSE_FITTED to 0 if the relay's spare pole is not wired back. The board
   then tracks state in RAM, which is correct until something moves the relay
   without asking — exactly the assumption a bought module makes. */
#define SENSE_FITTED 0

/* ---------------------------------------------------------------------------
   Coil drive
   --------------------------------------------------------------------------- */
static void legsIdle() {
#if DUAL_COIL
    digitalWrite(PIN_LEG_A, LOW);
    digitalWrite(PIN_LEG_C, LOW);
#else
    digitalWrite(PIN_LEG_A, LOW);   // both midpoints high: no differential
    digitalWrite(PIN_LEG_C, LOW);
#endif
}

// pulse(true) = SET (relay on, 36 V supply live). pulse(false) = RESET.
// With LATCHING 0 this holds instead of pulsing, and leg C is never touched.
static void pulse(bool set) {
#if !LATCHING
    digitalWrite(PIN_LEG_A, set ? HIGH : LOW);
    return;
#else
#if DUAL_COIL
    digitalWrite(set ? PIN_LEG_A : PIN_LEG_C, HIGH);
#else
    // drive the coil one way: one midpoint high, the other low
    digitalWrite(set ? PIN_LEG_A : PIN_LEG_C, LOW);   // this end HIGH
    digitalWrite(set ? PIN_LEG_C : PIN_LEG_A, HIGH);  // that end LOW
#endif
    delay(PULSE_MS);
    legsIdle();
    delay(COIL_REST_MS);
#endif
}

/* ---------------------------------------------------------------------------
   State
   --------------------------------------------------------------------------- */
static bool relayOn = false;

static bool readState() {
#if SENSE_FITTED
    return digitalRead(PIN_SENSE) == HIGH;   // spare pole closed when set
#else
    return relayOn;
#endif
}

static void setRelay(bool on) {
    if (readState() == on) return;           // already there; do not wear it out
    pulse(on);
    relayOn = on;
}

/* ---------------------------------------------------------------------------
   Setup — note what happens at power-up, it is the point of the whole board
   --------------------------------------------------------------------------- */
void setup() {
    pinMode(PIN_LEG_A, OUTPUT);
    pinMode(PIN_LEG_C, OUTPUT);
    legsIdle();

    pinMode(PIN_BUTTON, INPUT_PULLUP);
    pinMode(PIN_ECU,    INPUT_PULLUP);
#if SENSE_FITTED
    pinMode(PIN_SENSE,  INPUT);
#endif

    /* FAIL-SAFE OFF. A latching relay holds its state through a blackout, so
       without this the 36 V supply comes back on by itself when the mains
       returns — which is not what anyone wants from a bench supply. Fire RESET
       unconditionally: on a relay that is already reset it costs one pulse.

       The brown-out interlock is the BOD fuse, not code. Set it to 4.3 V and
       the part simply will not run low enough to emit a half-pulse and leave
       the armature stranded. See the firmware README. */
    delay(50);                 // let the 5 V rail settle before loading it
#if LATCHING
    pulse(false);
#endif                         // LATCHING 0 is already off: legsIdle() did it
    relayOn = false;
}

/* ---------------------------------------------------------------------------
   Loop
   --------------------------------------------------------------------------- */
void loop() {
    static uint32_t pressedAt = 0;
    static bool     wasDown   = false;
    static bool     handled   = false;

    bool down = (digitalRead(PIN_BUTTON) == LOW) ||
                (digitalRead(PIN_ECU)    == LOW);

    if (down && !wasDown) {                  // edge: start timing
        pressedAt = millis();
        handled   = false;
        wasDown   = true;
    } else if (down && wasDown && !handled) {
        uint32_t held = millis() - pressedAt;
        if (held >= LONGPRESS_MS) {          // long press: force OFF
            setRelay(false);
            handled = true;
        }
    } else if (!down && wasDown) {           // released
        uint32_t held = millis() - pressedAt;
        if (!handled && held >= DEBOUNCE_MS) setRelay(!readState());
        wasDown = false;
    }
}
