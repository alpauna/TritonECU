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
4. Confirm BUSY actually rises and falls.

**Correction, from the bench.** An earlier version of this document claimed
`begin()` would fail on a BUSY timeout rather than reporting zeros. It did not.
With nothing connected, BUSY floats **low**, so the wait-for-BUSY-to-fall
returned immediately; MISO floated high, every channel read `0xFFFF`, and the
firmware cheerfully announced "AD7606 responding" with a plausible −0.0003 V on
all eight channels.

Two checks now guard it, and both were added because the obvious one failed:

- **BUSY must be seen to RISE** after CONVST, not merely be low. The probe runs
  at ×64 oversampling so the conversion takes ~255 µs instead of ~3 µs, making
  the high period impossible to miss.
- **All eight channels reading an identical `0x0000` or `0xFFFF`** is treated as
  a floating DOUTA rather than data. Real inputs, even grounded ones, disagree
  in the low bits from noise alone.

---

## Does the ECU need 1 MSPS? No — 200 kSPS is enough

The AD7606C-16 and -18 are **1 MSPS on all channels** (verified from the
datasheets). The original **AD7606 is 200 kSPS** and cheaper. That is still
comfortably more than this application needs, for both the routine channels and
knock.

### Routine sensor channels

At 6000 rpm on an eight-cylinder four-stroke:

```
combustion events/s = (6000 / 60) x 8 / 2 = 400 /s
```

One sample set per event is 400 Hz. Sampling four times per event for decent
transient resolution is 1.6 kHz. Call it **2 kHz per channel**, generously.

Every one of these is simultaneous on this part, so 2 kHz of all eight channels
is 2 kSPS of the ADC's 200 kSPS — about **1 % utilisation**. The temperatures
and O2 sensors want a tenth of that. There is no argument for 1 MSPS here.

### Knock

Knock rings around **6–8 kHz** on a 3.55″ bore. Nyquist is 16 kSPS; a usable
FFT wants 4–10× the frequency of interest, so **40–80 kSPS**. At 200 kSPS that
is 25× oversampling of an 8 kHz signal — ample.

The knock window is short. At 6000 rpm a 30° window is about 0.8 ms, so 100
kSPS yields ~80 samples per window per cylinder. Workable.

### The real bottleneck is SPI, not the ADC

At 200 kSPS × 8 channels × 16 bits the bus would have to carry **25.6 Mbit/s**.
The current 8 MHz SPI cannot do that, and it does not have to — the two jobs
run at different rates:

| Job | Rate | Channels read | Bus load at 8 MHz |
|---|---|---|---|
| Routine sensors | 2 kHz | all 8 | 256 kbit/s — 3 % |
| Knock burst | 100 kHz | **1** | 1.6 Mbit/s — 20 % |

The AD7606 family clocks its channels out sequentially on DOUTA, so a knock
burst reads **one** 16-bit word and raises CS rather than clocking all eight.
That is what keeps a 100 kSPS knock window affordable on a modest SPI clock.
It does mean **knock should sit on channel 0**, so its word arrives first.

## Which part — and a naming trap worth knowing about

Three generations share one footprint:

| | AD7606 | AD7606**B** | AD7606**C**-16 |
|---|---|---|---|
| Throughput | 200 kSPS | 800 kSPS | 1 MSPS |
| Operating temp | **−40 to +85 °C** | −40 to **+125 °C** | −40 to +125 °C |
| Input clamp | ±16.5 V | **±21 V** | ±21 V |
| Input impedance | 1 MΩ | 5 MΩ | 5 MΩ (lower drift) |
| VDRIVE floor | 2.3 V | 1.71 V | 1.71 V |
| Software/register mode | no | yes | yes |
| Per-channel range | no | no | **yes** |
| On-chip diagnostics | no | yes | yes |

### The trap: "AD7606BSTZ" is not "AD7606B"

The `B` in **AD7606BSTZ** is a *grade letter* in the original AD7606's ordering
code (B grade, ST = LQFP-64, Z = RoHS). The **AD7606B** is a different, newer,
faster part. The two look almost identical in a parts listing.

