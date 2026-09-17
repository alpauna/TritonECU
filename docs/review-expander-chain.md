# Expander chain review — pre-schematic

The MCP23S17 chain has been on every pin budget since the first one, and has
never been reviewed on its own. It is treated everywhere as the place things go
when they are *not* interesting: `pin-budget.md` excludes it from the native
count because it "costs nothing beyond the one chip-select already counted", and
`cooling-fans.md` spends a bit on Fan 2 because "the expander chain is on the
board regardless and has spare bits".

Three questions, and the chain fails the first two:

1. Does it work electrically, given what it is wired to?
2. Does it fit?
3. Does it fail safely?

---

## 1. BLOCKING — a 3.3 V SPI master cannot drive a 5 V MCP23S17

[`v1-scope.md`](v1-scope.md) specifies **"2 × MCP23S17, at 5 V"**, and
[`output-drivers.md`](output-drivers.md) makes that binding: *"The
expander-driven channels need no buffer, **provided the MCP23S17 chain runs at
5 V.** That is now a requirement rather than a free choice."*

From the datasheet, DC characteristics D041:

| Input | Symbol | Min | Note |
|---|---|---|---|
| `CS`, GPIO, `SCK`, `SI`, A2, `RESET` (Schmitt) | V<sub>IH</sub> | **0.8 V<sub>DD</sub>** | *over the entire V<sub>DD</sub> range* |

```
VDD = 5.0 V  ->  VIH = 4.00 V
STM32F767 VOH, 3.3 V rail, push-pull   =  3.3 V max

                      3.3 V  <  4.0 V        FAILS BY 0.7 V
```

**Not marginal — short by 0.7 V, with no tolerance stack needed to get there.**
`SCK`, `SI` and `CS` all miss. The part may appear to work on a bench at room
temperature, because 0.8 V<sub>DD</sub> is a guaranteed limit rather than a
typical threshold, which is the worst possible failure mode: it works until it
is cold, or hot, or the rail is at 5.25 V.

