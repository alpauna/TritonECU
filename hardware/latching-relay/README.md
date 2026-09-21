# Latching relay driver

One momentary button, one relay. Push → on and **stays** on. Push again → off.
No firmware, no programmer. Built from two single-gate logic chips so the
control circuit is **~26 mm²** of board.

```
  +5V ──┬────────────┬──────────────┬──────────────────┬────────────┐
        │            │              │                  │            │
      [R1]        [C3 100n]      [R2 100k]         RELAY COIL    cathode
      100k           │              │                (5V)         [D1]
        │         U1,U2 VCC         │              ┌──┴──┐        anode
  SW1 ──┴──┬── U2 in (1G14)      U1 CLR ──┐        │     │          │
   │       │      │                       │        └──┬──┘          │
  GND  [C1 100n]  └── out ── U1 CLK    [C2 100n]      ├─────────────┘
           │                              │           │ drain
          GND                            GND       ┌──┴──┐
                                                   │ Q1  │ AO3400A
       U1  Q ──[R3 220]── GATE ───────────────────►└──┬──┘
       U1  /Q ── U1 D      (the toggle)            [R4 10k]  │ source
       U1  PRE ── +5V      (inactive)                  └────GND
```

| U1 | **SN74LVC1G74** single D flip-flop, V<sub>CC</sub> 1.65–5.5 V, has Q, /Q, PRE and CLR |
| U2 | **SN74LVC1G14** single Schmitt-trigger inverter, same supply range |

## Board area — the relay is the whole argument

Approximate land-pattern areas:

| Control circuit | Area |
|---|--:|
| CD4013 (SOIC-14) + 1G14 + 8 × 0805 | 99 mm² |
| **1G74 + 1G14 + 7 × 0402** ← this design | **26 mm²** |
| ATtiny202 (SOT-23-6) + 3 × 0402 | 12 mm² |

| What else is on the board | Area |
|---|--:|
| SRD-05VDC sugar-cube relay | **295 mm²** |
| G6K-2F signal relay (1 A, 125 VAC) | 109 mm² |
| 6 × 6 tact switch | 36 mm² |

**The relay is 80–90 % of the board whatever the logic does.** Shrinking the
control circuit from 99 to 26 mm² saves 73 mm²; choosing a signal relay instead
of a sugar cube saves 186 mm², and putting the button on a panel with a 2-pin
header saves another 36. Do those two first if area is really the constraint —
but note a signal relay is ~1 A at 125 VAC, so it is only an option if the load
side is small. There is no small relay that does 10 A at 250 VAC.

## Why two chips instead of one CD4013

The CD4013 is cheaper and needs no Schmitt in front *in theory*, but:

- **SOIC-14 is 52 mm² for one flip-flop**, and half of it is the unused second
  one. The 1G74 is 10 mm².
- **Slow edges are out of spec on both.** A CD4013B wants input transitions
  faster than ~15 µs at 5 V; a 100k/100nF debounce edge is ~10 ms. That is the
  classic hobby circuit and it *usually* works, but the failure mode is a
  double-toggle — a relay that ignores the button or flips twice. The Schmitt
  inverter is needed either way, so the 1G74 costs nothing extra in part count.
- The 1G14 in front buys a third thing: **the toggle moves to press.** Pressing
  pulls the RC node down hard, the inverter snaps its output up, and the rising
  edge clocks the flip-flop. Release is the slow edge and produces nothing.

## Why there is no optocoupler in this

**The relay is the isolation.** Coil and contacts are galvanically separate
inside the part — a sugar-cube relay is typically rated 4–5 kV coil-to-contact.
Whatever the contacts switch (5 VDC, 230 VAC, a pump, a doorbell) is invisible
to the gate circuit, and there is no path from the load back to the MOSFET. An
opto would isolate something the relay already isolated.

The load side *does* impose requirements. They are relay-selection and PCB
layout requirements, not gate-drive ones — see the last section.

## Why low side

| | |
|---|---|
| **Low side** (this circuit) | Source at GND, so V<sub>GS</sub> = the drive voltage. One transistor. |
| High side, N-channel | When on, the source sits near +5 V, so the gate needs ~+15 V to stay enhanced: a charge pump or bootstrap. |
| High side, bootstrapped off the switched node | **Cannot hold a static on-state.** A bootstrap cap only recharges when the node swings low. Works for PWM, dies for DC. |
| High side, P-channel | AO3401 plus a small N-FET inverting its gate. Two transistors, two resistors — only if the coil's negative *must* be chassis ground. |

The coil is a floating two-terminal load, so high side buys nothing.

## Connections

