# v1 scope — what gets built

**Goal: an engine that runs.** Everything else waits.

## On the board

| Block | Parts | Decided |
|---|---|---|
| Input protection | LTC4364-2 + pass FET + ideal-diode FET, fuse, TVS | ✅ |
| Main supply | LM5155-Q1 SEPIC → 6.0 V / 3 A, 2.2 MHz, 80 V devices | ✅ |
| Rails | buck → 3.3 V; LDOs → 5 V digital, 5 V analog, 5.00 V VREF | ✅ |
| MCU | ESP32-P4 (v3.x) + ESP32-C6-MINI-1 module + flash + crystal | ✅ |
| Analog in | AD7606, 8 channels, SPI_MODE2 | ✅ |
| Crank/cam | **1 × MAX9926**, Mode A2 | ✅ |
| Ignition | 8 × ISL9V3040 + 74HCT541 + 470 Ω gates | ✅ |
| Injection | 8 × ZXMS6005DGQ, direct from GPIO | ✅ |
| Slow I/O | 2 × MCP23S17 | ✅ |
| **Transmission I/O** | TCC + EPC PWM (native), SS1/SS2/CSS + 4× TR (expander), TFT (analog), OSS (VR) | ✅ |
| Storage | SD card, SDMMC | ✅ |
| Connector | EEC-V 104-pin, rusEFI footprint | ✅ |

That is a complete engine **and transmission** controller. Nothing in it is
unresolved.

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
| SS1, SS2, CSS | MCP23S17 outputs | free — expander already present |
| TR sensor, 4-bit | MCP23S17 inputs | free |
| TFT | analog channel | free |

**One board does both.** Only TCC and EPC cost native pins, and both were
already in the budget. The solenoids and the four TR inputs are slow enough to
live on the expander chain that is on the board anyway.

Splitting into two boards would add a CAN bus, a second MCU, a second power
supply and a second enclosure to solve a problem that no longer exists.

The dual-core P4 still gives the isolation that mattered: hard real-time spark
and injection on one core, transmission and everything else on the other. That
was always the point of the split, and it does not require two chips.

## Deferred — with footprints where they are cheap

| Deferred | Why it can wait | Fit a footprint? |
|---|---|---|
| **Alternator control** | The OEM alternator **self-regulates**. This is an addition, not a replacement — the truck charges fine without it | no |
| **ADR4525 precision reference** | Only needed *for* alternator control. The AD7606's internal reference is fine for everything else | **yes** — REF SELECT strap + footprint |
| **INA238-Q1 current monitor** | Diagnostics. The engine runs without knowing its own current draw | **yes** — I²C, two pads |
| **Knock sensing** | Run conservative timing until it works. The engine runs; it just cannot use all its timing | **yes** — one ADC channel routed |
| **J1850 / SCP** | Needed for the cluster and OBD-II, not to run. Tach and speedo can be discrete outputs | **yes** — it is only three GPIOs and a transceiver |
| **Second MAX9926** | TSS does not exist on the 4R70W, so only CKP, CMP and OSS need conditioning — three channels, and one dual package covers two. **[CONFIRM]** whether CMP is Hall; if so, one package does all of it | maybe — see below |
| **Transmission *software*** | The hardware is on the v1 board. The control logic comes after the engine runs | n/a |
| **Watchdog on `OE2`** | Real protection, but strap `OE2` low for v1 | **yes** |
| **Battery temperature** | Only matters for charging control | no |

Footprints for the "yes" rows cost almost nothing and save a respin. Everything
else stays off the board entirely.

## What actually remains open

Two things, and both are measurements rather than decisions:

1. **Coil primary inductance** — sets the dwell limit against the ISL9V3040's
   300 mJ rating. Measure one coil.
2. **CMP sensor type** — Hall or VR. Decides whether it uses a MAX9926 channel
   or connects nearly directly. One look at the connector.

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
