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

/* Print to BOTH ports, as ../ecu/src/stm32/Console.cpp does and for the same
 * reason: `Serial` is USART3 on PD8/PD9, which belongs to the ON-BOARD ST-Link.
 * With an external STLINK-V3 driving SWD and the Nucleo's own USB unplugged,
 * that port enumerates nowhere and output vanishes silently. USART2 on PD5/PD6
 * goes to the V3's VCP (or any USB-serial adapter). Mirroring costs nothing and
 * removes a failure that looks exactly like a crashed program. */
static HardwareSerial ExtSerial(PD6, PD5);   // RX, TX
#define OUT(...)  do { Serial.printf(__VA_ARGS__); ExtSerial.printf(__VA_ARGS__); } while (0)

static const uint8_t PIN_ENOUT = D7;   // 3.3_ENOUT - LTC4364 enable, level shifted
static const uint8_t PIN_5GOOD = D4;
static const uint8_t PIN_3GOOD = D2;

/* INA238 sits on the same 10 mOhm shunt the LTC4364 uses for current limit, so
 * it reads the current that trips the protector - just far too slowly to see
 * the trip itself. Useful for the trend as VIN is swept, not for the event. */
static const uint8_t REG_CONFIG = 0x00, REG_ADCCFG = 0x01;
static const uint8_t REG_VSHUNT = 0x04, REG_VBUS = 0x05;

/* ADCRANGE = 0: +/-163.84 mV full scale, 5 uV/LSB -> 500 uA/LSB on 10 mOhm,
 * +/-16.384 A. ADCRANGE 1 would resolve finer but clips at 4.1 A, below the
 * 5 A limit we are trying to watch approach. */
/* Scaled to INTEGERS, not floats. newlib-nano's printf drops %f unless float
 * support is linked - and worse, a dropped %f consumes no argument, so every
 * following %s reads a garbage pointer. The first run printed "VBUS  V  I  A"
 * and "  4  aw F" for exactly that reason: one missing linker flag corrupting
 * lines that had nothing to do with floats.
 *
 *   VBUS  3.125 mV/LSB      -> mV = raw * 25 / 8
 *   VSHUNT 5 uV/LSB on 10 mOhm -> 500 uA/LSB, so mA = raw / 2
 *   DWT at 216 MHz          -> 216 cycles per microsecond */
static const uint32_t CYC_PER_US = 216;

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
    ExtSerial.begin(115200);
    delay(300);
    OUT("\n\n=== POWER board diagnostic ===\n");

    // DWT cycle counter - the whole reason this runs on an M7
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0;
    DWT->CTRL  |= DWT_CTRL_CYCCNTENA_Msk;
    OUT("DWT at %lu Hz -> %lu cycles per us\n", (unsigned long)F_CPU, (unsigned long)CYC_PER_US);

    pinMode(PIN_ENOUT, INPUT);
    pinMode(PIN_5GOOD, INPUT);
    pinMode(PIN_3GOOD, INPUT);
    attachInterrupt(digitalPinToInterrupt(PIN_ENOUT), isr_enout, CHANGE);
    attachInterrupt(digitalPinToInterrupt(PIN_5GOOD), isr_5good, CHANGE);
    attachInterrupt(digitalPinToInterrupt(PIN_3GOOD), isr_3good, CHANGE);
    OUT("initial: ENOUT %d  5_GOOD %d  3.3_GOOD %d\n",
        digitalRead(PIN_ENOUT), digitalRead(PIN_5GOOD), digitalRead(PIN_3GOOD));

    Wire.begin();
    Wire.setClock(400000);
    OUT("I2C scan:");
    for (uint8_t a = 0x40; a <= 0x4F; a++) {       // INA238 strap range
        Wire.beginTransmission(a);
        if (Wire.endTransmission() == 0) { OUT(" 0x%02X", a); if (!ina_addr) ina_addr = a; }
    }
    if (!ina_addr) { OUT("  none found - check SDA/SCL and 3V3\n"); return; }
    OUT("  -> using 0x%02X\n", ina_addr);

    ina_write(REG_CONFIG, 0x8000); delay(5);       // reset
    ina_write(REG_CONFIG, 0x0000);                 // ADCRANGE = 0, see above
    ina_write(REG_ADCCFG, 0xFB68);                 // continuous, 1052 us, avg 1
    OUT("\ncyc-delta   pin        edge     (deltas are from the previous event)\n");
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
        OUT("%8lu.%03lu us  %s  %s\n",
            (unsigned long)(d / CYC_PER_US),
            (unsigned long)((d % CYC_PER_US) * 1000 / CYC_PER_US),
            NAME[pin], lvl ? "RISE" : "FALL");
    }

    if (millis() - last >= 500) {
        last = millis();
        int16_t vs, vb;
        if (ina_addr && ina_read(REG_VSHUNT, vs) && ina_read(REG_VBUS, vb)) {
            int32_t mv = (int32_t)vb * 25 / 8;
            int32_t ma = (int32_t)vs / 2;
            OUT("[%6lus] VBUS %ld.%03ld V   I %ld mA   ENOUT %d 5G %d 3G %d\n",
                millis()/1000, mv/1000, (mv<0?-mv:mv)%1000, (long)ma,
                digitalRead(PIN_ENOUT), digitalRead(PIN_5GOOD), digitalRead(PIN_3GOOD));
        }
    }
}
