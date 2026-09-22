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

## `pio/edge_capture.pio` + `include/PulseHistogram.h`

**Measure the bit timing; do not hard-code it.**

J1850 PWM carries meaning in *where the falling edge falls inside a bit*, so the
decoder needs tp values in nanoseconds. Taking those from a half-remembered
datasheet produces a decoder that fails **like broken hardware** — which is the
most expensive way to be wrong here. So the first firmware knows nothing about
the protocol: it times edges and reports what it saw.

### The PIO side

One 32-bit word per edge: `(count << 1) | level_after_the_edge`. The loop body is
two PIO cycles, so at 16 MHz one count is **125 ns** and a 24 µs bit is ~192
counts — small numbers, ample resolution.

Two deliberate choices:

- **The level rides in the LSB.** Bare intervals would be one lost FIFO word away
  from silently inverted polarity, and every later decode would be wrong with
  nothing to show for it.
- **`push noblock`.** Never stall the timer. Drop and detect — the SM's
  `RXSTALL` flag says it happened.

### The histogram side

Bin the intervals, report the clusters. Point it at a running truck for thirty
seconds and the output is a short list — *"8.0 µs ×41k, 16.1 µs ×39k, 24.2 µs
×2k"* — and **those are the constants**, measured on the bus that has to be
decoded rather than recalled.

> **The floor is a fraction of the TOTAL, not of the tallest bin.** This is not a
> detail — the host test caught it. SOF, EOF and IFS happen **once per frame**
> while ordinary bits happen dozens of times per frame, so the intervals that
> define frame structure sit two orders of magnitude below the common peaks. A
> peak-relative floor throws away exactly what the exercise is for. Default is
> 1 ‰ of all samples.

### Test

```bash
g++ -std=c++17 -Wall -Wextra -Iinclude -o /tmp/t test/pulsehistogram_test.cpp && /tmp/t
```

Feeds a synthetic stream shaped like a real bus — two common short intervals, a
rarer long one, and scattered noise — and checks that all three clusters are
found with the right centroids and populations while the noise is rejected.

## Building and running it

```bash
pio run                  # builds: 4.0% RAM, 1.8% flash on a Pico
pio run -t upload        # hold BOOTSEL on the first flash
pio device monitor       # 115200
```

`src/edge_capture.pio.h` is generated from `pio/edge_capture.pio` by `pioasm`,
committed because PlatformIO does not run it — the same pattern as
`hardware/vr-test-rig/firmware/src/stepgen.pio.h`. Regenerate with:

```bash
~/.platformio/packages/tool-pioasm-rp2040-earlephilhower/pioasm \
    -o c-sdk pio/edge_capture.pio src/edge_capture.pio.h
```

### The loopback self-test

`LOOPBACK 1` in `src/main.cpp` puts a **hardware PWM** square wave on GP3 —
8 µs high, 16 µs low, the shape a J1850 PWM bus has. **Jumper GP3 to GP2** and
the rig measures its own generated signal.

PWM rather than bit-banging on purpose: it is free-running, so draining the FIFO
cannot distort the very widths being measured. Bit-banged generation would put
the drain time straight into the pulse width and then the test would be
measuring itself.

**Pass = two clusters at 8.000 and 16.000 µs.** Anything else means the capture
chain is wrong, and it is far better to learn that on a jumper wire than on a
truck.

> ⚠ **Status: builds clean, not yet run on hardware.** The loopback test above is
> pending a working micro-USB cable. Until it has passed, treat the PIO timing
> and the count-to-nanosecond conversion as unverified.

## Still to write

- J1850 PWM bit decode, **using the constants the histogram produces**.
- Frame assembly and CRC.
- SD writer draining the ring, flushing on a 1 s timer.
- GPS on UART + PPS for a shared timebase.
