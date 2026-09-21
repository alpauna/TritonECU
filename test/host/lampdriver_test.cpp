// Host check of BURST timing: stub Arduino.h, drive the real header.
#include <cstdint>
#include <cstdio>
static uint32_t g_ms = 0;
uint32_t millis() { return g_ms; }
#include "LampDriver.h"

static int check(const char* what, long got, long want) {
    printf("  %-42s got %5ld  want %5ld  %s\n", what, got, want, got == want ? "ok" : "FAIL");
    return got == want ? 0 : 1;
}
int main() {
    int bad = 0;
    LampDriver crit;
    crit.setBurst(150, 150, 3, 10000);          // 3 beeps every 10 s
    int edges = 0; long on = 0; bool prev = false;
    for (uint32_t t = 0; t < 20000; t += 10) {
        bool s = crit.state(t);
        if (s && !prev) edges++;
        if (s) on += 10;
        prev = s;
    }
    puts("CRITICAL  3 x 150 ms beeps, repeating every 10 s, over 20 s:");
    bad += check("beeps", edges, 6);
    bad += check("total sounding time (ms)", on, 900);
    bad += check("quiet at t=1000ms (0=silent)", crit.state(1000), 0);
    bad += check("sounding at t=0", crit.state(0), 1);

    LampDriver full;
    full.setBurst(150, 150, 2, 60000);          // 2 beeps every 60 s
    edges = 0; on = 0; prev = false;
    for (uint32_t t = 0; t < 120000; t += 10) {
        bool s = full.state(t);
        if (s && !prev) edges++;
        if (s) on += 10;
        prev = s;
    }
    puts("FULL      2 x 150 ms beeps, repeating every 60 s, over 120 s:");
    bad += check("beeps", edges, 4);
    bad += check("duty cycle (parts per million)", on * 1000000 / 120000, 5000);

    // re-arming with identical parameters must not restart the phase
    LampDriver p; p.setBurst(150,150,3,10000);
    g_ms = 5000; p.setBurst(150,150,3,10000);
    bad += check("re-arm identical does not retrigger", p.state(5000), 0);
    printf("%s\n", bad ? "FAILURES" : "all pass");
    return bad ? 1 : 0;
}
