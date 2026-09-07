# Carrier board for the Nucleo-144

The Nucleo plugs into the carrier via the **ST morpho headers** (2 × 2×35,
0.1" pitch). The carrier holds everything else.

## Why this before a raw-chip board

- **The MCU section stops being a risk.** No flash, crystal, power sequencing or
  boot straps to get right on a first spin.
- **Programming and debug come free** — the on-board ST-Link, plus the USB VCP
  for console.
- **Ethernet comes free** — PHY, magnetics and RJ45 are already on the Nucleo.
- **The carrier can be iterated** without touching the MCU. Most first-board
  mistakes are in the analog and driver sections anyway.
- If the carrier proves out, a raw-F767 respin reuses the same schematic blocks.

## The rail tree changes

The earlier tree assumed a bare ESP32-P4 fed at 3.3 V. The Nucleo wants **5 V
into E5V** and makes its own 3.3 V, and it draws far more than the 30 mA the
old 5 V digital rail was sized for — roughly **150 mA, or ~300 mA with Ethernet
active**.

Revised:

```
 12 V ─[fuse]─[TVS]─[LTC4364-2]─► LM5155-Q1 SEPIC ──► 6.0 V main
                                                          │
        ┌─────────────────────────────────────────────────┤
   Buck → 5.0 V                                    LDO → 5.00 V VREF
   Nucleo E5V (~300 mA)                            ~25 mA, limited ~150 mA
   AD7606 AVDD, MAX9926, 74HCT541 (~80 mA)         harness-facing
   ~400 mA total
```

- **A buck, not an LDO, for the 5 V rail.** 400 mA across 1 V of headroom is
  0.4 W in a linear — survivable but needlessly warm in a sealed box.
- **VREF stays a linear from the 6 V rail.** 25 mA at 1 V is 25 mW, and the
  LDO's PSRR is what keeps switcher ripple off a reference every sensor is
  ratiometric to.
- **The 6 V main rail is unchanged**, so the SEPIC design and its calculator
  still apply.

### Powering the Nucleo — confirmed on the bench

**Feed E5V with 5 V. Do not use VIN.**

| Pin | Accepts | Notes |
|---|---|---|
| **E5V** | **5 V** | what the carrier's 5 V buck provides |
| VIN | **7–12 V** | its regulator will not start below ~7 V |
| U5V | — | ST-Link USB, the default |

Verified the hard way: **VIN fed with 5 V leaves the board dark.** The 6 V main
rail is also below VIN's minimum, so VIN is not an option for this design at
all — E5V is the only sensible feed, and the 5 V buck in the rail tree exists
precisely for it.

**The supply-select jumper must be moved** off its U5V default, or external
power on either pin does nothing. **[CONFIRM]** the designation on your board
revision from UM1974 rather than trusting a remembered reference number.

Note the ST-Link USB and the carrier's supply are independent: the board can be
powered from the carrier while the ST-Link USB is unplugged — it simply cannot
be programmed then, since SWD arrives over that same cable.

## Pins to avoid on the morpho headers

Some Nucleo-144 pins are already committed and must not be reused:

| Function | Pins |
|---|---|
| Ethernet RMII | PA1, PA2, PA7, PB13, PC1, PC4, PC5, PG11, PG13 |
| ST-Link VCP | PD8 (TX), PD9 (RX) |
| USB OTG FS | PA8–PA12 |
| LEDs | PB0, PB7, PB14 |
| User button | PC13 |

**[CONFIRM]** this list against the Nucleo-144 user manual before assigning —
it is from memory of the board family, not from the document, and a wrong entry
here is a wasted board spin.

Even after all of that, ~114 I/O against 37 needed leaves the assignment
unconstrained. That is the point of the platform change.

## Setting up a Nucleo from scratch

See [`nucleo-setup.md`](nucleo-setup.md) — the full runbook, including the one
thing that actually blocks a first-time bring-up (the ST-Link udev rule) and
the two quirks that waste time if you meet them unprepared.

## SD card — SPI4 on Port E

The Nucleo has no SD socket, so a module is wired to the morpho headers.

| SD module | Nucleo | Function |
|---|---|---|
| CLK / SCK | **PE2** | SPI4_SCK |
| MISO / DO | **PE5** | SPI4_MISO |
| MOSI / DI | **PE6** | SPI4_MOSI |
| CS | **PE4** | software chip select |
| 3V3 | 3V3 | **3.3 V modules only** |
| GND | GND | |

**Why Port E.** It carries no fixed function on the Nucleo-144 — no Ethernet,
no ST-Link, no USB, no LEDs — so nothing is displaced. It also leaves the
Arduino-header SPI alone, which matters because **PA7 is RMII_CRS_DV** on this
board and the conventional SPI1 trio is already broken by Ethernet.

**Why SPI rather than SDMMC.** Four signals instead of six, and the card holds
config and logs where bandwidth is not the constraint. SDMMC1 (PC8–PC12 + PD2)
stays available if high-rate logging later needs it.

**Bus speed starts at 4 MHz**, deliberately. Flying leads to an SD module are
not a controlled-impedance environment, and a card that enumerates at 4 MHz but
corrupts at 25 MHz is a miserable fault to chase. Raise it once the card is on
a PCB — same discipline as the AD7606's 1 MHz start.

The firmware distinguishes the two failure modes rather than reporting a
generic error:

| Report | Means |
|---|---|
| `card did not initialise (err 0x01…)` | nothing responded — wiring, CS, or 5 V module |
| `filesystem is unreadable` | card is there; wrong filesystem (FAT16/32 only) |

## AD7606 — SPI2, its own bus

| Signal | Nucleo | Note |
|---|---|---|
| SCK | **PB10** | SPI2_SCK |
| DOUTA | **PC2** | SPI2_MISO |
| *(MOSI)* | PC3 | unused in hardware mode; wired for a later software-mode part |
| CS | **PB12** | |
| CONVST | **PB11** | tie CONVSTA and CONVSTB together |
| BUSY | **PB1** | |
| RESET | **PB2** | active high — must sit low to run |
| FRSTDATA | **PB15** | optional |
| OS0 / OS1 / OS2 | **PB3 / PB4 / PB5** | oversampling off for now |
| RANGE | **PB6** | ±10 V high, ±5 V low |

**A separate bus from the SD card**, which is on SPI4. The ADC is sampled at
engine rate and must never wait behind a card write — sharing a bus would put
filesystem latency directly into the sampling interval.

Avoids PB0/PB7/PB14 (LEDs) and PB13 (Ethernet RMII_TXD1).

**The SPI mode must be re-established on this host.** The same AD7606 needed
MODE0 on the Teensy and MODE2 on the ESP32-P4 — it is a property of the
host/ADC pairing, not of the ADC. The driver's default is inherited from the P4
and is a placeholder until swept. A wrong CPHA reads **exactly 2× high while
looking perfectly stable**, which is the failure mode that cost time on the P4
and would cost it again.

## Using an external ST-Link

The Nucleo's on-board ST-Link failed during bring-up: first dropping characters
on its VCP, then refusing to enumerate at all. The same cable and the same USB
port enumerated a Teensy without trouble, which isolates it to the ST-Link.

To drive the on-board MCU from an external ST-Link:

1. **Remove both CN2 jumpers** — these connect the on-board ST-Link to the
   target MCU. Leaving them in puts two debuggers on one SWD bus.
2. Connect the external probe to **SWDIO (PA13)**, **SWCLK (PA14)**, **GND**,
   and **NRST**.
3. `upload_protocol = stlink` is unchanged — PlatformIO does not care which
   ST-Link it finds.

**[CONFIRM]** the CN2 designation against UM1974 for your board revision.

**Bring SWD out to a header on the carrier.** Four pins, and it means a failed
on-board debugger never blocks the project again. This session is the argument
for it.

## Order of work

1. ~~M0 on the Nucleo~~ **Done 2026-09-07.** Device ID 0x451 rev 0x1001,
   216 MHz, 2048 KB flash, all read from the chip's own registers.

   Two bench notes worth keeping: the ST-Link needed a **udev rule** before
   OpenOCD could claim it (`LIBUSB_ERROR_ACCESS`), and its **VCP and SWD share
   one USB device** — so resetting over SWD disconnects the console. The
   firmware reprints its identity on receiving `i`, which sidesteps that. The
   VCP also drops the occasional byte on a long burst at 115200; fine for a
   console, not something to base datalogging on.
2. **Pin map** — assign the 37 signals to real morpho pins, avoiding the list
   above.
3. **AD7606 on flying leads** — port the driver, **re-sweep the SPI mode**, and
   verify against the same known signals used on the P4.
4. **MAX9926 + crank sync** — the milestone everything else waits on.
5. **Carrier schematic**, once the interfaces are proven rather than assumed.

Steps 1–4 need no PCB at all.
