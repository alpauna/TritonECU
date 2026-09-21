# The Phase 0 rig — build the receiver, not the transceiver

Short answer: **yes, build it, and build it before anything else on the dash
depends on guesses.** It is the cheapest de-risking step in the project and the
one everything downstream of the cluster waits on.

But it is *smaller* than the board's SCP front end, because Phase 0 is
**receive-only**.

## What to build, and what to leave out

| Part | Phase 0 | Why |
|---|---|---|
| **TLV7031** comparator across PWM+/PWM− | **build it** | This is the RX path the board ships with. Phase 0 then validates shipping hardware instead of a breadboard stand-in |
| **DRV8837** H-bridge TX | **leave it off** | Two devices transmitting the same headers corrupt each other, and the OEM PCM is live. If fitted anyway, strap `nSLEEP` **hard low** — not firmware-low |
| Capture MCU | **RP2040** | See below |
| SD or USB logging | yes | |

Connection is non-invasive at the DLC: **pin 2 = SCP+, pin 10 = SCP−**, grounds
on 4/5, permanent 12 V on 16. No splicing, plugs in like a scan tool.

> Do not confuse those with the **EEC-V** numbers in
> [`f150-1999-target.md`](f150-1999-target.md) §5.3 — there, pin 16 is SCP+ and
> pin 15 is SCP−. Same two circuits (914 `TAN/ORG`, 915 `PNK/LT BLU`), different
> connector, and the numbers happen to be adjacent in both. Easy to transpose.

## Use the RP2040, and use PIO

J1850 PWM is ~41.6 kbps with a ~24 µs bit time where the meaning is carried by
**where the falling edge lands inside the bit**. That wants deterministic
sub-microsecond edge timing, which is exactly what PIO is for — and this repo
already uses PIO on an RP2040 in
[`../hardware/vr-test-rig/firmware`](../hardware/vr-test-rig/firmware).

ESP32 **RMT** is the alternative and is also built for pulse capture. Bit-banging
on a general-purpose loop is the one approach to avoid: a missed edge looks
exactly like a quiet bus.

## Decode on the fly — do not log raw edges

Worth doing the arithmetic before committing to a format, because the naive
choice is 40× larger:

| Logging | Rate | 10-minute capture |
|---|--:|--:|
| Raw edges, 32-bit timestamps | 325 KB/s | **200 MB** |
| Raw edges, 16-bit deltas | 163 KB/s | 100 MB |
| **Decoded frames + timestamp** | **7.8 KB/s** | **5 MB** |

PIO handles the bit timing, the CPU assembles bytes, and the log holds frames.
Five megabytes for a ten-minute drive fits anywhere and is directly greppable.

## Validate the rig before the truck

The same discipline as the cluster bench test: **prove the instrument on a known
signal first.** The RP2040 makes this nearly free — one PIO state machine
generates J1850 PWM bit patterns, another captures them, loopback on the bench.

If the decoder cannot read a frame it just generated, it will not read the truck,
and you will spend the afternoon blaming the comparator.

## One optional cross-check

An **STN2120**-based sniffer (OBDLink and similar) is not required, but it turns
"is my decode wrong, or is the bus actually quiet?" from a research project into
a five-minute comparison. If the two disagree, the front end is the suspect.

**Avoid cheap ELM327 clones** — J1850 PWM is the mode they implement worst, and a
clone that silently drops frames is indistinguishable from a bus with nothing on
it.

## Order of work

1. Build RX: comparator + RP2040, no TX stage.
2. **Loopback test on the bench.** Generate, capture, decode, compare.
3. Plug into the **2003** at the DLC and record — it has the on-demand MIL from a
   disconnected EGR, see
   [`phase0-capture-protocol.md`](phase0-capture-protocol.md).
4. Repeat on the **1999**, because that is the truck being converted and the
   2003 is only a hint.
5. Bench the spare cluster and try to move a needle. That is the proof.
