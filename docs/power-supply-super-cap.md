# Supercapacitor input — preliminary

**Status: idea, not a decision.** Nothing here is settled and the LM5155-Q1
SEPIC in [`power-supply.md`](power-supply.md) remains the current design.
Recorded so the reasoning is not lost.

## The idea

Replace the wide-input SEPIC with an ordinary buck (or an off-the-shelf USB-C
car-charger module) and put a **supercapacitor bank on its input**, so the
converter never sees the sag it could not tolerate.

```
12 V ─[fuse]─[TVS]─[P-FET, ideal diode + soft-start]─┬─[supercaps]─► buck ─► 5 V
                                                      │
                                          blocking, so the caps
                                          cannot back-feed the truck
```

## Why it is attractive

The SEPIC exists almost entirely to survive **cranking**, where the rail at the
ECU can fall to 6 V or below. Everything expensive about that design — the
magnetics, the parallel Cs bank carrying 3.1 A rms, the 2.2 MHz switching
chosen to clear the AM band, and the layout discipline that goes with it —
follows from needing to work at low line.

A local energy reservoir removes the requirement rather than engineering around
it. And it covers **every** brownout source, not just cranking: starter
engagement, headlights, blower, a corroded terminal going intermittent, load
dump recovery.

## It also solves the graceful-shutdown problem

Dropping the OEM's KAPWR left an open requirement: detect loss of power and
flush learned state — fuel trims, DTCs, a final log entry — before the rails
collapse.

**Stored energy is what makes that possible.** An SD write is tens of
milliseconds; the sizing below gives roughly two seconds.

One part, three problems: brownout immunity, graceful shutdown, and the KAPWR
replacement.

## Preliminary sizing

```
ECU draws ~150 mA from 12 V   (≈300 mA at 5 V, ~85 % efficient)
Hold from 12 V down to 7 V for 2 s:
    Q = 0.15 A × 2 s = 0.3 C
    C = Q / ΔV = 0.3 / 5 = 60 mF
```

**~0.1 F at 16 V** with margin. Physically small and inexpensive — which is
what makes this worth considering at all.

## The P-FET does three jobs

An ideal-diode P-channel MOSFET in the feed, with a deliberate gate ramp:

1. **Reverse polarity protection** — as already planned.
2. **Blocking** — the caps hold up the ECU rather than draining into the
   truck's load when the key goes off.
3. **Inrush limiting** — the important one.

### Inrush is the thing that will bite

Charging 0.1 F from 12 V through a low-impedance path is effectively a dead
short at every key-on. Without limiting it pops fuses, welds relay contacts, or
destroys the FET — reliably, every time, not occasionally.

**An RC on the P-FET gate ramps it on over tens of milliseconds**, so the FET
itself acts as the current limiter during charge. No extra parts, and it reuses
a device already in the design.

Open questions on that: the FET spends the ramp in **linear mode** dissipating
real power, so it is an **SOA selection**, not an R<sub>DS(on)</sub> one — the
same argument as the LTC4364's pass FET. Ramp time trades inrush current
against FET stress and neither has been worked out.

## A 20 F cell at $1 changes the shape, not the size

Cheap high-value supercaps are **2.7 V** parts, so they cannot sit on a 12 V
rail directly. That forces a choice, and the obvious one is the worse one.

### Series stack — the obvious answer, and worse

Six 2.7 V cells in series gives 16.2 V and **3.3 F**. That is 33× more than the
0.1 F actually needed, and the downsides scale with it:

- **Inrush becomes 33× worse** — the problem the gate ramp exists to solve
- **~240 J stored** at 12 V, all of which has to go somewhere in a fault
- **Balancing** across six cells

More capacitance is not free. Sizing for what is cheap rather than what is
needed makes the hard parts harder.

### One cell plus a boost — better

Keep a single 20 F cell at 2.7 V and boost it to 5 V only when the input fails:

```
usable energy  = ½ × 20 F × (2.7² − 1.0²) = 63 J
ECU load       = 5 V × 0.3 A = 1.5 W
runtime        ≈ 40 s
```

Against ~2 s for cranking and ~100 ms for a graceful shutdown, that is enormous
margin from one part. But the real win is **simplicity**:

- **No balancing** — one cell.
- **Inrush solves itself.** Charge from the 5 V rail through a resistor: 10 Ω
  limits initial current to 270 mA and it tops up over a few minutes while the
  ECU runs on main power. No gate ramp, no SOA calculation, no hot-swap
  controller — the whole inrush problem disappears.
- **73 J stored at 2.7 V** rather than 240 J at 16 V.

Cost is a small boost converter and a changeover, both idle until they are
needed.

**This moves the hold-up from the input side to the output side**, which
sidesteps inrush rather than engineering around it. If this idea is pursued,
this is the version to pursue.

## What it does not solve

