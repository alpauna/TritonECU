# Power supply

> **Alternative under consideration:** replacing the SEPIC with a plain buck
> plus a supercapacitor bank on its input — see
> [`power-supply-super-cap.md`](power-supply-super-cap.md). Preliminary only;
> what follows is still the current design.

## Current budget first — it decides the topology

| Load | 5 V rail draw |
|---|---|
| ESP32-P4 at 400 MHz + 32 MB PSRAM (via its 3.3 V regulator) | ~350–500 mA |
| ESP32-C6 module, peak TX | ~300 mA |
| SD card, peak | ~100 mA |
| AD7606 (110 mW) | ~25 mA |
| MAX9926 ×2 | ~20 mA |
| 74HCT541, MCP23S17 chain | ~20 mA |
| Sensor pull-ups | ~50 mA |
| **VREF** | **~25 mA** |
| **Total, realistic peak** | **~1.5 A** |

**Not 3 A.** That matters, because it removes the only argument for
interleaving.

Note this table is the *5 V-equivalent* load. Once the P4, C6 and SD card are
fed by a 3.3 V buck rather than directly, the actual draw on the SEPIC falls
further — see the rail tree below.

## Two-phase: no

The earlier SEPIC study established what a second phase actually buys — and it
was never efficiency. The two designs came within half a point at every
operating point. What it buys is **fault current halved per component**, output
ripple halved, and low-line losses spread across two packages.

All three matter at 3 A. **None of them matter at 1.5 A.**

What a second phase costs is the thing being optimised for here:

- Twice the inductors, switches and diodes — the parts that actually fail.
- Current sharing that the LM3481 datasheet does not specify, so it has to be
  designed and then trusted.
- A clock generator and phase relationship to get right.

**In a vibration and thermal-cycling environment, part count is the enemy of
reliability.** A second phase roughly doubles the switching component count to
solve problems this load does not have. Single phase is the more reliable
choice here, not the compromise.

## Topology: a SEPIC or buck-boost is genuinely justified

Not because of the upper end — a buck handles load dump fine — but because of
**cranking**.

The ECU must keep running while the starter is turning, since that is exactly
when it is controlling fuel and spark. A tired battery on a cold morning can
pull the rail at the ECU down to **6 V or below** after harness drop. A 5 V
buck runs out of duty cycle there and the ECU browns out at the worst possible
moment.

So the input range that matters is roughly **6 V to 40 V**, and it has to hold
5 V across all of it. That is a SEPIC or a four-switch buck-boost.

## Controller: LM5155-Q1 — decided

| | |
|---|---|
| Input range | **3.5 V – 45 V**, 50 V transient |
| Qualification | **AEC-Q100 Grade 1, −40 to +125 °C** |
| Topologies | boost, SEPIC, flyback |
| Max duty | 93 % |
| Switching frequency | 100 kHz – 2.2 MHz, programmable |

The **3.5 V minimum is the headline for this application** — it covers the
worst cranking sag with enormous margin, which is the whole reason a SEPIC was
chosen over a buck.

> **But 3.5 V is the SEPIC's floor, not the system's.** The LTC4364 ahead of it
> needs 4 V at V<sub>CC</sub>, plus whatever its series feed resistor drops, and
> when it shuts off its back-to-back FETs pass nothing at all. The real floor is
> **~4.4 V at the battery terminal** with R4 = 470 Ω, or 5.65 V with the 2.2 kΩ
> the datasheet example uses. See
> [`schematic-review-power.md`](schematic-review-power.md) §2.

It is a **controller with an external switch**, not an integrated converter, so
output current is set by the FET, inductors, diode and thermal design rather
than by the IC.

## SUPERSEDED: the 4 A analysis

**Decided 2026-09-08: 2 A at 6.0 V.** The section below worked out what 4 A
would cost and is kept because its reasoning still applies — but the answer went
the other way, for a reason that only emerged from the LTC4364 review.

The rail tree further down totals the real internal load at **~650 mA from the
6 V rail, about 4 W**. 2 A is 3× that. What settled it was the input side:
[`schematic-review-power.md`](schematic-review-power.md) fixes the LTC4364's
current limit at **4 A**, and at the 4.4 V input floor a 12 W output needs 3.2 A
of input current while an 18 W output needs 4.8 A. **18 W does not fit behind a
4 A limit at low line; 12 W does, with margin.** Raising the limit to suit would
have put the pass FET's short-circuit stress back up, and that part is already
the hardest one in the chain.