**The project had already computed this number and did not apply it here.**
[`output-drivers.md`](output-drivers.md#sizing-the-divider--and-why-it-is-not-a-logic-input)
sizes the drain-sense divider against **V<sub>IH</sub> = 4.0 V** — the same
figure, for the same chip, on the same rail — and concludes *"there are no values
that work."* That conclusion was applied to the divider and never to the three
SPI lines that drive the chip.

---

## 2. BLOCKING — the ADC's static pins cannot share a 5 V expander

[`adc-front-end.md`](adc-front-end.md) moves six ADS8588H pins onto this chain:
`RESET`, `FRSTDATA`, `OS0`, `OS1`, `OS2`, `RANGE` — *"static or near-static, so
they do not deserve native pins."* Correct reasoning about **which pins**, made
without checking **what voltage** they would arrive at.

From the ADS8588H datasheet:

| | |
|---|---|
| DVDD, recommended | **2.3 V to AVDD** |
| Digital input, absolute maximum | **−0.3 V to DVDD + 0.3 V** |
| V<sub>IH</sub> | **0.8 × DVDD** |

The bench mapping in that same document has **VDRIVE = 3.3 V**. So:

```
DVDD = 3.3 V   abs max digital in = 3.60 V   <-  a 5 V expander output
                                                  EXCEEDS IT BY 1.4 V
```

**And raising DVDD to 5 V does not rescue it**, because V<sub>IH</sub> is
0.8 × DVDD on this part too — the identical trap as §1, now on the ADC:

```
DVDD = 5.0 V   VIH = 4.00 V   <-  the STM32's own 3.3 V SCK/CS/SDI
                                   FAILS BY 0.7 V
```

There is no DVDD that satisfies both a 3.3 V master and a 5 V expander.

### The shared MISO net is the part that bites hardest

Even level-shifting the three outbound lines does not close it. `SO` on the
expander and `DOUTA` on the ADC are the **same net**:

```
   MCP23S17 SO  ──┬──────────────┬──  STM32 MISO
   (5 V push-pull)│              │
                  │        ADS8588H DOUTA
                  │        (DVDD = 3.3 V, abs max 3.6 V)
                  │
        drives this net to 4.3 V (VOH = VDD - 0.7)
        whenever the expander is selected
```

`DOUTA` is high-impedance when the ADC is deselected, but **absolute maximum is
a pin rating, not a driver rating** — 4.3 V on a 3.6 V pin conducts through the
ESD structure regardless of whether the output stage is enabled. The ADC is
damaged by traffic addressed to the expander.

---

## 3. IMPORTANT — the bit count has never been done, and it does not fit

"Has spare bits" is an assumption that appears in at least three documents and
is stated in none of them as a count. Counted:

| Explicitly assigned to the chain | Bits |
|---|--:|
| Relays — fuel pump, fan 1, **fan 2**, A/C clutch | 4 |
| NCV8405A — IMCC, HO2S heaters ×4, SS1, SS2, CSS | 8 |
| ADS8588H static — RESET, FRSTDATA, OS0-2, RANGE | 6 |
| MAX25239 `SYNC` — *added closing the power-chain review* | 1 |
| Inputs — TR ×4, brake, A/C pressure switch, 4x4 low | 7 |
| **Subtotal** | **26** |

| Has no native pin and no stated home | Bits |
|---|--:|
| VREF — `EN`, `IN1`, `IN2`, `DIAG_EN`, `SEL`, `FAULT` — [`vref-supply.md`](vref-supply.md) states *"Pin cost: 6 GPIO"* and the 37-pin native map does not contain them | 6 |
| Watchdog kick — *"can share the expander chain"*, [`custom-board.md`](custom-board.md) | 1 |
| 74HCT541 #2 `OE`, the PWM gate buffer | 1 |
| Power supervisory — LTC4364 `SHDN#` / `FLT#`, MAX25239 `PGOOD`, INA238 `ALERT` | 4 |
| **Subtotal** | **12** |

```
                2 x MCP23S17  =  32 bits
                       demand =  38 bits      OVER BY 6

    ignoring the four supervisory signals =  34 bits      OVER BY 2
```

**It is over even on the conservative count.** The VREF block alone is six bits
that every document assumed someone else was carrying — `vref-supply.md` says
"6 GPIO" and stops, `custom-board.md`'s 37-pin map does not list them, and this
chain was never told.

A third MCP23S17 costs one package and no pins — the chain is addressed, not
chip-selected. That is the cheap fix. **The count is the finding, not the
shortage.**

---

## 4. IMPORTANT — expander outputs survive an MCU reset

The MCP23S17 holds its output latches until it is written or reset. Its `RESET`
pin is not mentioned in any document.

If the MCU hangs and the watchdog resets it, the STM32's own GPIOs go
high-impedance and the ignition buffer's `OE2` — already watchdog-driven — kills
the coils. **Nothing does that for the expander.** Through the reset and the
several hundred milliseconds of re-boot:

| Latched output | Consequence |
|---|---|
| **Fuel pump relay** | pump runs with no injection and no spark |
| **HO2S heaters ×4** | ~4 × 1 A into cold sensors, unmonitored |
| **A/C clutch**, **shift solenoids** | held in whatever gear the fault caught |

**Drive `RESET` from the same watchdog that gates `OE2`**, not from a pull-up.
The power-on state is genuinely safe (§7), so a reset that reaches the expander
lands everything in a known-off condition.

---

## 5. IMPORTANT — two chips, one chip-select, and HAEN is off at power-up

[`custom-board.md`](custom-board.md) allocates **one** `MCP23S17 chain CS` for
both devices, which is correct and is why the chain is cheap. It depends on
hardware addressing, and the datasheet is explicit that hardware addressing is
**disabled** after reset:

> IOCON reset value `0000 0000` — and *"when disabled (HAEN = 0), the device's
> hardware address is A2 = A1 = A0 = 0"*, regardless of the strapping pins.

So out of reset **both chips are device 0**. Writes are harmless — both receive
the same IOCON byte, which is exactly how HAEN gets enabled in the first place.

**Reads are not.** A read of `GPIOA` before HAEN is set has both chips driving
`SO` simultaneously, and their `GPIOA` contents differ because their input pins
are connected to different things. Two push-pull outputs, opposite states, on
one net.

```
  firmware rule, and it is a hardware constraint not a style preference:

     1. write IOCON.HAEN = 1     (opcode address 000, reaches both)
     2. only then address, configure or READ either device
```

Worth stating in the schematic notes as well as the driver, because it is
invisible at the symbol level and it survives as a latent fault — the contention
is brief and the parts usually live through it.

---

## 6. MODERATE — INTA/INTB are unassigned and no polling rate is stated

Eleven of the bits are inputs. `INTA`/`INTB` appear in no document, so the
implied design is polling, at a rate nobody has written down.

The one input where this has a real deadline is the **A/C cycling pressure
switch**. [`cooling-fans.md`](cooling-fans.md) already establishes that this
truck has *no A/C request line* — only the cycling switch — and that its chatter
needs a hold-on timer. A hold-on timer built on a polled input needs the poll
to be fast relative to the chatter, and "fast relative to the chatter" is
currently unquantified in both directions.

`MIRROR` in IOCON ORs the two interrupt outputs into one pin, so this costs a
single native GPIO if it is wanted. **Decide it deliberately**: either wire
`INTA` with `MIRROR = 1`, or state the poll interval and show it bounds the
chatter.

---

## 7. Checked and clear

| | |
|---|---|
| **Power-on state is fail-safe** | MCP23S17 ports reset to **inputs**, high-Z. The NCV8405A gate draws I<sub>GSSF</sub> = 50–100 µA at V<sub>GS</sub> = 5 V, so it has a DC path to source and a floating gate sits at 0 V; the TBD62083A input draws 100 µA at 2.5 V, likewise. **Both driver families default off with nothing driving them** |
| **Per-pin and package current** | 25 mA per pin, 150 mA out of V<sub>SS</sub>, 700 mW. Actual load is 8 gates × 100 µA + 4 relay inputs × 100 µA ≈ **1.2 mA**. Three orders of margin |
| **Chain supply current** | I<sub>DD</sub> 1 mA max each at 1 MHz; standby 1 µA. The 20 mA carried for the pair in the 5 V budget is generous and stays |
| **Bus speed** | 10 MHz max on the MCP23S17, and nothing on this chain is fast. The SD card is on **SDMMC**, not SPI, so the only bus partner is the ADC |
| **`SYNC` on the expander** | Added in the power-chain review with a pulldown, and it holds up: high-Z at power-on means skip mode, which is the safe default |

---

## 8. Aside — the ADS8588H temperature claim is wrong, and it was load-bearing

Found while checking §2. [`adc-front-end.md`](adc-front-end.md) says of the
production ADC:

> *"**Temperature: −40 to +85 °C, not +125 °C.** This decides where the ECU can
> mount … it rules out an under-hood enclosure, and that is a decision better
> made now than after the board is built."*

The datasheet specifies min/max **over T<sub>A</sub> = −40 °C to +125 °C**, and
Recommended Operating Conditions gives operating free-air temperature as
**−40 to 125 °C**. The only 85 °C limit on the part is a condition on
I<sub>AVDD_PWR_DN</sub>, the power-down leakage spec.

**The ADS8588H does not rule out an under-hood enclosure.** The AD7606B *bench*
part is an 85 °C device, which is the likely source of the mix-up.

This matters to the recommendation below, because the MCP23S17 is only rated to
+125 °C **at V<sub>DD</sub> ≥ 4.5 V** — at 3.3 V it is an 85 °C part.

---

## Recommendation: move the chain to 3.3 V and buffer the eight gates

Two ways out, and they are not equal.

| | **A — keep 5 V, translate the SPI** | **B — 3.3 V chain, buffer the gates** |
|---|---|---|
| New parts | 1 × SN74LVC8T245 or similar dual-bank translator | 1 × **74HCT541** — already in the BOM twice |
| Fixes §1 | yes | yes |
| Fixes §2 | **only with a down-translator on `SO`** | **structurally** — one voltage domain on the whole bus |
| Expander temp rating | −40 to **+125 °C** | −40 to **+85 °C** |
| Side benefit | none | the 8 gates gain a hardware `OE`, which §4 wants anyway |

**Take B.**

The 5 V requirement was created in `output-drivers.md` to *save* a buffer. It
costs a level translator, an absolute-maximum violation on a $5.60 ADC, and a
mixed-domain SPI bus — to avoid a 20-pin part that already appears twice on this
board. The trade is upside down.

```
  STM32          MCP23S17 x2
  3.3 V SPI ──►  @ 3.3 V  ──┬──►  TBD62083A relays
                            │     (VIN(ON) 2.5 V - direct, unchanged)
                            │
                            ├──►  74HCT541 @ 5 V ──►  8 x NCV8405A gates
                            │     (HCT VIH 2.0 V in, 5 V out)
                            │
                            └──►  ADS8588H static pins
                                  (DVDD 3.3 V - now legal)
```

Every level in that chain is satisfied:

| Interface | Needs | Gets | |
|---|---|---|---|
| STM32 → MCP23S17 @ 3.3 V | V<sub>IH</sub> 0.8 × 3.3 = **2.64 V** | 3.3 V | ✓ |
| MCP23S17 → 74HCT541 | V<sub>IH</sub> **2.0 V** (HCT) | V<sub>OH</sub> = V<sub>DD</sub> − 0.7 = **2.6 V** | ✓ |
| 74HCT541 → NCV8405A gate | R<sub>DS(on)</sub> specified at **V<sub>GS</sub> = 5 V** | 5 V | ✓ |
| MCP23S17 → TBD62083A | V<sub>IN(ON)</sub> **2.5 V** | 2.6 V | ✓ *(see below)* |
| MCP23S17 → ADS8588H | V<sub>IH</sub> 0.8 × 3.3 = **2.64 V**, abs max 3.6 V | 2.6 V | ⚠ *(see below)* |
| MCP23S17 `SO` → STM32 | V<sub>IH</sub> **2.0 V** | 2.6 V | ✓ |

Two of those are tight enough to name rather than wave through, and both come
from the same place — V<sub>OH</sub> = V<sub>DD</sub> − 0.7 V is specified at
I<sub>OH</sub> = −3.0 mA, and these loads draw microamps:

- **Against the TBD62083A** the worst case is 2.6 V against 2.5 V — 100 mV. At
  100 µA of actual load the real V<sub>OH</sub> is within millivolts of the rail,
  so there is no practical risk, but the *specified* margin is thin.
- **Against the ADS8588H** the worst case is 2.6 V against 2.64 V, which is
  **specified-negative by 40 mV** on the same reasoning.

**[CONFIRM]** V<sub>OH</sub> at microamp loading before committing, or add a
pull-up on the six ADC static lines, which costs six resistors and removes the
question outright. The lines are static, so a pull-up has no speed cost.

### What B forfeits, deliberately

**The expander becomes an 85 °C part.** That is now a real constraint rather
than one already imposed by the ADC, because §8 shows the ADC never imposed it.
The OEM PCM on this truck mounts in the cabin and the plan has always been to do
the same — but after §8, **the cabin mount is a decision this design is now
making, not one it inherited.** Record it as such.

---

## Summary

| # | Finding | Severity |
|---|---|---|
| 1 | 3.3 V SPI cannot meet V<sub>IH</sub> = 0.8 V<sub>DD</sub> = 4.0 V on a 5 V MCP23S17 — short by 0.7 V. The project computed this exact number for the drain-sense divider and never applied it to `SCK`/`SI`/`CS` | **blocking** |
| 2 | Six ADS8588H pins were moved onto a 5 V chain; digital-input abs max is DVDD + 0.3 = 3.6 V. No DVDD satisfies both a 3.3 V master and a 5 V expander, and the shared MISO net exceeds the ADC's rating on expander traffic | **blocking** |
| 3 | The bit count had never been done. **38 against 32**, or 34 on the conservative count. The VREF block's six GPIOs have no home in any document | important |
| 4 | Expander outputs hold through an MCU reset — fuel pump and four O2 heaters latch on. `RESET` is unmentioned; it should be watchdog-driven | important |
| 5 | Two chips on one `CS` with HAEN off at power-up: both are device 0, and a read before HAEN is set puts two drivers on `SO` | important |
| 6 | `INTA`/`INTB` unassigned and no poll rate stated, against an A/C pressure switch whose chatter already needs a timer | moderate |
| 8 | `adc-front-end.md`'s "−40 to +85 °C" for the ADS8588H is wrong — it is a 125 °C part, and the claim was being used to rule out under-hood mounting | correction |

Findings 1, 2 and 3 are the same failure this session keeps turning up, in its
third form. Not a budget spent elsewhere this time, but a **requirement** —
*"the chain runs at 5 V"* — declared in `output-drivers.md` to serve the gate
drive, while `adc-front-end.md` moved six 3.3 V pins onto the same chain and
`vref-supply.md` charged six GPIOs to nobody. Each document was locally right.

**No document owns the expander chain.** That is the fix: this one now does.
