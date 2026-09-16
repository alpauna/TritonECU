/*
 * stepgen.pio.h — hand-assembled from stepgen.pio.
 *
 * The Pico SDK's CMake build generates this itself via pico_generate_pio_header()
 * and will overwrite nothing — it writes into the build tree. This copy exists
 * for PlatformIO, which does not run pioasm.
 *
 * Encoding per RP2040 datasheet 3.4, with `.side_set 1` (not optional), so bit
 * 12 carries the side-set value and bits 11:8 the delay:
 *
 *   addr  instruction            word     [15:13] [12] [11:8]  [7:0]
 *   0     pull block   side 0    0x80A0   100     0    0000    10100000
 *   1     mov x, osr   side 1    0xB027   101     1    0000    00100111
 *   2     jmp x--, 2   side 1    0x1042   000     1    0000    01000010
 *   3     mov x, osr   side 0    0xA027   101     0    0000    00100111
 *   4     jmp x--, 4   side 0    0x0044   000     0    0000    01000100
 *
 * Jump targets are stored relative to program start; pio_add_program() adds the
 * load offset to every JMP as it writes them, so this needs no fixing up here.
 *
 * To regenerate rather than trust the above:
 *     pioasm stepgen.pio stepgen.pio.h
 */
#pragma once
#include "hardware/pio.h"

#define stepgen_wrap_target 0
#define stepgen_wrap        4

static const uint16_t stepgen_program_instructions[] = {
            //     .wrap_target
    0x80a0, //  0: pull   block           side 0
    0xb027, //  1: mov    x, osr          side 1
    0x1042, //  2: jmp    x--, 2          side 1
    0xa027, //  3: mov    x, osr          side 0
    0x0044, //  4: jmp    x--, 4          side 0
            //     .wrap
};

static const struct pio_program stepgen_program = {
    .instructions = stepgen_program_instructions,
    .length = 5,
    .origin = -1,
};

static inline pio_sm_config stepgen_program_get_default_config(uint offset) {
    pio_sm_config c = pio_get_default_sm_config();
    sm_config_set_wrap(&c, offset + stepgen_wrap_target, offset + stepgen_wrap);
    sm_config_set_sideset(&c, 1, false, false);
    return c;
}

static inline void stepgen_program_init(PIO pio, uint sm, uint offset, uint pin) {
    pio_sm_config c = stepgen_program_get_default_config(offset);
    sm_config_set_sideset_pins(&c, pin);
    pio_gpio_init(pio, pin);
    pio_sm_set_consecutive_pindirs(pio, sm, pin, 1, true);
    /* Full system clock: 8 ns resolution, and the period comes entirely from
       the FIFO word so there is no divider to quantise it. */
    sm_config_set_clkdiv(&c, 1.0f);
    sm_config_set_out_shift(&c, false, false, 32);
    sm_config_set_fifo_join(&c, PIO_FIFO_JOIN_TX);
    pio_sm_init(pio, sm, offset, &c);
    pio_sm_set_enabled(pio, sm, true);
}
