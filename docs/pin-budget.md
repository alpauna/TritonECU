# Pin budget

Two questions, different answers: does the **Waveshare board** fit a full ECU
(no), and does the **ESP32-P4 chip** (yes, comfortably).

## What a full single-node ECU needs

Native pins only. Anything that can live on the MCP23S17 expander chain is
excluded, because it costs nothing beyond the one chip-select already counted.

| Function | Pins | Why it must be native |
|---|---|---|
| Coil drivers, COP | **8** | hardware-timed to sub-degree accuracy |
| Injector drivers | **8** | same |
| VR channels — CKP, CMP, OSS, TSS | **4** | edge interrupts, 2 × MAX9926 |
| AD7606: SCK, MISO, CS, CONVST, BUSY | **5** | the other six pins are static, on the expander |
| MCP23S17 chain chip-select | **1** | shares the SPI bus |
| J1850: TX_P, TX_N, RX | **3** | bit-timed at 41.6 kbps |
| TCC, EPC | **2** | PWM |
| IAC | **1** | PWM |
| Tach out, VSS out | **2** | frequency outputs |
| I2C: SDA, SCL | **2** | |
| **Total** | **36** | |

On the expander and costing nothing extra: fuel pump relay, EVAP purge, EGR
regulator, IMCC, cooling fan, A/C clutch, MIL, HO2S heaters, SS1/SS2/CSS, the
four TR inputs, brake and A/C switches, and the AD7606's RESET / FRSTDATA /
OS0-2 / RANGE.

## The Waveshare board is short by 11

It breaks out **27** GPIOs, of which GPIO24/25 are the USB D−/D+ pair, leaving
**25 usable**. Against 36, that is **11 short**.

The rest of the chip's pins are committed on the carrier to things a truck has
no use for:

| GPIO | Committed to | Wanted in an ECU? |
|---|---|---|
| 9–13 | I2S audio codec, microphone | no |
| 14–19 | **SDIO to the ESP32-C6** — Wi-Fi/BLE | **yes, keep** |
| 35–38 | boot strapping, UART0 | yes, keep |
| 39–45 | SD card, SDMMC slot 0 | yes, keep |
| 53, 54 | speaker amp enable, C6 reset | 54 yes, 53 no |
| — | MIPI-DSI, MIPI-CSI (not on the header at all) | no |

Splitting engine and transmission across two boards does not rescue it either.
The engine node alone still wants roughly **29** — the eight coils and eight
injectors dominate, and they cannot be moved.

## The chip is not short — the carrier is

The ESP32-P4 has **GPIO0–54, 55 pins**. On a custom carrier, keeping only what
an ECU actually needs:

| Committed | Pins |
|---|---|
| SDIO to the C6, plus its reset | 7 |
| SD card on SDMMC | 7 |
| UART0 for console and flashing | 2 |
| Boot strapping | 2 |
| **Total committed** | **18** |

That leaves roughly **37 free** against the 36 required — and dropping USB, or
putting the SD card on SPI instead of SDMMC, adds more headroom.

**[CONFIRM]** the exact free count against the ESP32-P4 datasheet before
committing a layout, particularly whether any GPIO in that range is consumed by
flash on the NRW32 package.

## Recommendation

**Bench on the Waveshare board with a reduced set. Build the truck ECU on a
bare ESP32-P4.**

A reduced bench set proves everything except scale, and fits comfortably:

| Function | Pins |
|---|---|
| CKP + CMP | 2 |
| AD7606 SPI + control | 5 |
| Expander CS | 1 |
| **Two** coils, **two** injectors | 4 |
| J1850 | 3 |
| Spare | 10 |

Two coils and two injectors on a scope prove dwell, advance, pulse width and
phasing exactly as well as eight do — the eighth channel demonstrates nothing
the second has not already. Everything in M3 to M6 can be closed this way.

What genuinely needs the full complement is running an engine, and that wants a
custom board regardless: coil and injector drivers, VREF supply, the MAX9926s,
input protection and the EEC-V connector are all going on a PCB anyway. Putting
a bare P4 module on that same board removes the pin constraint permanently and
costs very little extra — the Waveshare carrier's MIPI, camera and audio
hardware is dead weight in a truck.