Wired by pin **name**, because the numbering differs between package options —
check the pinout for the variant you order.

| Net | Wiring | Why |
|---|---|---|
| Debounce | SW1 to GND, R1 100k to +5V, C1 100nF to GND | 10 ms RC. Every bounce yanks the cap to 0 V, so one press gives one edge. |
| Edge shaping | that node → U2 (1G14) in; U2 out → U1 CLK | Turns a 10 ms ramp into a <100 ns edge, and inverts, so the clock fires on **press**. |
| Toggle | U1 **/Q → U1 D** | Each clock flips the state. This is the entire latch. |
| Power-on reset | U1 **CLR**: C2 100nF to GND, R2 100k to +5V | CLR is active **low**, so the cap holds it low at power-up → Q = 0 → relay off. Without it the flip-flop comes up random and the relay may click on. |
| U1 PRE | to +5V | Inactive. Never float it. |
| Gate | U1 **Q** → R3 220 Ω → gate, R4 10k gate to GND | Same values as `hardware/2N7002 Driver`. |
| Coil | D1 across it, **cathode to +5V** | The flyback path. |
| Decoupling | C3 100nF at each chip's V<sub>CC</sub> | One per chip if there is room; one shared is acceptable at this speed. |

## Choosing the FET

A 5 V sugar-cube coil pulls **70–90 mA**. The 2N7002 in `hardware/2N7002 Driver`
is rated ~115 mA continuous — it works, with thin margin. **AO3400A costs the
same, is rated 5.7 A, and drops into the same SOT-23 footprint.**

> ⚠ **The existing 2N7002 driver board has no flyback diode.** It is In → 220 Ω
> → gate, 10k pull-down, drain to the Load header, and that is all. A relay coil
> on that board punches the FET on the first turn-off. If you reuse that board
> instead of building this one, fit D1 across the coil at the relay.

## Parts considered and rejected

| Part | Why not |
|---|---|
| **SN74AUC2G80** (dual D-FF, the datasheet that prompted this) | V<sub>CC</sub> is **0.8–2.7 V**, designed for 1.8 V — it cannot run on the 5 V coil rail, and its ~1.2 V output will not drive a FET gate properly. **No preset or clear**, so no power-on reset and the relay may click on at power-up. Input transition limit is 20 ns/V against a button's ~10⁶ ns/V. Its one nice trait: the only output is Q̄, so the toggle is a single wire. Not enough. |
| CD4013 | See above — SOIC-14, and the slow-edge problem is not actually avoided. |
| ATtiny202 | **Smaller and cheaper than this** (12 mm², 5 parts) and gives long-press-off and auto-off timers for free. Rejected only because it needs UPDI programming. Take it if a programmer is not a problem. |
| Alternate-action pushbutton in series with the coil | One part, zero board. Genuinely the answer if a button is the only input you will ever want. |
| ESP32 GPIO + the existing driver board | Zero new parts if the ECU is already at the spot. Still needs the flyback diode. |

## The load side

None of this touches the gate circuit, but all of it decides whether the relay
survives:

- **Contact rating, both flavours.** A 10 A / 250 VAC contact is often only
  10 A / **30 VDC**. DC arcs do not self-extinguish at a zero crossing, so if
  "up to 220 V" ever means 220 **VDC**, almost no cheap relay will do it.
- **Creepage.** For 230 VAC keep ≥ **6.4 mm** (aim for 8) between coil-side and
  contact-side copper, and rout a slot under the relay body if the footprint
  allows it.
- **Snubber across the contacts** for inductive loads: RC (100 Ω + 100 nF X2) or
  a MOV for AC, a flyback diode for DC. That protects the *contacts*, and is
  separate from D1 which protects the FET.
- **Fuse the load side.** The MOSFET cannot tell a motor from a short.

## BOM

`BOM.csv` follows the column format of `hardware/2N7002 Driver`, UTF-8 BOM
marker included, so it imports the same way. Passives are specified **0402** for
area; move them to 0805 if you are hand-soldering — that costs about 12 mm².

Four supplier part numbers are carried over from the 2N7002 driver board and are
known good. The rest are left blank deliberately rather than guessed — **fill
them from LCSC before ordering**, and prefer Basic parts to avoid feeder
charges. Note the carried-over 220 Ω and 10 kΩ codes are the **0805** versions;
if you go 0402 those two need re-picking too.

| Carried over from the 2N7002 driver BOM | LCSC |
|---|---|
| 2N7002, SOT-23 | C916396 |
| 220 Ω 0805 | C17557 |
| 10 kΩ 0805 | C2907219 |
| PZ254V-11-02P 2-pin header | C492401 |