- **VREF.** A charger's 5 V is neither accurate nor quiet enough for a sensor
  reference, and every three-wire sensor is ratiometric to it. From a 5 V rail
  there is no LDO headroom, so it needs a small boost first — which was free
  when the main rail was 6 V.
- **Switching noise.** A sealed module next to a 16-bit ADC is a black box.
  With our own SEPIC the frequency and layout are controlled.
- **Supercap lifetime.** They age with temperature and voltage. A cabin-mounted
  ECU is kinder than an engine bay, but this needs checking against a real part
  rather than assumed.
- **Cell balancing** if more than one is in series at 16 V.

## Compared with what it replaces

| | SEPIC (current) | Buck + supercaps |
|---|---|---|
| Cranking | works to 3.5 V input | rides through on stored energy |
| Part count | high — magnetics, Cs bank, controller | low |
| Layout risk | **significant** — 2.2 MHz hot loop next to a 16-bit ADC | minimal |
| Brownout, other causes | not covered | **covered** |
| Graceful shutdown | needs separate hold-up | **included** |
| Inrush | handled by the LTC4364 | **our problem on the input side; disappears on the output side** |
| Noise near the ADC | controlled | unknown if a module is used |

Not a decision. But the layout row is the one that matters most, and it is the
part of the current design most likely to cause trouble on a first spin.

## Candidate parts

Two real parts have been looked at. The temperature spec decides between them.

### SLA3R8O2060813 — 3.8 V lithium-ion capacitor — rejected

**−20 °C lower limit.** That is the end of the discussion for a vehicle in this
climate; the ECU has to work on a cold morning. LICs also need an
over-discharge cutoff, because taking one below about 2.2 V damages it
permanently — an extra protection circuit the EDLC does not need.

### DGH504Q5R5 — 0.5 F / 5.5 V EDLC — viable, with one conflict

From the datasheet (`~/Documents/DGH504Q5R5-Datasheet.pdf`):

| | |
|---|---|
| Capacitance | 0.5 F, **−10 % / +30 %** |
| Working voltage | 5.5 V to +65 °C, **4.6 V at +85 °C** |
| **Operating temperature** | **−40 °C to +85 °C** (storage −40 to +70 °C) |
| ESR | 400 mΩ at 1 kHz, **800 mΩ DC** at 20 °C |
| Max continuous current | **0.6 A** (ΔT = 15 °C); 0.96 A for 1 s; 6.8 A short circuit |
| Leakage | **8 µA** at 72 h |
| Stored energy | 2.1 mWh = 7.6 J at 5.5 V |
| Life | 1500 h at rated voltage *and* rated temperature; **500,000 cycles** |
| Package | 17 × 16 × 8.5 mm, 2.2 g, 12 mm lead pitch, 0.6 mm leads |

**−40 °C is confirmed**, which was the open item and the LIC's disqualifier. The
8 µA leakage is the other good number: a parked truck loses nothing measurable
to it, which is what a KAPWR replacement has to be true of.

#### It sits directly on the 5 V rail — no boost needed

5.5 V is above the rail it holds up, so the changeover is a diode, not a
converter. Discharging 5.5 → 4.5 V:

```
½ × 0.5 F × (5.5² − 4.5²) = 2.5 J
÷ 1.5 W                   ≈ 1.7 s
```

At 0.3 A the 800 mΩ ESR costs 0.24 V, which is inside that budget.

#### But the deep-discharge numbers do not transfer

The 20 F sketch above assumed discharging to 1.0 V through a boost. Do that
here and the boost's input current climbs as the cap falls: at 2.0 V it needs
**0.75 A**, past the 0.6 A continuous rating, and 800 mΩ throws away 0.6 V of
what is left. **Small EDLCs are ESR-limited, not energy-limited.** The 63 J /
40 s figure belongs to the 20 F cell and does not scale down.

So this part buys **graceful shutdown (~1.7 s), not crank ride-through** — and
crank ride-through was the reason to consider replacing the SEPIC at all. It
supports the KAPWR requirement; it does not retire
[`power-supply.md`](power-supply.md).

#### The one conflict: 4.6 V at 85 °C

Sitting on a 5.0 V rail over-volts the part at 85 °C. A cabin-mounted ECU
should not see 85 °C, but "should not" is not a design margin. Options, none
worked out: charge through a series Schottky (→ ~4.7 V, still thin), clamp the
charge path to ~4.5 V, or measure the actual mounting-location temperature and
accept it.

#### Life: socketed, so it is a maintenance item

**Decision: the cap is socketed and field-replaceable.** 1500 h is a worst-case
figure — rated voltage at rated temperature simultaneously — and real service
is far longer at a derated charge and cabin temperature. But an EDLC is a wear
part with an electrolyte, unlike everything else on the board, and socketing
converts an unknown lifetime from a design risk into a service interval. It
also makes the 12 mm lead pitch and 17 × 16 mm footprint a fixed mechanical
commitment, so the socket choice comes before the layout.

