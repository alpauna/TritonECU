// Host-side test for the latching relay firmware. No hardware, no toolchain
// beyond g++: stub the Arduino API, include the firmware, drive it, and check
// that the right coil gets the right pulse.
//
//   g++ -std=c++17 -Wall -Wextra -o /tmp/sim test/sim.cpp && /tmp/sim
//
// Flip DUAL_COIL in src/main.cpp and re-run to check the H-bridge build.

#define HOST_SIM 1
#include <cstdint>
#include <cstdio>
#include <string>
#define HIGH 1
#define LOW 0
#define OUTPUT 1
#define INPUT 0
#define INPUT_PULLUP 2
#define PIN_PA1 1
#define PIN_PA2 2
#define PIN_PA3 3
#define PIN_PA6 6
#define PIN_PA7 7
static uint32_t g_ms = 0;
static int pinv[8] = {1,1,1,1,1,1,0,0};    // inputs idle HIGH (pull-ups)
static int outv[8] = {0};
static std::string log_;
void pinMode(int, int) {}
int  digitalRead(int p) { return pinv[p]; }
void digitalWrite(int p, int v) {
    if (outv[p] != v) { outv[p] = v;
        char b[48]; snprintf(b, sizeof b, "%s%s@%ums ",
                             (p == PIN_PA6 ? "A" : "C"), (v ? "hi" : "lo"), g_ms);
        log_ += b; }
}
void delay(uint32_t ms) { g_ms += ms; }
uint32_t millis() { return g_ms; }

#include "../src/main.cpp"

static int fails = 0;
static void tick(uint32_t ms) { for (uint32_t i = 0; i < ms; i++) { g_ms++; loop(); } }
static void press(uint32_t hold) { pinv[PIN_PA1]=LOW; tick(hold); pinv[PIN_PA1]=HIGH; tick(300); }
static void check(const char* what, bool want_pulse, bool want_on) {
    bool got = !log_.empty();
    bool ok  = (got == want_pulse) && (relayOn == want_on);
    printf("%-16s %-24s relayOn=%d  %s\n", what, log_.c_str(), relayOn, ok ? "ok" : "FAIL");
    if (!ok) fails++;
    log_.clear();
}
int main() {
    setup();                 check("boot",          true,  false);  // fail-safe off
    press(60);               check("short press",   true,  true);   // SET
    press(60);               check("short press",   true,  false);  // RESET
    press(60);               check("short press",   true,  true);
    press(1500);             check("long press on", true,  false);  // forced off
    press(1500);             check("long press off",false, false);  // already off
    for (int i = 0; i < 4; i++) { pinv[PIN_PA1]=LOW; tick(3); pinv[PIN_PA1]=HIGH; tick(3); }
    press(60);               check("bounce+press",  true,  true);   // exactly one
    pinv[PIN_PA3]=LOW; tick(60); pinv[PIN_PA3]=HIGH; tick(300);
                             check("ECU line",      true,  false);  // toggles too
    printf("%s\n", fails ? "FAILURES" : "all pass");
    return fails ? 1 : 0;
}
