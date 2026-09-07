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

**[CONFIRM]** the Nucleo's E5V jumper position — feeding E5V externally requires
the supply-select jumper moved off its default (ST-Link 5 V). Getting this wrong
either back-feeds the ST-Link or leaves the board unpowered.

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
