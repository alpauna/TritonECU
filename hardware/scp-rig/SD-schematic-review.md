# SD card page — review

Subject: [`SD-schematic-v1.1.png`](SD-schematic-v1.1.png) (was
[`v1.0`](SD-schematic-v1.0.png)), *SCP Scanner*, page 2 of 2. Socket **Molex
472192001**, SPI mode.

## ✅ V1.1 — all three findings fixed, verified against the drawing

| | Was | Now |
|---|---|---|
| **CS / SPCS pull-up** | missing | **R6, 10 kΩ** ✔ |
| **SCLK pull-up** | present, unnecessary | **removed** ✔ |
| **Pin 8** | on the `DAT2` net | **its own `DAT1` net, R3 10 kΩ** ✔ |

Pull-up bank now reads **DAT1, DAT2, MOSI, SPCS, MISO** — five lines, and
notably **not SCLK**. Card pins map cleanly: 1 DAT2, 2 SPCS, 3 MOSI, 4 VDD,
5 SCLK, 6 GND, 7 MISO, 8 DAT1. Decoupling unchanged at 100 nF + 10 µF.

Reference designators landed differently from the suggestion above (R3 is DAT1
rather than DAT2, and so on) — irrelevant, the **nets** are what matter and they
are right.

**One item remains open**, and it is not a schematic error: the 3V3 budget.

---

## The original findings, kept for the reasoning

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

## 2. Pin 8 is labelled DAT2 — it is DAT1, and splitting it needs R7

Pins **1 and 8 are both on the `DAT2` net**. Pin 1 is DAT2; **pin 8 is DAT1**.

Harmless in SPI mode — both are unused and both end up pulled high through R3 —
so the board will work. It is wrong the moment anyone tries 4-bit SD mode, and it
is the kind of copy-paste slip that survives into three later revisions because
nothing ever fails because of it.

**Splitting them orphans pin 8 from R3**, so DAT1 needs its own pull-up:
**R7, 10 kΩ to 3V3**. Otherwise the relabel quietly leaves DAT1 floating, which
is worse than the shared net it replaced — and for the same reason the pull-ups
were kept at all: 4-bit mode wants every DAT line held.

### Pull-up allocation, as fixed

| R | 10 kΩ to 3V3 | Card pin | |
|---|---|---|---|
| R3 | DAT2 | 1 | unchanged |
| **R5** | **SPCS / CS** | **2** | **moved off SCLK** |
| R4 | MOSI / CMD | 3 | unchanged |
| R6 | MISO / DAT0 | 7 | unchanged |
| **R7** | **DAT1** | **8** | **new** |
| — | SCLK | 5 | **no pull-up** — host-driven |

Net change: **one resistor added**, one moved, one deleted from SCLK.

## 3. ✅ Pins 9–12 are shell grounds — there is no card detect

Resolved from the Molex drawing
[`Molex-472192001-drawing.pdf`](Molex-472192001-drawing.pdf) (`SD-47219-001`,
*TFR reader, hinge type*). Its pin table is unambiguous:

| | | | |
|---|---|---|---|
| PIN1 DAT2 | PIN2 CD/DAT3 | PIN3 CMD | PIN4 VDD |
| PIN5 CLK | PIN6 VSS | PIN7 DAT0 | PIN8 DAT1 |
| **G1 GND** | **G2 GND** | **G3 GND** | **G4 GND** |

All four are shell and fitting-nail grounds. **Grounding them is correct** — the
schematic is right as drawn, and no GPIO is needed.

**But it means there is no hardware card-detect at all**, which has a
consequence for an unattended drive:

> **"No card" and "card present but every write failing" look identical to the
> firmware** unless it goes looking. On a rig that gets left recording while
> someone drives, that difference is the whole session.

**Mitigate in firmware, not hardware.** Attempt the mount at startup and use
**GP25**, the onboard LED, to say so before the truck moves:

| LED | Means |
|---|---|
| Steady | card mounted, file open, logging |
| Fast blink | **mount failed** — no card, bad card, or bad seating |
| Slow blink | running but ring overflows have been counted |

Also from the drawing, and worth knowing: **5 000 mating cycles**, 0.5 A per
contact, 100 mΩ max contact resistance, and the `472192001` variant carries
**20 µ″ gold** against the `472190001`'s 2 µ″ — the right choice for a socket
that will be re-seated constantly during bring-up.

## 4. ✅ Being solved — a dedicated 3.3 V source

