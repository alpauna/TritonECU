/* POWER board bring-up diagnostic.
 *
 * Answers one question the slow instruments cannot: WHICH RAIL LET GO FIRST.
 *
 * The board drops out above ~24 V and the protector's UV, OV and FB-clamp
 * inputs have all been cleared by measurement, so either the LTC4364 is
 * faulting on current limit or the MAX25239 is misbehaving as its on-time
 * hits the floor and the protector is merely reacting. Those two look
 * identical from outside - VIN disappears either way.
 *
 * They differ in ORDER, by microseconds:
 *
 *   3.3_ENOUT falls first, then 5_GOOD  -> protector faulted, starved the buck
 *   5_GOOD falls first, then 3.3_ENOUT  -> buck failed, protector reacted
 *
 * So the three status pins are captured on interrupt and timestamped with the
 * DWT cycle counter: at 216 MHz that is 4.63 ns per tick, which is four orders
 * of magnitude finer than the event being resolved. The INA238 cannot do this -
 * at 20 kSa/s it averages straight over the whole transition.
 */

#include <Arduino.h>
#include <Wire.h>

static const uint8_t PIN_ENOUT = D7;   // 3.3_ENOUT - LTC4364 enable, level shifted
static const uint8_t PIN_5GOOD = D4;
static const uint8_t PIN_3GOOD = D2;

/* INA238 sits on the same 10 mOhm shunt the LTC4364 uses for current limit, so
 * it reads the current that trips the protector - just far too slowly to see
 * the trip itself. Useful for the trend as VIN is swept, not for the event. */
static const float RSHUNT = 0.010f;
static const uint8_t REG_CONFIG = 0x00, REG_ADCCFG = 0x01;
static const uint8_t REG_VSHUNT = 0x04, REG_VBUS = 0x05;

/* ADCRANGE = 0: +/-163.84 mV full scale, 5 uV/LSB -> 500 uA/LSB on 10 mOhm,
 * +/-16.384 A. ADCRANGE 1 would resolve finer but clips at 4.1 A, below the
 * 5 A limit we are trying to watch approach. */
static const float VSHUNT_LSB = 5e-6f;
static const float VBUS_LSB   = 3.125e-3f;

static uint8_t ina_addr = 0;

struct Event { uint32_t cyc; uint8_t pin; uint8_t level; };
static volatile Event  ring[64];
static volatile uint8_t head = 0, tail = 0;

/* Fields written one at a time, not as a struct. A volatile array element
 * cannot be assigned from an aggregate - the implicit copy constructor takes a
 * non-volatile reference - and volatile is not decoration here: the ISR writes
 * what the main loop reads. */
static inline void log_edge(uint8_t pin, uint8_t level) {
    uint8_t h = head & 63;
    ring[h].cyc   = DWT->CYCCNT;
    ring[h].pin   = pin;
    ring[h].level = level;
    head = head + 1;                    // single writer, free-running index
}
static void isr_enout() { log_edge(0, digitalRead(PIN_ENOUT)); }
static void isr_5good() { log_edge(1, digitalRead(PIN_5GOOD)); }
static void isr_3good() { log_edge(2, digitalRead(PIN_3GOOD)); }

static const char* NAME[] = { "3.3_ENOUT", "5_GOOD   ", "3.3_GOOD " };

static bool ina_read(uint8_t reg, int16_t& v) {
    Wire.beginTransmission(ina_addr); Wire.write(reg);
    if (Wire.endTransmission(false) != 0) return false;
    if (Wire.requestFrom((int)ina_addr, 2) != 2) return false;
    v = (int16_t)((Wire.read() << 8) | Wire.read());
    return true;
}
static bool ina_write(uint8_t reg, uint16_t v) {
    Wire.beginTransmission(ina_addr);
    Wire.write(reg); Wire.write(v >> 8); Wire.write(v & 0xFF);
    return Wire.endTransmission() == 0;
}

void setup() {
    Serial.begin(115200);
    delay(300);
    Serial.println(F("\n\n=== POWER board diagnostic ==="));

    // DWT cycle counter - the whole reason this runs on an M7
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0;
    DWT->CTRL  |= DWT_CTRL_CYCCNTENA_Msk;
    Serial.printf("DWT at %lu Hz -> %.2f ns per tick\n",
                  (unsigned long)F_CPU, 1e9f / F_CPU);

    pinMode(PIN_ENOUT, INPUT);
    pinMode(PIN_5GOOD, INPUT);
    pinMode(PIN_3GOOD, INPUT);
    attachInterrupt(digitalPinToInterrupt(PIN_ENOUT), isr_enout, CHANGE);
    attachInterrupt(digitalPinToInterrupt(PIN_5GOOD), isr_5good, CHANGE);
    attachInterrupt(digitalPinToInterrupt(PIN_3GOOD), isr_3good, CHANGE);
    Serial.printf("initial: ENOUT %d  5_GOOD %d  3.3_GOOD %d\n",
                  digitalRead(PIN_ENOUT), digitalRead(PIN_5GOOD), digitalRead(PIN_3GOOD));

    Wire.begin();
    Wire.setClock(400000);
    Serial.print(F("I2C scan:"));
    for (uint8_t a = 0x40; a <= 0x4F; a++) {       // INA238 strap range
        Wire.beginTransmission(a);
        if (Wire.endTransmission() == 0) { Serial.printf(" 0x%02X", a); if (!ina_addr) ina_addr = a; }
    }
    if (!ina_addr) { Serial.println(F("  none found - check SDA/SCL and 3V3")); return; }
    Serial.printf("  -> using 0x%02X\n", ina_addr);

    ina_write(REG_CONFIG, 0x8000); delay(5);       // reset
    ina_write(REG_CONFIG, 0x0000);                 // ADCRANGE = 0, see above
    ina_write(REG_ADCCFG, 0xFB68);                 // continuous, 1052 us, avg 1
    Serial.println(F("\ncyc-delta   pin        edge     (deltas are from the previous event)"));
}

void loop() {
    static uint32_t last = 0, prev_cyc = 0;

    while (tail != head) {
        uint8_t t = tail & 63;
        uint32_t cyc = ring[t].cyc; uint8_t pin = ring[t].pin, lvl = ring[t].level;
        tail++;
        uint32_t d = cyc - prev_cyc; prev_cyc = cyc;
        /* The FIRST line after a quiet period is the one that matters - it names
         * the rail that failed. The deltas after it are the cascade. */
        Serial.printf("%10.3f us  %s  %s\n",
                      d / (F_CPU / 1e6f), NAME[pin], lvl ? "RISE" : "FALL");
    }

    if (millis() - last >= 500) {
        last = millis();
        int16_t vs, vb;
        if (ina_addr && ina_read(REG_VSHUNT, vs) && ina_read(REG_VBUS, vb)) {
            float i = (vs * VSHUNT_LSB) / RSHUNT;
            Serial.printf("[%6lus] VBUS %6.3f V   I %7.3f A   ENOUT %d 5G %d 3G %d\n",
                          millis()/1000, vb * VBUS_LSB, i,
                          digitalRead(PIN_ENOUT), digitalRead(PIN_5GOOD), digitalRead(PIN_3GOOD));
        }
    }
}
