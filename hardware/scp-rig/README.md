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

## Where to connect — DLC, not the 104-pin

The bus is the same net at both ends: EEC-V **pin 16 = SCP+ (914 `TAN/ORG`)** and
**pin 15 = SCP− (915 `PNK/LT BLU`)** are DLC **pins 2 and 10**. Back-probing
C174 would work. **Do not.**

| | DLC | Back-probe at C174 |
|---|---|---|
| Access | designed to be plugged into | behind the kick panel, awkward |
| Ground and 12 V | pins 4/5 and 16, right there | separate wires |
| Terminal risk | none | **a spread terminal causes intermittent faults later** — the worst kind to chase, and you will chase it believing it is your ECU |
| Neighbours | none that matter | **coil and injector drivers**. Pins 78 and 79 are coils 7 and 8 |
| Engine running | fine | coil driver pins carry clamped flyback spikes. Keep probes away from them |

**Both jobs exist and they are different measurements:**

- **Bus capture → the DLC.** It is a bus, not point-to-point, so everything the
  PCM, GEM and cluster say is visible there. Probing at the PCM adds risk and
  shows exactly the same traffic.
- **Pin identification → back-probe at C174.** Which pin sinks the MIL, or
  confirming the TCIL on pin 12 — those are pin-level questions the DLC cannot
  answer. This is the method that already settled pins 12 and 79.

### Check the connector before wiring it

⚠ **Many OBD-II cables and breakouts omit pins 2 and 10.** They are the J1850
PWM pair, and a CAN-era cable has no use for them — cheap ones populate only
4, 5, 6, 14 and 16. A bare connector shell is fine; a moulded cable may simply
not have the terminals. **Check before building anything around it**: continuity
from the pin-2 cavity to its wire, and the same for 10. A missing terminal looks
exactly like a quiet bus.

**Ground: use pin 5, not pin 4.** Pin 5 is *signal* ground and is the correct
reference for a bus measurement; pin 4 is *chassis* ground. If the rig is
powered from pin 16 (variant B), return that current on **pin 4** and keep the
comparator referenced to **pin 5** — otherwise the supply current shares a return
with the signal reference and puts its own drop into what you are measuring.

**Confirm the numbering with a meter before trusting it.** The 16-pin shell is
two rows and the numbering flips depending on which side you are looking at.
Find **+12 V — that is pin 16** — and orient from there. Ten minutes of checking
against an unplugged connector beats debugging a rig that was correct all along.

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
| GP0 / GP1 | UART to the GPS — NMEA in |
| **GP4** | **GPS 1PPS** — the edge that ties GPS time to the capture timebase |
| GP25 | Onboard LED, frame activity |
| 3V3 (pin 36) | Supplies the TLV7031 |
| GND (pin 38) | **Common with vehicle ground** |

## GPS — use the 1PPS, not the sentence timestamps

**ATGM336H-5NR32** (AT6558R) fits without an adapter: 2.7–3.6 V so it runs off
the Pico's 3V3, NMEA 0183 over UART, <26 mA at 3.3 V, TCXO, built-in LNA and SAW,
and — the part that matters — **1PPS with the rising edge aligned to UTC**
(§1.7).

### Why PPS rather than the NMEA timestamp

An NMEA sentence *describes* a fix that was taken at the second boundary, but it
**arrives late and by a variable amount** — the sentence has to be composed and
then clocked out of a UART. At 9600 baud a burst of sentences takes tens of
milliseconds, and the delay changes with how many satellites are in view.

Timestamping the *sentence arrival* therefore aligns GPS to the capture with an
error of tens to hundreds of milliseconds. At 45 mph that is **up to 10 m of
position error**, and worse, it is error that varies through the recording.

**PPS inverts the problem.** Capture the PPS rising edge with the *same*
microsecond counter used for bus frames, and let the NMEA sentence say only
*which second that edge was*. The sentence can then arrive whenever it likes.
Alignment goes from ~100 ms to **sub-millisecond**, and the drifting component
disappears.

### Practicalities

| | |
|---|---|
| Wiring | UART on GP0/GP1, **PPS on GP4** — treat PPS as another timestamped event and put it in the same log |
| Cold start | **TTFF 32 s**. Power it up a minute before recording, not as the engine starts |
| Antenna | Active or passive supported. In a truck, on the dash or against the windscreen — a steel roof is a very good GNSS shield |
| Speed | Take it from RMC/VTG (Doppler-derived), not from differencing positions. 2.5 m CEP50 position does not imply poor speed |
| Rate | 1 Hz is plenty — the capture script marks speeds at held points rather than sweeping |

## Powering it

