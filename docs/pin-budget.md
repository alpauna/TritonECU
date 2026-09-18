# Pin budget

Two questions, different answers: does the **Waveshare board** fit a full ECU
(no), and does the **ESP32-P4 chip** (yes, comfortably).

## The STM32F767ZI map — every signal native

**The MCP23S17 expander chain is dropped.** It existed because the ESP32-P4 had
40 GPIOs and needed 39; on ~114 the split stops being necessary. See
[`review-expander-chain.md`](review-expander-chain.md), superseded header.

This table carries the **driven by** column the old one was criticised for
lacking — the omission that let TCC, EPC, IAC and the tach/VSS outputs be
counted as handled when only a pin had been reserved.

| Function | Pins | Driven by |
|---|--:|---|
| Coil drivers, COP | 8 | ISL9V3040 via 74HCT541 #1 |
| Injector drivers | 8 | ZXMS6005DGQ, direct |
| VR channels — CKP, CMP, OSS, TSS | 4 | 2 × MAX9926 |
| ADS8588H: SCK, MISO, CS, CONVST, BUSY | 5 | direct, 3.3 V |
| J1850: TX_P, TX_N, RX, nSLEEP | 4 | DRV8837 + TLV7031 |
| TCC, EPC | 2 | NCV8405A / NCV8408B via 74HCT541 #2 |
| EVAP purge, EGR regulator | 2 | via 74HCT541 #2 |
| IAC | 1 | via 74HCT541 #2 |
| **VSS out** | 1 | **NCV8405A #13** via 74HCT541 #2, open-drain — EEC-V pin 68, circuit 679 |
| **TACH out** — reserved | 1 | **none, deliberately.** 3.3 V to a test header; does not reach the connector |
| **SPEED out** — reserved | 1 | same. A clean square wave for a gauge — **not** the OEM VSS above |
| I²C: SDA, SCL | 2 | — |
| **subtotal, as previously budgeted** | **38** | *(39 less the expander CS)* |
| Relays — fuel pump, fan 1, fan 2, A/C clutch | 4 | TBD62083AFNG, direct at 3.3 V |
| NCV8405A — IMCC, HO2S ×4, SS1, SS2, CSS | 8 | **74HCT541 #3 at 5 V** |
| ADS8588H static — RESET, FRSTDATA, OS0–2, RANGE | 6 | direct, 3.3 V — now legal |
| MAX25239 `SYNC` | 1 | direct, with a pulldown |
| Inputs — TR ×4, brake, A/C pressure, 4×4 low | 7 | conditioned; **edge interrupts, not polled** |
| VREF — EN, IN1, IN2, DIAG_EN, SEL, FAULT | 6 | TPS2H160B-Q1 |
| Watchdog kick | 1 | — |
| 74HCT541 #2 `OE` | 1 | software-releasable |
| Supervisory — `SHDN#`, `FLT#`, `PGOOD`, `ALERT` | 4 | — |
| **subtotal, formerly on the expander** | **38** | |
| **TOTAL** | **77** | of ~114. **35 spare** after SWD |

74HCT541 **#3**'s `OE` costs no pin — it shares the watchdog net that drives
`OE2` on #1.

Two things this table does *not* say are now settled by dropping the chain:
there is no poll interval to state, because the inputs are edge interrupts; and
there is no expander `RESET` to wire, because an STM32 GPIO goes high-Z on reset
and both driver families default off unaided.

---

## Historical — the ESP32-P4 budget

Everything below was written against the P4's 40 GPIOs and is kept for the
reasoning, not the numbers. The expander split it describes no longer exists.

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
| J1850: TX_P, TX_N, RX, **nSLEEP** | **4** | bit-timed at 41.6 kbps. nSLEEP releases the bus — [`review-scp-chain.md`](review-scp-chain.md) §1 |
| TCC, EPC | **2** | PWM |
| **EVAP purge, EGR regulator** | **2** | **PWM — see the correction below** |
| IAC | **1** | PWM |
| Tach out, VSS out | **2** | frequency outputs |
| I2C: SDA, SCL | **2** | |
| **Total** | **39** | |

On the expander and costing nothing extra: fuel pump relay, ~~EVAP purge, EGR
regulator,~~ IMCC, cooling fan, A/C clutch, MIL, HO2S heaters, SS1/SS2/CSS, the
four TR inputs, brake and A/C switches, the AD7606's RESET / FRSTDATA /
OS0-2 / RANGE, and the **MAX25239 `SYNC`** skip/FPWM select.

> `SYNC` changes only at sleep entry and exit, so it is static in the sense this
> split uses and needs no native pin. **Fit a pulldown**: at cold power-up the
> expander's outputs are high-Z, and the safe default is skip mode.
> [`power-supply.md`](power-supply.md#decided-keep-the-max25239--but-sync-is-a-gpio-not-a-strap)

> **Correction.** EVAP purge and EGR regulator are **PWM** loads and cannot
> live on an SPI expander — every edge would be a bus transaction. They take
> native timer pins. The split above was made by *current and criticality*,
> and PWM is neither, which is how they landed here. See
> [`review-solenoid-chain.md`](review-solenoid-chain.md) §1.

> **This table allocates pins, not drivers — and three loads were missed because
> it reads like both.** TCC, EPC and IAC each appeared here as `N | PWM` and
> were taken as handled when only a pin had been reserved. The audit is in
> [`review-ignition-injection.md`](review-ignition-injection.md), and it found a
> fourth still open: **tach and VSS outputs have no driver assigned.**
>
> **Whatever replaces this table for the STM32 should carry a "driven by" column.**

## The Waveshare board is short by 11

It breaks out **27** GPIOs, of which GPIO24/25 are the USB D−/D+ pair, leaving
**25 usable**. Against 39, that is **14 short**.

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