Lower output current also improves every magnetic and thermal number at once —
switch peak 6.96 A → **4.78 A**, Cs ripple 3.1 → **2.1 A rms**, inductor
saturation 4.5 → **3.1 A**, continuous dissipation 3.2 → **2.1 W**.

### The original 4 A analysis

Achievable, and the existing 3–30 V design already handles comparable switch
stress — at 3 V in and 3 A out it drew 5.9 A of input current, which is harder
than 4 A out from 6 V.

At the worst realistic corner, **6 V in, 4 A out**:

```
D    = Vout / (Vin + Vout) = 5 / 11        = 45 %
Iin  = Pout / (η · Vin)    = 20 / (0.85·6) = 3.9 A
```

In a SEPIC the switch and diode both carry **IL1 + IL2**, so:

| | |
|---|---|
| IL1 (input inductor), average | ~3.9 A |
| IL2 (output inductor), average | 4.0 A |
| **Switch and diode peak** | **~10 A** with ripple |

What that costs:

- **Magnetics get large.** Two inductors rated for ~10 A saturation.
- **Thermal.** 20 W out at 85 % is **3.5 W dissipated**, needing real copper
  pour. Helped considerably by the ECU living in the cabin rather than the
  engine bay.
- **The input path must carry 3.9 A at low line** — the P-FET, the resettable
  fuse and the TVS all sized for that, not for the 1.5 A the rail actually
  delivers.
- **Light-load efficiency suffers.** Against the ~1.5 A budget, a 4 A design
  runs at 37 % load for its whole life.

Worth being deliberate about *why* 4 A rather than defaulting to it: 2.7×
headroom over the measured budget is generous, and the cost is size, heat and
the input-side ratings. **2.5 A would give a comfortable 1.7× margin at
noticeably smaller magnetics.** If the extra is earmarked for something
specific — a display, more sensors, powering something external — 4 A is a fine
call; if it is general headroom, 2.5 A buys most of it for less.

## Overvoltage: a surge stopper, not a crowbar

The LM3481 works and there is already a validated 3–30 V design for it in
`~/Claude/3-30-sepic-3A-DCtoDC`, which is worth reusing rather than starting
over.

But for something going in a truck, **[CONFIRM]** whether the LM3481 is
AEC-Q100 qualified — it is a long-established general-purpose part and it may
not be. The **LM5155-Q1** is a modern automotive-qualified boost/SEPIC/flyback
controller covering the same job, and qualification here is not box-ticking: it
is the difference between a part characterised to 125 °C with known behaviour
under automotive transients and one that is not.

Reusing the existing design at a lower current is otherwise sound — derating a
3 A design to 1.5 A improves margin everywhere.

## Decided: 2 A at 6.0 V, 2.2 MHz

Reproducible in [`../hardware/calc/sepic_lm5155.py`](../hardware/calc/sepic_lm5155.py).

| | |
|---|---|
| Output | **6.0 V at 2 A** (12 W) |
| Input design range | **6 V** (cold crank) to **45 V** (LM5155-Q1 max) |
| Switching frequency | **2.2 MHz** |
| Inductors | **2 × 3.3 µH**, separate |

### Why 2.2 MHz, and not 400 kHz

This is an EMC decision, not an efficiency one, and it is easy to miss.

**The AM broadcast band is 530–1710 kHz.** A 400 kHz converter puts its 3rd
harmonic at 1.2 MHz and its 4th at 1.6 MHz — both squarely inside it. In a
vehicle, on a harness running the length of the truck, next to a radio. That is
a hard problem to filter away after the fact.

The LM5155-Q1 reaches 2.2 MHz specifically so the **fundamental and every
harmonic sit above the band**. It also shrinks the inductors from 10 µH to
3.3 µH.

The cost is switching loss — and, more importantly, **layout difficulty**.
Radiated emission scales with loop area × di/dt × frequency², so raising the
fundamental 5.5× makes the hot-loop area far less forgiving. 2.2 MHz solves the
AM-band problem and creates a layout problem in its place. See
[`supply-layout.md`](supply-layout.md); this is not a detail to leave until
after the schematic.

