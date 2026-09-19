# v1 scope — what gets built

**Goal: an engine that runs.** Everything else waits.

## Form factor: carrier board, Nucleo plugs in

v1 is a **carrier for the Nucleo-144**, not a raw-chip board — see
[`carrier-board.md`](carrier-board.md). The MCU section stops being a risk, and
ST-Link, USB console and Ethernet all come for free.

## On the board

| Block | Parts | Decided |
|---|---|---|
| Input protection | LTC4364-2 + pass FET + ideal-diode FET, fuse, TVS — on **VPWR** (pins 71/97, key-switched) | ✅ |
| **Always-on feed** | **Dedicated battery lead** (2 A fuse at the post) → SMDJ43A + D3 + **470 Ω** + **SMBJ30A**, joining the **protected rail** downstream of the ideal diode. Leaves the LTC4364 unpowered when parked — **184 µA**, not 944. Battery-sense divider **180 k/30 k** sits upstream, reading true battery — [`always-on-domain.md`](always-on-domain.md#the-kapwr-feed-where-the-constant-12-v-comes-from) | ✅ |
| Main supply | **MAX25239AFFA buck-boost → 5.0 V**, 2.1 MHz, spread spectrum, 2.2 µH | ✅ |
| Rails | **TLV62085 buck → 3.3 V** from 5 V; ADC reference MAX6070AAUT25 2.5 V, gated | ✅ |
| **VREF output chain** | **TPS2H160B-Q1** dual switch → **LM74700-Q1** + **DMN6040SVTQ-7** ideal diode → **SMAJ24CA** TVS, per feed | ✅ |
| **VREF supply** | **NCV8772CDT504RKG** 5.00 V LDO off the **LTC4364 protected rail** — not the 5 V switcher, which has no headroom and is spread-spectrum. [`vref-supply.md`](vref-supply.md) | ✅ |
| MCU | **STM32F767ZI** — see [`platform-decision.md`](platform-decision.md) | ✅ |
| Analog in | **ADS8588H** — 8 ch, 16-bit, 500 kSPS simultaneous, ±10 V, 9 kV clamp. Bench: Tokmas AD7606BSTZ, same LQFP-64 | ✅ |
| Crank/cam/OSS/TC | **2 × MAX9926**, Mode A2 — CKP, CMP, OSS, **transfer case speed**. No spare | ✅ |
| Ignition | 8 × ISL9V3040 + 74HCT541 + 470 Ω gates | ✅ |
| Injection | 8 × ZXMS6005DGQ, direct from GPIO | ✅ |
| Slow I/O | ~~MCP23S17 expander chain~~ — **dropped. Every signal is native.** 76 of ~114 pins, 36 spare. Gates still buffered by a third 74HCT541 at 5 V, which was always a voltage question — [`review-expander-chain.md`](review-expander-chain.md) | ✅ |
| **Relay / lamp drivers** | **TBD62083AFNG** — 8ch DMOS sink, clamps built in | ✅ |
| **PWM gate buffer** | 2nd **74HCT541** at 5 V — EVAP, EGR, TCC, EPC, **IAC** take native timer pins at 3.3 V (5 of 8 used) | ✅ |
| **Solenoid / heater drivers** | **NCV8405ASTT1G** ×**13** — self-protected low-side, drain-sense diagnosis. ~~×10~~ predated the canister vent solenoid, IAC and VSS | ✅ |
| **VREF output stage** | **TPS2H160B-Q1** — dual high-side, 250 mA limit, 40 V, current sense | ✅ |
| **Transmission I/O** | TCC + EPC PWM (native pins; TCC **NCV8405A**, EPC **NCV8408B** DPAK, ≥200 Hz), SS1/SS2/CSS + 4× TR (expander), TFT (analog), OSS (VR) | ✅ |
| Storage | SD card, SDMMC | ✅ |
| **SCP / J1850 PWM** | **DRV8837** H-bridge differential TX + **TLV7031** comparator RX, **4 GPIOs** (incl. `nSLEEP`), 5 V | ✅ |
| Connector | EEC-V 104-pin, rusEFI footprint | ✅ |

That is a complete engine **and transmission** controller. Nothing in it is
unresolved.

**The wiring view is [`Schematics/schematic-ecu-v1.txt`](Schematics/schematic-ecu-v1.txt)** —
block by block, with the document behind each value cited inline. **78 native
pins of ~114, 34 spare.**

### Correction: there is no separate transmission node

Earlier notes referred to a "transmission node" — a second board over CAN, as
the MegaSquirt build used with an MS3Pro and a MicroSquirt. **That was an
artifact of the Waveshare carrier's 25 usable pins, and moving to a raw
ESP32-P4 removed the need.**

The 37-pin assignment in [`custom-board.md`](custom-board.md) already includes
everything the 4R70W needs:

| 4R70W function | Where it lives | Cost |
|---|---|---|
| TCC | GPIO10, PWM | native pin, already allocated |
| EPC | GPIO11, PWM | native pin, already allocated |
| OSS | GPIO22, via MAX9926 | native pin, already allocated |
| SS1, SS2, CSS | native pins via 74HCT541 #3 | 3 of the 36 spare |
| TR sensor, 4-bit | native inputs, edge interrupts | 4 of the 36 spare |
| TFT | analog channel | free |

**One board does both.** Only TCC and EPC cost native pins, and both were
already in the budget. ~~The solenoids and the four TR inputs are slow enough to
live on the expander chain that is on the board anyway.~~ **The chain is gone —
they take native pins, 7 of the 36 spare.**

Splitting into two boards would add a CAN bus, a second MCU, a second power
supply and a second enclosure to solve a problem that no longer exists.

The dual-core P4 still gives the isolation that mattered: hard real-time spark
and injection on one core, transmission and everything else on the other. That
was always the point of the split, and it does not require two chips.

## Deferred — with footprints where they are cheap

| Deferred | Why it can wait | Fit a footprint? |
|---|---|---|
| **Wi-Fi (ESP32-C6)** | **Dropped, not deferred.** An always-on radio on an engine controller is a remote attack surface with a path to code execution via OTA. Ethernet does the job and needs physical access | **no** |
| **Alternator control** | The OEM alternator **self-regulates**. This is an addition, not a replacement — the truck charges fine without it | no |
| **ADR4525 precision reference** | Only needed *for* alternator control. The AD7606's internal reference is fine for everything else | **yes** — REF SELECT strap + footprint |
| **INA238-Q1 current monitor** | Diagnostics. The engine runs without knowing its own current draw | **yes** — I²C, two pads |
| **Knock sensing** | Run conservative timing until it works. The engine runs; it just cannot use all its timing | **yes** — one ADC channel routed |
| ~~**J1850 / SCP**~~ | **Moved onto the board** — see below | n/a |

| **Transmission *software*** | The hardware is on the v1 board. The control logic comes after the engine runs | n/a |
| **Watchdog on `OE2`** | Real protection, but strap `OE2` low for v1. **Quantified on the measured 1.5 mH / 0.5 Ω:** a stuck-on coil stores **622 mJ, 2.07× the IGBT's rating**, reached after 3.56 ms — ~2.7× nominal dwell — [`output-drivers.md`](output-drivers.md) | **yes** |
| **Battery temperature** | Only matters for charging control | no |

### Why J1850 / SCP moved onto the board

It was deferred on the grounds that *"tach and speedo can be discrete outputs."*
Ford's cluster diagrams show that is **false**: the cluster's only connection to
the PCM is SCP, and neither the tachometer, the speedometer nor the MIL has a
discrete PCM pin. See
[`1999-Ford-F150-4wd-5.42v/schematic-findings.md`](1999-Ford-F150-4wd-5.42v/schematic-findings.md)
§10.

So the choice was never "SCP or discrete wires". It was **SCP or no dash at
all** — no tachometer, no speedometer, no check-engine lamp.

Three things make including it cheap rather than a scope increase:

- **The front end is already designed.** DRV8837 H-bridge driving TX_P/TX_N
  complementary, TLV7031 comparator across PWM+/PWM−, 5 V, no boost rail. See
  [`f150-1999-target.md`](f150-1999-target.md) §5.3.
- **The pins were already budgeted** — though the count was wrong: `nSLEEP` makes
  it **four**, not three. See [`review-scp-chain.md`](review-scp-chain.md) §1.
  Against ~77 spare it changes nothing.
- **Phase 0 exercises this exact front end before the board exists.** Listening
  on the DLC with the OEM PCM still installed is the *first* thing on the plan,
  so by fabrication the design will have been proven against this truck rather
  than against a datasheet.

That last point matters because the reference design carries its own warning —
*"the PWM side is experimental and expects per-vehicle tuning"* — and Phase 0 is
exactly where that tuning happens. Deferring the hardware would mean doing
Phase 0 on a breadboard and then trusting the transfer.

**One connection note:** the ECU reaches the bus through **EEC-V pins 15 and 16**
(SCP− PNK/LT BLU, SCP+ TAN/ORG), which are circuits 915 and 914 — the same wires
as DLC pins 10 and 2. One connection serves both the cluster and a scan tool.

> **[CONFIRM]** automotive qualification for both parts. Everything else in the
> signal path is AEC-Q; the DRV8837 has a Q1 variant, the TLV7031 wants checking.

Footprints for the "yes" rows cost almost nothing and save a respin. Everything
else stays off the board entirely.

## Pin budget is no longer a constraint

Moving to the STM32F767ZI replaces the 40-pin ESP32-P4 budget with **~114 I/O
against 37 needed**. The levers previously held in reserve — semi-sequential
injection, 1-bit SDMMC, tach/VSS over SCP — are all unnecessary. Full
sequential injection, full coil-on-plug, 4-bit SD, discrete cluster outputs,
and room left for a newer vehicle.

The section below is retained as the record of why a second CPU was never
needed even on the tighter budget.

## Does it need a second CPU? No.

Counted by [`../hardware/pinmap.py`](../hardware/pinmap.py) rather than by hand:

```
GPIOs on the P4                 55
Committed (C6, SD, UART, strap) 15
Available                       40
Core (engine + transmission)    34
J1850, routed for later          3
ASSIGNED                        37
SPARE                            3     <- GPIO42, 43, 44
```

**One CPU, one board, engine and transmission together.** The core build needs
**34** pins of the 37 available, and J1850 fits in the remaining three.

The SD card runs **1-bit SDMMC**, which frees GPIO42–44. It carries config and
logs only, so 4-bit bandwidth buys nothing, and three spare pins turn a
zero-margin layout into one that can absorb a mistake found at assembly.

Still in reserve: semi-sequential injection (+4) and tach/VSS over SCP (+2).

## What actually remains open

**Not the specification — that is complete.** What remains is *building* it: the
carrier board has never been captured as a schematic or laid out. The two
measurements this section used to list are both closed.

1. ~~**Coil primary inductance**~~ — **MEASURED: 1.5 mH.** The 300 mJ rating is
   reached at exactly **20.0 A**; a healthy 80 mJ spark needs **10.3 A**, so the
   operating point sits **3.75× under**. The
   ISL9V3040 is comfortably right. See
   [`output-drivers.md`](output-drivers.md#-measured-l--148-mh-lcr-meter-2026-09-18).
   **Primary resistance measured too: 0.5 Ω** (DCR, good leads — a first 2-wire
   reading of 1.8 Ω was the leads). **Dwell is 1.33 ms at 14.4 V rising to
   2.56 ms at 9 V cranking**, a 1.9× span that makes the dwell-vs-voltage table
   mandatory. Overlap is irrelevant — it starts above 11 300 rpm.
   **Both measurements are closed.**

~~CMP sensor type~~ **Resolved: VR, single-ended.** Two MAX9926 packages,
three channels used, one spare.

Everything else in `docs/` is decided or deliberately deferred.

## Firmware, in the same spirit

M0–M2 are done and verified on hardware. M3–M5 are written and unit-tested. The
remaining path to a running engine is:

1. **M3 electrical** — MAX9926 on the bench, verify crank sync against a signal
   generator.
2. **M4/M5 electrical** — cam sync, then spark on a scope.
3. **M6** — injection.
4. **First start.**

Web UI, MQTT, logging, closed-loop O2, knock and SCP all come after the engine
runs, not before.
