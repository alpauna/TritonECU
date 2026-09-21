# Latching relay driver

One momentary button, one relay. Push → on and **stays** on. Push again → off.
No firmware, no programmer, ~$0.25 of parts plus the relay.

```
   +5V ──┬──────────────┬─────────────┬──────────────┐
         │              │             │              │
       [R1]          [C3 100n]     RELAY COIL     cathode
       100k             │            (5V)          [D1]
         │            CD4013                       anode
   SW1 ──┴── CLK(3)   pin 14                         │
    │       ┌──────────────────┐                     │
   GND      │ D(5) ── /Q(2)    │   Q(1) ──[R3]──┬────┴── drain
         [C1 100n]  SET(6)─GND      220Ω      GATE     Q1
            │       RST(4)──┬──[C2 100n]── +5V     [R4 10k]
           GND              └──[R2 100k]── GND        │  source
                                                     GND
```

## Why there is no optocoupler in this

**The relay is the isolation.** Coil and contacts are galvanically separate
inside the part — a sugar-cube relay is typically rated 4–5 kV coil-to-contact.
Whatever the contacts switch (5 VDC, 230 VAC, a pump, a doorbell) is invisible
to the gate circuit, and there is no path from the load back to the MOSFET. An
opto would be isolating something the relay already isolated.

The load side *does* impose requirements. They are relay-selection and PCB
layout requirements, not gate-drive ones — see the last section.

## Why low side

| | |
|---|---|
| **Low side** (this circuit) | Source at GND, so V<sub>GS</sub> = the drive voltage. One transistor. |
| High side, N-channel | When on, the source sits near +5 V, so the gate needs ~+15 V to stay enhanced: a charge pump or bootstrap. |
| High side, bootstrapped off the switched node | **Cannot hold a static on-state.** A bootstrap cap only recharges when the node swings low, so it works for PWM and dies for DC. |
| High side, P-channel | AO3401 plus a small N-FET inverting its gate. Two transistors, two resistors — use only if the coil's negative *must* be chassis ground. |

The coil is a floating two-terminal load, so there is nothing high side buys.

## Connections

| Net | Wiring | Why |
|---|---|---|
| Toggle | D (5) → /Q (2) | Each clock flips the state. This is the entire latch. |
| Clock | SW1 from CLK (3) to GND, R1 100k to +5V, C1 100nF to GND | Debounce. Toggles on **release** — the 4013 clocks on the rising edge. |
| Power-on reset | RST (4): C2 100nF to +5V, R2 100k to GND | Without it the flip-flop powers up in a random state and the relay may click on at power-up. |
| SET (6) | to GND | Unused input. Never float a CMOS input. |
| Pins 8, 9, 10, 11 | to GND | The unused second flip-flop, same reason. Pins 12, 13 left open. |
| Gate | Q (1) → R3 220 Ω → gate, R4 10k gate to GND | Same values as `hardware/2N7002 Driver`. |
| Coil | D1 across it, **cathode to +5V** | The flyback path. |
| Decoupling | C3 100nF across pins 14 and 7, at the chip | |

**Debounce maths.** 100k × 100nF = 10 ms rising. Contact bounce is ~1–5 ms and
every bounce yanks the cap back to 0 V, so only the final release produces a
rising edge that crosses the ~2.5 V threshold. One press, one toggle.

**Toggles on release, not on press.** That is a consequence of the 4013 being
rising-edge only with the switch wired to ground — which is the right way round
for a panel button on a long wire. To toggle on press instead, wire SW1 to +5V
with R1 to GND, and accept that the switched wire is now the noise-sensitive one.

## Choosing the FET

A 5 V sugar-cube coil pulls **70–90 mA**. The 2N7002 in `hardware/2N7002 Driver`
is rated ~115 mA continuous — it works, with thin margin. **AO3400A costs the
same and is rated 5.7 A**, which retires the question. Either drops into the
same SOT-23 footprint.

> ⚠ **The existing 2N7002 driver board has no flyback diode.** It is In → 220 Ω
> → gate, 10k pull-down, drain to the Load header, and that is all. A relay coil
> on that board as-is will punch the FET on the first turn-off. If you reuse the
> board rather than building this one, fit D1 across the coil at the relay.

## Cheaper or smaller, if either matters more

| Approach | Parts | Board area | Catch |
|---|--:|---|---|
| **Alternate-action pushbutton** in series with the coil | **1** | none | No electronic control at all. If a button is the only input you will ever have, this is honestly the answer. |
| **ATtiny202** (SOT-23-6) | 5 | ~3 × 3 mm | Needs a UPDI programmer. Gives long-press-off, auto-off timer, soft start for free. |
| **CD4013**, this board | 9 | SOIC-14 + 7 passives | None. This is the no-firmware pick. |
| **ESP32 GPIO** + the existing driver board | 0 new | none | Only if the ECU is already at the spot. Still needs the flyback diode. |

## The load side

None of this touches the gate circuit, but all of it decides whether the relay
survives:

- **Contact rating, both flavours.** A 10 A / 250 VAC contact is often only
  10 A / **30 VDC**. DC arcs do not self-extinguish at a zero crossing, so if
  "up to 220 V" ever means 220 **VDC**, almost no cheap relay will do it — that
  wants a DC-rated part or contacts in series.
- **Creepage.** For 230 VAC keep ≥ **6.4 mm** (aim for 8) between coil-side and
  contact-side copper, and rout a slot under the relay body if the footprint
  allows it.
- **Snubber across the contacts** for inductive loads: RC (100 Ω + 100 nF X2) or
  a MOV for AC, a flyback diode for DC. That protects the *contacts*, and is
  separate from D1 which protects the FET.
- **Fuse the load side.** The MOSFET cannot tell a motor from a short.

## BOM

`BOM.csv` follows the column format of `hardware/2N7002 Driver`. Four supplier
part numbers are carried over from that board and are known good; the rest are
left blank deliberately rather than guessed — **fill them from LCSC before
ordering**, and prefer Basic parts to avoid JLC feeder charges.

| Carried over from the 2N7002 driver BOM | LCSC |
|---|---|
| 2N7002, SOT-23 | C916396 |
| 220 Ω 0805 | C17557 |
| 10 kΩ 0805 | C2907219 |
| PZ254V-11-02P 2-pin header | C492401 |
