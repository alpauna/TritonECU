/*
 * VR test rig — step generator
 *
 * Drives a 17HS19 through a DM542 to spin a 36-1 trigger wheel at a commanded
 * angle and speed, so a decoder's output can be checked against a known truth.
 *
 * The point of this firmware is NOT constant-speed stepping. It is the crank
 * profile: a real engine surges and collapses across every compression stroke,
 * and that is the regime where sync acquisition fails. A rig that only spins
 * smoothly never tests it.
 *
 * Signal chain, and note it inverts twice:
 *   GPIO high -> 2N7002 on -> DM542 PUL- pulled low -> optocoupler conducts
 * so a HIGH here is an active pulse, and the pin idles low — which is also what
 * the driver board's 10k gate pulldown holds during reset.
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

/* One source, two toolchains. The Arduino-Pico core is built on the Pico SDK,
   so the hardware headers are identical either way — only the entry points and
   the console differ. */
#ifdef ARDUINO
  #include <Arduino.h>
  #define OUT(...) Serial.printf(__VA_ARGS__)
#else
  #include "pico/stdlib.h"
  #include "pico/multicore.h"
  #define OUT(...) printf(__VA_ARGS__)
#endif
#include "hardware/pio.h"
#include "hardware/clocks.h"
#include "stepgen.pio.h"

/* ---- wiring ------------------------------------------------------------- */
#define PIN_PUL         2       /* -> 2N7002 board IN, board LOAD -> DM542 PUL- */
#define PIN_DIR         3
#define PIN_ENA         4

/* The DM542's ENA opto DISABLES the driver when energised; leaving it open
   enables. Our FET energises it on a GPIO high, so LOW = running. */
#define ENA_ENERGISED_DISABLES 1

/* ---- mechanical --------------------------------------------------------- */
#define PULSES_PER_REV  3200    /* DM542 SW5-8. 16x microstep on a 1.8 deg motor */
#define WHEEL_TEETH     36      /* 36-1: the gap is one missing tooth */

/* ---- limits ------------------------------------------------------------- */
/* 1200 rpm is a safety cap, not a capability one: 0.7 kg of steel at 1200 rpm
   carries 15 J. At 6000 it would carry 375 J, which is a different object. */
#define MAX_RPM         1200.0f
#define MIN_RPM         0.5f

/* Acceleration limit. The DOWN ramp is the one that matters and it is not a
   nicety: a decelerating stepper pushes energy back, a switching supply cannot
   sink it, and no practical bulk capacitor absorbs a hard stop — 2200 uF still
   reaches 64 V against the DM542's 50 V maximum. At 3 s only ~5 W comes back,
   which the driver's own losses absorb. See BOM.md. */
#define ACCEL_RPM_S     400.0f  /* 0 -> 1200 in 3 s */
#define DECEL_RPM_S     400.0f  /* 1200 -> 0 in 3 s. DO NOT RAISE. */

/* ---- PIO cycle accounting ----------------------------------------------- */
/* period = 2x + 5 cycles (see stepgen.pio), so x = (period - 5) / 2. */
#define X_FROM_PERIOD(p) (((p) - 5u) / 2u)
/* The DM542's input ceiling is ~200 kHz, but the binding constraint is its
   2.5 us minimum pulse width, and at 50 %% duty that is the tighter of the two.
   high = x + 2 = (period - 1) / 2, so period must be >= 627 cycles at 8 ns.
   630 gives 2.512 us; 625 would give 2.496 us — four nanoseconds short. */
#define MIN_PERIOD_CYC  630u

static PIO  pio = pio0;
static uint sm  = 0;
static uint32_t sys_hz;

/* ---- profile ------------------------------------------------------------ */
typedef enum { P_STOP, P_CONST, P_CRANK, P_SWEEP } profile_t;

static volatile profile_t profile      = P_STOP;
static volatile float     target_rpm   = 0.0f;
static volatile float     crank_irreg  = 0.30f;   /* +-30 % is typical cranking */
static volatile float     sweep_from   = 0.0f;
static volatile float     sweep_to     = 0.0f;
static volatile float     sweep_secs   = 0.0f;
static volatile bool      sweep_new    = false;
static volatile bool      zero_request = false;

