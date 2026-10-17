# MCU module — STM32F767ZIT6 on a 46 × 46 mm daughterboard

**Decided 2026-10-16.** The Nucleo-144 takes about 70 × 133 mm of the
158 × 174 carrier, roughly a third of the usable area. It is replaced by a
small module carrying only the MCU and its essential parts. That leaves room on
the carrier for the drivers, the analog front end and the CAN/J1850
interfaces. The module stacks on M3 standoffs like the power board, but at
**7.47 mm**, the height of its connector pair (see Interconnect).

This keeps what the Nucleo stage was for ([`carrier-board.md`](carrier-board.md)):
the MCU section is a separate, swappable board, so a carrier respin never
touches it and a damaged MCU is a module swap. Ethernet was already dropped,
and USB is the tuning path, so the module needs **no PHY, magnetics or RJ45**.

## What is on the module

| Item | Detail |
|---|---|
| MCU | STM32F767ZIT6, LQFP144 (same silicon as the Nucleo's F767ZI) |
| HSE | **8 MHz crystal** on PH0/PH1 |
| LSE | 32.768 kHz crystal on PC14/PC15 for the RTC (Standby + RTC, [`always-on-domain.md`](always-on-domain.md)) |
| Decoupling | 100 nF per VDD pin, bulk 4.7 µF; VCAP_1/VCAP_2 2.2 µF each |
| VDDA / VREF+ | ferrite from VDD, 1 µF + 100 nF; VREF+ tied to VDDA |
| PDR_ON | tied to VDD (internal supervisor on) |
| BOOT0 | 10 k pull-down, also on header D |
| NRST | 100 nF on the module; the carrier's TPS3823 drives it via header A |
| Programming | **ST STDC14** (Samtec FTSH-107-01-L-DV-K, 2×7 1.27 mm SMT) on the module **top**, beside the QFP. It is reachable with the module mounted and plugs straight into an STLINK-V3. It carries SWD (PA13/PA14), SWO (PB3), NRST, and the ST-Link VCP on **USART3 PD8 TX / PD9 RX**, the Nucleo's console UART, so the firmware is unchanged. The same pins also reach the carrier through the headers. There is no Tag-Connect: its alignment holes would land under the QFP or a header |
| Regulator | **none.** +3.3 V comes from the power board's TLV62085 through the carrier |

## Interconnect

Four **2×18, 1.27 mm surface-mount** headers form a square around the module
edge, one on each side of the QFP, between the corner standoffs:

| Side | Part | Notes |
|---|---|---|
| module, bottom | **Samtec FTSH-118-02-L-DV-A** | SMT header; `-02` 1.91 mm post (the FLE mate), `-L` gold on the post, `-A` alignment pins into the module |
| carrier, top | **Samtec FLE-118-01-G-DV-K-TR** | SMT socket strip; `-G` gold, `-K` pick-up pad, `-TR` reel; no alignment pins |
| mated | **7.47 mm** | Samtec's listed FTSH-xx-02 + FLE-xx-01 set; the M3 standoffs are 7.47 mm too |

> **Chosen 2026-10-17 by the user,** replacing the first pick (TFM-118-22 /
> SFM-118-02, 9.91 mm). FTSH lead style **-02** is the one Samtec lists as the FLE
> mate; -01 (3.05 mm post) is for the FFSD cable socket, with no FLE stack height
> published.
>
> **Standoffs: 7.47 mm in two parts** (user, 2026-10-17):
>
> | Where | Part | Height |
> |---|---|---|
> | module bottom, soldered | **Würth 9774050982R** WA-SMST SMT steel spacer, Ø4.5 bore | 5.0 mm ±0.1 |
> | carrier top, soldered | **PEM SMTSO-M3-2ET** ReelFast SMT standoff, M3 thread through (Mouser 153-SMTSO-M3-2ET) | 2.0 mm ±0.13 |
> | between them | **M3 washer, 0.5 mm** (DIN 433 / ISO 7092) | 0.5 mm |
> | **total** | | **7.5 mm** against 7.47 mated |
>
> The washer is needed: PEM makes no 2.5 mm SMTSO (M3 lengths are 2, 3, 4, 6,
> 8, 10 mm). Without it the stack is 7.0 mm and the screw would press the
> connectors 0.47 mm past full mating; the 3 mm part would leave them 0.53 mm
> short. 7.5 mm is 0.03 mm over, well inside the contact wipe.
>
> An M3 screw goes down from the module top through the spacer and washer into
> the SMTSO thread: **M3 × 10**. The head sits 7.1 mm above the standoff
> (1.6 board + 5.0 spacer + 0.5 washer), so 10 mm engages the whole 2 mm
> thread and the tip ends 0.9 mm into the carrier's Ø4.3 hole, inside the
> board. An M3 × 8 would catch under two threads. Put a washer under the head
> too, since the module hole is Ø5.4. The carrier land is the Samacsys
> `SMTSOM32ET` footprint the user imported: plated Ø4.3 hole, Ø6.45 pad (PEM:
> hole 4.22 +0.08, pad ≥ 6.2). Carrier parts under the module must stay below the module's
> bottom-side parts, with about 7.5 mm instead of 10 mm.
>
> The spacer footprint (`TritonECU-MCU:Wurth_WA-SMST_9774050982R`, made in
> `gen_module.py` from Würth's land pattern; the zip from Samacsys/DigiKey has
> only the STEP) is a Ø5.4 non-plated hole with a Ø9.4 copper ring on GND. The
> ring starts at Ø5.9 rather than at the hole edge, for the 0.25 mm
> hole-to-copper rule, and the stencil ring at Ø6.0; the Ø8.2 flange still
> lands fully on copper. That pad is why the module grew from 44 to **46 mm**:
> at 44 mm it would have reached the board edge.
>
> **Polarization comes from the standoffs.** The four headers are
> identical, and with the M3 holes on a square the module would also fit
> rotated 90°, 180° or 270°, which puts +3.3V and GND on signal pins. **H1, the
> QFP pin-1 corner, is offset 0.7 mm inward per axis** (−16.8, −16.8 instead
> of −17.5, −17.5) on both boards. It first moved outward, but the spacer's
> Ø9.4 pad would then reach the edge. A check of both finished boards confirms
> the holes coincide and that no rotated fit exists.

Pad size, pad offset and the FTSH's Ø1.02 mm alignment holes (on the header
centreline, ±10.16 mm) come from the vendor footprints the user imported via
Component Search Engine and impart (Samacsys `FTSH-118-XX-YYY-DV-A` and
`FLE11801GDVKTR`). Positions come from `mcu_pinout.py`. One change from the
vendor data: the FTSH pads are 0.1 mm shorter at their inner end (2.69 mm, not
2.79), because Samacsys leaves only 0.18 mm between the alignment holes and the
neighbouring pads, under the 0.25 mm hole-clearance rule. The outer, soldered
end is unchanged and the pads still reach about 1 mm under the body.

