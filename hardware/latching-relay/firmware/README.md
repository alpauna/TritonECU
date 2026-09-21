# Latching relay firmware — ATtiny202

The relay remembers its own state, so this firmware never holds anything. It
emits a **30 ms pulse** on one coil to set and on the other to reset, and spends
the rest of its life watching a button.

```bash
pio run                 # build
pio run -t upload       # flash over UPDI
pio run -t fuses        # write the fuses — INCLUDING the BOD level, see below
```

## Two switches at the top of `src/main.cpp`

| | |
|---|---|
| `DUAL_COIL 1` | Two coils, two low-side FETs. Asserting a leg pin energises that coil. |
| `DUAL_COIL 0` | One coil across the bridge. Each leg is a CMOS pair with its gates tied, so the pin is **inverting**: LOW = midpoint HIGH, and idle (both LOW) puts both midpoints high so the coil sees no differential. |
| `SENSE_FITTED 0` | State is tracked in RAM. |
| `SENSE_FITTED 1` | State is read from the relay's spare pole, so the board knows where the relay *is* rather than where it thinks it put it. |

## Pins — ATtiny202 SOIC-8

Five usable I/O, which is exactly what this needs.

| Pin | Signal |
|---|---|
| PA6 | leg A — SET coil, or bridge leg A |
| PA7 | leg C — RESET coil, or bridge leg C |
| PA1 | button, to GND, internal pull-up |
| PA2 | state sense from the relay's spare pole |
| PA3 | ECU line — the ESP32 pulls it low briefly to toggle |

**For a classic ATtiny on an ISP programmer** (13A, 25/45/85) change those five
defines and the `[env:]` block in `platformio.ini`. Everything else is plain
Arduino API and ports unchanged.

## Two behaviours that are the point of building this

**Fail-safe off at boot.** A latching relay holds through a blackout, so without
this the 36 V supply comes back on by itself when the mains returns. `setup()`
fires RESET unconditionally — on an already-reset relay that costs one pulse.

**The brown-out interlock is a fuse, not code.** `board_hardware.bod = 4.3v` in
`platformio.ini`. Below that the part stops, so it cannot emit a half-length
pulse and leave the armature stranded between positions — the failure that makes
latching relays look unreliable. Verify the key name against megaTinyCore's
PlatformIO docs and confirm with `pio run -t fuses`; code cannot do this job,
because code needs a running CPU.

## Timing constants

| | | |
|---|--:|---|
| `PULSE_MS` | 30 | Datasheet set times are usually 10–15 ms, so this is a comfortable 2×. Tune to the relay you have. |
| `COIL_REST_MS` | 150 | Minimum between pulses — stops a held or chattering input hammering the coil. |
| `DEBOUNCE_MS` | 25 | Bounce is 1–5 ms. 25 is lazy and free, since nothing else is happening. |
| `LONGPRESS_MS` | 1000 | Long press forces OFF whatever the state. |

## Test it without hardware

```bash
g++ -std=c++17 -Wall -Wextra -o /tmp/sim test/sim.cpp && /tmp/sim
```

`test/sim.cpp` stubs the Arduino API, includes `src/main.cpp` and drives the
state machine on a PC — boot, short presses, long press on and off, a bouncing
contact, and the ECU line. It checks which coil fired and what state resulted,
and exits non-zero on failure. Flip `DUAL_COIL` and re-run to check the
H-bridge build; the pulses should swap legs and stay 30 ms.

```
boot             Chi@50ms Clo@80ms        relayOn=0  ok
short press      Ahi@291ms Alo@321ms      relayOn=1  ok
short press      Chi@831ms Clo@861ms      relayOn=0  ok
long press on    Chi@2851ms Clo@2881ms    relayOn=0  ok
long press off                            relayOn=0  ok
bounce+press     Ahi@5715ms Alo@5745ms    relayOn=1  ok
ECU line         Chi@6255ms Clo@6285ms    relayOn=0  ok
all pass
```