The Tokmas datasheet on file (`~/Documents/Tokmas AD7606B-Datasheer.pdf`) is
headed **AD7606BSTZ**, and its specifications are the original AD7606's:

- 16-bit, **200 kSPS** on all channels
- **±16.5 V** input clamp
- **1 MΩ** input impedance
- **−40 °C to +85 °C**
- VDRIVE 2.3–5 V, AVDD 4.75–5.25 V

So this is an AD7606-class part at an AD7606B-sounding part number. That is not
necessarily misrepresentation — it is the correct ordering code for what it is
— but it is easy to read as the 800 kSPS part.

ADI themselves warn about the sharper version of this: because all three are
**footprint-identical**, a re-marked 200 kSPS AD7606 can be sold as an 800 kSPS
AD7606B and pass visual inspection. If throughput ever actually mattered, it
would need measuring rather than trusting the marking. Here it does not.

### Verdict at a 10× price difference

**Use the cheap part.** At roughly $5.60 against $55, and with the throughput
analysis above showing ~1 % utilisation, the AD7606C's advantages do not come
close to justifying ten times the price for this build.

The clamp question raised earlier is **resolved in its favour**: ±16.5 V is
present, along with 1 MΩ input impedance, 8 kV ESD protection on the analog
inputs, and a second-order anti-aliasing filter at −3 dB / 22 kHz. That is the
protection package that makes this family suit an automotive harness, and the
cheap part has it.

Two things to weigh before ordering:

1. **Temperature: −40 to +85 °C, not +125 °C.** This decides where the ECU can
   mount. The OEM PCM on this truck sits in the cabin, not the engine bay, so
   85 °C is very likely fine — but it rules out an under-hood enclosure, and
   that is a decision better made now than after the board is built.
   **[CONFIRM]** the intended mounting location.
2. **1 MΩ input impedance, not 5 MΩ.** It loads the source slightly. Irrelevant
   for low-impedance sensors, but the battery-voltage divider should be stiff
   enough that 1 MΩ across it does not shift the ratio — keep the divider
   resistances well under 100 kΩ.

Neither is a reason to spend the extra $50.

---

## Oversampling is global, so do the averaging in software

The hardware oversampling pins trade throughput for noise, and the conversion
time scales with the ratio (typical values from the datasheet):

| OS | Conversion time | Max throughput |
|---|---|---|
| off | 2.9 µs | 200 kSPS (spec limit) |
| ×2 | 7 µs | ~143 kSPS |
| ×4 | 15 µs | ~67 kSPS |
| ×8 | 31 µs | ~32 kSPS |
| ×16 | 63 µs | ~16 kSPS |
| ×32 | 127 µs | ~7.9 kSPS |
| ×64 | 255 µs | ~3.9 kSPS |

**OS0–2 are one setting shared by all eight channels.** There is no way to
oversample the slow sensors while sampling knock fast — at ×16 the whole part
drops to ~16 kSPS, which is at Nyquist for an 8 kHz knock signal and useless
for an FFT.

So: **run with oversampling off and average in software.** Averaging N samples
gives the same √N noise reduction as hardware oversampling, applied per channel
at whatever depth each one deserves — heavy on coolant temperature, none on
knock. The cost is SPI traffic and a little CPU, both of which there is plenty
of.

Nothing is lost in anti-aliasing by doing this: the second-order analog filter
at 22 kHz is always in circuit and is independent of the OS setting. The
digital filter was only ever noise averaging, and software does that just as
well with far more control.

---

## Which part is actually on the bench? Measure BUSY.

The part bought for the Teensy scope turned out to be a **B-series, not a C**.
For the scope that is a real setback — a scope's whole value is bandwidth, and
200 kSPS against 1 MSPS is a fivefold cut. For this ECU it changes nothing: the
throughput analysis above puts utilisation around 1 % either way.

**So the ECU should take the B-series part now**, rather than waiting behind a
new C-series board. The scope gets the C when that PCB exists. The part that
disappointed one project is the correct choice for the other.

