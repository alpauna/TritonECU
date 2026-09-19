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
| **ECU carrier board** | ○ | **the largest piece left.** Fully specified in [`schematic-ecu-v1.txt`](docs/Schematics/schematic-ecu-v1.txt) — 736 lines, every part chosen — but **not yet captured as a schematic or laid out**. Envelope and the height constraint: [`carrier-envelope.md`](docs/carrier-envelope.md) |
| **Power board V1** | 🔒 | **released and frozen** — tagged `power-v1-released`, [`Schematics/README`](docs/Schematics/README.md) |
| **Power board V2** | ✅ | V1 **+ one part**: `C1` 100 nF 1206 X7R **200 V** across B+/PGND at the connector — a 19 mm² loop against D1's 131. Reviewed clean, **ready to fab** |
| **VR board V1** | ✅ | 4 channels, 2 × MAX9926 Mode A2 — reviewed clean, **fabricating** |
| **VR test rig** | ◐ | all dimensions measured; 9 of 10 parts ready to print, [STLs](hardware/vr-test-rig/stl/) + [BOM](hardware/vr-test-rig/BOM.md). Parts ordered bar the stepper |
| **VR rig firmware** | ✅ | RP2040 PIO step generator with a cranking profile — builds clean, [`firmware/`](hardware/vr-test-rig/firmware/) |
| **2N7002 driver board** | ✅ | 3.3 V → DM542 opto inputs, reviewed clean from Gerbers — [`hardware/2N7002 Driver/`](hardware/2N7002%20Driver/) |
| **Knock front end** | ◐ | **next build after the VR board** — schematic, net list and BOM drawn, [`knock-front-end-schematic.md`](docs/Schematics/knock-front-end-schematic.md) |
| **EEC-V connector** | ✅ | sourcing solved — Ranger donor + the TE controlled drawing |
| **Enclosure** | ◐ | **cabin, behind the glovebox**, connector face through the firewall — vent on the cabin side, [`enclosure.md`](docs/enclosure.md) |
| **Carrier template** | ✅ | printable measurement jig for the donor case floor — captures the mounting-boss pattern the layout is waiting on, [`hardware/carrier-template/`](hardware/carrier-template/) |
| **Harness label** | ✅ | printed plate for the always-hot battery lead and the four added pins — [STL](hardware/harness-label/stl/label.stl) + [`README`](hardware/harness-label/README.md) |

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
| Analog in | **ADS8588H** — 8 ch, 16-bit, 500 kSPS simultaneous, ±10 V, **9 kV input clamp**, −40…+125 °C |
| Analog in *(bench)* | **Tokmas AD7606BSTZ** — same LQFP-64 footprint, 200 kSPS, already in hand |
| Crank / cam / OSS | 2 × MAX9926 Mode A2 — 4 channels, adaptive threshold + zero crossing |
| Knock | TLV9064-Q1 differential charge amp + own 2.5 V ref — [schematic](docs/Schematics/knock-front-end-schematic.md) |
| Barometric | **KP497** (Infineon) on I²C/SPI, AEC-Q100 −40…+105 °C, 3.3 V always-on rail — **requires a vented enclosure** |
| Ignition | 8 × ISL9V3040 ignition IGBT + 74HCT541 |
| Injection | 8 × ZXMS6005DGQ IntelliFET |
| SCP / J1850 PWM | **DRV8837** differential TX + **TLV7031** comparator RX — the cluster's only link to the PCM |
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
- **One ADC footprint, five parts, two vendors.** AD7606 / B / C and ADS8588S / H
  are pin-for-pin in the same LQFP-64 — verified pin by pin, not assumed. So the
  part is a **populate-time choice, not a layout one**: **ADS8588H in production**
  for its 9 kV input clamp on harness-connected pins, and the **Tokmas
  AD7606BSTZ already on the bench** for development. *(The ADS9324 is not in this
  set — 16 channels, VQFN, and a 1.8 V rail this board does not have.)*
  [`docs/adc-front-end.md`](docs/adc-front-end.md)
- **A "level shifter" is not a current driver.** The DM542's step inputs are
  optocouplers wanting **14 mA**; a BSS138 + 10 kΩ bidirectional module supplies
  **0.38 mA**, and an IRF520 module is not logic-level at all — its gate threshold
  spans 2–4 V against a 3.3 V drive, so it works warm and fails cold. The answer
  is a logic-level FET *sinking* the input, with a gate pulldown so nothing moves
  while the Pico boots. [`hardware/2N7002 Driver/`](hardware/2N7002%20Driver/)