### Worked numbers

| Condition | Vin | Duty | Switch + diode peak | Blocking V |
|---|---|---|---|---|
| Cold crank | 6.0 V | 52 % | **4.78 A** | 12.5 V |
| Running | 13.8 V | 32 % | 3.63 A | 20.3 V |
| Surge pass-through | 30 V | 17.8 % | 3.21 A | 36.5 V |
| LM5155 max | 45 V | 12.6 % | 3.10 A | **51.5 V** |

Duty peaks at 52 % against a 93 % ceiling — comfortable, and the reason a SEPIC
handles cranking where a buck cannot.

### The ripple figures are not what they look like

The table shows inductor ripple reaching "166 % of IL1" at 45 V, which reads
like a runaway. It is not.

```
Vin · D = Vin · (Vout + Vd)/(Vin + Vout + Vd)  →  (Vout + Vd)  as Vin rises
```

Ripple is set by the **output**, not the input, and asymptotes to **0.90 A**.
The large percentage at high line is that same fixed ripple measured against a
much smaller average current. The input inductor simply runs discontinuous at
high line and light input current, which is normal for a SEPIC.

### Components

| Part | Requirement |
|---|---|
| MOSFET | ≥ 52 V blocking, ≥ 4.8 A peak → **80 V**, not 100 V — see below |
| Diode | ≥ 52 V, 2 A average, 4.8 A peak → **80 V Schottky** |
| Inductors | 2 × 3.3 µH, **saturation > 3.1 A each** |
| **Coupling cap Cs** | ≥ 52 V, **2.1 A rms** |

**On the voltage class:** 52 V comes from the LM5155-Q1's 45 V maximum, but the
surge stopper regulates the rail well below that — around 36.5 V of switch
stress during a surge, 20.3 V running. **80 V parts** cover it with margin, and
at 2.2 MHz their lower gate charge and output capacitance cut switching loss and
ringing as well as package size. See [`supply-layout.md`](supply-layout.md).

**Cs is the part most often under-specified.** It carries 2.1 A rms at cold
crank — one ceramic will not do it, and its ESR is dissipating that current
squared. Several 100 V X7R in parallel, chosen for ripple-current rating rather
than capacitance alone.

### Thermal — the case that actually sizes the design

At 13.8 V nominal, 12 W out at 85 % efficiency is **2.1 W dissipated**.

Not during cranking, which is brief. **Continuously, forever**, at whatever the
enclosure's ambient turns out to be. That is the number the copper pour and the
enclosure have to be designed around, and it is why the LM5155-Q1's Grade 1
125 °C rating matters rather than being a nicety.

## Rail tree

VREF draws from the main rail — it has to, since it must hold up through
cranking and that is the only rail that does. But it goes through its own
regulator, not a tap.

```
 12 V ─[PTC]─[P-FET]─[TVS]─[surge stopper]─► LM5155-Q1 SEPIC ──► 6.0 V main
                                                                     │
        ┌────────────────────────────────────────────────────────────┤
        │                                                            │
   Buck → 3.3 V                LDO → 5.0 V digital        LDO → 5.0 V analog
   P4, C6, SD card             74HCT541, MCP23S17         AD7606 AVDD, MAX9926 x2
   ~900 mA @ 3.3 V             ~30 mA                     ~50 mA
                                                                     │
                                                        LDO → 5.00 V VREF
                                                        ~25 mA, limited to ~150 mA
                                                        harness-facing
```

### Why this shape

- **The big load goes through a buck, not an LDO.** The P4, C6 and SD card all
  run at 3.3 V and together draw the great majority of the power. Taking them
  down with a switcher keeps the dissipation out of the box.
- **Every 5 V load is small**, so every 5 V rail can be a linear regulator.
  With 1 V of headroom from the 6 V main:

  | Rail | Current | Dissipation |
  |---|---|---|
  | 5.0 V digital | ~30 mA | 30 mW |
  | 5.0 V analog | ~50 mA | 50 mW |
  | 5.00 V VREF | ~25 mA | 25 mW |

  All negligible. Linears here are not a compromise — they are free.
- **The AD7606 and the MAX9926s get their own quiet rail**, separate from the
  74HCT541 and the expander chain. Those are digital parts switching eight
  ignition gates; keeping them off the ADC's supply is worth one extra
  regulator.