### FXU0H105ZF — KEMET 1 F / 5.5 V, AEC-Q200 — the qualification winner, wrong job

This is the first genuinely **automotive-qualified** part looked at, and on
paper it is not close:

| | |
|---|---|
| Capacitance | 1.0 F, **−20 % / +80 %** |
| Working voltage | 5.5 V, no temperature derating stated |
| Operating temperature | **−40 °C to +105 °C** |
| Qualification | **AEC-Q200 rev E**, IATF 16949 plant, PPAP/PSW, change control |
| Endurance | 1000 h at **105 °C** rated voltage; 1000 h **85 °C / 85 % RH** biased |
| **ESR** | **10 Ω max at 1 kHz** |
| Leakage | 1.5 mA at 30 min |
| Package | Ø21.5 × 10.0 mm, **7.62 mm pitch**, 8.0 g |
| Assembly | wave solder only, **once**, body ≤ 90 °C |

AEC-Q200 rev E with PPAP and change control is the thing the DGH does not have
and cannot be argued into having. +105 °C and 85/85 mean it is not restricted
to the cabin.

#### 10 Ω is disqualifying, and it is a category difference

The DGH is 0.8 Ω DC. This is **12× worse**, and it is not a manufacturing
spread — it is what separates a *memory-backup* EDLC from a *power* EDLC. The
ceiling on what any source can deliver is V²/4R:

```
warm, new    (10 Ω)  →  5.5² / 40  = 0.76 W   theoretical, at 50 % efficiency
warm, aged   (20 Ω)  →             = 0.38 W   ESR doubles over rated life
```

Usable output is a small fraction of a matched-load maximum. Against a
shutdown draw of ~0.5 W this has no margin when new and none at all aged.
Concretely, at 100 mA a fresh part drops **1.0 V** across its own ESR and an
aged one drops **2.0 V** — out of a 5.5 V start, before any energy is used.

#### The cold-temperature spec is the real find

KEMET publishes what happens at temperature, and it is sobering:

| | Capacitance | ESR |
|---|---|---|
| −25 °C | ≥ 50 % of initial | ≤ 400 % of initial |
| **−40 °C** | **≥ 30 % of initial** | **≤ 700 % of initial** |

At −40 °C this is a **0.3 F, 70 Ω** part — 0.11 W matched-load ceiling. A
cold-start hold-up is precisely the case we care about most, and it is the case
where an EDLC is weakest, because ionic mobility in the electrolyte falls with
temperature.

**"−40 °C to +105 °C" is a survival range, not a performance range.** This is a
correction that applies to everything above.

#### And it retroactively weakens the DGH

The DGH datasheet gives a −40 °C rating and **no cold-temperature curve at
all** — no capacitance derating, no ESR multiplier. The FXU almost certainly
does not have worse cold physics than the DGH; it has a better datasheet. So
the DGH's headline −40 °C should be read as unsupported rather than good, and
its 0.8 Ω is a **+20 °C** number that may be several times higher when it
matters.

Disclosure is not a defect. The part that tells you is the safer part.

## The measurement that was never made: how much energy is actually needed

Both parts were sized against a number nobody checked. Doing it:

```
SD block write, generously          ~100 ms
MCU + card during that              ~0.7 W
                                    -------
energy required                      0.07 J
```

**0.07 J.** The DGH's 2.5 J is 35× that. And a figure that small does not need
a supercapacitor at all — it needs bulk capacitance that is *already in the
design*:

```
2200 µF on the 12 V input, held from 12 V to the SEPIC's 3.5 V floor:
    ½ × 2200 µF × (12² − 3.5²)  =  0.15 J   ≈ 200 ms at 0.7 W
```

The input bulk capacitor the LM5155-Q1 needs anyway covers graceful shutdown
with margin, at zero added parts, zero leakage, zero wear-out, and no
temperature curve worth worrying about.

### What this changes

The supercapacitor was justified by **three** jobs. It only ever had one.

| Job | Energy | Verdict |
|---|---|---|
| Graceful shutdown / KAPWR replacement | 0.07 J | **input bulk capacitance already does this** |
| Crank ride-through | ~3 J for 2 s | the only real case for a supercap |
| Brownout immunity generally | as above | same case |

And crank ride-through is the job **neither part can do**: the FXU is
ESR-limited out of contention, and the DGH's 1.7 s is a +20 °C figure with no
cold data behind it.

**So the LM5155-Q1 SEPIC stays, and it stays for the reason it was chosen —
it works at low line, which is what cranking actually demands.** The
supercapacitor idea is not blocked on finding a better part; it is blocked on
there being no requirement left that justifies one.

If it is revisited, the order is: measure the shutdown current budget, then the
cold ESR of a real part on a bench at −40 °C, then decide. Not the reverse.