| Source | Logging | Survives cranking? | Ground |
|---|---|---|---|
| Laptop USB | USB serial | n/a — engine off or idling | laptop ↔ vehicle |
| **Truck USB adapter** | **must be SD** — no host, so no serial | ⚠ **no** | second path to vehicle ground |
| **USB power bank** ⭐ | SD | ✅ **yes** | **single reference, through DLC pin 5 only** |
| DLC pin 16 + buck | SD | with holdup | single, if returned on pin 4 |

**The truck's USB adapter is fine for idle, the RPM sweep and the drive — and
wrong for two of the seven capture steps.** Step 1 is *key off → on* and step 2
is *crank*. Anything fed from vehicle 12 V sags during cranking, and a cheap
adapter will brown the Pico out at precisely the moment being recorded. If the
socket is switched rather than always-hot, step 1 cannot be captured at all.

**A USB power bank solves it outright**, and it is the cheapest answer:

- Immune to cranking sag, so the crank frames actually get recorded.
- No second path to vehicle ground — the rig then references the bus **only**
  through DLC pin 5, which is what the comparator wants.
- No mains-adjacent noise from a cheap switching adapter riding on the same 12 V
  the bus lives on.

**Also note: powering from a charger means no USB host, so there is no serial
log.** SD becomes mandatory the moment the laptop goes away. That is variant B's
logging with variant A's simplicity.

Whatever the source, put **bulk plus ceramic decoupling at the Pico** — a few
hundred µF and 100 nF. The rig is a measuring instrument sharing a vehicle with
injectors and coils.

## Logging to SD — yes, and throughput is not the problem

A decoded frame is small, so the card is never the bottleneck:

| Record | Rate at 500 frames/s | 10 min | 1 hour |
|---|--:|--:|--:|
| **Binary**, 8 B µs-timestamp + len + flags + 12 B payload = **22 B** | **10.7 KB/s** | 6.6 MB | 40 MB |
| CSV, ~60 B/line | 29 KB/s | 18 MB | 108 MB |

An SD card over SPI sustains hundreds of KB/s at worst, so there is roughly
**27× headroom**. Log **binary and convert offline** — a four-hour session is
158 MB, and CSV costs 3× that for nothing the converter cannot give back.

### The real risk is stall latency, not bandwidth

Cheap cards pause **100–250 ms** for internal housekeeping — wear levelling, block
erase — and during that pause the writer blocks. Without somewhere to put frames,
they are simply lost, and a dropped frame in the middle of a MIL transition is
the one you needed.

**Fix it with RAM, which the Pico has plenty of** (264 KB). Built and tested —
[`firmware/include/FrameRing.h`](firmware/include/FrameRing.h):

| | |
|---|--:|
| Frames arriving in a 250 ms stall, busy bus | **125** |
| Ring as built, 2048 slots × 24 B | **48 KB** |
| **Occupancy at that worst stall** | **6.1 %** |

The measured number is ~16× smaller than the earlier estimate, which had assumed
a longer stall. The margin stays anyway: it is nearly free on 264 KB, a tired
card can stall longer than its datasheet says, and a bursty bus can exceed 500
frames/s briefly.

Capture writes into the ring from the PIO side; a second loop drains it to the
card. **Count and log ring overflows** — a capture that silently dropped frames
is worse than no capture, because nothing tells you the gap is there. `highWater()`
reports the deepest it ever got, so the sizing is a measurement after the first
session rather than an article of faith.

### Four things that bite on a vehicle

- **Flush on a timer, not just on close.** The key gets cut, the plug gets
  pulled. Sync every second — 10 KB at this rate — and preallocate the file so
  FAT metadata is not being rewritten constantly.
- **DLC pin 16 is permanent 12 V**, unswitched. The rig runs whenever it is
  plugged in. Add a switch, or accept a flat battery.
- **That 12 V is vehicle 12 V**, with everything that implies — so the buck needs
  the same input protection as anything else on this truck: reverse-polarity
  diode and a TVS that stands off above 16 V and clamps below the buck's rating.
  See [`../../docs/harness-protection.md`](../../docs/harness-protection.md).
- **Log GPS time as well as the µs counter.** The µs timer restarts every boot,
  so a multi-session capture has no common timebase without it — and the GPS
  fix is what ties road speed to the frames.

### File naming

One file per session, rotated at a size that stays manageable, named from GPS
date/time when a fix is available and a boot counter when it is not. A directory
of `capture_0007.bin` with no timestamps is a capture you will not be able to
put back in order later.

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
| J1 | OBD-II male connector or breakout — **verify pins 2 and 10 are populated**, see below |
| opt. | **ATGM336H-5NR32** GNSS module (AT6558R) — 2.7–3.6 V, UART NMEA 0183, **1PPS**, <26 mA at 3.3 V |
| opt. | microSD breakout |
