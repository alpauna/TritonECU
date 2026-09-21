# SD card page — review of V1.0

Subject: [`SD-schematic-v1.0.png`](SD-schematic-v1.0.png), *SCP Scanner*, page 2
of 2, dated 2026-09-21. Socket **Molex 472192001**, SPI mode.

**The shape is right**: SPI-mode wiring, pull-ups present, VDD decoupled with
100 nF + 10 µF, shell pins grounded. Five notes, ordered by how much they matter.

## 1. ⚠ CS has no pull-up, and CLK has one it does not need

This is the one worth changing. The pull-up bank is on **DAT2, MOSI, SCLK,
MISO** — but **SPCS (pin 2, CD/DAT3) is bare**.

CS is the pin the SD specification actually asks for a pull-up on, and for a
reason that bites exactly this build: **the card samples CS at power-up to decide
between SD mode and SPI mode.** Between the rail coming up and the Pico
configuring its GPIOs, that line is floating — the same class of problem already
solved on GPS `ON/OFF` and the DRV8837's `nSLEEP`, and solved the same way.

**SCLK, by contrast, is driven by the host and never floats meaningfully.** A
pull-up there is harmless and does nothing.

**Fix:** move R5 from SCLK to SPCS. No part-count change.

### Do DAT1 and DAT2 need their 10 k pull-ups?

**No — not in SPI mode.** The protocol touches only CS, CMD (MOSI), CLK and DAT0
(MISO). DAT1 and DAT2 are unused, and the majority of microSD-SPI designs leave
them unconnected with no pull-ups at all.

Keep them anyway, for two reasons that cost nothing:

- **No running cost.** A pull-up only draws current if something pulls the line
  low. Against a high-Z card pin that is zero — two resistors and no power.
- **They become required if 4-bit SD mode is ever used**, where all DAT lines
  want pull-ups. Cheap future-proofing rather than clutter.

So the pull-up bank is not wrong, it is just aimed one pin short: **DAT1/DAT2
optional, CS mandatory, and CS is the one missing.**

| Line | Pull-up? | Why |
|---|---|---|
| **CS / SPCS** | **yes — missing** | Card samples it at power-up to choose SPI vs SD mode |
| MISO / DAT0 | yes ✔ | Open-drain during some card states |
| MOSI / CMD | yes ✔ | Recommended |
| DAT1, DAT2 | **optional** | Unused in SPI mode — see below |
| SCLK | **not needed** | Host-driven |

## 2. Pin 8 is labelled DAT2 — it is DAT1

Pins **1 and 8 are both on the `DAT2` net**. Pin 1 is DAT2; **pin 8 is DAT1**.

Harmless in SPI mode — both are unused and both end up pulled high through R3 —
so the board will work. It is wrong the moment anyone tries 4-bit SD mode, and it
is the kind of copy-paste slip that survives into three later revisions because
nothing ever fails because of it.

## 3. Check what pins 9–12 actually are

All four are tied to GND. On many microSD sockets those are shell tabs, in which
case grounding them is correct. On others **one pair is a card-detect switch**,
and grounding it throws the detection away.

**[CONFIRM]** against the Molex 472192001 drawing. If a CD switch exists, it is
worth a GPIO — "no card" is otherwise indistinguishable from "card present but
every write failing", and on a capture rig that difference is the whole evening.

## 4. The 3V3 rail is tighter than it looks

Everything hangs off the Pico's `3V3(OUT)`:

| Load | Typ | Peak |
|---|--:|--:|
| RP2040 + Pico | 25 mA | 40 mA |
| ATGM336H V<sub>CC</sub> | 26 mA | **100 mA** |
| Active antenna via `VCC_RF` | 15 mA | 20 mA |
| microSD, idle → **write burst** | 5 mA | **100 mA** |
| TLV7031 | ~0 | 1 mA |
| **Total** | **71 mA** | **261 mA** |

Those peaks do not all coincide — but **GPS acquisition during an SD write is an
ordinary combination, not a contrived one**, and that pair alone is ~200 mA.

- **Verify the Pico's 3V3(OUT) budget** against the RT6150's rating before
  trusting it, rather than assuming the rail is free.
- **Keep C9 local to the socket**, and consider raising it. A sagging rail during
  a write shows up as corrupted files *or* as a GPS that quietly resets — and the
  second one is diagnosed as "the antenna is bad" for a week.

## 5. Optional: series damping on CLK and MOSI

22–33 Ω in series with SCLK and MOSI costs nothing and tames ringing if the
traces are long or the card is on a flying lead. Not needed for a short
board-level run; worth having footprints for.

## Summary

| # | Item | Action |
|--:|---|---|
| 1 | CS pull-up missing, SCLK pull-up redundant | **Move R5 to SPCS** |
| 2 | Pin 8 on the DAT2 net | Relabel to DAT1 |
| 3 | Pins 9–12 all grounded | Confirm shell vs card-detect |
| 4 | 3V3 peak ~261 mA | Verify budget, keep bulk local |
| 5 | No series damping | Optional footprints |
