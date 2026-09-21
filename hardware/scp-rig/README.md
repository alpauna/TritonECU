# Phase 0 SCP capture rig

Receive-only J1850 PWM listener for the DLC. **No transmit stage** — the OEM PCM
is live on that bus. See [`../../docs/phase0-rig.md`](../../docs/phase0-rig.md)
for why, and [`../../docs/phase0-capture-protocol.md`](../../docs/phase0-capture-protocol.md)
for what to record.

**Micro: Raspberry Pi Pico (RP2040).** PIO gives deterministic sub-microsecond
edge timing on a ~24 µs bit, it is 3.3 V native so it shares the comparator's
rail with no level shifting, and this repo already runs PIO on an RP2040 in
`hardware/vr-test-rig/firmware`.

**The RX network below is the corrected one** from
[`../../docs/f150-1999-target.md`](../../docs/f150-1999-target.md) §5.3 — not the
upstream reference, which has two known traps (a 10 k : 100 k divider that puts
4.5 V on a 3.6 V input, and a bias resistor returned to 3.3 V instead of ground).
Building the rig with the shipping values means Phase 0 validates the board.

## Schematic

```
  DLC (OBD-II, under dash)                            RASPBERRY PI PICO
  ┌───────────────────────┐                        ┌────────────────────┐
  │ pin 2   SCP+  914 TAN/ORG ──┐                  │                    │
  │ pin 10  SCP−  915 PNK/LT BLU ─┐                │  GP2   RX in       │
  │ pin 4,5 GND ──────────────┐ │ │               │  GP3   loopback    │
  │ pin 16  +12V (variant B)  │ │ │               │  GP0/1 GPS (opt)   │
  └───────────────────────────┼─┼─┼───────────────│  3V3   OUT (pin36) │
                              │ │ │               │  GND               │
                              │ │ │               └────────────────────┘
        SCP+ ────[ R1 100k ]──┼─┼─┴──┬──────────┬─────────► IN+
                              │ │    │          │
                              │ │  [R2 100k]  [D1 MM3Z3V3BW]
                              │ │    │          │
                              │ │   GND        GND
                              │ │
        SCP− ────[ R3 100k ]──┼─┴───────┬──────────┬──────► IN−
                              │         │          │
                              │      [R4 100k]  [D2 MM3Z3V3BW]
                              │         │          │
                              │        GND        GND
                             GND
                                    ┌──────────────────┐
                              IN+ ──┤                  │
                              IN− ──┤    TLV7031       ├── OUT
                              3V3 ──┤  (SOT-23-5)      │
                              GND ──┤                  │
                                    └──────────────────┘
                                             │
              hysteresis  OUT ──[ R5 4.7M ]──┴──► IN+      ≈ ±35 mV

                    OUT ──[ R6 100R ]──┬───────────────────► Pico GP2
                                       │
                                   [D3 SMF3.3]
                                       │
                                      GND

              3V3 ──[ C1 100n ]── GND                 (at the TLV7031)

  BENCH LOOPBACK ONLY — remove before connecting to a vehicle:
        Pico GP3 ──[ R7 1k ]──► the SCP+ node, ahead of R1
        and strap SCP− to GND
```

## Why each part is the value it is

| | | |
|---|--:|---|
| R1–R4 | **100 k : 100 k** | Symmetric 1:1. A 5 V bus HIGH lands at **2.5 V**, inside the TLV7031's V<sub>CC</sub>+0.3 ≈ 3.6 V limit. The reference's 10 k : 100 k puts 4.5 V there **during ordinary reception** |
| R2/R4 return | **to GND** | The reference returns the bias to 3.3 V. Harmless at 10:1, destructive at 1:1 — it pulls half the node |
| D1, D2 | MM3Z3V3BW | 3.3 V clamp, **after** the divider |
| R5 | **4.7 MΩ** | Hysteresis, ≈ ±35 mV against a 2.5 V swing — the bus idles at 0 V differential, so without it the comparator chatters on noise |
| R6 + D3 | 100 Ω + SMF3.3 | Output protection into the Pico |
| Bus loading | **200 kΩ per line** | Genuinely non-invasive — the rig is a voltmeter, not a node |

## Pico pin map

| Pin | Use |
|---|---|
| **GP2** | Comparator output — PIO edge capture |
| **GP3** | Loopback generator. **Set to INPUT whenever connected to a vehicle** |
| GP0 / GP1 | UART to an optional GPS — puts road speed in the same log on the same timebase, which is what makes the speedometer correlation possible |
| GP25 | Onboard LED, frame activity |
| 3V3 (pin 36) | Supplies the TLV7031 |
| GND (pin 38) | **Common with vehicle ground** |

## Two power variants

| | A — bench and cab | B — unattended drive |
|---|---|---|
| Pico power | USB from a laptop | DLC pin 16 (+12 V) → buck/LDO → VSYS |
| Logging | USB serial to the laptop | SD card on SPI (GP16–19) |
| Use for | everything up to and including the RPM sweep in park | the road-speed drive, if nobody is riding along |

Variant A is enough for the whole capture protocol if someone holds the laptop.
**Start there** — one fewer subsystem to debug while chasing a bus.

## Build order

1. **Assemble RX only.** Confirm with a meter: 2.5 V at IN+ when SCP+ is held at
   5 V on the bench, and that both clamps are the right way round.
2. **Loopback.** Fit R7, strap SCP− to GND, generate PWM patterns on GP3, decode
   on GP2. *If the decoder cannot read a frame it just generated, it will not
   read the truck.*
3. **Remove R7. Set GP3 to input.** Then plug into the 2003.
4. Capture per [`phase0-capture-protocol.md`](../../docs/phase0-capture-protocol.md).

## BOM

| Ref | Part |
|---|---|
| U1 | Raspberry Pi Pico (RP2040) |
| U2 | TLV7031 comparator, SOT-23-5 — **check the pinout against the datasheet; this drawing labels by function** |
| R1–R4 | 100 kΩ 1 % |
| R5 | 4.7 MΩ |
| R6 | 100 Ω |
| R7 | 1 kΩ — bench only |
| D1, D2 | MM3Z3V3BW |
| D3 | SMF3.3 |
| C1 | 100 nF |
| J1 | OBD-II male connector or breakout |
| opt. | GPS module (NMEA, UART), microSD breakout |
