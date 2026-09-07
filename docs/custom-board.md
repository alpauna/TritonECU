# Custom ECU board — raw ESP32-P4

Replaces the Waveshare carrier. Everything the truck needs, nothing it does not.

## GPIO0–15 are usable — question resolved

An earlier concern: ESP-IDF's `SOC_GPIO_VALID_DIGITAL_IO_PAD_MASK` for the P4
is `0x007FFFFFFFFF0000`, which excludes GPIO0–15 and looked like it might halve
the usable pin count.

It does not. `SOC_RTCIO_PIN_COUNT = 16` — **GPIO0–15 are the RTC/LP IO pins**.
They are dual-domain: ordinary digital I/O through the HP GPIO matrix, *and*
reachable by the LP core. The mask means "digital-only pads", and these have an
extra function rather than a missing one. The Waveshare board runs an I2S codec
on GPIO9–13, which settles it empirically.

One useful consequence: RTC/LP pins support **hold** — they retain their state
across resets and sleep. For an ECU that is worth having on outputs that must
stay in a known state, though it also means hold has to be explicitly released
on wake or the pin appears stuck.

## Pin assignment

55 GPIOs. Committed first:

| GPIO | Reserved for |
|---|---|
| 14–19 | SDIO to the ESP32-C6 — D0 14, D1 15, D2 16, D3 17, CLK 18, CMD 19 |
| 54 | ESP32-C6 reset |
| 35, 36 | boot strapping — BOOT_MODE, BOOT_MODE2 |
| 37, 38 | UART0 — console and flashing |
| 39–45 | SD card, SDMMC slot 0 (45 = card power) |

That is 20 committed, leaving **35**, plus GPIO24/25 if USB OTG is not fitted.

### Engine control

| Function | GPIO | Notes |
|---|---|---|
| Coil 1–8 | **46, 47, 48, 49, 50, 51, 52, 53** | contiguous, no strapping pins |
| Injector 1–8 | **26, 27, 28, 29, 30, 31, 32, 33** | contiguous |
| CKP (VR ch1) | **20** | MAX9926 #1 COUT1 |
| CMP (VR ch2) | **21** | MAX9926 #1 COUT2 |
| OSS (VR ch3) | **22** | MAX9926 #2 COUT1 |
| TSS (VR ch4) | **23** | MAX9926 #2 COUT2 — spare until a 4R100 appears |

### Buses and analog

| Function | GPIO |
|---|---|
| SPI SCK | 34 |
| SPI MISO | 2 |
| AD7606 CS | 3 |
| AD7606 CONVST | 4 |
| AD7606 BUSY | 5 |
| MCP23S17 chain CS | 6 |
| I2C SDA / SCL | 1 / 24 |

### Timed outputs and the bus

| Function | GPIO |
|---|---|
| J1850 TX_P / TX_N / RX | 7 / 8 / 9 |
| TCC PWM | 10 |
| EPC PWM | 11 |
| IAC PWM | 12 |
| Tach out | 13 |
| VSS out (to cruise) | 0 |

**36 assigned, 1 spare (GPIO25).** Tight but complete.

If more headroom is wanted, in order of least pain:
1. **SD in 1-bit SDMMC** — CLK, CMD, D0 only. Frees 3.
2. Drop USB OTG entirely — already assumed above, frees 24/25.
3. Move the SD card onto the shared SPI bus with its own CS. Frees 6, but the
   card then contends with the ADC, which is a poor trade in an ECU.

## The one thing that must not be got wrong

**Every coil and injector gate needs a hard pulldown to ground — around 10 kΩ,
at the gate, on the board.** Decided, and being done.

At reset and during the whole bootloader sequence, every P4 GPIO is an input
and therefore high-impedance. A driver gate left floating can drift high enough
to turn the device partly on. That means:

- **A coil held on** — no current limit, and an ignition coil will destroy
  itself in seconds.
- **An injector held open** — fuel poured into a cylinder while the engine is
  not turning, then hydraulic lock or a crankcase full of petrol.

Neither is recoverable and both happen before a single line of firmware runs,
so this cannot be solved in software. The pulldown is the fix. Verify it with a
meter on a bare board before any coil or injector is ever connected.

The same argument applies more mildly to the fuel pump relay and the EVAP,
EGR and IMCC solenoids — all should default off.

### With a gate driver in the path, pull down its input too

Gate drivers are the right call for real power MOSFETs — the P4 cannot supply
the peak gate current a large FET wants, and slow switching is where the heat
comes from. But adding a driver moves where the boot-state problem lives.

