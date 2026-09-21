// Host test for PulseHistogram — can it find the clusters in a noisy stream?
//   g++ -std=c++17 -Wall -Wextra -Iinclude -o /tmp/t test/pulsehistogram_test.cpp && /tmp/t
#include <cstdio>
#include <cstdlib>
#include "PulseHistogram.h"

static int bad = 0;
static void near(const char* what, long got, long want, long tol) {
    const bool ok = labs(got - want) <= tol;
    printf("  %-44s %7ld  (want %ld +/-%ld)  %s\n", what, got, want, tol, ok ? "ok" : "FAIL");
    if (!ok) bad++;
}
static void check(const char* what, long got, long want) {
    printf("  %-44s %7ld  (want %ld)  %s\n", what, got, want, got == want ? "ok" : "FAIL");
    if (got != want) bad++;
}

int main() {
    // 250 ns bins out to 64 us — comfortably past anything on a 24 us bit
    static PulseHistogram<256, 250> h;
    h.clear();

    srand(1);
    auto jitter = [](int centre, int spread) { return centre + (rand() % (2*spread+1)) - spread; };

    // A synthetic stream with the shape a J1850 PWM bus actually has: two common
    // short intervals, a rarer long one (SOF/EOF-ish), and noise.
    for (int i = 0; i < 40000; i++) h.add(jitter(8000,  300));   // "tp1"
    for (int i = 0; i < 38000; i++) h.add(jitter(16000, 400));   // "tp2"
    for (int i = 0;  i < 2000; i++) h.add(jitter(32000, 600));   // rarer, long
    for (int i = 0;  i <  200; i++) h.add(jitter(45000, 5000));  // scattered noise

    printf("total samples %u, over range %u\n\n", h.total(), h.overRange());

    PulseHistogram<256,250>::Cluster c[8];
    const uint32_t n = h.clusters(c, 8);
    for (uint32_t i = 0; i < n; i++)
        printf("  cluster %u: %6.2f us  x%-7u  span %.2f-%.2f us\n", i,
               c[i].centroidNs/1000.0, c[i].count,
               c[i].loNs/1000.0, c[i].hiNs/1000.0);
    printf("\n");

    check("clusters found", n, 3);
    if (n >= 3) {
        near("cluster 0 centroid (ns)", c[0].centroidNs,  8000, 200);
        near("cluster 1 centroid (ns)", c[1].centroidNs, 16000, 200);
        near("cluster 2 centroid (ns)", c[2].centroidNs, 32000, 300);
        near("cluster 0 population",    c[0].count,      40000, 400);
        near("cluster 1 population",    c[1].count,      38000, 400);
    }
    // the 200 scattered noise samples must NOT become a cluster
    check("scattered noise rejected by the floor", n, 3);

    // over-range is counted, not silently dropped
    h.clear();
    h.add(1000); h.add(999999);
    check("over-range counted", h.overRange(), 1);
    check("in-range counted",   h.total(),     1);

    printf("%s\n", bad ? "FAILURES" : "all pass");
    return bad ? 1 : 0;
}
