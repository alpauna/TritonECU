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
| **M3** Crank sync | ◐ | decode logic proven — 10 native tests; **VR board on order**, CKP sensor + pigtail ordered |
| **M4** Cam sync | ◐ | logic proven — 6 native tests; **CMP sensor + pigtail ordered** — same connector as CKP |
| **M5** Spark output | ◐ | scheduler proven — 12 native tests |
| **M6+** Injection, closed loop, SCP, transmission | ○ | |
| **Power board V1** | ✅ | schematic, BOM and Gerbers reviewed clean — **ready to fab** |
| **VR board V1** | ✅ | 4 channels, 2 × MAX9926 Mode A2 — reviewed clean, **fabricating** |
| **VR test rig** | ◐ | designed, rendered and costed — 12 mm shafts, printed involute gears, [STLs](hardware/vr-test-rig/stl/) + [BOM](hardware/vr-test-rig/BOM.md) |
| **Knock front end** | ◐ | **next build after the VR board** — schematic, net list and BOM drawn, [`knock-front-end-schematic.md`](docs/Schematics/knock-front-end-schematic.md) |
| **EEC-V connector** | ✅ | sourcing solved — Ranger donor + the TE controlled drawing |
| **Enclosure** | ◐ | **cabin, behind the glovebox**, connector face through the firewall — vent on the cabin side, [`enclosure.md`](docs/enclosure.md) |

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

**Two boards are finished.** Schematics, BOMs and Gerbers are all version
controlled in [`docs/Schematics/`](docs/Schematics/) — the fab outputs, not just
pictures of them.

| Board | Size | Review |
|---|---|---|
| **Power V1** | 76.58 × 46.74 mm, 4 layer | [`review-power-v1-bom-gerbers.md`](docs/review-power-v1-bom-gerbers.md) |
| **VR V1** | 35.43 × 33.91 mm, 2 layer | [`review-vr-v1.md`](docs/review-vr-v1.md) |

Both reviews were **measured out of the Gerbers** — copper polygon areas, via
positions, pad geometry and the flying-probe netlist — rather than read off a
render. That is how the MAX25239 footprint, Q2's thermal path and the output-cap
pour were actually checked. The earlier schematic-only pass on the power board
is [`schematic-review-power-v2.md`](docs/schematic-review-power-v2.md).

| Block | Part |
|---|---|
| MCU | STM32F767ZI (Nucleo-144 now, raw chip later) |
| Input protection | LTC4364-2 — reverse polarity, load dump, overcurrent, brownout holdup |
| Pass element | IRF540NS (D2Pak) on HGATE — planar, published SOA, 20 tented vias into 1.14 in² of B+ |
| 5 V rail | MAX25239AFF**A** buck-boost, 2.1 MHz, spread spectrum, 2.2 µH |
| 3.3 V rail | TLV62085 buck from 5 V, 2.4 MHz, 500 nH |
| ADC reference | MAX6070AAUT25, 2.5 V, gated for sleep |
| Battery sense | INA238 on the LTC4364's own 10 mΩ / 1 % / 50 ppm shunt |
| Analog in | AD7606B, 8 ch, 16-bit, simultaneous, ±10 V — **TI ADS8588S is pin-for-pin**, second source |
| Crank / cam / OSS | 2 × MAX9926 Mode A2 — 4 channels, adaptive threshold + zero crossing |
| Knock | TLV9064-Q1 differential charge amp + own 2.5 V ref — [schematic](docs/Schematics/knock-front-end-schematic.md) |
| Barometric | **KP497** (Infineon) on I²C/SPI, AEC-Q100 −40…+105 °C, 3.3 V always-on rail — **requires a vented enclosure** |
| Ignition | 8 × ISL9V3040 ignition IGBT + 74HCT541 |
| Injection | 8 × ZXMS6005DGQ IntelliFET |
| Connector | EEC-V 104-pin |

### Decisions worth knowing

- **No Wi-Fi.** An always-on radio on an engine controller is a remote attack
  surface with a path to code execution via OTA. Ethernet needs physical
  access. [`docs/platform-decision.md`](docs/platform-decision.md)
- **2.1 MHz switching** to clear the AM broadcast band — a 400 kHz converter
  puts harmonics at 1.2 and 1.6 MHz, inside it. The MAX25239's `A` and `B`
  suffixes are 2100 kHz and 400 kHz respectively, and the board was nearly
  built with the wrong one.
  [`docs/always-on-domain.md`](docs/always-on-domain.md)
- **The MCU never fully powers down.** It sleeps on an always-on 3.3 V rail at
  ~3 µA and brings the rest up on demand, which removes the graceful-shutdown
  problem, replaces KAPWR and makes supply-fault latching implementable in
  firmware. Parked drain is ~950 µA, about 1 % of the battery per month.
  [`docs/always-on-domain.md`](docs/always-on-domain.md)
- **The ADC lives on a daughterboard.** Not for proximity — that is a placement
  problem — but for analog ground plane control on a board that low-side
  switches eight ignition coils, and so the front end can be respun without the
  carrier. [`docs/adc-daughterboard.md`](docs/adc-daughterboard.md)
- **The SEPIC was retired.** An integrated buck-boost deletes the external FET,
  the Schottky, both inductors and the coupling-cap bank, and adds spread
  spectrum the controller design never had.
  [`docs/power-supply.md`](docs/power-supply.md) keeps the input-chain analysis
  and marks the rest superseded.
- **Clamp both loads, dissipate neither.** A coil's flyback *is* the spark
  (400 V clamp); an injector's is waste but a plain diode makes it close
  slowly and over-fuel at idle (60–70 V clamp).
  [`docs/output-drivers.md`](docs/output-drivers.md)
