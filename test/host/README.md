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
