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
| Storage | SD card, SDMMC | ✅ |
| Connector | EEC-V 104-pin, rusEFI footprint | ✅ |

That is a complete engine controller. Nothing in it is unresolved.

## Deferred — with footprints where they are cheap

| Deferred | Why it can wait | Fit a footprint? |
|---|---|---|
| **Alternator control** | The OEM alternator **self-regulates**. This is an addition, not a replacement — the truck charges fine without it | no |
| **ADR4525 precision reference** | Only needed *for* alternator control. The AD7606's internal reference is fine for everything else | **yes** — REF SELECT strap + footprint |
| **INA238-Q1 current monitor** | Diagnostics. The engine runs without knowing its own current draw | **yes** — I²C, two pads |
| **Knock sensing** | Run conservative timing until it works. The engine runs; it just cannot use all its timing | **yes** — one ADC channel routed |
| **J1850 / SCP** | Needed for the cluster and OBD-II, not to run. Tach and speedo can be discrete outputs | **yes** — it is only three GPIOs and a transceiver |
| **Second MAX9926** | TSS does not exist on the 4R70W, and OSS belongs to the transmission node | no |
| **Transmission control** | Separate node over CAN, as the MegaSquirt build did | no |
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
