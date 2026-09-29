#pragma once
// External hardware watchdog — TPS3823A-33 on the custom board.
//
// The supervisor holds the MCU in reset (NRST) and disables the coil buffer
// (74HCT541 OE2, through a BSS138 inverter) unless it sees an edge on WDI at
// least every 0.9 s worst case, 1.6 s typical. Firmware proves it is alive by
// toggling that pin from the engine loop.
//
// Rules, from docs/output-drivers.md "DECIDED: TPS3823A-33DBVR":
//   - Kick from the engine loop, never from a free-running timer. A hung main
//     loop with a live timer must trip the watchdog, not feed it. The one
//     exception is BlockingGuard below, and it is bounded by construction.
//   - The kick is an edge, rising or falling, so kick() simply toggles.
//   - Nothing else on the WDI net, no pull resistor. A floating WDI is how the
//     part disables itself when the STM32 is in Standby and its GPIOs float.
//
// On the Nucleo bench there is no supervisor fitted; the pin toggles into
// thin air and the calls are harmless.

#include <stdint.h>

namespace watchdog {

// Configures the kick pin and produces the first edge. Call it first thing in
// setup(): the 0.9 s window opens the moment NRST is released.
void begin();

// One edge on WDI. Call on a steady cadence of 10 ms or better from the loop
// that must be proven alive.
void kick();

// Covers a call that blocks longer than the window and cannot kick from
// inside: SdFat's 2 s card-init, a flash write, a log rotation. While a guard
// is alive a hardware timer kicks WDI every 20 ms -- but only until the
// guard's deadline, maxMs after construction. Past that the timer stops
// kicking and the supervisor fires, so a hang inside the guarded call is
// still caught, just later. The bound is the whole point: this is never a
// way to keep a stuck process alive, and maxMs should be the longest the
// call can legitimately take, not a round number.
//
//   {
//       watchdog::BlockingGuard guard(3000);   // SdFat: 2 s timeout + margin
//       storage::begin();
//   }                                          // timer stops here
//
// Guards nest; the timer runs until the outermost one ends, and the deadline
// is the latest of those in force. Only appropriate where nothing is armed
// that depends on the engine loop -- at boot, or on the bench.
class BlockingGuard {
public:
    explicit BlockingGuard(uint32_t maxMs);
    ~BlockingGuard();
    BlockingGuard(const BlockingGuard&) = delete;
    BlockingGuard& operator=(const BlockingGuard&) = delete;
};

}  // namespace watchdog
