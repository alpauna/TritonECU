#include "Console.h"

#include <stdarg.h>

#include "Board.h"

// USART2 on PD5/PD6. USART3 (PD8/PD9) belongs to the ST-Link.
HardwareSerial ExtSerial(board::console::kRx, board::console::kTx);

namespace console {
namespace {
// The ST-Link VCP is kept at a low rate because it is unreliable regardless.
constexpr uint32_t kVcpBaud = 57600;
}  // namespace

void begin() {
    Serial.begin(kVcpBaud);
    ExtSerial.begin(board::console::kBaud);
    delay(200);
}

void printf(const char* fmt, ...) {
    char buf[192];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    Serial.print(buf);
    ExtSerial.print(buf);
}

void println(const char* line) {
    Serial.println(line);
    ExtSerial.println(line);
}

void settle() {
    Serial.flush();
    ExtSerial.flush();
    delay(2);
}

int read() {
    if (ExtSerial.available()) return ExtSerial.read();
    if (Serial.available())    return Serial.read();
    return -1;
}

}  // namespace console
