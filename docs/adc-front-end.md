# Analog front end — AD7606C-16

The part is already on hand, wired to the Teensy 4.1 in
`~/Claude/LxScanner/firmware-teensy` as a bench scope. The driver here is a
port of that bench-validated code (checked against a known ±1.24 V reference,
2026-08-27/28), with the conversion sequence and SPI mode carried over
unchanged because they were proven on hardware.

## Moving it from the Teensy to the P4

Eleven signals plus power. The Teensy build runs VDRIVE at 3.3 V, and the P4 is
also 3.3 V, so **no level shifting is needed** — this is a wire-for-wire move.

| AD7606C signal | Teensy 4.1 | → ESP32-P4 | Notes |
|---|---|---|---|
| SCLK | 13 | **27** | Teensy 13 is also its onboard LED |
| DOUTA (MISO) | 12 | **33** | |
| CS | 16 | **46** | software-driven, not hardware SPI CS |
| CONVST | 14 | **26** | also drives WR on the usual breakouts |
| BUSY | 17 | **28** | |
| RESET | 15 | **29** | |
| FRSTDATA | 18 | **30** | optional — pass −1 if not wired |
| OS0 | 19 | **31** | |
| OS1 | 20 | **47** | |
| OS2 | 21 | **48** | |
| RANGE | 22 | **2** | one setting shared by all 8 channels |
| VDRIVE | 3.3 V | 3.3 V | |
| GND | GND | GND | common ground |

MOSI is not wired. In hardware mode range and oversampling are set by pins
rather than registers, so the P4 opens SPI with MOSI as −1.

**In the final ECU, six of these move to the MCP23S17 expander chain** —
RESET, FRSTDATA, OS0, OS1, OS2 and RANGE are static or near-static, so they do
not deserve native pins. That leaves SCK, MISO, CS, CONVST and BUSY, which is
the five the pin budget in `f150-1999-target.md` assumes. The mapping above is
the *bench* mapping, using native pins because nothing else is connected yet.

## Channel allocation

Eight channels, and they are all spoken for:

| Ch | Signal | Why here |
|---|---|---|
| 0 | MAF signal (+) / return (−) | **differential** — the whole reason for this part |
| 1 | TPS | fast, and ratiometric to VREF |
| 2 | O2 upstream bank 1 | |
| 3 | O2 upstream bank 2 | |
| 4 | CHT — cylinder head temperature | |
| 5 | IAT — intake air temperature | |
| 6 | Battery voltage | via divider; injector dead-time compensation |
| 7 | **VREF sense** | sensors are ratiometric, and this ADC is not — see below |

Moved to the P4's own ADC because they are slow and not fuelling-critical:
DPFE, TFT, downstream O2 ×2, fuel pump monitor.

Knock (C103) is **not** on this ADC as a routine channel — it is a piezo
needing a charge amplifier and windowed sampling around each combustion event.
See `1999-Ford-F150-4wd-5.42v/oem-connectors.md`.

## Why channel 7 is spent on VREF

The AD7606C measures against its own internal 2.5 V reference. Every
three-wire sensor on the truck is **ratiometric to VREF** — a TPS reports a
*fraction* of VREF, not an absolute voltage. The two references are unrelated,
so a 1 % VREF error reads as a 1 % throttle error.

Sampling VREF on channel 7 and dividing in software cancels it exactly, because
simultaneous sampling means VREF and the sensor are captured at the *same
instant* — a sequential ADC would leave a residual error whenever VREF moved
between the two conversions. That property is worth the channel.

## Scaling

| Range | Volts per count |
|---|---|
| ±10 V | 305.18 µV |
| ±5 V | 152.59 µV |

±10 V takes 0–5 V sensors directly with headroom for overshoot. ±5 V doubles
the resolution but leaves no margin — worth switching to only once every input
is known to be well-behaved.

Battery voltage exceeds both ranges and needs a divider regardless.

## Bench verification before it goes near the truck

1. Short an input to ground — expect 0 counts ±noise.
2. Apply a known bench voltage to each channel in turn and confirm within 1 %.
3. Check the differential pair: drive both inputs from the same source and
   confirm the reading collapses to near zero. This is the property the MAF
   depends on, and it is the one that silently does not work if a −IN is
   accidentally grounded.
4. Confirm BUSY actually rises and falls. `begin()` fails on a BUSY timeout
   rather than returning happily, because a stuck BUSY is a wiring fault, not
   something to retry.