- **VREF gets its own again**, so a harness fault on VREF cannot pull down the
  ADC's supply. An LDO's PSRR also isolates VREF from the switcher's ripple —
  which matters because every sensor on VREF is ratiometric, so supply ripple
  reads as sensor movement.

### This reframes the 4 A question

Totalling what the SEPIC actually delivers at 6 V:

| | |
|---|---|
| 3.3 V buck input (900 mA at 3.3 V, ~90 % eff) | ~550 mA |
| All three 5 V linears | ~105 mA |
| **Total from the SEPIC** | **~650 mA** |

So the internal ECU load is under **1 A at 6 V, about 4 W** — not 20 W.

Sizing the SEPIC for 4 A is then a decision about **headroom for things not yet
on the board**, not about feeding the ECU. **2 A gives 3× margin** on the real
load at much smaller magnetics and less heat. If 4 A is wanted because
something external will hang off the 5 V rail, that is a good reason — but it
should be a stated load, not a default.

## Two rails, but only one switcher

Requested: a solid 5 V for internal use and a separate 5 V for VREF. Correct
instinct — sensor-supply noise and harness fault current should never reach the
logic rail or the ADC. But it does not need two switching supplies:

```
  12 V ─[protection]─► SEPIC ──► 5.0 V main, ~1.5 A ─┬─► logic, SD, ADC, drivers
                                                     │
                                                     └─► small boost ~7 V
                                                              │
                                                              └─► LDO ──► 5.00 V VREF
                                                                   ~150 mA limit
```

Why this shape:

- **VREF must survive cranking too** — a TPS reading during cranking matters —
  so it has to come from the rail that already holds up, not from raw battery.
- **An LDO is the right regulator for VREF.** At 25 mA it dissipates about
  50 mW, is inherently quiet, and its PSRR isolates VREF from the switcher's
  ripple. Every sensor on VREF is ratiometric, so ripple there reads as sensor
  movement.
- **The small boost exists only to give the LDO headroom.** Roughly 7 V in for
  5.00 V out. It carries 25 mA, so it is a tiny part.
- **Two independent switchers would be worse**, not better — a second switching
  node next to the analog front end is precisely the noise this arrangement is
  trying to avoid.

Current limiting stays per-feed as described in
[`vref-supply.md`](vref-supply.md) — roughly 150 mA electronic limit with a
fault flag, PTC as backstop only.

The instinct that a crowbar must not be fast-acting in a vehicle is exactly
right — and following it to its conclusion argues for a different device.

### Why a crowbar is awkward here

**Load dump is a normal event, not a fault.** ISO 7637-2 pulse 5 on an
unclamped 12 V system reaches tens of volts and lasts up to **400 ms**. Any
crowbar slow enough to ignore short ISO pulses is still far too fast to ignore
a load dump — so it fires during exactly the event it was fitted for.

And when it fires, **the ECU dies.** The crowbar shorts the rail, the engine
stops, and with a *resettable* fuse it stays stopped for as long as the PTC
takes to cool. On a running vehicle that is a stall, not a protection.

There is also a component problem: **a crowbar and a PTC are a poor pair.** A
crowbar is normally sized against a fast fuse that clears in milliseconds. A
PTC takes **seconds**, and the SCR has to carry full short-circuit current for
all of it — which means a much larger SCR than the threshold alone suggests.

### Use a surge stopper instead — **LTC4364-2**

Selected; full configuration in [`surge-stopper.md`](surge-stopper.md). It is
**AEC-Q100 qualified**, runs 4–80 V, protects against reverse input to −40 V
via an integrated **ideal diode controller**, and includes a timed current
limit — so it absorbs the reverse-polarity P-FET and the primary overcurrent
protection as well as the overvoltage job.

A surge stopper puts a MOSFET in series and holds it in *linear* regulation
during an overvoltage, clamping the downstream rail while the surge passes:

- **The ECU keeps running.** The rail is limited, not shorted — no stall.
- **It rides out a 400 ms load dump by design**, which is the case a crowbar
  cannot handle gracefully.
- **No fuse event**, so no PTC cooldown.
- It has a fault timer, so a *sustained* overvoltage — a 24 V jump start left
  connected, a failed regulator — shuts the output down properly. That is the
  case a crowbar is genuinely for, and the surge stopper covers it too.
