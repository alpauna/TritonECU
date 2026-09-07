# Wiring the AD7606 to the ESP32-P4

Bench wiring for M2. All pin numbers are **GPIO numbers as silkscreened on the
Waveshare board**, not header positions — the silkscreen is unambiguous.

## Power — check this first

| AD7606 | P4 header | Note |
|---|---|---|
| **AVDD** | **VBUS** (5 V) | 4.75–5.25 V. Draws ~22 mA, so USB 5 V is fine |
| **VDRIVE** (DVDD) | **3V3** | **must be 3.3 V — see the warning below** |
| **AGND, DGND** | any **GND** | use at least two GND wires, one per side |

> **The P4 is not 5 V tolerant.** If the breakout has VDRIVE strapped to 5 V,
> DOUTA will swing to 5 V and damage the P4 input.
>
> It is very probably already at 3.3 V: the Teensy 4.1 is also 3.3 V and also
> not 5 V tolerant, so the module must already be set that way to have worked
> there. **Confirm with a meter on the DOUTA pin before connecting anyway** —
> it costs a minute and the alternative is a dead board.

## Signals

**Right side of the header** (top to bottom as printed):

| AD7606 | GPIO | Direction |
|---|---|---|
| CONVST (CONVSTA+CONVSTB) | **26** | P4 → ADC |
| SCLK (RD/SCLK) | **27** | P4 → ADC |
| *(reserved — MOSI, unused)* | *32* | — |
| **DOUTA** (DB7/DOUTA) | **33** | ADC → P4 |
| CS | **46** | P4 → ADC |
| OS1 | **47** | P4 → ADC |
| OS2 | **48** | P4 → ADC |

**Left side of the header** (top to bottom as printed):

| AD7606 | GPIO | Direction |
|---|---|---|
| OS0 | **31** | P4 → ADC |
| FRSTDATA | **30** | ADC → P4 |
| RESET | **29** | P4 → ADC |
| BUSY | **28** | ADC → P4 |
| RANGE | **2** | P4 → ADC |

Eleven signals. MOSI is not wired — in hardware mode range and oversampling are
set by pins, not registers, so nothing is ever written to the part.

## Straps the module must already have right

Most breakouts handle these, but they are worth checking before blaming the
software:

| Pin | Must be | Why |
|---|---|---|
| **PAR/SER/BYTE SEL** | **HIGH** | selects the serial interface |
| **DB15/BYTE SEL** | **LOW** | high *with* PAR/SER high selects parallel byte mode instead |
| **REF SELECT** (34) | **HIGH** | enables the internal 2.5 V reference. Low means the part converts against nothing unless an external reference is fed to REFIN/REFOUT |
| **STBY** (7) | **HIGH** | low puts the part in standby/shutdown |
| **CONVSTA / CONVSTB** (9, 10) | **tied together** | so all eight channels sample simultaneously. Usually already tied on the breakout |
| REFCAPA / REFCAPB (44, 45) | shorted, 10 µF to AGND | on-module |

## Analog inputs

For the first bench test only channel V1 needs anything connected:

- **V1 (49)** — the signal under test
- **V1GND (50)** — to AGND for a normal single-ended measurement

Later, for the MAF, **V1GND takes circuit 968 (the MAF signal return)** rather
than AGND — that is the differential measurement the whole part was chosen for.
See `1999-Ford-F150-4wd-5.42v/oem-connectors.md`.

Unused inputs should not float. Tie V2–V8 to their own VxGND on the module.

## Dupont leads: only two wires actually matter

Eleven jumpers sounds like a signal-integrity problem. It mostly is not — of the
eleven, **nine are DC or single slow edges**:

| Wires | Character | Care needed |
|---|---|---|
| RESET, OS0, OS1, OS2, RANGE | **static** — set once at startup and never change | none |
| FRSTDATA | one edge per conversion, only read, currently unused | little |
| CS, CONVST, BUSY | one edge per conversion, microseconds apart | moderate |
| **SCLK, DOUTA** | **the clocked pair** — every bit rides these | **all of it** |

So the effort belongs on **SCLK (GPIO27) and DOUTA (GPIO33)**:

- **Keep those two shortest**, and give each a **ground return running alongside
  it**. Return current has to get back somehow; with a loose bundle of Duponts
  it finds the longest possible loop, and that loop is the antenna. The header
  has four GND pins per side — use them, do not share one ground for eleven
  signals.
- Avoid running SCLK as the outermost wire of a bundle where it can couple into
  DOUTA. If they must be adjacent, put a ground wire between them.
- The static lines can be any length and can share a ground. They are set once
  and read never.

### Start slow, then raise it

The driver now defaults to **1 MHz SPI**, not 8 MHz, and the clock is settable
at runtime. The Teensy build did the same — 1 MHz through initial bring-up,
raised to 8 MHz only after readings were validated against a known reference.

Bring-up order:

1. Wire it, boot at 1 MHz, confirm the part is detected and grounded inputs read
   near zero.
2. Apply a known voltage and confirm it within 1 %.
3. *Then* raise the clock and re-check the same known voltage. If the reading
   changes, the wiring is the limit, not the part — the AD7606 itself will take
   63.5 MHz.

At 1 MHz, eight channels take about 128 µs of bus time. At the 2 kHz sampling
this ECU needs, that is 26 % duty — workable, but tight enough that the clock
does want raising once the wiring is trusted, and definitely before knock
sampling.

## What M2 will print

Once wired, the firmware reports all eight channels in volts, twice a second.
Expected first results:

1. **All channels near 0 V** with inputs tied to ground.
2. Apply a known bench voltage to V1 — should read within 1 %.
3. `begin()` fails loudly on a BUSY timeout rather than reporting zeros, so a
   wiring mistake shows up as an error message rather than plausible-looking
   garbage.

Default range is **±10 V**, oversampling **off** (averaging is done in software
— see `adc-front-end.md`).
