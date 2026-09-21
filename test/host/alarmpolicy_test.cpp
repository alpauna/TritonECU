// Host test for AlarmPolicy: auto-silence and re-arm, no hardware.
//   g++ -std=c++17 -Wall -Wextra -Itest/host/stub -Iinclude -o /tmp/t test/host/alarmpolicy_test.cpp && /tmp/t
#include <cstdint>
#include <cstdio>
static uint32_t g_ms = 0;
uint32_t millis() { return g_ms; }
#include "AlarmPolicy.h"

static int bad = 0;
static void check(const char* what, bool got, bool want) {
    printf("  %-52s %-5s %s\n", what, got ? "sound" : "quiet", got == want ? "ok" : "FAIL");
    if (got != want) bad++;
}
int main() {
    const uint32_t FIVE_MIN = 300000;
    AlarmPolicy a; a.configure(FIVE_MIN);
    uint32_t t = 0;

    check("no fault", a.update(t, 0x00, 0), false);

    t = 1000;
    check("fault 0x01 appears", a.update(t, 0x01, 1), true);
    t += FIVE_MIN - 1000;
    check("4m59s later, still sounding", a.update(t, 0x01, 1), true);
    t += 2000;
    check("past 5 minutes, auto-silenced", a.update(t, 0x01, 1), false);
    printf("  %-52s %-5s %s\n", "silenced() while the fault persists",
           a.silenced() ? "yes" : "no", a.silenced() ? "ok" : "FAIL");
    if (!a.silenced()) bad++;

    // the same fault flapping must NOT re-arm — this is what makes real alarms
    // unsilenceable and gets them disconnected
    t += 1000; a.update(t, 0x03, 1);          // a second bit joins (re-arms)
    t += FIVE_MIN + 1000; a.update(t, 0x03, 1);
    check("after re-arm expires again", a.update(t, 0x03, 1), false);
    for (int i = 0; i < 5; i++) {
        t += 1000; a.update(t, 0x01, 1);      // 0x02 drops out
        t += 1000; a.update(t, 0x03, 1);      // and comes back
    }
    check("bit flapping in and out does not re-arm", a.update(t, 0x03, 1), false);

    // a genuinely new bit does
    t += 1000;
    check("a NEW fault bit re-arms", a.update(t, 0x07, 1), true);

    // escalation with the same bits re-arms
    t += FIVE_MIN + 1000;
    check("expired again", a.update(t, 0x07, 1), false);
    t += 1000;
    check("escalation to critical re-arms on the same bits", a.update(t, 0x07, 2), true);

    // clearing everything ends the episode; the next fault is fresh
    t += FIVE_MIN + 1000; a.update(t, 0x07, 2);
    check("expired once more", a.update(t, 0x07, 2), false);
    t += 1000;
    check("all faults clear", a.update(t, 0x00, 0), false);
    t += 1000;
    check("an old bit returning after a clear re-arms", a.update(t, 0x01, 1), true);

    printf("%s\n", bad ? "FAILURES" : "all pass");
    return bad ? 1 : 0;
}
