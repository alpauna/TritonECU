// SCP capture rig — Phase 0, stage 1.
//
// Knows nothing about J1850 PWM. It times edges and reports what it saw, so the
// protocol constants come from the bus rather than from someone's memory of a
// datasheet. See ../README.md.
//
// LOOPBACK: GP3 emits a hardware-PWM square wave of known width. Jumper it to
// GP2 and the histogram must report back what was generated. That is the only
// evidence the capture chain is correct.

#include <Arduino.h>
#include <hardware/pio.h>
#include <hardware/pwm.h>
#include <hardware/clocks.h>
#include "edge_capture.pio.h"
#include "PulseHistogram.h"

static const uint PIN_RX   = 2;      // comparator output (or the loopback jumper)
static const uint PIN_GEN  = 3;      // loopback generator — INPUT on a vehicle
static const uint LED_OUT  = LED_BUILTIN;

// 16 MHz PIO clock, 2-cycle loop -> 125 ns per count.
static const float    PIO_HZ  = 16'000'000.0f;
static const uint32_t NS_PER_COUNT = 125;

// The counter cannot time the cycles the PIO spends detecting an edge and
// pushing the word, so every interval reads SHORT by its service path.
//
// The two paths are not the same length. `jmp pin` only branches when the pin
// is HIGH, so the falling-edge path needs one extra instruction to invert the
// sense (`jmp pin, still_high` / `jmp fell`) where the rising path branches
// straight to `rose`. That single cycle is the whole asymmetry:
//
//   interval ended HIGH (pushed at `fell`, level bit 0) -> 4 cycles lost
//   interval ended LOW  (pushed at `rose`, level bit 1) -> 5 cycles lost
//
// Both numbers were measured, not assumed: an uncorrected loopback of a known
// 8 us / 16 us wave read 7.749 and 15.687, which is 4 and 5 cycles at 16 MHz to
// better than a nanosecond. Corrected, the same loopback must read 8.000 and
// 16.000 -- that is the check that keeps these honest.
// Residual after correction is +/- half a bin (62.5 ns), which is resolution,
// not error. The loopback reads 7.999 and 15.937: the 8 us count dithers 61/62
// because the generator's edges are asynchronous to the PIO clock, and that
// dither averages the quantisation out. The 16 us count locks at 125, so it
// reports its bin CENTRE -- and true 16000 ns sits exactly on a bin boundary,
// reachable only as 15.937 or 16.062. Do NOT "fix" it by raising CAL_CYCLES_LOW
// to 6; that just moves the same 62.5 ns to the other side.
static const uint32_t CAL_CYCLES_HIGH = 4;
static const uint32_t CAL_CYCLES_LOW  = 5;
static const uint32_t CAL_HIGH_NS = (uint32_t)(CAL_CYCLES_HIGH * 1e9f / PIO_HZ + 0.5f);
static const uint32_t CAL_LOW_NS  = (uint32_t)(CAL_CYCLES_LOW  * 1e9f / PIO_HZ + 0.5f);

// Generated loopback widths. 8 us high / 16 us low is the shape a J1850 PWM bus
// has, which makes a wrong answer obvious rather than plausible.
static const uint32_t GEN_HIGH_US = 8;
static const uint32_t GEN_LOW_US  = 16;
#define LOOPBACK 1

static PIO      pio = pio0;
static uint     sm;
static PulseHistogram<512, 125> hist;   // 125 ns bins out to 64 us

static uint32_t edges = 0, dropped = 0;

static void gen_start() {
#if LOOPBACK
    // Free-running PWM: accurate widths with no CPU involvement, so draining the
    // FIFO cannot distort the signal being measured. Bit-banging would put the
    // drain time straight into the pulse widths.
    gpio_set_function(PIN_GEN, GPIO_FUNC_PWM);
    const uint slice = pwm_gpio_to_slice_num(PIN_GEN);
    const uint32_t sys = clock_get_hz(clk_sys);
    const uint32_t wrap  = (uint32_t)((uint64_t)sys * (GEN_HIGH_US + GEN_LOW_US) / 1'000'000u);
    const uint32_t level = (uint32_t)((uint64_t)sys * GEN_HIGH_US / 1'000'000u);
    pwm_set_wrap(slice, wrap - 1);
    pwm_set_chan_level(slice, pwm_gpio_to_channel(PIN_GEN), level);
    pwm_set_enabled(slice, true);
#else
    pinMode(PIN_GEN, INPUT);        // never drive a line that reaches a vehicle
#endif
}

void setup() {
    Serial.begin(115200);
    pinMode(LED_OUT, OUTPUT);

    const uint offset = pio_add_program(pio, &edge_capture_program);
    sm = pio_claim_unused_sm(pio, true);
    edge_capture_init(pio, sm, offset, PIN_RX, PIO_HZ);

    gen_start();
}

static void drain() {
    while (!pio_sm_is_rx_fifo_empty(pio, sm)) {
        const uint32_t w = pio_sm_get(pio, sm);
        // LSB is the level AFTER the edge, so it says which interval just
        // ended: 0 means the line had been high, 1 means it had been low.
        // Each gets its own correction because the service paths differ.
        hist.add((w >> 1) * NS_PER_COUNT + ((w & 1u) ? CAL_LOW_NS : CAL_HIGH_NS));
        edges++;
    }
    // A noblock push into a full FIFO sets RXSTALL. Count it — a capture that
    // silently dropped edges is worse than no capture.
    if (pio->fdebug & (1u << (PIO_FDEBUG_RXSTALL_LSB + sm))) {
        pio->fdebug = 1u << (PIO_FDEBUG_RXSTALL_LSB + sm);
        dropped++;
    }
}

void loop() {
    static uint32_t lastReport = 0;
    drain();

    if (millis() - lastReport >= 5000) {
        lastReport = millis();
        digitalWrite(LED_OUT, !digitalRead(LED_OUT));

        PulseHistogram<512,125>::Cluster c[8];
        const uint32_t n = hist.clusters(c, 8);

        Serial.printf("\n--- %lu edges, %lu overruns, %lu over-range ---\n",
                      (unsigned long)edges, (unsigned long)dropped,
                      (unsigned long)hist.overRange());
        if (!n) { Serial.println("  no clusters — is anything connected to GP2?"); return; }
        for (uint32_t i = 0; i < n; i++)
            Serial.printf("  %u.%03u us  x%-8lu  span %u.%03u-%u.%03u us\n",
                          c[i].centroidNs / 1000, c[i].centroidNs % 1000,
                          (unsigned long)c[i].count,
                          c[i].loNs / 1000, c[i].loNs % 1000,
                          c[i].hiNs / 1000, c[i].hiNs % 1000);
#if LOOPBACK
        Serial.printf("  LOOPBACK expects 8.000 and 16.000 us\n");
#endif
    }
}