/* Reported state, written by core 1 and read by core 0. 32-bit loads and
   stores are atomic on this core, so no lock is needed for these. */
static volatile int32_t   step_count   = 0;
static volatile float     actual_rpm   = 0.0f;

/* Compression modulation, precomputed so the hot loop never calls cosf().
   A V8 fires eight times per 720 deg, so speed dips four times per crank
   revolution — and the dips land at TDC, which is where the wheel's gap is. */
#define MOD_N           256
#define STEPS_PER_DIP   (PULSES_PER_REV / 4)
static float mod_tab[MOD_N];

static void build_mod_table(void) {
    for (int i = 0; i < MOD_N; i++) {
        /* -cos: minimum speed at the start of each 90 deg segment, i.e. at TDC */
        /* Literal rather than M_PI: that macro is not guaranteed by C11
           <math.h> without _USE_MATH_DEFINES, and this has to build wherever. */
        mod_tab[i] = -cosf(6.283185307179586f * (float)i / (float)MOD_N);
    }
}

static inline float crank_modulation(int32_t step) {
    int32_t s = step % STEPS_PER_DIP;
    if (s < 0) s += STEPS_PER_DIP;
    int idx = (int)(((int64_t)s * MOD_N) / STEPS_PER_DIP);
    return mod_tab[idx & (MOD_N - 1)];
}

static inline uint32_t rpm_to_x(float rpm) {
    if (rpm < MIN_RPM) rpm = MIN_RPM;
    float steps_per_s = rpm * (float)PULSES_PER_REV / 60.0f;
    uint32_t period = (uint32_t)((float)sys_hz / steps_per_s + 0.5f);
    if (period < MIN_PERIOD_CYC) period = MIN_PERIOD_CYC;
    return X_FROM_PERIOD(period);
}

static void set_enable(bool on) {
#if ENA_ENERGISED_DISABLES
    gpio_put(PIN_ENA, on ? 0 : 1);
#else
    gpio_put(PIN_ENA, on ? 1 : 0);
#endif
}

/* ---- core 1: the pacer -------------------------------------------------- */
/* State the pacer carries between steps. File scope rather than local, because
   under Arduino this is re-entered as loop1() rather than being one long loop. */
static float base_rpm   = 0.0f;
static float sweep_rate = 0.0f;
static bool  approach   = false;   /* sweep still ramping to its start point */
static volatile bool pacer_ready = false;