- The same series FET can provide **reverse-polarity protection**, absorbing
  the P-FET.

The LTC4364 is AEC-Q100 qualified. What still needs sizing is the **pass FET's
safe operating area**: while clamping it dissipates roughly 40 W for up to
400 ms, about 16 J, in linear mode. See [`surge-stopper.md`](surge-stopper.md).

### Resulting input chain

```
Battery ─► fuse ─► TVS ─► LTC4364-2 ─► LM5155-Q1 SEPIC ─► 6.0 V
                (fast pulses)  (reverse, load dump, overcurrent, brownout holdup)
```

Each element covers what the next cannot:

| Element | Handles |
|---|---|
| Fuse | the pass FET failing short — the one mode nothing downstream can self-protect against |
| TVS | sub-microsecond ISO 7637 pulses, faster than any FET-based scheme can respond |
| **LTC4364-2** | **reverse polarity to −40 V, load dump, overcurrent, brownout holdup, UV lockout** |
| LM5155-Q1 | everything from 3.5 V to 45 V, which is most of the job |

The TVS stays: it catches the sub-microsecond pulses faster than any active
device can respond. The surge stopper handles the long events the TVS cannot
absorb thermally.

If a crowbar is still wanted as a genuine last resort, set it **above the
surge stopper's clamp** and pair it with a **fast fuse rather than the PTC** —
at that point it is protecting against the surge stopper itself failing short,
which is a real if unlikely mode.

## Input bulk capacitance — 1000 µF in, hold-up on the 6 V side

**Decided: 1 × 1000 µF / 50 V at the SEPIC input, hold-up energy on the 6 V
output.** An earlier revision specified 2000 µF on the input. That was
over-specified, and the reason is worth keeping.

### Placement: after the surge stopper, not before

```
Battery ─ fuse ─ TVS ─ LTC4364-2 ─┬─ 1000 µF ─ LM5155-Q1 SEPIC ─ 6.0 V ─┬─ 2 × 3300 µF
                                   │                                      │
                            clamped side, 30 V max               ripple + hold-up
```

On the harness side the cap would see raw ISO 7637 pulses, need a 100 V rating,
and sit in parallel with the TVS fighting it. On the clamped side it sees at
most the 30 V surge pass-through and gets the LTC4364's inrush limiting free.

### Why the second 1000 µF bought nothing

The input capacitor's real job is damping the filter formed with harness
inductance, so the converter does not oscillate against its own supply. Peak
filter output impedance is:

```
Zpeak = Z0 · Q = Z0² / ESR = (L/C)/ESR = L / (C · ESR)
```

**Paralleling identical electrolytics leaves that unchanged.** Doubling C
halves ESR, and the two cancel exactly:

| | Z0 | ESR | Q | Zpeak |
|---|---|---|---|---|
| 1 × 1000 µF | 70.7 mΩ | 24 mΩ | 2.95 | **0.208 Ω** |
| 2 × 1000 µF | 50.0 mΩ | 12 mΩ | 4.17 | **0.208 Ω** |

Identical. Against the worst-case negative input resistance at cold crank:

```
R_in = −Vin²/Pin  =  −6.0² / 4 W  =  −9 Ω      (design max 2 A → −2.7 Ω)
f0   = 1/(2π√(5 µH · 1000 µF))  =  2.25 kHz
```

0.208 Ω against 2.7 Ω is **13× — 22 dB of Middlebrook margin** even at the
2 A design point. The second can adds margin of zero and costs board area,
money, and 6 ms of extra inrush through the LTC4364's pass FET.

What *does* improve damping is a proper damping branch, not more bulk.

### Ripple current is not the input constraint

A SEPIC's input current is **continuous** — the source feeds an inductor, not a
switch. That is a structural advantage over a buck, and it means the input cap
carries only L1's ripple:

```
0.90 A pk-pk triangular  →  0.90/(2√3)  =  0.26 A rms
```

against ~3 A rms of rating on the part chosen for capacitance. Met 12× over.

### Why hold-up belongs on the 6 V rail

Energy per µF strongly favours the high side, since energy goes as V²:

```
input,  12 V → 4.4 V (system floor)  62.3 µJ/µF
output,  6 V → 4.0 V (3.3 V buck)    10.0 µJ/µF     6.6× worse
```