A 10 kΩ pulldown at the MOSFET gate defends against **leakage and charge
injection**. It does not defend against a **driver actively sourcing current**
into that gate: a driver output will overpower 10 kΩ without noticing. So the
pulldown at the gate is necessary but no longer sufficient on its own.

Two additions:

1. **Pull down the driver's input as well.** During reset the P4 pin driving
   it is high-impedance, and a floating driver input may give an undefined
   output. This is the cheap fix and it is where the real protection now sits.
2. **Use the driver's enable/shutdown pin if it has one**, held disabled by a
   pulldown and asserted only once firmware has taken control. That is a
   stronger guarantee than relying on input state, because it holds the output
   off regardless of what the input is doing.

Also check the driver's **UVLO** behaviour: many hold the output low until
their supply is valid, which covers the brown-out and cranking cases for free.
Worth choosing a part that does.

### Coils are not just another inductive load

**[CONFIRM ON TRUCK]** whether the '99 5.4L COP coils are "dumb" two-wire coils
or "smart" coils with an integrated driver and logic-level input. It decides
the whole ignition output stage:

- **Smart coils** — feed them a logic-level signal. The coil owns the current
  limiting and clamping. Nothing more needed.
- **Dumb coils** — the board must provide the switch, and an ignition primary
  flies back to several hundred volts on turn-off. That wants a purpose-built
  **ignition IGBT with integrated clamp**, not a general-purpose MOSFET. The
  clamp is what dissipates the coil's stored energy in a controlled way; a
  plain FET without one avalanches, and repeated avalanche at 400 sparks per
  second is not a long life.

Injectors are gentler but still inductive: a saturated high-impedance Ford
injector needs a flyback path, either an avalanche-rated FET within its energy
spec or an explicit clamp.

Also: keep coil and injector outputs off GPIO35/36. They are strapping pins,
sampled at reset, and a driver's pulldown would fight the boot configuration.

## What the raw chip costs you

Against a module, the board now owns:

- **QSPI flash** — the P4NRW32 carries PSRAM in package but needs external NOR
  flash, with the usual length-matching and termination care.
- **40 MHz crystal** and its loading.
- **Power sequencing and rails.** **[CONFIRM]** the P4's supply requirements
  against the datasheet before drawing the power tree; this is the part with
  the least margin for guessing.
- **The ESP32-C6, if Wi-Fi is wanted** — a second chip, its own flash, an
  antenna and RF layout.

**Decided: raw P4, with the ESP32-C6 as a pre-certified module.** That keeps
full P4 pin access — the whole reason for going raw — while avoiding RF layout
and certification entirely. The C6-MINI-1 is what the Waveshare board uses, and
it connects over the SDIO pins already reserved above (GPIO14–19 plus reset on
54).

## Chip revision: buy v3.x

Chip revision matters, and the bench board is not representative of what to
build with. The Waveshare board reports **rev v1.3** — engineering-sample era.
Current production is **v3.x**, and the differences are worth having:

| Change | Relevant here? |
|---|---|
| **360 MHz → 400 MHz** | modestly |
| **MSPI power-on wake-up fault (load access fault) fixed** | **yes — see below** |
| Secure boot verification failures fixed | if secure boot is ever used |
| Dedicated RNG, AES DPA resistance, ECC P-384 | no |
| ISP, PPA, I2S improvements | no — multimedia |
| Zb bit-manipulation extensions, PIE tuning | marginally |

**No GPIO or pin-function changes**, so the assignment above stands on either
revision.

### The MSPI fix is the reason to insist on v3.x

MSPI is the memory interface to flash and PSRAM. A **power-on wake-up fault**
there means a load access fault at start-up — the processor failing to read the
memory it is executing from.

An ECU is close to the worst case for that bug. It power-cycles every time the
key turns, and it does so through cranking, where the battery sags to 8–9 V and
the rails are at their most marginal. A fault that appears at power-on, on a
device that power-cycles several times a day, in a vehicle, is not a defect to
live with.

### Consequence for the firmware

The PlatformIO target changes from `esp32-p4` (ES variant, 360 MHz) to
**`esp32-p4_r3`** (400 MHz). Trivial, but worth flagging: anything validated on
the bench board runs 11 % faster on production silicon. Hardware-timer-driven
spark and injection are unaffected — timers have their own clock source — but
any delay loop or cycle-counting written against 360 MHz would shift, which is
a good reason not to write any.