The original finding: everything hung off the Pico's `3V3(OUT)`, peaking around
**261 mA** if a GPS acquisition coincided with an SD write burst. A separate
regulator removes that, and the reason it matters is not just current — a rail
that sags during a card write shows up as **corrupt files, or as a GPS that
quietly resets**, and the second gets diagnosed as a bad antenna for a week.

### ⛔ One thing not to do

**Do not tie a new 3.3 V supply onto the Pico's `3V3(OUT)` while the Pico's own
regulator is still running.** Two regulators fighting over one net is a good way
to destroy both. There are two clean topologies instead:

| | Topology | `3V3_EN` |
|---|---|---|
| A | New LDO → its own rail for GPS + SD. Pico keeps `3V3(OUT)` for the RP2040 and TLV7031 | **leave alone** |
| **B** ⭐ | New LDO powers **everything**, Pico included | **tie to GND** |

**B is the better choice, and for a reason worth stating plainly: the Pico's
onboard regulator is itself a switcher** — an RT6150 buck-boost. If the argument
for using an LDO is *"do not put a switching regulator next to a GNSS front
end"*, then leaving the Pico's buck running keeps one on the board regardless.
Disabling it and feeding everything from one quiet LDO removes the last switcher
from the design.

Under topology A the GPS would sit on a clean LDO while a buck-boost switched
away 20 mm from the antenna trace. That is the wrong half of the problem solved.

### Wiring topology B

| | |
|---|---|
| **`3V3_EN` → GND** | Disables the Pico's buck-boost. **Not optional** — without it, two regulators fight over `3V3(OUT)` |
| **LDO output → `3V3(OUT)`** | The documented way to run a Pico from an external 3.3 V supply |
| LDO must carry | RP2040 **and** GPS **and** SD: the full **261 mA** peak, so ≥500 mA |
| USB | VBUS may still be connected for data; the buck stays off because `3V3_EN` is grounded |

**Verify `3V3_EN` is grounded before first power-up**, with the LDO fitted and a
meter on `3V3(OUT)`. Getting this wrong is not a subtle fault — it is two
regulators back-driving each other.

### Choosing the part — LDO, not a buck

A switcher near a GNSS front end is a classic way to desense a receiver: its
harmonics land in or near the band. Headroom is 1.7 V from USB 5 V, which is
ample for any LDO, so there is no efficiency argument worth the risk.

Dissipation is `(5 − 3.3) × I`:

| Load | Current | Power |
|---|--:|--:|
| GPS + SD idle | 46 mA | 0.08 W |
| GPS acquiring | 120 mA | 0.20 W |
| **GPS acq + SD write burst** | **220 mA** | **0.37 W** |

And the package decides whether that matters:

| Package | R<sub>θJA</sub> | Rise at idle | **Rise at burst** |
|---|--:|--:|--:|
| SOT-23-5 | 250 °C/W | 20 °C | **94 °C** ⚠ |
| SOT-89 | 110 °C/W | 9 °C | 41 °C |
| **SOT-223** | **65 °C/W** | **5 °C** | **24 °C** |

Bursts are brief, so SOT-23-5 will survive — but **SOT-223 or SOT-89 with a
copper pour costs nothing on a board this empty**, and takes the thermal question
off the table entirely.

Pick something rated **≥500 mA** with low noise: AP2112K-3.3, XC6220, TLV1117-33
or NCP1117-3.3 all qualify. Keep **10 µF in and 10 µF out** minimum, and put the
**output bulk local to the SD socket**, where the burst actually is.

## 5. Optional: series damping on CLK and MOSI

22–33 Ω in series with SCLK and MOSI costs nothing and tames ringing if the
traces are long or the card is on a flying lead. Not needed for a short
board-level run; worth having footprints for.

## Summary

| # | Item | Action |
|--:|---|---|
| 1 | CS pull-up missing, SCLK pull-up redundant | **Move R5 to SPCS** |
| 2 | Pin 8 on the DAT2 net | Relabel to DAT1 **and add R7, 10 kΩ** |
| 3 | Pins 9–12 all grounded | ✅ **Correct — all shell GND, no CD switch.** Cover it in firmware |
| 4 | 3V3 peak ~261 mA | ✅ **Dedicated 3.3 V LDO, powering everything.** **Tie the Pico's `3V3_EN` to GND** — its onboard regulator is a switcher, and the point is to have none near the GNSS front end |
| 5 | No series damping | Optional footprints |