But **energy per cm³ and per dollar favour the low side**, because the input
cap's 50 V rating is forced by the 30 V surge and is then mostly unused at 12 V
nominal, while a 10 V part runs at 60 % of its rating:

| | Volume | Usable energy | Density |
|---|---|---|---|
| 1000 µF / 50 V, 18 × 20 mm | 5.09 cm³ | 0.066 J | 13.0 mJ/cm³ |
| 3300 µF / 10 V, 10 × 20 mm | 1.57 cm³ | 0.033 J | **21.0 mJ/cm³** |

**And on the output the capacitors are needed anyway.** A SEPIC's output
current is *discontinuous* — the diode conducts only during off-time — so Cout
carries real ripple:

```
Irms = Iout · √(D/(1−D))

   2 A design point, D = 0.52 (cold crank)    2.08 A rms   ← sizes the bank
   0.65 A actual load, D = 0.52               0.68 A rms
```

Size the 6 V bank for its ripple rating and the hold-up arrives free:

```
2 × 3300 µF, 6 V → 4 V:   ½ × 6600 µF × (36 − 16)  =  0.066 J
   at 0.7 W after load shed                        ≈  94 ms
   at 4.6 W actual full load                       ≈  14 ms
```

94 ms covers the ~100 ms SD flush that
[`power-supply-super-cap.md`](power-supply-super-cap.md) sized at 0.07 J. The
requirement is met by capacitors that had to be there regardless.

### What hold-up is *not* for

Not cranking. The chain runs down to **~4.4 V input** — the SEPIC alone would
manage 3.5 V, but the LTC4364 ahead of it cuts off first — so a starter dip to
6 V is not a brownout for this design, it is normal operation. Bulk capacitance
covers the gaps the topology cannot: contact bounce, an intermittent terminal,
and the shutdown flush. Sizing it as if it had to carry a crank is what
produced the 2000 µF figure.

### Parts

| Ref | Part | Why |
|---|---|---|
| C_in | **1 × 1000 µF / 50 V, 105 °C low-impedance radial** | filter damping — 50 V is 40 % derating on the 30 V clamp |
| C_out | **2 × 3300 µF / 10 V, 105 °C low-impedance** | 2.1 A rms ripple; hold-up is the by-product |
| C_hf | 2 × 10 µF X7R/50 V in, 4 × 22 µF X7R/16 V out, + 100 nF | the 2.2 MHz content no electrolytic can carry |
| R_d + C_d | 0.1 Ω 1 W + 220 µF — **stuff option** | populate only if the input rings; leave the footprint |

Panasonic FR / Nichicon UPW class, 10,000 h at 105 °C, −40 °C rated. **Do not
substitute low-ESR polymer or ceramic for C_in** — ESR is doing the damping
there, and 5 mΩ would raise Q to 14.

### Three things that will bite during bring-up

1. **The LTC4364 fault timer must outlast the inrush.** 1000 µF at a 2 A limit
   is `t = CV/I` = **6 ms**, pass FET dissipating ~12 W in linear mode (0.07 J,
   inside SOA for an 80 V part — still check it). Set the TMR capacitor shorter
   and the supply **faults every key-on**, which will look like a broken board.

2. **A current-limited bench supply will trip on the inrush.** Raise the limit,
   ramp from zero, or let the LTC4364 soft-start do it. Not a fault.

3. **6600 µF on the output invalidates the designed loop.** It drops the output
   pole by more than an order of magnitude. For a SEPIC that is broadly
   stabilising — the RHP zero caps bandwidth anyway — but the compensation
   numbers must be recomputed against the actual Cout before trusting them, and
   transient response will be slow.

## What actually determines reliability here

Topology is not the risk. Beyond the input chain above:

- **Cold-crank ride-through** — carried by the chain running down to ~4.4 V,
  not by capacitance. See [input bulk](#input-bulk-capacitance--1000-µf-in-hold-up-on-the-6-v-side) for
  why the two are often confused.
- **Thermal design at the top of the input range.** The worst case for a
  switcher is not cranking; it is 14 V continuous, forever, at whatever the
  enclosure's ambient turns out to be.

An ordinary single-phase SEPIC with those handled will outlast an elegant
two-phase one without them.
