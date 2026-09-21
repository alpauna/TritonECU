# Host tests

Timing logic that can be checked on a PC, with no hardware and no toolchain
beyond `g++`. `stub/Arduino.h` supplies just enough for the headers under test.

```bash
g++ -std=c++17 -Wall -Wextra -Itest/host/stub -Iinclude \
    -o /tmp/t test/host/lampdriver_test.cpp && /tmp/t
```

`lampdriver_test.cpp` covers `LampDriver`'s BURST mode — beep count, total
sounding time, the quiet tail between bursts, and that re-arming with identical
parameters does not restart the phase (it is called every loop, so it must not).
Exits non-zero on failure.

`alarmpolicy_test.cpp` covers `AlarmPolicy` — the buzzer's 5-minute auto-silence
and its re-arm rules. The case worth having a test for is the one that makes real
alarms unsilenceable: a fault bit that **flaps in and out must not re-arm**, while
a genuinely new bit, an escalation in severity, or a fault returning after
everything cleared all must. Exits non-zero on failure.