The contact rows sit **16.5 / 17.77 mm** from the module centre, the same as
with the first connector choice, so the pinout and the carrier footprint
positions did not move. Both new bodies are ±11.43 mm long, shorter than the
TFM, so the corners have more room. Because the headers are SMT, they use no
through-holes, apart from the small alignment holes in the module, so the
inner layers route freely under them.

Each header carries the pins of
the QFP side it faces, in package order, so the module escape is a straight
fan-out with no crossings. **All 110 port pins are broken out**, everything
except the four crystal pins. The carrier's pin assignment
([`pin-budget.md`](pin-budget.md), 83 of ~114) therefore stays free; nothing is
fixed by the module.

The source of truth is
[`Schematics/KiCad/TritonECU-MCU/mcu_pinout.py`](Schematics/KiCad/TritonECU-MCU/mcu_pinout.py).
The carrier footprint `TritonECU-Main:MCUModule_F767_Mate` (DB3) is generated
from it by `TritonECU-Main/gen_floorplan.py`. Running the script checks that
every port pin appears exactly once.

Each header has 36 pins. Odd numbers are the inner row (nearer the QFP), and
pin 1 is at the start of each side in package order:

| Header | Side | Package pins |
|---|---|---|
| A | left | 1–36, top → bottom (pin 1 corner) |
| B | bottom | 37–72, left → right |
| C | right | 73–108, bottom → top |
| D | top | 109–144, right → left |

## Firmware consequence

The Nucleo's HSE comes from the ST-LINK's 8 MHz MCO, in **bypass** mode. The
module has a real crystal. The PLL settings stay identical because the
frequency is the same 8 MHz, but `SystemClock_Config` must switch
`RCC_HSE_BYPASS` to `RCC_HSE_ON`. Firmware that runs on the Nucleo will fall
back to HSI, or fail to start HSE, until that change is made.

## Open

- **Schematic: done.** `TritonECU-MCU/gen_module.py` generates it. ERC is clean,
  and the netlist matches `mcu_pinout.py` pin for pin, both the headers and all
  144 MCU pins.
- **PCB: 6 layers**, at the user's call: 144 pins fan out to four headers in
  46 mm. `gen_module_pcb.py` places it in KiCad's Python, with a via at every
  power pad; Freerouting does the signals (see below).
  - **Stack:** F sig / In1 GND / In2 sig / In3 sig / In4 +3.3V / B sig.
  - **Top:** the QFP.
  - **Bottom:** decoupling, crystals, the four SMT headers and the four spacers.
  - **Routed** (2026-10-17, 46 mm, FTSH/FLE, Würth spacers): Freerouting 2.4.1
    on the placed board, the 104 power-fanout vias locked. 969 track segments
    (F 352, B 443, In2 96, In3 78) and 276 vias. Four 0.09 mm neck-downs were
    widened to 0.1 mm.
  - **Checks:** KiCad DRC 0 violations, 0 unconnected, schematic parity clean
    apart from the Exclude-from-BOM flags left by the per-supplier BOM exports.
    Every header pad is checked against `mcu_pinout.py` when the board is built.
  - **Mating check:** reading both finished boards, all 144 module pads line up
    with the carrier's FLE pads: same position along the header, same contact
    row, same net. The M3 holes coincide too.
  - **Pin numbers** are by position, from `mcu_pinout.py`, not Samtec's. Male
    pins mate by position, and a bottom-mounted header is mirrored.