static void pacer_step(void) {
    {
        if (zero_request) { step_count = 0; zero_request = false; }

        profile_t p = profile;
        float want = (p == P_STOP) ? 0.0f : target_rpm;
        if (want > MAX_RPM) want = MAX_RPM;

        /* Idle: nothing commanded, nothing turning. */
        if (want < MIN_RPM && base_rpm < MIN_RPM && p != P_SWEEP) {
            base_rpm = 0.0f;
            actual_rpm = 0.0f;
            sweep_rate = 0.0f;
            set_enable(false);
            sleep_ms(2);
            return;
        }
        set_enable(true);

        /* Starting from rest, step in at the floor. Ramping up from exactly
           zero cannot work: the first increment is smaller than MIN_RPM and
           would be clamped back to zero on every pass, forever. At 0.5 rpm the
           wheel is stationary for any practical purpose. */
        if (base_rpm < MIN_RPM) base_rpm = MIN_RPM;

        float dt = 60.0f / (base_rpm * (float)PULSES_PER_REV);

        if (p == P_SWEEP) {
            if (sweep_new) { sweep_rate = 0.0f; approach = true; sweep_new = false; }
            if (approach) {
                /* Reach the start speed under the normal limits first, so
                   "sweep 200 1200 60" means what it says regardless of what
                   the rig happened to be doing. */
                float w = sweep_from;
                if (w > base_rpm) { base_rpm += ACCEL_RPM_S * dt; if (base_rpm > w) base_rpm = w; }
                else              { base_rpm -= DECEL_RPM_S * dt; if (base_rpm < w) base_rpm = w; }
                if (fabsf(base_rpm - w) < 0.5f) { base_rpm = w; approach = false; }
            } else {
                if (sweep_rate == 0.0f && sweep_secs > 0.0f)
                    sweep_rate = (sweep_to - base_rpm) / sweep_secs;
                base_rpm += sweep_rate * dt;
                if ((sweep_rate > 0.0f && base_rpm >= sweep_to) ||
                    (sweep_rate < 0.0f && base_rpm <= sweep_to)) {
                    base_rpm = sweep_to;
                    sweep_rate = 0.0f;
                    target_rpm = sweep_to;
                    profile = (sweep_to < MIN_RPM) ? P_STOP : P_CONST;
                }
            }
        } else {
            sweep_rate = 0.0f;
            approach = false;
            if (want > base_rpm) {
                base_rpm += ACCEL_RPM_S * dt;
                if (base_rpm > want) base_rpm = want;
            } else if (want < base_rpm) {
                base_rpm -= DECEL_RPM_S * dt;
                if (base_rpm < want) base_rpm = want;
            }
        }

        float inst = base_rpm;
        if (p == P_CRANK)
            inst = base_rpm * (1.0f + crank_irreg * crank_modulation(step_count));
        if (inst < MIN_RPM) inst = MIN_RPM;
        if (inst > MAX_RPM) inst = MAX_RPM;

        actual_rpm = inst;
        pio_sm_put_blocking(pio, sm, rpm_to_x(inst));
        step_count++;
    }
}

/* ---- core 0: commands --------------------------------------------------- */
static void print_status(void) {
    int32_t s = step_count;
    int32_t in_rev = s % PULSES_PER_REV;
    if (in_rev < 0) in_rev += PULSES_PER_REV;
    float deg = (float)in_rev * 360.0f / (float)PULSES_PER_REV;
    static const char *names[] = {"stop", "const", "crank", "sweep"};
    OUT("profile=%s rpm=%.1f steps=%ld rev=%ld angle=%.4f deg\n",
           names[profile], (double)actual_rpm, (long)s,
           (long)(s / PULSES_PER_REV), (double)deg);
}