- **Model the part you are designing around, then print it.** The rig's two VR
  sensors are modelled from the *same* parameters the mount uses, so a printed
  copy held against the real sensor tests every one of those numbers at once — and
  a mismatch proves the mount wrong in the same way. Cheaper on a 20 g print than
  after the base. [`hardware/vr-test-rig/`](hardware/vr-test-rig/)
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

## External references — to read, not yet read

| | |
|---|---|
| [4R100 rebuild manual for the DIY](https://www.powerstrokearmy.com/threads/4r100-rebuild-manual-for-the-diy.20642/) | ⚠ **4R100, not 4R70W** — this truck has the 4R70W. Worth having anyway: the **MegaSquirt pinout this project cross-checks against was developed on a 4R100**, which is why it listed a coast clutch solenoid that does not exist here ([`output-drivers.md`](docs/output-drivers.md)). If another MS-sheet entry ever looks wrong, this is where the explanation will be |

## Layout

```
firmware/ecu/
  src/core/     decode, cam sync, spark scheduling — portable, unit-tested
  src/stm32/    STM32 platform layer
  src/esp32/    ESP32-P4 platform layer (earlier target, still builds)
  test/         native unit tests
hardware/       pin budget and supply calculators
  vr-test-rig/    parametric OpenSCAD for the 36-1 + cam bench rig
  psu-enclosure/  printed box for the bench supply
  harness-label/  printed label - the always-hot lead and the added pins
  carrier-template/ measurement jig for the donor ECU case
docs/           design documents and vehicle schematics
  Schematics/   board schematics, BOMs and Gerbers — fab-ready
  Datasheets/   every part datasheet the decisions were made against
  1999-Ford-F150-4wd-5.42v/  Ford's own diagrams and service manual
  DonorECU/     the scrap PCM the connector and case come from
tools/          USB permission setup
```

### What gets committed, and why the repo is big

**~300 MB, and that is a deliberate trade.** The breakdown:

| | MB | |
|---|--:|---|
| Vendor datasheets | 79.8 | re-downloadable, but manufacturers pull obsolete parts |
| Ford service manual | 29.5 | **hard to re-source, and getting harder** |
| Ford scans — diagrams, connectors | 24.4 | same |
| Interactive BOMs | 22.9 | regenerable |
| Board design files | 11.9 | |
| STLs | 4.4 | regenerable from the `.scad` |
| **Source and docs — the actual project** | **1.5** | **0.9 %** |

**The thinking is 1.5 MB. Everything else is evidence.**

**Keep the evidence.** Design decisions across these documents are justified by
*"Ford's own sheet says X"*, and that phrase only means something if the sheet is
here. The archive has been re-read repeatedly to *correct* conclusions, not just
to support them — pin 64's function, the MAF's Kelvin wiring, the EPC resistance
that showed a suspect part was healthy. A 1999 service manual gets harder to find
every year.

**Do not commit regenerable artifacts.** Interactive BOMs, build outputs, export
by-products. The two BOM HTMLs predate this rule; they stay because removing them
now would not reclaim anything.

> **Why "not reclaim anything":** git keeps every blob ever committed. Deleting a
> file from the working tree shrinks the checkout, not the history. Only
> `git filter-repo` and a force-push reclaims space — and that rewrites shared
> history, invalidates the `power-v1-released` tag's SHA, and breaks every
> existing clone. **Not worth it at this size.**

**Revisit at ~700 MB.** GitHub soft-warns near 1 GB and hard-limits *individual
files* at 100 MB; the largest here is 30 MB. If it ever does need shrinking, the
lever is the **vendor datasheets at 45 %** — not the Ford material, which is the
least replaceable thing in the repository.

## Bench setup

[`docs/nucleo-setup.md`](docs/nucleo-setup.md) is a runbook for bringing a
Nucleo up from scratch, including the failures that actually cost time — the
ST-Link udev rule, programming the ELF rather than the `.bin`, and
`-Wl,-u,_printf_float`.

```bash
tools/setup-usb-permissions.sh      # debug probe access
```