- Crystals (user, 2026-10-17): **Y1 ABRACON ABM8AIG-8.000MHZ-1Z-T** with 27 pF
  load caps, **Y2 ECS ECS-.327-12.5-12QS-TR** (12.5 pF) with 18 pF. The BOM is
  split by supplier: `TritonECU-MCU-Mouser.csv` and `TritonECU-MCU-Future.csv`.
- USB: PA11/PA12 come out on header C. The connector, ESD protection and VBUS
  sense live on the carrier.

## Pinout

| pad | net | pad | net |
|---|---|---|---|
| A1 | GND | A2 | GND |
| A3 | GND | A4 | PE2 |
| A5 | PE3 | A6 | PE4 |
| A7 | PE5 | A8 | PE6 |
| A9 | VBAT | A10 | PC13 |
| A11 | PF0 | A12 | PF1 |
| A13 | PF2 | A14 | PF3 |
| A15 | PF4 | A16 | PF5 |
| A17 | GND | A18 | +3.3V |
| A19 | PF6 | A20 | PF7 |
| A21 | PF8 | A22 | PF9 |
| A23 | PF10 | A24 | NRST |
| A25 | PC0 | A26 | PC1 |
| A27 | PC2 | A28 | PC3 |
| A29 | +3.3V | A30 | GND |
| A31 | PA0 | A32 | PA1 |
| A33 | PA2 | A34 | GND |
| A35 | GND | A36 | GND |
| B1 | GND | B2 | PA3 |
| B3 | GND | B4 | +3.3V |
| B5 | PA4 | B6 | PA5 |
| B7 | PA6 | B8 | PA7 |
| B9 | PC4 | B10 | PC5 |
| B11 | PB0 | B12 | PB1 |
| B13 | PB2 | B14 | PF11 |
| B15 | PF12 | B16 | GND |
| B17 | +3.3V | B18 | PF13 |
| B19 | PF14 | B20 | PF15 |
| B21 | PG0 | B22 | PG1 |
| B23 | PE7 | B24 | PE8 |
| B25 | PE9 | B26 | GND |
| B27 | +3.3V | B28 | PE10 |
| B29 | PE11 | B30 | PE12 |
| B31 | PE13 | B32 | PE14 |
| B33 | PE15 | B34 | PB10 |
| B35 | PB11 | B36 | +3.3V |
| C1 | GND | C2 | PB12 |
| C3 | PB13 | C4 | PB14 |
| C5 | PB15 | C6 | PD8 |
| C7 | PD9 | C8 | PD10 |
| C9 | PD11 | C10 | PD12 |
| C11 | PD13 | C12 | GND |
| C13 | +3.3V | C14 | PD14 |
| C15 | PD15 | C16 | PG2 |
| C17 | PG3 | C18 | PG4 |
| C19 | PG5 | C20 | PG6 |
| C21 | PG7 | C22 | PG8 |
| C23 | GND | C24 | +3.3V |
| C25 | PC6 | C26 | PC7 |
| C27 | PC8 | C28 | PC9 |
| C29 | PA8 | C30 | PA9 |
| C31 | PA10 | C32 | PA11 |
| C33 | PA12 | C34 | PA13 |
| C35 | GND | C36 | +3.3V |
| D1 | GND | D2 | PA14 |
| D3 | PA15 | D4 | PC10 |
| D5 | PC11 | D6 | PC12 |
| D7 | PD0 | D8 | PD1 |
| D9 | PD2 | D10 | PD3 |
| D11 | PD4 | D12 | PD5 |
| D13 | GND | D14 | +3.3V |
| D15 | PD6 | D16 | PD7 |
| D17 | PG9 | D18 | PG10 |
| D19 | PG11 | D20 | PG12 |
| D21 | PG13 | D22 | PG14 |
| D23 | GND | D24 | +3.3V |
| D25 | PG15 | D26 | PB3 |
| D27 | PB4 | D28 | PB5 |
| D29 | PB6 | D30 | PB7 |
| D31 | BOOT0 | D32 | PB8 |
| D33 | PB9 | D34 | PE0 |
| D35 | PE1 | D36 | +3.3V |

110 port pins, 19 GND, 12 +3.3V, plus NRST, VBAT, BOOT0
