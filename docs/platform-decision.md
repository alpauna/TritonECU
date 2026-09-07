# MCU platform: STM32F767ZI

Changed from ESP32-P4 to **STM32F767ZI** (Nucleo-144 for prototyping, raw chip
for the truck board).

## Why

| | STM32F767ZI | ESP32-P4 (raw) | Teensy 4.1 |
|---|---|---|---|
| **ECU precedent** | **rusEFI Proteus runs this exact part** | none | some |
| I/O available | **~114** | 40 | 55 |
| Timers | TIM1/TIM8 advanced + 4 × 32-bit GP | GPTimer | FlexPWM/QuadTimer |
| Determinism | **ITCM/DTCM, zero wait state** | fine if PSRAM avoided | TCM |
| Flash / RAM | 2 MB / 512 KB | 32 MB / 32 MB | 8 MB / 1 MB |
| Custom board risk | **low — internal flash** | **high** — QSPI, crystal, power sequencing | none (module) |
| Ethernet | **MAC on-die, PHY on the Nucleo** | no | via add-on |
| CAN | **3 controllers** | 2 | 3 |
| Toolchain maturity | high | rough | high |
| In hand | **yes** | bench board | yes |

Three things decided it:

1. **rusEFI's Proteus ECU runs on the STM32F767** — 12 ignition outputs, 16
   low-side drivers, dual VR crank/cam, knock, up to 12 cylinders. A production
   open-source ECU on this exact silicon is a stronger endorsement than any
   datasheet comparison.
2. **The pin budget stops being a design constraint.** 37 needed against ~114.
   Every compromise held in reserve — semi-sequential injection, 1-bit SDMMC,
   tach/VSS over SCP — is now unnecessary. Several earlier decisions existed
   only to fit 40 pins.
3. **It was already on the bench**, so prototyping starts immediately rather
   than after a board spin.

## Future-proofing, which was an explicit goal

- **~77 spare I/O.** Enough for drive-by-wire throttle, VVT solenoids, direct
  injection, wideband per bank, more coils — the things a newer vehicle needs
  and this one does not.
- **Ethernet.** The MAC is on-die and the Nucleo carries the PHY and RJ45
  already. For bench tuning it beats Wi-Fi outright: no association, no channel
  hunting, deterministic latency, and the bandwidth to log every combustion
  event continuously — which is where Wi-Fi gives up. It is also the direction
  vehicle networks are moving, **and it has no radio attack surface** — see
  below.
- **Three CAN controllers**, against a truck that has none. Any later vehicle
  will.
- **1.1 % flash and 0.3 % RAM used** by M0. Nothing here is sized to just fit.

## Security: no radio is a category difference, not a degree

Worth stating as a design principle rather than a side effect.

The original ESP-ECU exposed a **web server, MQTT and OTA firmware update** over
Wi-Fi. On a bench that is convenient. On a vehicle it is an always-on radio
attack surface with a path to **remote code execution inside engine control** —
OTA is exactly that, by design.

This is not hypothetical. The 2015 Jeep Cherokee work went remote network →
in-vehicle bus → physical vehicle control, and the entry point was a
network-reachable service on a module nobody expected to be an attack surface.

**Ethernet requires someone to be in the cab with a cable.** That is not a
stronger password or a better protocol — it is a different threat model. An
attacker needs physical access, at which point they could equally cut a wire.

Consequences adopted:

- **No radio on the v1 board.** The ESP32-C6 module previously planned for
  Wi-Fi is dropped, not deferred.
- **Ethernet is the tuning and logging interface**, and it is better at the job
  anyway — deterministic, no association, and enough bandwidth to log every
  combustion event.
- **If Wi-Fi is ever wanted**, it should be a physically removable module or
  behind a hardware switch, not a permanently soldered always-on radio.
- **Firmware update should require a physical action** regardless of transport —
  a jumper, a button, or key-off — so no network path alone can rewrite engine
  control.
- **Never accept a firmware update or a tune write while the engine is
  running.** Cheap to enforce, and it removes the worst-case outcome entirely.

That last pair costs almost nothing to implement and closes the gap that
matters most.

The core is unaffected. `CrankDecoder`, `EnginePosition` and `SparkScheduler`
are `<stdint.h>`-only and build for both targets unchanged, with all 28 native
tests passing — that portability was deliberate and it paid for itself here.

Rewritten for STM32: `main`, `Storage`, `Ad7606c`, `Board`. `PinSelfTest` is
dropped, having done its job on the P4.

`src/` is now split `core/` · `esp32/` · `stm32/`, selected per environment.

## What carries over unchanged

Everything decided about the *hardware outside the MCU* still stands, because
none of it depended on the processor:

- LTC4364-2 input protection, LM5155-Q1 SEPIC at 6 V / 3 A, 2.2 MHz
- AD7606 analog front end
- 2 × MAX9926, Mode A2
- 8 × ISL9V3040 + 74HCT541, 8 × ZXMS6005DGQ
- EEC-V connector, harness protection, grounding architecture

## One thing not to carry over

**Re-establish the AD7606's SPI mode on STM32.** The Teensy needed MODE0 and
the ESP32-P4 needed MODE2 — the mode is a property of the host/ADC pairing, not
of the ADC, and a wrong CPHA reads exactly 2× high while looking perfectly
stable. Sweep it against a known signal, as `spisweep` did on the P4.
