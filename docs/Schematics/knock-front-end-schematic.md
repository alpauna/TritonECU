# Knock front end — schematic

Differential charge amplifier for the two-wire piezo knock sensor, EEC-V pins
**57** (KNOCK+, YEL/RED) and **32** (KNOCK−, DK GRN/VIO). Rationale and component
sizing in [`../knock-front-end.md`](../knock-front-end.md).

Built around **one TLV9064-Q1 quad** and its **own 2.5 V reference**, kept
separate from the ADC's.

---

## Schematic

```
                    R1 1k              C1 220p C0G
  pin 57  ──┬───────/\/\/──┬──────┬──────||──────┐
  KNOCK+    │              │      │             │
            │           [KP_IN]   │   R3 1M     │
           D1                     └──/\/\/──────┤
        BAV199                                  │
        to +5VA                    ┌────────────┴─── KA_OUT
        and AGND                   │  ╲
                                   └──╲  −
                                       ╲      U1A          VMID = 2.5 V, buffered
                                VMID ──╱  +   ╱───┬──────► KA_OUT
                                      ╱      ╱    │
                                     ╱──────╱     │
                                                  │
                    R2 1k              C2 220p C0G│
  pin 32  ──┬───────/\/\/──┬──────┬──────||──────┐│
  KNOCK−    │              │      │             ││
            │           [KN_IN]   │   R4 1M     ││
           D2                     └──/\/\/──────┤│
        BAV199                                  ││
        to +5VA                    ┌────────────┴┼─── KB_OUT
        and AGND                   │  ╲          │
                                   └──╲  −       │
                                       ╲      U1B│
                                VMID ──╱  +   ╱──┼┬─────► KB_OUT
                                      ╱      ╱   ││
                                     ╱──────╱    ││
                                                 ││
  ── difference amplifier, unity gain, pole 1 ───┘│
                                                  │
            R5 10k 0.1%          R7 10k 0.1%      │
  KA_OUT ───/\/\/────┬───────────/\/\/────┬───────┘   (KA to the − input)
                     │                    │
                     │          C3 620p ──┤            pole 1 = 25.7 kHz
                     │           C0G      │
                     │   ╲               │
                     └───╲  −            │
                          ╲     U1C      │
            R6 10k 0.1%   ╱  +   ╱───────┴──┬── KNOCK_DIFF
  KB_OUT ───/\/\/────┬───╱      ╱           │
                     │  ╱──────╱            │  R9 470R
                     │                      └──/\/\/──┬── KNOCK_ADC ► MCU ADC
            R8 10k 0.1%                               │
                     ├───/\/\/─── VMID            C4 15n     pole 2 = 22.6 kHz
                     │                                │
                  C3b 620p C0G                       AGND
                     └──────────── VMID


  ── VMID buffer and its own reference ───────────────────────────────────────

                 U2 MAX6070AAUT25          R10 100R
   +5VA ──┬── IN          OUT ──┬──────────/\/\/───┬──────┐
          │                     │                  │      │   ╲
          ├── EN (tie to IN)    │              C5 1u      └───╲  +
          │                     │                  │          ╲   U1D
        C6 100n              C7 100n              AGND        ╱     ╱──┬── VMID
          │                     │                            ╱  −  ╱   │
         AGND                  AGND                         ╱──────╱   │
                                                                │      │
                                                                └──────┘
```

---

## Net list

| Net | Connects |
|---|---|
| `KNOCK_P` | EEC-V pin 57 · D1 · R1 |
| `KNOCK_N` | EEC-V pin 32 · D2 · R2 |
| `KP_IN` | R1 · C1 · R3 · **U1A pin 2 (IN−)** |
| `KN_IN` | R2 · C2 · R4 · **U1B pin 6 (IN−)** |
| `KA_OUT` | C1 · R3 · **U1A pin 1 (OUT)** · R5 |
| `KB_OUT` | C2 · R4 · **U1B pin 7 (OUT)** · R6 |
| `U1C_N` | R5 · R7 · C3 · **U1C pin 9 (IN−)** |
| `U1C_P` | R6 · R8 · C3b · **U1C pin 10 (IN+)** |
| `KNOCK_DIFF` | R7 · C3 · **U1C pin 8 (OUT)** · R9 |
| `KNOCK_ADC` | R9 · C4 · **→ MCU ADC input** |
| `VMID` | **U1D pin 14 (OUT)** · U1D pin 13 (IN−) · U1A pin 3 (IN+) · U1B pin 5 (IN+) · R8 · C3b |
| `VREF_KNK` | U2 OUT · R10 · C7 |
| `VMID_F` | R10 · C5 · **U1D pin 12 (IN+)** |
| `+5VA` | U2 IN · U2 EN · U1 pin 4 (V+) · C6 · C8 |
| `AGND` | U1 pin 11 (V−) · C4 · C5 · C6 · C7 · C8 · D1 · D2 |

