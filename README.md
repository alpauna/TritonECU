# TritonECU

Standalone engine and transmission controller for **Ford modular V8s of the
EEC-V era** — replacing the factory PCM.

Developed against a **1999 F-150 4WD, 5.4L Triton 2V, 4R70W**, but the
architecture is the modular family rather than one truck: 4.6L and 5.4L 2V
share the crank trigger, the sensor set, the SCP bus and the connector, so
Mustangs and other EEC-V modular applications of the period are the same
problem with a different calibration.

Built on an **STM32F767ZI**. Rewritten from scratch on the `rebuild` branch;
the previous ESP32-S3 firmware is described in
[`docs/legacy-esp32s3-README.md`](docs/legacy-esp32s3-README.md) and still
lives on `main`.

**What is vehicle-specific and what is not:**

| Portable across EEC-V modulars | Specific to this truck |
|---|---|
| 36-1 VR crank decode, cam sync | firing order, displacement |
| EEC-V 104-pin connector and pinout | 4R70W shift logic (4R100 differs) |
| SCP / J1850 PWM bus | 4x4 transfer case inputs |
| Ignition and injection output stages | VE and spark tables |
| Sensor conditioning and protection | |

---

## Status

| Milestone | | |
|---|---|---|
| **M0** Board bring-up | ✅ | 216 MHz, 2 MB flash, verified from the chip's own ID registers |
| **M1** Storage + config | ✅ | SD on SPI4, JSON config, persists across resets |
| **M2** Analog front end | ✅ | AD7606 reading known signals within tolerance |
| **M3** Crank sync | ◐ | decode logic proven — 10 native tests; needs a MAX9926 |
| **M4** Cam sync | ◐ | logic proven — 6 native tests |
| **M5** Spark output | ◐ | scheduler proven — 12 native tests |
| **M6+** Injection, closed loop, SCP, transmission | ○ | |

**28 native unit tests passing.** The decode, cam-sync and spark-scheduling
modules are `<stdint.h>`-only and testable without hardware — which is how M3–M5
were proven before the sensors existed.

```bash
pio test -e native              # logic, no hardware
pio run -e nucleo -t upload     # flash the board
```

## Why it is being rebuilt

The previous firmware worked, but was written against an ESP32-S3 that was
never in a truck, and one of its structural decisions turned out to be wrong:
**coils and injectors were driven through MCP23S17 SPI expanders.**

At 6000 rpm one crank degree is **27.8 µs**. An SPI transaction is several
microseconds at best, is not deterministic, and cannot be driven from a
hardware timer. Spark timing cannot live behind a port expander. That is not a
bug to patch — it changes ignition, injection and the pin map together.

Proven pieces get ported forward deliberately. Everything else earns its place
again. See [`docs/roadmap.md`](docs/roadmap.md).

## Hardware

Design is frozen — [`docs/v1-scope.md`](docs/v1-scope.md) is the build list.

| Block | Part |
|---|---|
| MCU | STM32F767ZI (Nucleo-144 now, raw chip later) |
| Input protection | LTC4364-2 — reverse polarity, load dump, overcurrent, brownout holdup |
| Main supply | LM5155-Q1 SEPIC, 6.0 V / 3 A at 2.2 MHz |
| Analog in | AD7606, 8 ch, 16-bit, simultaneous, ±10 V |
| Crank / cam / OSS | 2 × MAX9926, Mode A2 |
| Ignition | 8 × ISL9V3040 ignition IGBT + 74HCT541 |
| Injection | 8 × ZXMS6005DGQ IntelliFET |
| Connector | EEC-V 104-pin |

### Decisions worth knowing

- **No Wi-Fi.** An always-on radio on an engine controller is a remote attack
  surface with a path to code execution via OTA. Ethernet needs physical
  access. [`docs/platform-decision.md`](docs/platform-decision.md)
- **2.2 MHz switching** to clear the AM broadcast band — a 400 kHz converter
  puts harmonics at 1.2 and 1.6 MHz, inside it.
  [`docs/power-supply.md`](docs/power-supply.md)
- **Clamp both loads, dissipate neither.** A coil's flyback *is* the spark
  (400 V clamp); an injector's is waste but a plain diode makes it close
  slowly and over-fuel at idle (60–70 V clamp).
  [`docs/output-drivers.md`](docs/output-drivers.md)
- **The MAF is a differential measurement.** It has a dedicated signal return
  separate from the ground its supply current flows in — which is the whole
  reason for the AD7606 over the MCU's own ADC.

## The reference vehicle

Every design decision traces to a factory schematic, recorded in
[`docs/1999-Ford-F150-4wd-5.42v/`](docs/1999-Ford-F150-4wd-5.42v/). Several
overturned assumptions taken from parts catalogues and forums:

| Assumed | Actually |
|---|---|
| Wasted spark, 4 coil drivers | **Coil-on-plug, 8 individual coils** |
| ECT coolant sensor | **CHT — cylinder head temperature** |
| Oil pressure sender | **A switch.** Binary, not analog |
| No knock sensor on the 2V | **Present** — C103 |
| 4R70W has a TSS | **It does not.** 4R100 only |
| GEM is on the SCP bus | **It is on ISO 9141.** Only the PCM and cluster are on SCP |

PATS is a non-issue: the anti-theft logic lives in the instrument cluster and
authorises *the PCM* over SCP. A replacement ECU never asks, so there is
nothing to defeat.

## Layout

```
firmware/ecu/
  src/core/     decode, cam sync, spark scheduling — portable, unit-tested
  src/stm32/    STM32 platform layer
  src/esp32/    ESP32-P4 platform layer (earlier target, still builds)
  test/         native unit tests
hardware/       pin budget and supply calculators
docs/           design documents and vehicle schematics
tools/          USB permission setup
```

## Bench setup

[`docs/nucleo-setup.md`](docs/nucleo-setup.md) is a runbook for bringing a
Nucleo up from scratch, including the failures that actually cost time — the
ST-Link udev rule, programming the ELF rather than the `.bin`, and
`-Wl,-u,_printf_float`.

```bash
tools/setup-usb-permissions.sh      # debug probe access
```
