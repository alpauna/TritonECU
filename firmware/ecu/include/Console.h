#pragma once
// Console output, mirrored to both serial ports.
//
// The Nucleo's ST-Link VCP drops characters even on light, steady output --
// verified on the bench at 115200 and 57600, with no host traffic. USART2 on
// PD5/PD6 with an ordinary USB-UART adapter is clean.
//
// Everything is written to both, so whichever is connected works. Modules must
// use these rather than Serial directly, or their output only reaches the
// unreliable port.

#include <Arduino.h>

namespace console {

void begin();
void printf(const char* fmt, ...) __attribute__((format(printf, 1, 2)));
void println(const char* line = "");

// Flush both ports and pause. Used between banner lines.
void settle();

// Any byte waiting on either port, or -1.
int read();

}  // namespace console
