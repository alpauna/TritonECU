# VR rig step generator — RP2040

Spins the 36-1 wheel at a **commanded angle and speed**, so a decoder's output
can be checked against a known truth rather than against itself.

**The point is not constant-speed stepping.** A real engine surges and collapses
across every compression stroke, and that is the regime where sync acquisition
fails. A rig that only spins smoothly never tests it — so the `crank` profile is
the reason this firmware exists.

---

## Build — PlatformIO

```sh
pio run -t upload        # hold BOOTSEL on the first flash
pio device monitor
```

**Builds clean**, no warnings at `-Wall -Wextra`: 9.8 kB RAM, 54 kB flash.

The platform is **Max Gerhardt's fork**, not the official `raspberrypi` one —
the official platform carries only the Arduino Mbed core. The earlephilhower core
is built *on* the Pico SDK, so `hardware/pio.h` and the rest are reachable
directly, and core 1 arrives as `setup1()`/`loop1()` instead of
`multicore_launch_core1()`.

### Or the Pico SDK directly

```sh
sudo apt install cmake gcc-arm-none-eabi libnewlib-arm-none-eabi
git clone --depth 1 https://github.com/raspberrypi/pico-sdk
cp pico-sdk/external/pico_sdk_import.cmake .
export PICO_SDK_PATH=$PWD/pico-sdk
mkdir build && cd build && cmake .. && make
```

`src/main.cpp` serves **both** toolchains — `#ifdef ARDUINO` picks the entry
points and the console, and everything between them is shared. Two copies of a
control loop would have drifted apart within a week.

Commands arrive over **USB CDC** (`/dev/ttyACM0`), not the UART pins.

### The PIO program is committed, not generated

PlatformIO does not run `pioasm`, so `src/stepgen.pio.h` is **hand-assembled and
committed**, and CMake uses the same file rather than regenerating — which also
guarantees both builds run the identical program.

`stepgen.pio` remains the readable source of truth. To regenerate rather than
trust the committed copy:

```sh
pioasm stepgen.pio src/stepgen.pio.h
```

The encoding is spelled out instruction by instruction in the header's comment,
against RP2040 datasheet §3.4, and was verified by decoding all five words back
with an independent decoder. Jump targets are stored relative to program start —
`pio_add_program()` adds the load offset to every JMP as it writes them.

## Wiring

Each signal goes through its own [2N7002 driver board](../../2N7002%20Driver/):
Pico GPIO → board `IN`, board `LOAD` → the DM542's **`−`** terminal. The DM542's
**`+`** terminals go to **+5 V from the DC-DC in the [PSU
enclosure](../../psu-enclosure/README.md)** — the same rail that powers the
Pico, so the 5 V, the Pico's ground and the FET sources are one node.

**Not the Pico's `VBUS`.** `VBUS` is the USB connector's 5 V with nothing in
between, so taking the opto commons from it means the rig only runs while a host
is plugged in. The Pico itself is fed on **`VSYS` (pin 39)**, ground on pin 38 —
see [the rig BOM](../BOM.md#powering-the-pico--vsys-never-vbus).

| Pico | driver board | DM542 |
|---|---|---|
| GP2 | board 1 `IN` | `PUL−` |
| GP3 | board 2 `IN` | `DIR−` |
| GP4 | board 3 `IN` | `ENA−` *(optional)* |
| GND | both headers' pin 1 | — |
| `VSYS` (pin 39), `GND` (pin 38) | — | fed from the enclosure's 5 V rail |
| — | — | `PUL+`, `DIR+`, `ENA+` ← that same +5 V |

**The chain inverts twice and ends up non-inverting in intent:** a GPIO high
turns the FET on, which pulls the DM542's `−` low and lights the optocoupler. So
a high *is* an active pulse, and the pin idles low — which is also what the
board's 10 kΩ gate pulldown holds during reset, before any firmware runs.

**`ENA` note:** on a DM542 the ENA optocoupler *disables* the driver when
energised. `ENA_ENERGISED_DISABLES` in `main.c` reflects that, so a GPIO low
means running. Leave `ENA` unconnected entirely and the driver is simply always
enabled.

**Set the driver to 3200 pulse/rev** (SW5–8) and **SW4 off** for half current at
standstill, so the motor is not heating between runs.

## Commands

```
rpm <v>                    constant speed, ramped
crank <rpm> [irreg%]       cranking profile — default 200 rpm, ±30 %
sweep <from> <to> <secs>   ramps to <from>, then sweeps
stop                       ramped, never abrupt
zero                       reset the angle counter
status                     profile, rpm, steps, revolutions, angle
help
```

`zero` is called with the hub's **index flute at the sensor** — the flute points
at the missing tooth, which on this wheel is TDC #1. After that, commanded steps
*are* crank degrees.

## Why the deceleration is rate-limited

`DECEL_RPM_S` is not a comfort setting. A decelerating stepper pushes energy back
at the supply, a switching supply **cannot sink current**, and the wheel carries
**15 J at 1200 rpm**. No practical bulk capacitor absorbs a hard stop — 2200 µF
still reaches 64 V against the DM542's 50 V maximum. At a 3 s ramp only ~5 W
comes back, which the driver's own losses swallow. See [BOM.md](../BOM.md).

The `sweep` command refuses a down-sweep that would exceed the same limit, rather
than silently clipping it.

## The crank profile

A V8 fires eight times per 720°, so crank speed dips **four times per
revolution**, and the dips land at TDC — which is where this wheel's gap is.

```
mod[i] = -cos(2πi/256)        minimum at the start of each 90° segment
inst   = base × (1 + irreg × mod)
```

Precomputed into a 256-entry table so the hot loop never calls `cosf()`. At
64 kHz there are ~1950 core cycles per step, and a transcendental would not fit.

## Verified

The firmware is **not compiled for the target here** — no ARM toolchain on this
machine. What *was* done, and it found three real bugs:

| check | result |
|---|---|
| Compile with SDK stubs, `-Wall -Wextra` | **clean** |
| Spin-up 0 → 1200 rpm | 2.958 s (400 rpm/s) |
| **Deceleration 1200 → 0** | **3.038 s — the regen limit holds** |
| Crank modulation | 4 dips/rev, minima at 0/90/180/270° |
| Speed accuracy | worst 363 ppm, at 700 rpm |
| Pulse width at max rate | 2.512 µs, above the DM542's 2.5 µs |
| Sweep guard | rejects 1200→200 in 2 s, accepts 3 s |

**The three bugs, since they are the sort that survive a code review:**

1. **`MIN_PERIOD_CYC` was 625**, giving a 2.496 µs pulse — **4 ns under** the
   DM542's minimum. Now 630.
2. **Startup deadlocked.** Ramping from rest, the first increment was smaller
   than `MIN_RPM`, so it was clamped back to zero on every pass — forever. The
   rig would simply never have moved.
3. **`M_PI` is not guaranteed** by C11 `<math.h>`. Replaced with a literal.

Bench-check before trusting the datum: **the commanded step count against the
decoder's own gap detection**, once per revolution. If they ever disagree, steps
were lost and the absolute angle is a fiction.
