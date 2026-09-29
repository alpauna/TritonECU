#include "Watchdog.h"

#include <Arduino.h>
#include <HardwareTimer.h>

#include "Board.h"

namespace watchdog {
namespace {

// TIM14: a general-purpose timer with no core use (TIM6/TIM7 are the core's
// tone and servo timers) and no pin needed. Its interrupt only ever toggles
// one GPIO, so priority is left at the default.
constexpr uint32_t kGuardKickIntervalUs = 20000;   // 45x margin on 0.9 s

HardwareTimer* g_timer = nullptr;
volatile uint8_t  g_guardDepth = 0;
volatile uint32_t g_guardDeadlineMs = 0;

void onGuardTick() {
    // Signed compare so millis() wrap-around does not extend a deadline.
    if (g_guardDepth != 0 && (int32_t)(g_guardDeadlineMs - millis()) > 0) {
        kick();
        return;
    }
    // Deadline passed, or the last guard ended between ticks. Stop feeding it;
    // if the guarded call is genuinely hung, the supervisor takes over from
    // here.
    g_timer->pause();
}

}  // namespace

void begin() {
    pinMode(board::watchdog::kKick, OUTPUT);
    digitalWrite(board::watchdog::kKick, LOW);
    kick();

    g_timer = new HardwareTimer(TIM14);
    g_timer->setOverflow(kGuardKickIntervalUs, MICROSEC_FORMAT);
    g_timer->attachInterrupt(onGuardTick);
    // Configured but not running. Only a BlockingGuard starts it.
}

void kick() {
    digitalToggle(board::watchdog::kKick);
}

BlockingGuard::BlockingGuard(uint32_t maxMs) {
    const uint32_t deadline = millis() + maxMs;
    noInterrupts();
    if (g_guardDepth == 0 || (int32_t)(deadline - g_guardDeadlineMs) > 0) {
        g_guardDeadlineMs = deadline;
    }
    g_guardDepth++;
    interrupts();
    kick();
    if (g_timer) g_timer->resume();
}

BlockingGuard::~BlockingGuard() {
    noInterrupts();
    if (g_guardDepth != 0) g_guardDepth--;
    const bool last = (g_guardDepth == 0);
    interrupts();
    if (last) {
        if (g_timer) g_timer->pause();
        kick();
    }
}

}  // namespace watchdog