### Identifying it without buying anything

There is still a question worth answering: is it a genuine 800 kSPS AD7606B, or
an AD7606-class 200 kSPS part in AD7606B-looking clothing? The Tokmas datasheet
on file is headed `AD7606BSTZ` but specifies 200 kSPS — and ADI warn that all
three generations are footprint-identical, so a re-marked part passes visual
inspection.

**Conversion time settles it, and the Teensy rig can already measure it.** Time
the BUSY pulse — CONVST rising to BUSY falling — with oversampling off:

| Part | Conversion time, OS off | Implied throughput |
|---|---|---|
| AD7606 (200 kSPS) | **~2.9 µs** typ (2.6–3.2) | 200 kSPS |
| AD7606B (800 kSPS) | **~1.25 µs** | 800 kSPS |

More than a 2× separation, far wider than any measurement error on a Teensy 4.1
with `micros()` — or better, capture BUSY on a scope channel directly.

Two supporting checks that need no instrumentation, both from the datasheet
differences:

- **Input impedance.** 1 MΩ (AD7606) vs 5 MΩ (AD7606B). Measurable with a known
  series resistor and a DC input: the divider ratio reveals which.
- **VDRIVE floor.** The AD7606B runs down to 1.71 V, the AD7606 only to 2.3 V.
  Not worth testing deliberately, but relevant if 1.8 V logic were ever wanted.

Whatever it turns out to be, **both are adequate here**. The measurement matters
for knowing what was actually bought — and for deciding whether the same
supplier is worth using again for the scope's C-series part, where the
difference is the whole point.

### One footprint, but not identical pin functions

All three generations are **LQFP-64 and footprint-compatible**, so one PCB
layout can serve both projects — the ECU board populating a B, the scope board a
C. Worth drawing once, properly, with the input protection and decoupling the
datasheets ask for.

But **footprint-compatible is not function-identical**. Comparing the Tokmas
AD7606-class datasheet against the AD7606C-16 datasheet:

| Pin | AD7606 (200 kSPS) | AD7606C-16 | Matters? |
|---|---|---|---|
| **9, 10** | **CONVSTA, CONVSTB** — two conversion-start inputs | **CONVST (9), WR (10)** — WR is the parallel write strobe | **Yes — see below** |
| 3–5 | OS0–OS2, oversampling only | OS0–OS2, and one code **selects software mode** | Yes |
| 6 | PAR/SER/**BYTE** SEL | PAR/SER SEL — no byte mode | Minor |
| 7 | STBY (with RANGE, selects power-down mode) | STBY **ignored in software mode**; tie high | Minor |
| 8 | RANGE | RANGE **ignored in software mode**, but must still be tied | Minor |
| 19–22 | DB3–DB6 / DOUTE–DOUTH in serial | same | No |
| 23 | VDRIVE 2.3–5 V | VDRIVE **1.71**–5.25 V | No |

**The pin 9/10 difference is the one to get right.** Standard AD7606 practice is
to short CONVSTA and CONVSTB together so all eight channels sample
simultaneously — which is what the existing breakout does (the Teensy driver
notes CONVST "also drives WR via the breakout's own tie").

On an AD7606C those same two pads are CONVST and WR. That is **safe**: the C's
datasheet explicitly permits WR to be "tied high, tied low, or shorted to
CONVST" in hardware mode, and WR is unused entirely over the serial interface.

So a board that shorts 9 and 10 works with either part — as long as it is
driven over SPI, or in hardware mode. It would only break if a C were later run
in **software mode over the parallel interface**, where WR becomes an active-low
register write strobe and shorting it to CONVST would corrupt every write.

Since this design uses the serial interface throughout, shorting them is fine.
Worth a jumper or a 0 Ω link rather than a hard trace, so the scope board keeps
the option of software mode later.

**AD7606C-16 and AD7606C-18 are pin-identical to each other**, so an 18-bit
upgrade on the scope board is a populate-different-part change with no layout
work.

### If it is the 200 kSPS part, the only constraint that bites

Operating temperature: **−40 to +85 °C**, against −40 to +125 °C for the
AD7606B and C. That decides mounting location, not performance. The OEM PCM on
this truck sits in the cabin, so 85 °C is very likely fine — but it rules out an
under-hood enclosure. **[CONFIRM]** where the ECU will live before committing
to an enclosure design.

---

## PCB notes: serial mode, and why the pull-downs matter

### Serial data outputs differ substantially

| | AD7606 (200 kSPS) | AD7606C-16 |
|---|---|---|
| Serial outputs | **DOUTA (24), DOUTB (25)** — two lines | **DOUTA (24), DOUTB (25), DOUTC (27), DOUTD (28), DOUTE (19), DOUTF (20), DOUTG (21), DOUTH (22)** — eight |
| Serial data **input** | none | **DB11/SDI (29)** — register writes in software mode |
| Byte-mode pins | DB14/**HBEN** (32), DB15/**BYTE SEL** (33) | plain DB14, DB15 — byte mode dropped |

The C can stream all eight channels on eight separate lines simultaneously,
which is how it sustains 1 MSPS. Reading a single DOUTA works on both parts, so
a design that uses only DOUTA is portable — it just leaves the C's throughput
on the table, which for this ECU is fine.

**Byte mode is the pin reuse on the AD7606:** with `PAR/SER/BYTE SEL` high and
`DB15/BYTE SEL` high, the part enters parallel *byte* mode and `DB14/HBEN`
selects whether the **high byte or the low byte** of the 16-bit result comes out
first on DB[7:0]. The C drops this entirely — those pins are plain data bits.

### Pins that must be tied in serial mode — and the hazard

The AD7606C-16 datasheet is explicit: *"When using the serial interface, tie the
DB0 to DB2 pins to AGND."* (pins 16–18).

On the **AD7606**, those same pads are DB0–DB2, plain **parallel data outputs**.
A board that hard-grounds pins 16–18 for the C, then has an AD7606 populated,
is shorting three digital outputs to ground any time they drive high.

**The 10 kΩ resistor arrays are the correct fix.** A 10 kΩ pull-down satisfies
the C's requirement — it is a logic-level tie, not a current path — while
limiting fault current to about 0.5 mA if an AD7606 ever drives that pin high.
Safe with either part populated, and it keeps one layout genuinely usable for
both projects.

Worth extending the same treatment to every pin whose function differs:

| Pin | Treat how | Why |
|---|---|---|
| 16–18 (DB0–DB2) | **10 kΩ to AGND** | C requires grounding in serial mode; AD7606 drives them |
| 29 (DB11/SDI) | 10 kΩ, and route to MCU MOSI | SDI on the C in software mode; a data output on the AD7606 |
| 19–22 (DB3–DB6 / DOUTE–H) | leave routed, no hard tie | serial outputs on the C, parallel outputs on the AD7606 |
| 9/10 (CONVST, WR) | 0 Ω link, not a hard trace | see the pin 9/10 note above |
| 32, 33 | no hard tie | HBEN / BYTE SEL on the AD7606, plain data on the C |

### Two pins to get right regardless of part

- **REF SELECT (34)** — identical on both. **High selects the internal 2.5 V
  reference.** Tied low, the internal reference is *disabled* and an external
  2.5 V must be supplied on REFIN/REFOUT (42). Leaving this floating or low by
  accident produces a part that converts, but against nothing.
- **REFCAPA (44) / REFCAPB (45)** — must be shorted together and decoupled to
  AGND with a low-ESR 10 µF. They sit at about 4.5 V. REFIN/REFOUT wants its own
  10 µF to REFGND.

### The VxGND pins are what make the MAF measurement work

Each analog input is a **pair**: V1 (49) and V1GND (50), V2 (51) and V2GND, and
so on. The block diagram shows both going into the front-end amplifier as `+`
and `−` through separate input clamps.

The datasheets advise connecting VxGND to the AGND plane, which is right for an
ordinary single-ended sensor. **The MAF is the exception, and the reason this
part was chosen:** MAF signal (circuit 967) to V1, and MAF *signal return*
(circuit 968) to V1GND — not to AGND. That is what cancels the ground drop
caused by the hot-wire's own supply current. See
`1999-Ford-F150-4wd-5.42v/oem-connectors.md`.

**[CONFIRM]** the allowable VxGND voltage range relative to AGND before relying
on this. It only needs to accommodate a few tens of millivolts of harness ground
drop, which should be comfortably inside spec — but exceeding it would be a
design error rather than a degradation, so it is worth reading the number rather
than assuming.

---

## Resolution: 18-bit is pointless here, and 16-bit is not really 16-bit

### The datasheet already concedes it

From the Tokmas AD7606 figures, converting to effective number of bits with
`ENOB = (dB − 1.76) / 6.02`:

| Datasheet figure | Value | ENOB |
|---|---|---|
| SNR typ, no oversampling, ±10 V | 87 dB | **14.16 bits** |
| SNR min | 83 dB | 13.50 bits |
| **SINAD typ** (includes distortion) | 84.5 dB | **13.74 bits** |
| SINAD min | 83 dB | 13.50 bits |
| SNR with 64× oversampling | 90 dB | 14.66 bits |

**A 16-bit part delivers about 13.7 effective bits on a lab bench**, before a
single wire is run through an engine bay. The two bits at the bottom are noise
in the part itself.

### And that is the good case

In a truck the limits are elsewhere entirely, all of them larger than
quantisation:

- **Harness pickup.** Eight coil-on-plug primaries and eight injectors switching
  inductive loads, metres from the signal wires. This dominates everything.
- **Sensor noise.** A TPS is a potentiometer with a wiper — contact noise alone
  exceeds 14-bit resolution.
- **VREF.** Every three-wire sensor is ratiometric, so sensor accuracy is capped
  by VREF accuracy. The channel-7 correction cancels VREF *drift*, but not VREF
  *noise*.
- **Ground drop**, even with the Kelvin sense on the MAF.

Realistically **11 to 12 genuinely trustworthy bits** is the target in a
vehicle, and getting there is a wiring, shielding and grounding problem — not a
converter problem.

### How much resolution the sensors actually deserve

| Signal | Useful resolution | Bits needed |
|---|---|---|
| TPS | 0.1 % throttle | ~10 |
| MAF | better than the sensor's own repeatability | ~11 |
| CHT / IAT | 0.5 °C | ~10 |
| O2 narrowband | it is a switching sensor | ~8 |
| Battery voltage | 0.1 V | ~8 |

Nothing on this truck needs more than about 11 bits. At ±10 V a 16-bit LSB is
305 µV, so 0.1 % of throttle travel already spans 16 codes — resolution is not
close to being the limiting factor.

### So why this part at all?

**The front end, not the bit count.** What is actually being bought:

- **±16.5 V input clamps** — survives a harness fault.
- **8 kV ESD** on the analog inputs.
- **1 MΩ input impedance** — does not load the sensors.
- **Second-order anti-aliasing filter at 22 kHz**, always in circuit.
- **True bipolar ±10 V inputs** — 0–5 V sensors connect directly, no scaling.
- **Simultaneous sampling** — which is what makes the VREF correction exact.
- **Paired VxGND inputs** — the only way to measure the MAF correctly.

Any of those matter more in a truck than the difference between 14 and 16 ENOB.
The 18-bit C-18 would add roughly two more bits of lab-bench SNR and nothing at
all that survives the drive home.

### What this means for the software

- **Do not chase resolution.** Software averaging is for rejecting harness
  noise, not for recovering sub-LSB detail that does not exist.
- Averaging 16 samples buys 2 bits against *uncorrelated* noise. Ignition noise
  is **not** uncorrelated — it is periodic with engine position — so averaging
  blindly across a coil event does less than the √N maths promises. Sampling
  *away from* known switching events is worth more than averaging through them.
- Treat anything below about bit 4 of a 16-bit reading as noise, and do not
  build control logic that depends on it.
