# SCP rig firmware

Not a complete firmware yet — the PIO decoder waits on the hardware existing.
What is here is the piece that must be right before any of it matters.

## `include/FrameRing.h`

Single-producer / single-consumer ring between the capture side (PIO/ISR) and the
SD writer. Lock-free, no blocking either way.

**Why it exists:** an SD card stalls **100–250 ms** for wear levelling, and the
writer blocks for the whole pause. Without a buffer, every frame arriving during
that stall is gone — and the one you drove out for is a MIL transition lasting
milliseconds.

Two design decisions worth knowing:

- **Free-running indices, masked only on access.** The classic ring bug is
  wrapping the indices themselves, which makes `head == tail` mean both *empty*
  and *full*. Here fullness is `(head - tail) >= SLOTS`, which is wrap-safe.
- **Overflow drops the NEWEST and counts it.** The counter is not decoration:
  **a silently dropped frame is worse than no capture**, because nothing in the
  file says the gap is there. Write `dropped()` into the capture, and emit a gap
  marker frame (`flags` bit 2) so the log is self-describing.

`highWater()` reports the deepest the ring ever got — after a session it tells
you whether the size was right, rather than leaving it to faith.

## Sizing, measured rather than assumed

| | |
|---|--:|
| Worst normal card stall | 250 ms |
| Frames arriving in it, busy bus at 500/s | **125** |
| Slots configured | 2048 (48 KB) |
| **Occupancy at that worst stall** | **6.1 %** |

So 2048 slots is ~16× more than the nominal worst case needs. That margin is
close to free on a Pico's 264 KB, and it is the right place to spend it: a tired
card can stall longer than its datasheet suggests, and a bursty bus can exceed
500 frames/s briefly. **256 slots would technically cover the stall; do not.**

## Test

```bash
g++ -std=c++17 -Wall -Wextra -Iinclude -o /tmp/t test/framering_test.cpp && /tmp/t
```

Covers FIFO order, empty/full boundaries, **50 000 frames driven through a 2048
slot ring** so the wrap is exercised fifty times over, exact-capacity fullness,
refusal and counting on overflow, that the *oldest* survives an overflow, and the
250 ms stall sizing above. Exits non-zero on failure.

## Still to write

- PIO program: edge capture and J1850 PWM bit decode.
- Frame assembly and CRC.
- SD writer draining the ring, flushing on a 1 s timer.
- Optional GPS on UART for a shared timebase.