- **The shunt is sensed twice and sets two things.** The LTC4364's current
  limit and the INA238's battery-current reading both come off one 10 mΩ
  resistor, so its tolerance and TCR are the accuracy of both — which is why it
  is a 1 %, ±50 ppm/°C, AEC-Q200 metal-element part in 2512 rather than
  whatever was cheapest.
- **Leave the factory harness alone.** Every "this should be referenced
  differently" question is answered by **PCB routing, not by moving wires** — the
  board defines what each of the 104 cavities connects to. An unmodified harness
  stays diagnosable by anyone with a Ford wiring diagram, and the PCB is the half
  that can be revised.
  [`docs/1999-Ford-F150-4wd-5.42v/connector-sourcing.md`](docs/1999-Ford-F150-4wd-5.42v/connector-sourcing.md)
- **The VR trigger point needs no calibration term.** MAX9926 Mode A2 arms on
  33 % of the previous peak but *triggers* on the zero crossing
  (−6.5 / +10 mV) — which is the tooth centre, because a VR sensor outputs
  dΦ/dt. Amplitude, rpm and acceleration cannot move it; scaling a waveform does
  not shift where it crosses zero. Propagation delay is 50 ns, or 0.0018° at
  6000 rpm. This repo previously had it wrong in three places, claiming the
  comparator switched at ⅓ of peak and that the offset would need characterising.
  [`docs/1999-Ford-F150-4wd-5.42v/vr-conditioning.md`](docs/1999-Ford-F150-4wd-5.42v/vr-conditioning.md)
- **MAX9926 over the LM1815, on arming margin.** Both arm adaptively and trigger
  on zero crossing, so timing is a wash. The LM1815 arms at **80 %** of the
  previous peak against the MAX9926's **33 %** — tolerating a 1.25:1 amplitude
  collapse between teeth where the MAX9926 tolerates **3:1**. Cranking, slowing
  hard against each compression stroke, is exactly where that collapse happens.
  The differential input the single-ended LM1815 cannot offer settles the rest.
- **Keyway to missing tooth is zero, on the rig and on the truck.** The bench
  wheel's keyway lines up with the gap, and the 5.4L was timed to the same datum,
  so `CKP_GAP_TO_TDC_DEG = 0` for both. It stays a *named* constant rather than a
  vanished zero — the rig's absolute angle is then the engine's absolute angle,
  which makes the rig a timing calibration bench rather than a functional check.
  [`hardware/vr-test-rig/README.md`](hardware/vr-test-rig/README.md)
- **Stiffness comes from section, not from material.** Two 8 mm rods in ribs
  under the rig's base take it from `EI` 20.5 to 826 N·m² — 40× — because the
  offset contributes `A·d²`. A 5 mm rod in a rib beats a 10 mm rod buried in the
  plate. The same arithmetic found the real soft spot: the printed bearing
  bracket was less stiff than the shaft it was holding.
  [`hardware/vr-test-rig/BOM.md`](hardware/vr-test-rig/BOM.md)
- **A printed trigger wheel produces nothing.** A VR sensor works on reluctance
  change; printed plastic is magnetically identical to air. The bench rig is
  printed, the 36-1 wheel is steel, and the cam target is a printed disc with one
  steel bolt. [`hardware/vr-test-rig/`](hardware/vr-test-rig/)
- **The knock sensor is differential, and that decides its front end.** A
  two-wire floating piezo (pins 57, 32) into a single-ended knock IC would ground
  one leg and inject sensor-ground noise straight into a microvolt signal. A
  differential charge amp is needed either way, so it is the part to build — and
  it defers the IC-versus-DSP choice rather than forcing it. One TLV9064-Q1 quad
  holds the lot: two charge amps, a difference stage and a VMID buffer.
  [`docs/knock-front-end.md`](docs/knock-front-end.md)
- **Charge mode, because the harness moves.** Read a piezo as a *voltage* and the
  cable capacitance divides the signal down — 100 pF of loom against a 1 nF
  sensor is a 10 % error that **changes if the harness is rerouted**. Read as
  *charge*, both terminals sit at a virtual ground, the cable sees no swing, and
  sensitivity stops depending on how the loom was dressed. The feedback caps then
  *are* the calibration (`Q/Cf`), which is why they are C0G and not X7R.
- **Analog blocks get their own references.** The knock front end has a 2.5 V
  reference separate from the ADC's. It does not save an amplifier though: the
  difference stage's reference leg is one arm of a resistor bridge, and CMRR
  depends on that bridge staying balanced, so it still wants a buffer between the
  reference and `R8` rather than the reference's own output impedance in series
  with one arm.
- **The enclosure must be vented, and not only for the barometer.** A sealed box
  tracks its own temperature rather than the weather, so the barometric sensor
  would be useless in one. But a sealed automotive housing also **pumps moisture
  past its own seals** — every heat cycle pushes air out, every cool-down draws it
  and whatever is near the seal back in. A vent membrane gives that breathing a
  deliberate path; the correct pressure reading is a side effect of doing the
  housing properly. **The vent goes on the cabin side** — the box straddles the
  firewall, and its connector face lives under-hood in the spray.
  [`docs/enclosure.md`](docs/enclosure.md)
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
  vr-test-rig/  parametric OpenSCAD for the 36-1 + cam bench rig
docs/           design documents and vehicle schematics
  Schematics/   board schematics, BOMs and Gerbers — fab-ready
  Datasheets/   every part datasheet the decisions were made against
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