static void handle(char *line) {
    char *cmd = strtok(line, " \t");
    if (!cmd) return;

    if (!strcmp(cmd, "stop")) {
        profile = P_STOP; target_rpm = 0.0f;
        OUT("ok stop (ramping down over %.1f s)\n",
               (double)(actual_rpm / DECEL_RPM_S));
    } else if (!strcmp(cmd, "rpm")) {
        char *a = strtok(NULL, " \t");
        if (!a) { OUT("err: rpm <value>\n"); return; }
        float v = strtof(a, NULL);
        if (v < 0 || v > MAX_RPM) { OUT("err: 0..%.0f\n", (double)MAX_RPM); return; }
        target_rpm = v; profile = (v > 0) ? P_CONST : P_STOP;
        OUT("ok rpm %.1f\n", (double)v);
    } else if (!strcmp(cmd, "crank")) {
        char *a = strtok(NULL, " \t"), *b = strtok(NULL, " \t");
        float v = a ? strtof(a, NULL) : 200.0f;
        float pct = b ? strtof(b, NULL) : 30.0f;
        if (v <= 0 || v > MAX_RPM) { OUT("err: 0..%.0f\n", (double)MAX_RPM); return; }
        if (pct < 0 || pct > 90) { OUT("err: irregularity 0..90 %%\n"); return; }
        crank_irreg = pct / 100.0f; target_rpm = v; profile = P_CRANK;
        OUT("ok crank %.1f rpm +-%.0f%%, 4 dips/rev at TDC\n",
               (double)v, (double)pct);
    } else if (!strcmp(cmd, "sweep")) {
        char *a = strtok(NULL, " \t"), *b = strtok(NULL, " \t"), *c = strtok(NULL, " \t");
        if (!a || !b || !c) { OUT("err: sweep <from> <to> <secs>\n"); return; }
        float f = strtof(a, NULL), t = strtof(b, NULL), s = strtof(c, NULL);
        if (f < 0 || t < 0 || f > MAX_RPM || t > MAX_RPM || s <= 0) {
            OUT("err: 0..%.0f rpm, secs > 0\n", (double)MAX_RPM); return; }
        /* A sweep down must still respect the deceleration limit. */
        if (t < f && (f - t) / s > DECEL_RPM_S) {
            OUT("err: %.0f rpm in %.1f s exceeds the %.0f rpm/s decel limit; "
                   "needs >= %.1f s\n", (double)(f - t), (double)s,
                   (double)DECEL_RPM_S, (double)((f - t) / DECEL_RPM_S));
            return;
        }
        sweep_from = f; sweep_to = t; sweep_secs = s;
        target_rpm = f; sweep_new = true; profile = P_SWEEP;
        OUT("ok sweep %.0f -> %.0f over %.1f s\n", (double)f, (double)t, (double)s);
    } else if (!strcmp(cmd, "zero")) {
        zero_request = true;
        OUT("ok zero — call this with the hub's index flute at the sensor\n");
    } else if (!strcmp(cmd, "status")) {
        print_status();
    } else if (!strcmp(cmd, "help")) {
        OUT("rpm <v> | crank <rpm> [irreg%%] | sweep <from> <to> <secs>\n"
               "stop | zero | status\n"
               "%d pulses/rev, %.4f deg/step, max %.0f rpm\n",
               PULSES_PER_REV, 360.0 / PULSES_PER_REV, (double)MAX_RPM);
    } else {
        OUT("err: unknown '%s' — try help\n", cmd);
    }
}

/* ---- shared bring-up ----------------------------------------------------- */
static void rig_init(void) {
    gpio_init(PIN_DIR); gpio_set_dir(PIN_DIR, GPIO_OUT); gpio_put(PIN_DIR, 0);
    gpio_init(PIN_ENA); gpio_set_dir(PIN_ENA, GPIO_OUT);
    set_enable(false);
    /* The DM542 wants DIR settled before the first pulse, and a moment after
       enabling before it will step. */
    sleep_ms(200);

    sys_hz = clock_get_hz(clk_sys);
    build_mod_table();

    uint offset = pio_add_program(pio, &stepgen_program);
    stepgen_program_init(pio, sm, offset, PIN_PUL);
    pacer_ready = true;
}

static void banner(void) {
    OUT("\nVR rig step generator. %d pulses/rev, %.4f deg/step. 'help' for commands.\n",
        PULSES_PER_REV, 360.0 / PULSES_PER_REV);
}

static char linebuf[96];
static int  linelen = 0;

static void feed(int ch) {
    if (ch == '\r' || ch == '\n') {
        if (linelen) { linebuf[linelen] = 0; handle(linebuf); linelen = 0; }
    } else if (linelen < (int)sizeof(linebuf) - 1) {
        linebuf[linelen++] = (char)ch;
    }
}

#ifdef ARDUINO
/* ---- Arduino / PlatformIO ------------------------------------------------ */
void setup(void) {
    Serial.begin(115200);
    rig_init();
    banner();
}

void loop(void) {
    while (Serial.available()) feed(Serial.read());
    delay(1);
}

void setup1(void) {
    /* Core 1 may start before core 0 has configured the PIO. */
    while (!pacer_ready) tight_loop_contents();
}

void loop1(void) { pacer_step(); }

#else
/* ---- Pico SDK / CMake ---------------------------------------------------- */
static void core1_main(void) {
    while (!pacer_ready) tight_loop_contents();
    while (true) pacer_step();
}

int main(void) {
    stdio_init_all();
    rig_init();
    multicore_launch_core1(core1_main);
    banner();

    while (true) {
        int ch = getchar_timeout_us(100000);
        if (ch != PICO_ERROR_TIMEOUT) feed(ch);
    }
}
#endif
