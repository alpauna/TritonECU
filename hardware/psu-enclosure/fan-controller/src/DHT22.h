#pragma once
#include <Arduino.h>

/* A DHT22 read, without a library.
 *
 * The protocol is forty bits of pulse-width encoding on one open-drain wire,
 * which is little enough to own outright rather than take a dependency for. It
 * also means the timing is visible here, where it can be reasoned about, rather
 * than inside something fetched at build time.
 *
 * Wire format, all times from the datasheet:
 *   host  pulls low >= 1 ms, then releases
 *   dht   answers ~80 us low, ~80 us high
 *   then 40 bits, each ~50 us low followed by a high whose LENGTH is the bit:
 *         ~26-28 us high = 0        ~70 us high = 1
 *   byte order: humidity hi, humidity lo, temp hi, temp lo, checksum
 *
 * Temperature is signed via the TOP BIT of the high byte, not two's complement.
 * That catches people out and costs a below-zero reading its sign.
 */
class DHT22 {
public:
    enum Result { OK, ERR_NO_RESPONSE, ERR_TIMEOUT, ERR_CHECKSUM };

    explicit DHT22(uint8_t pin) : _pin(pin) {}

    void begin() {
        pinMode(_pin, INPUT_PULLUP);
        _lastRead = 0;
    }

    Result read(float& tempC, float& humidity) {
        // The datasheet asks 2 s between reads. Closer than that and the sensor
        // returns its previous conversion, so a fast poll is not just rude, it
        // is stale data wearing fresh data's clothes.
        if (_lastRead && (millis() - _lastRead) < 2000) return ERR_TIMEOUT;
        _lastRead = millis();

        uint8_t bytes[5] = {0,0,0,0,0};

        pinMode(_pin, OUTPUT);
        digitalWrite(_pin, LOW);
        delay(2);                       // >= 1 ms start pulse
        pinMode(_pin, INPUT_PULLUP);

        noInterrupts();                 // the bit windows are ~25 us apart
        Result r = readFrame(bytes);
        interrupts();
        if (r != OK) return r;

        uint8_t sum = bytes[0] + bytes[1] + bytes[2] + bytes[3];
        if (sum != bytes[4]) return ERR_CHECKSUM;

        humidity = ((bytes[0] << 8) | bytes[1]) * 0.1f;
        uint16_t raw = ((bytes[2] & 0x7F) << 8) | bytes[3];
        tempC = raw * 0.1f;
        if (bytes[2] & 0x80) tempC = -tempC;     // sign bit, NOT two's complement
        return OK;
    }

    static const char* strerror(Result r) {
        switch (r) {
            case OK:              return "ok";
            case ERR_NO_RESPONSE: return "no response - check wiring and the 10k pull-up";
            case ERR_TIMEOUT:     return "timeout mid-frame";
            case ERR_CHECKSUM:    return "checksum - line is noisy or too long";
        }
        return "?";
    }

private:
    uint8_t  _pin;
    uint32_t _lastRead = 0;

    // Returns how long the pin stayed at `level`, or 0 on timeout.
    inline uint32_t waitWhile(int level, uint32_t limitUs) {
        uint32_t t0 = micros();
        while (digitalRead(_pin) == level)
            if (micros() - t0 > limitUs) return 0;
        return micros() - t0;
    }

    Result readFrame(uint8_t* bytes) {
        if (!waitWhile(HIGH, 100)) return ERR_NO_RESPONSE;   // sensor pulls low
        if (!waitWhile(LOW,  150)) return ERR_NO_RESPONSE;   // ~80 us low
        if (!waitWhile(HIGH, 150)) return ERR_NO_RESPONSE;   // ~80 us high

        for (int i = 0; i < 40; i++) {
            if (!waitWhile(LOW, 100)) return ERR_TIMEOUT;    // ~50 us low
            uint32_t high = waitWhile(HIGH, 150);
            if (!high) return ERR_TIMEOUT;
            // 26-28 us means 0, ~70 us means 1. 50 splits them with margin
            // either side, which is what makes this robust to a slow read.
            bytes[i / 8] <<= 1;
            if (high > 50) bytes[i / 8] |= 1;
        }
        return OK;
    }
};