*TLV9064 pinout is the standard quad-14 arrangement — confirm against the
datasheet when placing.*

---

## Bill of materials

| Ref | Value | Package | Notes |
|---|---|---|---|
| U1 | **TLV9064-Q1** | TSSOP-14 / SOIC-14 | quad, 10 MHz, RRIO, **CMOS input**, AEC-Q100 |
| U2 | **MAX6070AAUT25** | SOT23-6 | 2.5 V, **dedicated to this block** |
| R1, R2 | 1 kΩ 1 % | 0603 | input protection; 159 kHz pole with the sensor, above band |
| R3, R4 | **1 MΩ** 1 % | 0603 | DC bias return + 723 Hz high-pass |
| R5–R8 | **10 kΩ 0.1 %** | 0603 | difference amp — **matched set or a network** |
| R9 | 470 Ω 1 % | 0603 | ADC isolation + pole 2 |
| R10 | 100 Ω 1 % | 0603 | reference RC filter |
| C1, C2 | **220 pF C0G/NP0** 5 % | 0603 | **the calibration — see below** |
| C3, C3b | **620 pF C0G/NP0** 5 % | 0603 | anti-alias pole 1, 25.7 kHz |
| C4 | 15 nF X7R | 0603 | anti-alias pole 2, 22.6 kHz |
| C5, C7 | 1 µF X7R | 0603 | reference filtering |
| C6, C8 | 100 nF X7R | 0402 | decoupling, one per supply pin |
| D1, D2 | **BAV199** | SOT23 | **low-leakage** clamp to +5VA / AGND |

---

## Five things to get right

**C1 and C2 must be C0G/NP0.** Charge-amp gain is `Q/Cf`, so these capacitors
*are* the knock calibration. An X7R part drifts ±15 % over temperature and loses
capacitance under bias — sensitivity would wander with under-hood temperature,
which is the worst possible way to lose it.

**D1/D2 are BAV199, not BAV99.** The summing nodes are megohm impedance. A
standard BAV99's leakage across R3/R4 becomes a DC offset; BAV199 is the
low-leakage part in the same package for exactly this job.

**R5–R8 must be matched, and U1D is not optional.** A difference amplifier's CMRR
is set by how well those four resistors match — 0.1 % or a matched network, not
four 1 % parts. And **the reference leg must be driven from a low impedance**:
feeding `R8` from the reference IC directly would put the reference's output
impedance in series with one arm of the bridge and unbalance it. That is why the
fourth amplifier stays a buffer even though the block now has its own reference.

**U2's EN ties to IN, not to logic.** The MAX6070's enable threshold is
**0.7 × VIN**, which on a 5 V rail is **3.5 V** — a 3.3 V GPIO cannot reliably
assert it. This is the same trap that put the ADC's reference on the 3.3 V rail.
Tie EN to IN and the reference simply follows the switched 5 V rail, which is the
behaviour wanted anyway.

**Guard the summing nodes.** `KP_IN` and `KN_IN` sit at megohms. Ring each with a
`VMID` guard trace so surface leakage across a fluxy board has nowhere to go, and
keep `C1`/`C2` right at the amplifier pins.

## Layout

- Route `KNOCK_P`/`KNOCK_N` as a **differential pair**, guarded, and keep them
  away from the eight coil drivers — the signal being hunted is microvolts of
  ringing while 40 kV events happen on the same board.
- `+5VA` and `AGND` belong to the **analog** domain, per the split described in
  [`../adc-daughterboard.md`](../adc-daughterboard.md).
- Single-point tie between analog and digital ground.

## [MEASURE] before fixing values

- **Sensor capacitance.** Everything scales off the assumed 1 nF.
- **Open-circuit output under real knock.** Decides whether `C1`/`C2` are 100 pF
  (2.0 V out) or 470 pF (0.43 V out). 220 pF is the starting point, not a result.
