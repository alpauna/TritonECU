/* Find the DHT22. Throwaway diagnostic, not part of the controller.
 *
 * Tries the start-pulse handshake on every output-capable pin that was declared
 * free, and reports which one answers. Cheaper than asking which wire went
 * where, and it distinguishes "wrong pin" from "not powered" - a sensor with no
 * VCC answers on NO pin, which is a different finding from answering on one.
 */
#include <Arduino.h>
#include "DHT22.h"

static const uint8_t PINS[] = {2, 4, 5, 12, 13, 14, 15, 21, 22, 23, 32};

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("\n\n=== DHT22 pin scan ===");
    Serial.println("idle = level with the internal pull-up, before the start pulse.");
    Serial.println("A DHT22 that is powered holds the line HIGH and answers the pulse.\n");
}

void loop() {
    int found = 0;
    for (uint8_t i = 0; i < sizeof(PINS); i++) {
        uint8_t p = PINS[i];
        pinMode(p, INPUT_PULLUP);
        delay(5);
        int idle = digitalRead(p);

        DHT22 d(p);
        d.begin();
        float t = NAN, h = NAN;
        DHT22::Result r = d.read(t, h);

        if (r == DHT22::OK) {
            Serial.printf("  GPIO%-2u  idle %s   *** FOUND ***  %.1f C  %.1f %%RH\n",
                          p, idle ? "HIGH" : "LOW ", t, h);
            found++;
        } else {
            Serial.printf("  GPIO%-2u  idle %s   %s\n",
                          p, idle ? "HIGH" : "LOW ", DHT22::strerror(r));
        }
        delay(2100);        // the 2 s floor applies per sensor, so be generous
    }
    if (!found) {
        Serial.println("\n  Nothing answered on any pin.");
        Serial.println("  That points at POWER or WIRING, not at the pin choice:");
        Serial.println("   - VCC on 3V3 (not 5V, and not left off)");
        Serial.println("   - GND common with the ESP32");
        Serial.println("   - bare 4-pin part: 1=VCC 2=DATA 3=n/c 4=GND, and it");
        Serial.println("     needs a 10k from DATA to 3V3 - the internal pull-up");
        Serial.println("     is ~45k and is often too weak on a long lead");
    }
    Serial.println("\n--- sweep done, repeating ---\n");
}
