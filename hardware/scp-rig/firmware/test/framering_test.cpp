// Host test for FrameRing. No Pico, no card:
//   g++ -std=c++17 -Wall -Wextra -Iinclude -o /tmp/t test/framering_test.cpp && /tmp/t
#include <cstdio>
#include "FrameRing.h"

static int bad = 0;
static void check(const char* what, long got, long want) {
    printf("  %-52s %8ld  %s\n", what, got, got == want ? "ok" : "FAIL");
    if (got != want) bad++;
}
static ScpFrame mk(uint64_t t) { ScpFrame f{}; f.tUs = t; f.len = 12; return f; }

int main() {
    // 2048 slots x 24 B = 48 KB, near the 64 KB the doc sizes for
    static FrameRing<2048> r;
    ScpFrame f{};

    check("empty ring pops nothing", r.pop(f), 0);
    check("size when empty", r.size(), 0);

    for (int i = 0; i < 100; i++) r.push(mk(i));
    check("size after 100 pushes", r.size(), 100);
    r.pop(f);
    check("first out is first in (FIFO)", (long)f.tUs, 0);
    check("size after one pop", r.size(), 99);

    // wrap the index many times over — the classic place rings break
    while (r.pop(f)) {}
    for (int cycle = 0; cycle < 50; cycle++) {
        for (int i = 0; i < 1000; i++) r.push(mk(cycle * 1000 + i));
        for (int i = 0; i < 1000; i++) {
            r.pop(f);
            if (f.tUs != (uint64_t)(cycle * 1000 + i)) { bad++; break; }
        }
    }
    check("50k frames through a 2048 ring, order intact", r.size(), 0);
    check("no drops while draining kept up", r.dropped(), 0);

    // fill exactly to capacity, then overflow
    r.clearStats();
    for (uint32_t i = 0; i < r.capacity(); i++) r.push(mk(i));
    check("full at exactly capacity", r.size(), r.capacity());
    check("high-water equals capacity", r.highWater(), r.capacity());
    check("push when full is refused", r.push(mk(9999)), 0);
    check("and counted", r.dropped(), 1);
    for (int i = 0; i < 9; i++) r.push(mk(9999));
    check("nine more drops counted", r.dropped(), 10);
    r.pop(f);
    check("oldest survived the overflow (newest dropped)", (long)f.tUs, 0);

    // THE SIZING CLAIM: 500 frames/s against a 250 ms card stall
    static FrameRing<2048> s;
    const int fps = 500, stall_ms = 250;
    const int arrivals = fps * stall_ms / 1000;
    for (int i = 0; i < arrivals; i++) s.push(mk(i));
    printf("\n  250 ms stall at %d frames/s = %d frames\n", fps, arrivals);
    check("  none dropped", s.dropped(), 0);
    check("  slots used", s.size(), arrivals);
    printf("  %-52s %7.1f%%\n", "  ring occupancy at the worst stall",
           100.0 * arrivals / s.capacity());

    printf("%s\n", bad ? "FAILURES" : "all pass");
    return bad ? 1 : 0;
}
