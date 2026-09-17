# VREF supply design

The replacement ECU must source the buffered 5 V sensor reference the OEM PCM
provides on two pins (A-20, C-20). See
`1999-Ford-F150-4wd-5.42v/oem-connectors.md`.

**Originally specified:** separate supply, isolated from the internal 5 V,
outbound resettable fuse, **3 A** output.

**Decided:** a 5.00 V linear regulator of its own, **fed from the LTC4364's
protected output** rather than from any switching rail, common ground, feeding a
**TPS2H160B-Q1** dual-channel smart high-side switch — one channel per VREF
feed, current limit set at **250 mA**, per-channel current sense, fault
reporting, and a 40 V output rating that survives a short to battery. See
[§ The output stage](#the-output-stage-tps2h160b-q1).

The separation was right and matters. The current figure moved, and the
protection scheme had a hole in it.

**Closed — there is one VREF pin.** Ford's own wiring diagrams show **circuit
351 BN/WH to PCM pin 90**, spliced at S136/S137 to the DPFE sensor, the TP sensor
and C150. See
[`schematic-findings.md`](1999-Ford-F150-4wd-5.42v/schematic-findings.md) §1.
The power-pin sheet's "A-20 and C-20" does not describe this truck. The second
channel becomes a **stuffing option**, not a requirement. The reasoning that
followed is kept below because it is why nothing had to wait for the answer.

**Superseded — the EEC-V pinout shows one (pin 90,
BRN/WHT); Ford's power-pin sheet lists two (A-20, C-20).** That mattered when the
answer set the number of output stages. It no longer does: **the chosen part is
dual-channel**, so both are built either way and the unused one is simply never
enabled. Beyond that, the pinout sheet is the *MegaSquirt install's* record —
it carries its own caveat that the flat 1–104 numbering does not map cleanly to
Ford's connector-relative numbering, and a PNP install only connects the VREF
it uses. Ford's sheet is authoritative, and its A-20 / C-20 pattern matches the
SIGRTN A-17 / B-17 / C-17 pattern directly above it: one per connector.
**[CONFIRM ON TRUCK]** remains worth doing, but nothing waits on it.

---

## What VREF actually draws

Every three-wire sensor on this truck, at its worst case:

| Load | Draw | Note |
|---|---|---|
| TPS (C123) | ~1.1 mA | ~4.7 kΩ pot across VREF |
| DPFE (C122) | ~12 mA | the largest single VREF load |
| CHT pull-up (C179) | ~0.4 mA | pull-up is inside the ECU, sourced from VREF |
| IAT pull-up (C107) | ~0.4 mA | same |
| ~~TR sensor~~ | — | **not on VREF** — a switch array on SIGRTN, per Ford's diagrams |
| Speed control switches | ~5 mA | **[CONFIRM]** whether on VREF |
| **Total** | **~25 mA** | |

Not on VREF at all: MAF (12 V on circuit 361), CKP and CMP (variable
reluctance, self-generating), knock sensor (piezo, self-generating), HO2S
(self-generating, heaters on 12 V).

Ford's own EEC-V VREF is rated in the region of 250 mA across both pins.
**A 3 A supply is roughly 100× the real load.**

---

## Why the number fights itself

**1. At 3 A you are forced into a switching regulator, on the one rail that
most wants to be quiet.**

3 A at 5 V from a 14 V rail is 27 W in, 15 W out — 12 W of heat if linear. That
is not a linear regulator, so it becomes a buck, and a buck puts 10–50 mV of
switching ripple directly onto the sensor reference.

Every sensor on VREF is **ratiometric** — the TPS reports a fraction of VREF.
Ripple on VREF is indistinguishable from throttle movement unless the ADC
samples VREF at the same instant, which it does not.

At the real ~25 mA load, a linear regulator dissipates about 0.25 W. It is
inherently quiet, needs no inductor, and costs almost nothing. The 3 A
requirement throws that away to serve current nothing draws.

**2. A 3 A supply behind a 3 A resettable fuse does not protect the harness.**

This is the more serious point. A shorted VREF wire — chafed loom, wet
connector, dropped probe — is a routine field fault, and it is the specific
thing VREF protection exists for.

- A PTC trips at roughly **twice** its hold current and takes **100 ms to
  several seconds** to do it.
- Sized to pass 3 A, it does not begin to react until ~6 A, and passes fault
  current the whole time.
- VREF runs on thin signal wire. Holding several amps through 20–22 AWG long
  enough for a polyfuse to warm up cooks insulation inside the loom, where the
  damage is invisible and permanent.

The supply is strong enough to damage the harness before its own protection
notices. **A current limit only protects what it is set below.**

**3. It cannot isolate a fault between the two feeds.**

The OEM uses two VREF pins so one faulted harness branch does not starve the
sensors on the other. One 3 A supply behind one fuse gives up that property:
a short on the A-20 branch collapses C-20 with it, and the engine loses TPS and
DPFE together.

---

## Recommended instead

Keep the separation — that part is correct and valuable. Change where the
current limit sits, and make the thing that sits there survive a short to
battery.

```
  LTC4364 protected rail        ← 14 V nom, clamped 27–30 V
  (NOT the 5 V switcher)
          │
          ▼
  [ 5.00 V linear regulator ]   ← its own, EN under MCU control
          │
          ▼
  ┌──────── TPS2H160B-Q1, dual channel ────────┐
  │  ch1  limit 250 mA                         │──► ideal diode ──► A-20
  │  ch2  limit 250 mA                         │──► ideal diode ──► C-20
  │                                            │
  │  FAULT ─► GPIO  SEL ─► GPIO  CS ─► ADC     │
  └────────────────────────────────────────────┘
```

- **Fed from the LTC4364's protected output, not from the 5 V rail.** See
  [§ Where the supply comes from](#where-the-supply-comes-from). Sensor-supply
  noise and harness fault current never reach the logic rail or the ADC supply,
  and — just as important — the switching rail's ripple never reaches VREF.
- **Per-feed current limit at 250 mA**, set by one resistor. Ten times the
  ~25 mA real load, and it matches what Ford's own VREF is rated at across both
  pins. A 22 AWG wire is untroubled by it.
- **Fault flag into a GPIO** so a VREF short becomes a logged DTC — "VREF
  circuit A shorted" — rather than a truck that mysteriously will not run.
- **No PPTC, and no rail clamp.** Both were carried in earlier revisions for
  jobs the ideal diode does better or that stopped existing. See
  [§ Why there is no PPTC](#why-there-is-no-pptc).

---

## Where the supply comes from

**The LTC4364's protected output** — the ideal-diode / surge-stopper rail,
~14 V nominal and **clamped at 27–30 V** during a load dump.

Not the 5 V rail. The board's 5 V comes from a **MAX25239AFFA buck-boost at
2.1 MHz with spread spectrum**, and there are two reasons that cannot feed VREF:

1. **No headroom.** A linear regulator cannot make 5.00 V from 5 V, and running
   one near dropout is worse than it looks — **PSRR collapses as an LDO
   approaches dropout**, so it would stop rejecting the very ripple it was put
   there to reject.
2. **Spread spectrum is unhelpful here specifically.** It is the right call for
   EMC, which is why `SPS` is strapped to VCC. But it smears the switching
   energy across a band instead of one tone, so the ripple on a ratiometric
   reference cannot be notched out or synchronised to. Good for the FCC, bad for
   VREF.

### How this came to be missed

[`power-supply.md`](power-supply.md) records the rail change as:

> | 6.0 V main rail | **5.0 V**, since there are no LDOs needing headroom |

That was true of every rail on the power sheets. **VREF's LDO needed headroom
and lived in this document**, so it was not in view when the 6.0 V rail went
away. Worth remembering as a documentation failure rather than a design one.

### Why the protected rail is the right source

- **Completely independent of the switching supply.** No spread-spectrum ripple
  on the reference at all — the strongest form of the separation this document
  has argued for throughout.
- **Already protected.** Reverse polarity, load dump clamped to 27–30 V, and the
  4.47 V UV holdoff. The regulator sees a bounded 27 V, not an 87 V transient.
- **Rides out cranking on the LTC4364's holdup**, so VREF does not sag
  independently of the sensors it feeds.
- **Restores the headroom** the rail change removed, without adding a second
  switcher to solve a ripple problem.

### Dissipation

The sizing case is not the 25 mA load. It is **a fault on one feed while the
other keeps working** — 250 mA in current limit plus 25 mA healthy:

| Condition | V<sub>in</sub> | I | P |
|---|--:|--:|--:|
| Normal | 14 V | 25 mA | **0.22 W** |
| One feed in current limit | 14 V | 275 mA | **2.5 W** |
| Clamping, normal load | 27 V | 25 mA | 0.55 W |
| Clamping **and** a shorted feed | 27 V | 275 mA | 6.1 W, ~400 ms |

**None of these is a steady state except the first.** The 2.5 W row lasts only
until firmware sheds the faulted channel — see
[§ Shedding a faulted feed](#shedding-a-faulted-feed) — which is milliseconds,
not the life of the fault. Size the regulator for that energy pulse and its
retry policy, not for 2.5 W continuous. The last row is a load dump coinciding
with a chafed harness: survive it on thermal shutdown, do not design around it.

### Shedding a faulted feed

The part already carries everything needed to make the fault transient, for
reasons that had nothing to do with thermals:

```
short occurs         ->  channel clamps at 250 mA
80–180 µs            ->  FAULT asserts        (t_CL(deg), datasheet)
firmware reads CS    ->  identifies the channel
firmware drops INx   ->  that channel off
                     ->  dissipation back to 0.22 W
```

**This is a firmware requirement, not just a diagnostic.** The regulator's
thermal sizing depends on it, so it is load-bearing:

- deglitch **longer than `t_CL(deg)` (80–180 µs)**, and longer than the inrush
  into sensor capacitance at power-up, so a healthy start is not read as a short;
- a retry policy — **settled**, see [§ The retry policy](#the-retry-policy);
- the DTC is logged either way. A shed channel must be visible, not silent.

Shedding is not a loss compared to the alternative. If the shorted feed is the
one carrying TPS, throttle position is gone and the engine is unrunnable whether
or not VREF stays up. What shedding preserves is **the other feed** — which is
the entire reason for two of them.

It also softens the open `THER` question below: if firmware sheds the channel in
milliseconds, the part's own thermal latch-versus-retry behaviour rarely gets
the chance to matter.

### The regulator's capacitors

| | Value | Rating | Why |
|---|---|---|---|
| **C<sub>in</sub>** | **1 µF + 100 nF** | **50 V** | datasheet minimum is 0.1 µF; the rating clears the 27–30 V clamp at the board's 40 % derating precedent |
| **C<sub>out</sub>** | **22 µF X7R + 100 nF** | ≥ 16 V | datasheet minimum is 1 µF, which is a *stability* floor — not enough for this load step |

#### The 1 µF minimum is not the answer here

The NCV8772C's reference application is a microprocessor: a steady load. Ours
has a **250 mA step** every time a channel enters current limit, and the dip
during the loop's response is `ΔI × t / C`:

| C<sub>out</sub> | 5 µs | 10 µs | 20 µs |
|---|--:|--:|--:|
| 1 µF | 1250 mV | 2500 mV | 5000 mV |
| 10 µF | 125 mV | 250 mV | 500 mV |
| **22 µF** | **57 mV** | **114 mV** | **227 mV** |

**22 µF**, comfortably inside the datasheet's 1–100 µF stable region, and the
part requires no minimum ESR so plain ceramic is fine.

**Rate it for DC bias, not just voltage.** A 22 µF X7R loses a substantial
fraction of its value at 5 V of bias — use 16 V or 25 V and treat the derated
figure as the real one. A 6.3 V part would lose most of it and put you back near
the stability floor.

> How much the dip matters is worth being clear about, because it is less than
> it looks. VREF and the sensor are sampled **simultaneously** on the same
> converter, so a common-mode dip **cancels ratiometrically**. What it must not
> do is disturb the *healthy* feed badly enough to matter, or drop an active
> sensor below its operating range — which at ~100 mV it will not.

#### The input side is already handled upstream

The datasheet asks that input edges stay **below 50 V/µs**, and warns that an
input filter is needed otherwise. Nothing is needed here:

```
to slew the LTC4364 rail at 50 V/us through its 1000 uF bulk
   I = C dV/dt = 50,000 A
```

The system bulk cap makes that rate unreachable, so the local input capacitance
is doing ordinary high-frequency decoupling rather than slew limiting. 1 µF plus
100 nF at the pin covers the 275 mA step locally until the upstream rail
responds; at 1 µF that is a 0.275 V local dip per microsecond, refilled from the
bulk.

**The 50 V rating is not optional.** This part sits on the clamped rail, so it
sees 27–30 V during a load dump — the same reasoning that put a 50 V part on the
1000 µF bulk.

### The retry policy

`THER` is strapped to latch, so the switch never retries on its own —
**firmware owns this entirely.** The policy is what keeps the 2.5 W fault case a
pulse rather than a steady state, so it is part of the thermal design, not a
convenience.

```
startup blanking   20 ms after any channel enable, FAULT ignored
confirm            hardware deglitch 80-180 us, plus 2 ms in software
shed               drop INx, capture CS first, log the DTC
retry              1 s, then 5 s, then 30 s          (3 attempts)
latch              after the third, until key cycle or explicit clear
reset              60 s of good operation clears the attempt counter;
                   the cumulative count stays in the DTC
```

**Thermally, 1 s is already generous.** Average dissipation in the shared LDO,
against its 47.1 °C/W:

| shed time | spacing | duty | avg power | junction rise |
|---|--:|--:|--:|--:|
| 10 ms | 0.1 s | 10 % | 250 mW | 11.8 °C |
| 10 ms | **1 s** | 1 % | 25 mW | **1.2 °C** |
| 2 ms | 1 s | 0.2 % | 5 mW | 0.2 °C |

So the "seconds, not milliseconds" rule holds with enormous margin at the first
retry. **The escalation to 5 s and 30 s is not thermal** — it is there to avoid
hammering a shorted harness with repeated 250 mA pulses, to stop endless
retrying from masking a real fault, and to give a genuinely transient fault
(a wet connector drying, a vibrating terminal) more than one chance.

Three implementation notes that are easy to get wrong:

**Retry and fault-clear are the same action.** Toggling `INx` both re-enables the
channel *and* clears the latched thermal fault — the datasheet is explicit that
it is "cleared after toggling the related INx pin". There is no separate clear
step to forget.

**`FAULT` is ORed across both channels**, so on assertion firmware must attribute
it: read `CS` with `SEL` low, then high, allowing the 50 µs `t_SEL` settling.
**Capture `CS` before shedding** — the magnitude is the diagnostic, and it is
gone once the channel is off.

**Blanking, not deglitching, handles startup.** Sensor capacitance charging
through a slew-rate-controlled turn-on can engage the limit briefly. Trying to
tune a deglitch around that is fragile; a fixed window after enabling is not.
**[CONFIRM]** the 20 ms on the bench against the real sensor load.

**Blanking covers faults. Reading validity is a separate question, and a timer
is the wrong tool for it.** At startup, current flows through the ideal diode
FET's **body diode** until the LM74700's charge pump establishes gate drive, so
VREF sits near **5 − V<sub>SD</sub> ≈ 4.3 V**. Any ratiometric reading taken then
is wrong by ~14 %.

Gate validity on the **measured VREF**, not on elapsed time:

```
sensor readings valid  <=>  VREF sense within 4.75 - 5.25 V
```

VREF is already on the precision ADC as the ratiometric divisor, so this costs
nothing and is strictly better than a window: it catches the body-diode plateau
at startup, and equally a brownout, a sagging regulator, or a channel that came
up into a fault — none of which a timer would notice.

#### The two sense paths resolve all four states

Neither `CS` nor the per-feed divider is sufficient alone; together they are
unambiguous:

| `CS` | feed divider | State |
|---|---|---|
| load current | ~5 V | healthy |
| **at limit, 250 mA** | ~0 V | **short to ground** |
| ~0 | **~14 V** | **short to battery** — the ideal diode is blocking |
| ~0 | ~5 V | open load |

That is the payoff for spending an internal ADC channel per feed, and it is why
losing the switch's own short-to-battery detection to the ideal diode cost
nothing.

> **Out of scope here:** what the ECU does about *fuelling* with a VREF feed
> down. If the shed feed carries TPS, throttle position is gone and that is limp
> mode's problem, not this document's. Whether a feed carrying critical sensors
> deserves a more persistent retry depends on which sensors sit on which pin —
> which is still open above.

### Put EN under MCU control

VREF only matters while sensors are being read, so the regulator should be
**enabled by the MCU rather than always on**. Three things follow:

- it stays out of the always-on domain's ~780 µA parasitic budget
  ([`always-on-domain.md`](always-on-domain.md));
- the ECU can **power-cycle VREF** to clear a latched fault;
- with the feeds disabled and `CS` still reading current, a short is **inside the
  box**, not in the harness. That is a diagnosis you cannot otherwise make.

---

---

## The blind spot: short to battery

Both this document and `oem-connectors.md` say "short-to-ground survivable", and
a current limit does handle that. **Nothing addressed short to battery**, which
is at least as common a harness fault — a chafed VREF wire finding a 12 V
circuit rather than a ground.

Walk the fault against the original scheme:

```
battery ──► harness ──► A-20 ──► PTC ──► limiter output node rises to 14 V
```

**Almost no current flows**, so the PTC — a current-operated device — never
trips. It contributes nothing at all. The limiter's output pin simply sits at
14 V, and any ordinary 5 V load switch dies there. The **TPS2052B**
([datasheet](Datasheets/TPS2052BDR-Datasheet.pdf)) was considered for this and
is rated **6 V absolute maximum** on its output — it also has a *fixed* 0.75–
1.3 A current limit, which would let a short on one feed pull the shared
regulator down and take the other feed with it. That is the exact failure the
two-feed split exists to prevent.

So the requirement is sharper than "current limit with a fault flag":

> **The VREF output stage must be rated to battery voltage, not to 5.5 V.**

That one line is what selects the part.

---

## The output stage: TPS2H160B-Q1

A 40 V, 160 mΩ dual-channel smart high-side switch. Datasheet:
[`Datasheets/TPS2H160BQPWPRQ1-Datasheet.pdf`](Datasheets/TPS2H160BQPWPRQ1-Datasheet.pdf).

VREF is a *supply output*, so high-side is the natural topology here — the one
place on this ECU where it is, which is why the low-side parts chosen elsewhere
were never candidates.

| Requirement | How it is met |
|---|---|
| Two feeds | **Dual channel**, one package. Settles the one-or-two question |
| Runs from the 5 V rail | Operating range **3.4 V to 40 V** |
| **Survives short to battery** | **40 V rated — and it *detects* the condition** |
| Adjustable limit | External R<sub>CL</sub>: I<sub>CL</sub> = V<sub>CL(th)</sub> / R<sub>CL</sub>, V<sub>CL(th)</sub> = 0.8 V |
| Fault flag | `FAULT`, open-drain, ORed across channels |
| Per-circuit identification | `SEL` + `CS` — see below |
| Negligible drop | 160 mΩ × 25 mA = **4 mV** |
| Qualification | **AEC-Q100 Grade 1, −40 to +125 °C** |

Also: open-load detection, short-to-ground detection, thermal shutdown with
latch or auto-retry (`THER` pin), loss-of-ground and loss-of-power protection,
and functional-safety documentation.

### Why 250 mA rather than 150 mA

The external limit's accuracy is only specified down to **I(limit) ≥ 0.25 A**
(±20%; ±15% from 0.5 A to 7 A). Below 250 mA it is uncharacterised, so setting
150 mA would be operating outside the datasheet to hit a number that was
approximate anyway.

250 mA is the better figure regardless: it is **what Ford rates its own VREF at
across both pins**, it is ten times the measured ~25 mA load, and it is far
below anything that harms 22 AWG.

**R<sub>CL</sub> is mandatory, not optional.** With the `CL` pin tied to ground
the *internal* limit applies, and that is **9–15 A**.

### Diagnosis: FAULT, SEL and CS

Version B carries an analog current-sense output and a single global `FAULT`.
Per-channel identification comes from `SEL`, the CS channel-selection bit
(50 µs settling):

```
FAULT asserts        ->  something happened
SEL = 0, read CS     ->  channel 1 current
SEL = 1, read CS     ->  channel 2 current
```

That is strictly more than a pair of binary status flags would give, because it
reports **how much** as well as **which**. A partially shorted sensor or a
slowly drifting load shows as a rising VREF draw long before it becomes a hard
fault — worth having on a truck where a chafed harness is the expected failure.

#### Setting R<sub>CL</sub> and R<sub>CS</sub>

```
R_CL = K_CL x VCL(th) / I_limit  =  2500 x 0.8 / 0.250  =  8000 ohm
                                                        -> 8.06k, E96 1%  = 248 mA
```

R<sub>CL</sub> carries 99 µA against a 6 mA pin rating, and the resistor's
tolerance is a rounding error against the part's own ±20 % limit accuracy.

**R<sub>CS</sub> is constrained by something that only exists because we run at
5 V.** The current-sense output is linear only up to
**V<sub>CS(lin)</sub> = V<sub>VS</sub> − 2.5 V**, which at V<sub>VS</sub> = 5 V
is **2.5 V**. At the datasheet's usual 13.5 V it would be 4 V — so the headroom
is 40 % smaller here than the tables suggest at a glance.

It also has to be sized against **K(CS)'s ±17 %**, not its nominal 290:

| R<sub>CS</sub> | at 250 mA nom | at 250 mA **+17 %** | at 25 mA | |
|---|--:|--:|--:|---|
| 3.3 kΩ | 2.84 V | 3.33 V | 0.284 V | **over 2.5 V** |
| 2.7 kΩ | 2.33 V | 2.72 V | 0.233 V | **over** |
| **2.2 kΩ** | **1.90 V** | **2.22 V** | **0.190 V** | ok |

**R<sub>CS</sub> = 2.2 kΩ.** An earlier revision of this document proposed
3.3 kΩ, reasoning from a 3.3 V ADC span — that is outside the linear range and
was wrong.

#### The CS pin is driven high in a fault, and the ADC needs protecting

`V_CS(H)`, the current-sense pin output voltage **in fault mode**, is
`Min(V_VS − 2, 4.5)` minimum — **3 V at V<sub>VS</sub> = 5 V** — with at least
15 mA of drive behind it. Into 2.2 kΩ that takes only 1.4 mA, so **the node
genuinely leaves the measurement range and heads for the rail.**

That is deliberate: it is how the part flags a fault on the CS pin. But 3–5 V
into an STM32 ADC input rated V<sub>DDA</sub> + 0.3 V is a damage path.

| | |
|---|---|
| **4.7 kΩ series** from the CS node to the ADC pin | limits clamp current to a few hundred µA |
| **Schottky to V<sub>DDA</sub>** (BAT54 class) | preferable to relying on the internal ESD diode, which injects into the die and can disturb other ADC channels |
| **Long ADC sampling time** | source impedance is ~2.2 kΩ plus the series resistor |

No measurement error results: the ADC input is high-impedance, so there is no DC
drop across the series resistor. And a reading pinned at the rail is
unambiguous — it *is* the fault flag.

### THER: strapped high, latch mode

`THER` selects what the switch does after its own thermal shutdown. **Strap it
high — latch.** It has an **internal pulldown of 100 / 175 / 230 kΩ**, so
floating is *low*, and low is auto-retry: the choice has to be made actively.

**1. Auto-retry would take the retry cadence away from the device that sets
it.** [§ Shedding a faulted feed](#shedding-a-faulted-feed) established that
retries must be **seconds apart**, because the binding thermal constraint lives
in the **shared LDO**, not in the switch. Hardware auto-retry retries as soon as
the *switch's* junction falls below T<sub>SD</sub> − hysteresis — a far faster
cadence, set by the wrong part.

**2. On a shared supply, retrying endangers the healthy channel.** Both channels
draw from one regulator. Each retry pulls up to `I_CL(TSD)` — **60 % of the
external limit**, so ~149 mA — through that regulator. Repeated retries walk the
LDO toward *its* thermal shutdown, which drops **both** feeds: the precise
failure the two-feed split exists to prevent. Latching contains the fault to the
channel that has it.

**3. The fault stays sticky.** In auto-retry the thermal fault signal clears on
its own once T<sub>J</sub> < T<sub>SD,rst</sub>, so a brief event can self-clear
and never be logged. Latched, it clears only when firmware toggles `INx` — so
firmware always sees it, and the DTC is never silently lost.

The cost is that a genuinely transient fault needs firmware to clear it. That is
not a cost here: firmware owns the retry policy regardless, and if firmware were
hung, auto-retry would not rescue anything — it would thermally cycle both feeds
instead of one.

#### Wiring it

**10 kΩ to the switch's own V<sub>S</sub>**, not to the 3.3 V logic rail.
V<sub>S</sub> is the gated VREF rail, so `THER` is never held high on an
unpowered device. Against the worst-case 100 kΩ internal pulldown that gives
4.5 V, comfortably above V<sub>IH</sub> = 2 V and well inside the 7 V pin rating.

> The same discipline applies to `IN1`, `IN2`, `DIAG_EN` and `SEL`: firmware
> should hold them low whenever the VREF rail is gated off, so no logic pin is
> driven into an unpowered part.

A GPIO instead of a strap would let firmware fall back to auto-retry, and the
pin budget allows it — but it buys a capability firmware already has, at the
price of a new failure mode: a GPIO stuck low is silent auto-retry.

### CS does not belong on the precision ADC

Two VREF-related analog signals exist and only one is precision-critical.
Conflating them is easy and wrong:

| Signal | Converter | Why |
|---|---|---|
| **VREF sense** — the 5.00 V rail itself | **ADS8588H** (bench: AD7606) | it is the ratiometric divisor; measuring it on the same converter as the sensors, which sample **simultaneously**, lets common-mode error cancel |
| **CS** — diagnostic current | **STM32 internal ADC** | ±17% inherent accuracy, static, fault detection only |

Putting CS on the precision converter would be measuring a ±17% signal with a
16-bit instrument, and it would occupy one of only eight channels. The internal ADC's own error is a rounding difference against
the sense ratio's tolerance.

There is no shortage of native channels to worry about, either. The four-channel
limit noted in the firmware's `Board.h` was an **ESP32-P4** constraint — the C6
radio link occupied ADC1 channels 0–3. On the STM32F767ZI there are three ADCs,
against a pin budget of 37 used out of ~114.

---

## The output chain

```
TPS2H160B OUT ──► [ LM74700-Q1 + N-FET ] ──┬──► connector pin
                     ideal diode           │          │
                                          TVS         └──► divider ──► STM32 ADC
                                    SMAJ24CA, bidir
                                           │
                                         PGND
```

Two protection elements and a sense tap, each doing one job:

- the **ideal diode** blocks every DC reverse condition — a short to battery
  never reaches anything inboard of it;
- the **TVS** clamps transients, standing off **above any DC fault** so it never
  conducts continuously and never needs a series element to survive;
- the **diagnostic divider** taps the connector, so it sees what the harness
  sees.

> **There is no PPTC.** An earlier revision had one, sized 16 V, with two jobs
> it could not do — see
> [§ Why there is no PPTC](#why-there-is-no-pptc).

### The TVS, and why it is not the clamp that was deleted

[§ The ideal diode closes it](#the-ideal-diode-closes-it-lm74700-q1) deleted a
clamp on the **5 V rail, inside the box**, whose job was to survive the rail
being back-driven. The ideal diode prevents that condition, so that clamp has no
job.

This is a different part in a different place doing a different job: **clamping
what arrives from the harness.** VREF leaves the box, so
[`harness-protection.md`](harness-protection.md) already requires it — the same
rule it applies to the tach and VSS outputs.

**Bidirectional**, not unidirectional. On a negative transient — ISO 7637
pulse 1 and 3a are large and negative — a *unidirectional* TVS forward-conducts,
becoming a low-impedance path that must absorb the whole pulse as a diode. A
bidirectional part blocks until −V<sub>BR</sub> instead.

> The trade, recorded so it is not a surprise: a bidirectional TVS lets the line
> swing to −V<sub>BR</sub> before clamping, and the ideal-diode FET's **body
> diode forward-conducts** long before that — source at 5 V, drain going
> negative. **The switch's 250 mA limit bounds that current** — it sits between
> the 5 V rail and the FET's source — so it is contained, but the body diode is
> what takes a negative pulse first.

### Standing off above the fault, not clamping through it

The hard problem with a TVS on a 5 V line is that **no standoff low enough to
protect 5 V logic can also withstand 14 V continuously.** A 6.0 V part conducts
the moment the feed is shorted to battery, and then needs a series element —
a PPTC — to limit and clear the current before it fails.

That series element is what created
[review finding 1](review-vref-chain.md), and it could not do its other job
either. **The way out is to stop clamping through DC faults at all:**

| | 6.0 V standoff | **24 V standoff** |
|---|---|---|
| Short to battery, 14 V | conducts — needs a PPTC to clear | **never conducts** |
| Short during our 27 V clamp | conducts hard | **never conducts** |
| Genuine transient | clamps at 10.3 V | clamps at 38.9 V |
| Leakage at 5.1 V | 800 µA spec | **5 µA** |
| Series element required | **yes** | **no** |

The DC cases belong to the ideal diode, which blocks them outright. The TVS is
left with the one job a TVS is actually good at.

**What clamps below 24 V is nothing, and nothing needs it.** The only part of
the ECU exposed to the feed is the ideal-diode FET's drain, rated **60 V** — the
switch's 40 V OUT sits behind the FET, which blocks. And a TVS at the ECU never
protected the sensors out on the harness anyway: the transient is on the wire
between them.

### Selecting it: SMAJ24CA

Bidirectional — the `C` suffix in this series. Datasheet:
[`Datasheets/SMAJ6.0CA-Datasheet-C908810.pdf`](Datasheets/SMAJ6.0CA-Datasheet-C908810.pdf).

| Parameter | Value | |
|---|---|---|
| V<sub>RWM</sub> standoff | **24 V** | above every DC fault, so it never conducts continuously |
| V<sub>BR</sub> | 26.7 min / 30.7 max at 1 mA | |
| V<sub>C</sub> clamping | **38.9 V** at 10.3 A | below the FET's 60 V |
| Peak power | 400 W, 10/1000 µs | |
| Reverse leakage | **5 µA** | 160× lower than the 6.0 V part |
| T<sub>J</sub> | −55 to +150 °C | |
| Package | SMA | |

**Leakage stops being a question at this standoff.** It was worth watching when
the part stood off 6.0 V against a 5.1 V rail — operating close to breakdown is
where leakage lives. At 24 V standoff against the same 5.1 V the part is nowhere
near conducting, and the spec is **5 µA** rather than 800 µA. Two of them draw
10 µA against a 25 mA load.

**The gap is qualification, not electrical.** This datasheet makes no AEC-Q101
or automotive claim anywhere — it is a generic SMAJ series part. Every other
device in this chain is qualified: TPS2H160B-Q1 and NCV8772C to AEC-Q100 Grade 1,
LM74700-Q1 to AEC-Q100, DMN6040SVTQ to AEC-Q101, MF-NSHT050KX to AEC-Q200. A
non-qualified TVS would be the only exception.

**SMAJ24CA is an industry-standard part number available from qualified
sources** — Littelfuse, Vishay, Bourns among others — so this is a sourcing
decision rather than a redesign. The generic part is fine for a bench build.

> **[DECIDE]** which manufacturer. The part number is settled; buy it from an
> AEC-Q101 qualified source to match the rest of the chain.

### The reverse path, and why a PTC cannot close it

`TPS2H160B` §8.3.6.3: on a short to battery, if V<sub>OUT</sub> −
V<sub>S</sub> exceeds the body-diode drop, reverse current flows and must be
externally limited to below **I<sub>R(1)</sub> = 2.5 A**. At V<sub>S</sub> =
13.5 V a 14 V short is a 0.5 V differential and nothing happens; **at
V<sub>S</sub> = 5 V it is a 9 V differential**, so real current flows.

Two things follow, and an earlier revision of this document got both wrong.

**A PTC cannot limit it.** For current limiting you must assume R<sub>min</sub>
— a fresh part — not R<sub>1max</sub>. Against the whole Bourns MF-NSHT family:

| Part | I<sub>hold</sub> | R<sub>min</sub> | peak reverse current |
|---|--:|--:|--:|
| NSHT010 | 0.10 A | 1.00 Ω | 6.8 A |
| NSHT020 | 0.20 A | 0.60 Ω | 11 A |
| NSHT035 | 0.35 A | 0.40 Ω | 17 A |
| NSHT050 | 0.50 A | 0.17 Ω | 40 A |

**Not one of them reaches 2.5 A.** Even the highest-resistance device is 2.7×
over, and the low-resistance parts exceed their own I<sub>max</sub>. A PPTC is
low-resistance until it heats; it is not a current limiter in the first
millisecond, which is the only millisecond that matters here.

**And a rail clamp only survives the fault rather than preventing it.** Reverse
current does not merely flow — with nothing to sink it, it *raises the 5 V rail*
toward 13.3 V. Both candidate regulators die there: the NCV8772C's output is
rated **7 V** absolute maximum, the TPS7E82's is 2 × V<sub>OUT(nom)</sub>. A
clamp in the 5.1 V → 7 V window would have to sink a 40 A pulse, which is not a
window a TVS clamps inside.

### The ideal diode closes it: LM74700-Q1

Break the path instead of surviving it. Datasheet:
[`Datasheets/LM74700-Q1-Datasheet.pdf`](Datasheets/LM74700-Q1-Datasheet.pdf).

| Parameter | Value | |
|---|---|---|
| **CATHODE to ANODE** | **−5 to +75 V** abs max | our reverse case is +9 V |
| ANODE operating | **3.2 V to 65 V** | runs from the 5 V rail |
| Reverse blocking response | **< 0.75 µs** | against a PPTC's milliseconds |
| DC reverse current | **zero** | |
| Forward regulation | **20 mV** | |
| I<sub>Q</sub> | 80 µA operating, 1 µA shut down | |
| Package | SOT-23-6, 2.90 × 1.60 mm | |
| Qualification | AEC-Q100 | |

N-channel, source at the switch's OUT, drain toward the feed, so the body diode
conducts forward and blocks reverse while the controller holds the gate off.

#### The FET: Diodes **DMN6040SVTQ-7**

TSOT26, single. Datasheet:
[`Datasheets/DMN6040SVTQ-7-Datasheet.pdf`](Datasheets/DMN6040SVTQ-7-Datasheet.pdf).

| Parameter | Value | |
|---|---|---|
| V<sub>DSS</sub> | **60 V** | 6.7× the 9 V reverse case |
| **V<sub>GSS</sub>** | **±20 V** | clears the controller's 15 V requirement |
| V<sub>GS(th)</sub> | **1–3 V** | standard threshold — see below |
| R<sub>DS(on)</sub> | 30 typ / **44 mΩ max** at V<sub>GS</sub> = 10 V | 0.9 mV at 20 mA |
| I<sub>D</sub> | 5.0 A at 25 °C, 4.0 A at 70 °C | the switch-fails-short case is 400 mA |
| Qualification | AEC-Q101, PPAP capable | |

> **ADVANCE INFORMATION**, DS38508 Rev. 1 — preliminary, so specs can move.
> Check stock and status before committing, as with any preliminary part.

Nothing here is demanding: 0.4 mW of dissipation and 20 mA through a part rated
5 A. The two ratings that *do* matter are both easy to get wrong.

#### Two constraints, and both rule out the obvious parts

**1. V<sub>GS</sub> rating ≥ 15 V — so a *standard*-threshold FET, not a
logic-level one.** This is backwards from the usual reflex. The LM74700's charge
pump drives to approximately 15 V and its own GATE-to-ANODE absolute maximum
*is* 15 V; the datasheet states the requirement directly as
`External MOSFET max VGS rating: GATE to ANODE — 15 V minimum`. Gate sensitivity
buys nothing when the controller supplies that much drive, and the thin gate
oxide that gives a logic-level part its low threshold is exactly what caps it at
±12 V.

**2. R<sub>DS(on)</sub> comfortably under 1 Ω.** The controller regulates the
forward drop at **20 mV**. If `I × R_DS(on)` exceeds that, the loop cannot
regulate: the FET sits fully on and the drop becomes **resistive and drifting** —
precisely the property the PTC was demoted for.

| Part | Fails on | |
|---|---|---|
| **NVTR4503N** | V<sub>GS</sub> **±12 V** | V<sub>GS(th)</sub> 0.6–1.2 V; a logic-level part, thin oxide |
| **BSS123** | ~6 Ω → **120 mV** at 20 mA | already on the power BOM for Q3/Q4 — the obvious reuse, and wrong |
| **2N7002** | ~3 Ω → **60 mV** at 20 mA | in `hardware/2N7002 Driver/`; same problem |

Both small-signal FETs already on this board fail, for different reasons. Worth
recording, because BSS123 is what you would reach for to delete a BOM line.

> **Why not a passive P-FET with no controller.** Blocking reverse current
> requires the body diode to oppose it, which forces **source-toward-load**. With
> the source at the load, a rising load makes V<sub>gs</sub> *more* negative, so
> a passively-biased FET turns **on** exactly when it must turn off — 5 V gives
> V<sub>gs</sub> = −5 V, and a 14 V short gives −14 V. No passive gate network
> fixes that: a divider scales V<sub>gs</sub> and a zener clamps it, neither can
> invert it. Turning the FET off means pulling the gate up to a source sitting at
> 14 V, which requires comparing against the input — and that comparison is the
> controller. Passive ideal diodes also generate gate drive *from the forward
> drop*, which here is deliberately microvolts.

**What this deletes:** the rail clamp, the Schottky that would have diverted the
pulse, the TVS sized for 40 A, and the tight 5.1 → 7 V window. Net part count is
roughly a wash and the unquantified item is gone.

**The forward drop is 20 mV** — similar in magnitude to a PPTC's, but
**regulated rather than resistive**, so it is a stable offset rather than
something that drifts with current, ambient and trip history. That is the
difference that matters for a ratiometric reference.

### Why there is no PPTC

An earlier revision carried a `MF-NSHT050KX` per feed, with two jobs. It could
not do either, and
[`review-vref-chain.md`](review-vref-chain.md) finding 1 is what exposed it.

**Job one — limit current into the TVS on a sustained short to battery.** That
job existed only because the TVS stood off 6.0 V, below battery. Raising the
standoff to 24 V deletes the job rather than doing it better.

**Job two — backstop if the switch fails short.** It cannot:

```
NCV8772C current limit, what would actually flow    400 - 1100 mA
MF-NSHT050KX Itrip, guaranteed trip at 23 C            2500 mA
                              derated to 60 C          1850 mA
```

The fault current lands **between I<sub>hold</sub> and I<sub>trip</sub>** — the
indeterminate zone where a PPTC may or may not trip. It never reliably clears
the one fault it was there for. **What actually protects in that case is the
LDO's own thermal shutdown**, and it always did.

**And the 30 V part cannot be substituted.** Finding 1 was that the 16 V rating
is exceeded by a short to battery coinciding with a load dump. The obvious fix
is `NSHT035` at 30 V — but its hold current derates below the switch's 250 mA
limit well inside the operating range:

| Ambient | NSHT035 (30 V) | NSHT050 (16 V) |
|---|--:|--:|
| 50 °C | 0.28 A | 0.41 A |
| 60 °C | 0.26 A | 0.37 A |
| **70 °C** | **0.23 A — trips** | 0.34 A |
| 85 °C | 0.20 A — trips | 0.28 A |

[`enclosure.md`](enclosure.md) is explicit that behind the glovebox is "a
confined space with poor convection", that "a closed cavity raises local ambient
above cabin temperature", and that the connector face conducts heat *in* from
the engine bay. 70 °C in-cavity is not a stretch. A PPTC that trips on a fault
the switch is already containing turns a contained single-channel fault into a
dead feed needing a power cycle — **worse than the problem it solves.**

#### What removing it buys

- **Finding 1 disappears** rather than being mitigated. There is no voltage
  rating left to exceed.
- Two components, and the only series element in the feed.
- **The last drifting term leaves the ratiometric path** — see
  [§ The accuracy argument](#the-accuracy-argument-corrected).

Every fault still has an owner: forward overcurrent is the switch's 250 mA
limit, DC reverse is the ideal diode, transients are the TVS, and switch-fails-
short is the LDO's current limit and thermal shutdown — which was always the
real answer there.

### Diagnosis, now that the switch cannot see the fault

The ideal diode blocks the battery from reaching OUT, so **the TPS2H160B loses
short-to-battery detection** — a short now reads as *no current*, which is
indistinguishable from an open load.

Recover it with **a divider from each feed into an STM32 internal ADC**. It sees
14 V directly and says unambiguously which feed is shorted, which is better than
the detection it replaces. Same reasoning as `CS`: a diagnostic, not a
ratiometric measurement, so it does not belong on the precision converter, and
internal channels are plentiful.

**100 kΩ / 12.4 kΩ, plus a Schottky to V<sub>DDA</sub>.** Sized so our own 27 V
clamp lands just inside the ADC range rather than so 14 V does — the first
version of this was scaled for the nominal short only, and presented 5.7 V to
the ADC when the shorted circuit was itself in a load dump:

| Feed at | ADC sees | |
|---|--:|---|
| 0 V | 0.00 V | channel off, or short to ground |
| 5 V | 0.55 V | healthy |
| 14 V | 1.54 V | short to battery |
| 27 V | 2.98 V | short during a clamp — just inside range |
| 35 V+ | clamped | Schottky |

**No series resistor is needed here**, unlike on `CS`: the 100 kΩ top leg *is*
the series element. Even with the feed at 100 V it passes 964 µA, of which the
bottom leg takes 290 µA, leaving the Schottky under 700 µA.

Two consequences worth carrying into layout:

- **Source impedance is 11 kΩ.** Use a long ADC sampling time, and a 10 nF cap
  at the ADC node to supply the sampling capacitor. The resulting ~110 µs time
  constant is irrelevant for a diagnostic.
- **Continuous load is 44 µA**, which sits downstream of the ratiometric sense
  point but ahead of nothing that matters: 0.07 mV across the PTC.

### The accuracy argument, corrected

Earlier revisions argued VREF must be *sensed downstream of the PTC*, because a
PPTC is a thermistor by construction — resistance rising with current and
ambient, roughly doubling after each trip, putting 75 mV of wandering error on a
ratiometric reference.

A later revision claimed the switch's 4 mV drop retired that argument. **It did
not, and that was an error**: the switch and the PTC are in *series*, so a small
drop across one says nothing about the other.

What actually retires it is the chain above. Per feed at ~20 mA:

| Element | Drop | Character |
|---|--:|---|
| TPS2H160B, 160 mΩ | 3 mV | resistive, **stable** |
| LM74700-Q1 + FET | 20 mV | **regulated**, a fixed offset |

**Both remaining terms are stable.** The PPTC was the only drifting one, and
[§ Why there is no PPTC](#why-there-is-no-pptc) removed it for unrelated
reasons — the accuracy improvement is a side effect.

Take the ratiometric sense at the regulator — one channel, covering both feeds.
23 mV of stable, characterisable offset on 5.00 V is 0.46 %, and it does not
wander with current, ambient or fault history.

## Grounds

Worth being explicit: this should be a **separate regulator with a common
ground**, not galvanic isolation.

### Which leg of the star each element returns to

One ground, star topology — but *which leg* matters, and the two protection
elements want different ones.

| Element | Returns to | |
|---|---|---|
| **TVS** | **PGND** | transient energy to the heaviest copper |
| **Divider bottom leg** | **AGND**, the ADC's own reference | so the reading means what it says |
| Sensor returns | **SIGRTN** — one net, PCM pin 91 | [`schematic-findings.md`](1999-Ford-F150-4wd-5.42v/schematic-findings.md) §2 |

**The divider must return to the ADC's ground, not SIGRTN.** Referencing it to
SIGRTN passes any SIGRTN-to-AGND offset straight through at **(1 − k) = 0.89×**,
against a healthy-state signal of only **0.55 V**:

| Offset | Adds to the reading |
|---|--:|
| 0.1 V | 0.09 V |
| 0.5 V | **0.44 V** — nearly doubles it |
| 1.0 V | 0.89 V |

A high-ratio divider is unusually sensitive this way: the *signal* is attenuated
11× while the *offset* is not attenuated at all.

**The TVS must not return to SIGRTN.** A clamping TVS carries amps. Pushing that
into the sensor return would offset SIGRTN for **every sensor on that
connector** — briefly, but by far more than any of them can tolerate, and
precisely when the readings are already suspect. PGND is the defined
low-impedance path and the TVS is protecting the ECU, not the harness.

### The assumption that buys, and the second reason for 6.0 V

Returning the TVS to PGND means a SIGRTN-to-PGND offset eats directly into its
standoff margin:

```
TVS standoff 6.0 V  -  VREF max 5.1 V  =  0.9 V of margin
dedicated sensor return, ~25 mA through ~0.1 ohm  =  ~2.5 mV
```

**360× margin**, so the assumption is safe — but it *is* an assumption, and it
rests on SIGRTN being a dedicated low-current return rather than a shared one.

It also gives a **second, independent reason not to shave the TVS standoff to
5.5 V.** [§ Selecting it](#selecting-it-smaj24ca) declined that on leakage
grounds; ground-offset margin says the same thing for a different reason.

> **Related, and larger than this document:** whether **VREF sense** itself
> should be measured *differentially against SIGRTN* rather than single-ended.
> That would make the ratiometric cancellation exact rather than merely good,
> and the converter has differential capability — it is already used for the MAF,
> which has its own dedicated return. That is an ADC architecture question, not
> a VREF one.

VREF's return path is SIGRTN, and the ADC has to measure sensor voltages
against that same reference. Galvanically isolating VREF would break the
measurement entirely — there would be no defined relationship between the
sensor output and the ADC's ground. Separation of *supply*, shared ground at
the star point.

---

## If 3 A is still wanted

It is a reasonable spec for a **general isolated 5 V rail** that also feeds the
AD7606B analog supply, the J1850 transceiver and any level shifting. If that is
the intent, the answer is the same diagram: build the rail at 3 A, and still
current-limit each VREF feed at 250 mA on its way out of the box.

The rail can be as strong as you like. What leaves the connector and goes into
the truck's harness should not be.

---

## The regulator: onsemi NCV8772CDT504RKG

**Settled: onsemi NCV8772CDT504RKG**, 5.0 V, DPAK-5. Datasheet:
[`Datasheets/NCV8772CDT504RKG-Datasheet.pdf`](Datasheets/NCV8772CDT504RKG-Datasheet.pdf).

| Parameter | Value | Against the requirement |
|---|---|---|
| Input | 4.5–40 V operating, **40 V abs max DC**, 45 V load-dump suppressed | 33 % over the 30 V clamp max |
| Output | **5.0 V fixed**, ±2 % (4.9–5.1 V) | ratiometric, so absolute accuracy is low-stakes |
| Current | **350 mA** rated, limit **400 mA min** / 1100 mA max | clears the 275 mA fault case without limiting |
| Rθ<sub>JA</sub> | **47.1 °C/W** (DPAK-5, 1 in² of 1 oz Cu) | |
| **Rθ<sub>JC</sub>** | **12.6 °C/W** | the number that governs the pulse |
| Thermal shutdown | 150 / 175 / 195 °C, 10 °C hysteresis | |
| `EN` | yes, 1 µA disabled | [§ Put EN under MCU control](#put-en-under-mcu-control) |
| Reverse output current protection | **yes** | |
| Qualification | **AEC-Q100 Grade 1**, EMC compliant | |
| Iq | 18 µA typ | irrelevant — the part is EN-gated |

### Why this one

**Rθ<sub>JC</sub> = 12.6 °C/W is what made the decision.** The fault is a pulse,
and junction-to-case governs a pulse: `2.5 W × 12.6 = 32 °C` rise to the case,
which is a non-event. It also means **most of the 47.1 °C/W lives in the board**,
so copper pour buys real margin rather than a rounding difference.

That matters more than usual here, because at 5 V **DPAK-5 is the only package
offered** — the D2PAK-5 variant (42.3 °C/W) is 3.3 V only. Pour is the single
thermal lever available.

**Reverse output current protection** earns its place given the part is
`EN`-gated: VREF bulk plus sensor capacitance can hold the output up while
V<sub>in</sub> falls.

It is also an established part rather than a recent release, and onsemi is
already on this board via the NCV8405A — the same qualification and supply path.

### Three constraints it had to meet

**1. Thermals — a pulse, not a steady state.** Continuous dissipation is
**0.22 W** → 10 °C rise, nothing. The 2.5 W fault case lasts until firmware
sheds the channel; see [§ Shedding a faulted feed](#shedding-a-faulted-feed).

> **No candidate survives 2.5 W continuously**, which is worth stating because
> it means the shedding requirement is structural rather than an artifact of
> this part:
>
> ```
> NCV8772  DPAK-5    2.5 W x 47.1 = 118 C rise -> TJ 178 C  (TSD min 150 C)
> TPS7E82  HVSSOP-8  2.5 W x 58.5 = 146 C rise -> TJ 206 C  (TSD     163 C)
> ```
>
> Both shut down. The architecture has to shed, whatever part is fitted — and
> the **retry policy must be seconds apart, not milliseconds**, or the part
> simply re-heats into shutdown.

**2. Placement — downstream of the pass FET.** This matters more than any
voltage rating. Upstream, the part sees what
[`surge-stopper.md`](surge-stopper.md) describes the LTC4364 surviving: *a 200 V
1 ms transient, clamping a 92 V surge to 27 V.* No LDO rating saves you there —
the topology does.

**3. Voltage rating — clear the clamp, with derating.**

| | |
|---|---|
| Clamp, design | **27 V** — [`power-supply.md`](power-supply.md) §"V<sub>IN(MAX)</sub>" |
| Clamp, maximum | **30 V** |
| Derating precedent on this board | the 1000 µF bulk is **50 V on the 30 V clamp**, 40 % |

**>30 V is the requirement**, not 40 V. The NCV8772C's 40 V DC maximum clears it
by 33 %. A clamp **overshoots on the transient edge** before its loop settles, so
30 V is not a number to design exactly to — that is the argument for margin,
rather than the 30 V figure itself.

**PSRR is a non-issue on this rail**, unlike the 5 V-switcher option this
document rejects: 9 V of headroom at 14 V in means the part never operates near
dropout, which is precisely why this source works. Worth noting anyway that the
NCV8772C characterises PSRR **only at 100 Hz** (75 dB) — a real gap if anything
ever couples in, and the one place the rejected alternative was stronger.

### Considered: TI TPS7E8250QDGNRQ1

40 V (42 V abs max), 300 mA, ±1.2 % accuracy, PSRR 70 dB at 1 kHz and 45 dB at
100 kHz, HVSSOP-8 at 58.5 °C/W. Better accuracy and far better characterised
PSRR, and 2 V more headroom over the clamp.

Passed over on thermals and margin: no published Rθ<sub>JC</sub>, a worse
Rθ<sub>JA</sub> in a package where copper helps less, 300 mA against 350, and a
350 mA limit minimum against 400. It also derates current above **15 V of
headroom** (`V_HEADROOM`), so it delivers less during a 27 V clamp — protective,
but a behaviour the NCV8772C does not impose. And it is a November 2025 release
where the onsemi part has been in production since 2018.

The accuracy and PSRR advantages are largely neutralised here: VREF is measured
ratiometrically, and the source is a linear-fed protected rail rather than a
switcher.

---

## BOM

**One regulator and one switch — not one per feed.** Isolation between feeds
comes from the switch's two independent current limits, not from separate
regulators. Two regulators was rejected: it costs two precision ADC channels and
gives ~2 % channel-to-channel spread where one regulator through one switch
gives **4 mV**.

The 275 mA sizing figure is the tell — `250 mA (one channel in limit) + 25 mA
(the healthy one)` only exists because both channels share one regulator.

| Qty | Part | |
|--:|---|---|
| 1 | **NCV8772CDT504RKG** | 5.00 V LDO, DPAK-5 |
| 1 | **TPS2H160BQPWPRQ1** | dual high-side switch, both feeds |
| **2** | **LM74700QDBVRQ1** | ideal diode controller, SOT-23-6 — **one per feed** |
| **2** | **DMN6040SVTQ-7** | N-FET, TSOT26, 60 V / ±20 V V<sub>GS</sub> — **one per feed** |
| **2** | **SMAJ24CA** | bidirectional TVS, SMA — **one per feed**, to PGND. Buy AEC-Q101 qualified |
| 1 | R<sub>CL</sub> = **8.06 kΩ 1 %** | sets the limit to 248 mA |
| 1 | R<sub>CS</sub> = **2.2 kΩ** | current sense; 2.5 V linear ceiling at V<sub>VS</sub> = 5 V |
| 1 | R<sub>series</sub> = **4.7 kΩ** + Schottky to V<sub>DDA</sub> | protects the ADC pin when CS is driven high in a fault |
| 1 | R<sub>THER</sub> = **10 kΩ to V<sub>S</sub>** | straps `THER` high — latch mode, not auto-retry |
| **1** (2 if the second feed is populated) | divider **100 kΩ / 12.4 kΩ** + Schottky to V<sub>DDA</sub> + 10 nF | short-to-battery sense → internal ADC. One VREF feed on this truck |
| 1 | C<sub>in</sub> = **1 µF + 100 nF, 50 V** | LDO input, on the clamped rail |
| 1 | C<sub>out</sub> = **22 µF X7R ≥ 16 V + 100 nF** | LDO output; sized for the 250 mA step, not the 1 µF stability floor |
| 2 | **0.1 µF** VCAP–ANODE, **22 nF** ANODE | per LM74700-Q1, one set per controller |

**Not fitted, and worth recording why:** no rail clamp, no Schottky, no TVS on
the 5 V rail. The ideal diodes prevent the reverse condition that would have
needed all three — see
[§ The ideal diode closes it](#the-ideal-diode-closes-it-lm74700-q1).

**Pin cost: 6 GPIO and 3 internal ADC channels.**

| | |
|---|---|
| GPIO | `EN` (LDO), `IN1`, `IN2`, `DIAG_EN`, `SEL`, `FAULT` |
| STM32 internal ADC | `CS` (via 4.7 kΩ + Schottky — it is driven to the rail in a fault), plus **one per feed** for short-to-battery sense |
| Precision ADC | one VREF sense at the regulator, covering both feeds |
| Strapped, not driven | `THER` **high via 10 kΩ to V<sub>S</sub>** — latch mode; the LM74700 `EN` pins tie high, gated with the rail |

If the truck turns out to have **one** VREF pin rather than two, nothing changes
except populating one PTC and never enabling channel 2. Regulator and switch
counts stay at one each.

---

## Why not a buck here

A buck would cut the fault-case dissipation, but a switcher does not go directly
on a ratiometric reference — the shape would have to be **buck → ~6.5 V → LDO →
5.00 V**, with the LDO's PSRR cleaning up the ripple. That puts the linear's
fault case at `(6.5 − 5) × 275 mA = 0.41 W`.

The cost is another inductor, another switching node, more EMC surface, and a
**second uncorrelated switching frequency** near the sensor reference, given the
5 V rail is already spread-spectrum. That is a lot of board to buy back a
millisecond transient that firmware already closes.

**It would become the right answer** if VREF had to ride out a short
indefinitely rather than shed the channel — then 2.5 W really is continuous.
That argument does not hold here, for the reason in
[§ Shedding a faulted feed](#shedding-a-faulted-feed): the fault has already
cost you the sensors on that branch.

---

## Still open

**A pre-schematic review of this chain is in
[`review-vref-chain.md`](review-vref-chain.md)** — four findings, two of which
are the same class of error: a protection element specified against the nominal
fault but not against that fault coinciding with a load dump.


| | |
|---|---|
| **[CONFIRM]** | the 20 ms startup blanking window, on the bench against the real sensor load — see [§ The retry policy](#the-retry-policy) |
| **[DECIDE]** | TVS **manufacturer** — SMAJ24CA from an AEC-Q101 qualified source; the generic datasheet in the repo claims no automotive qualification |
| **[CONFIRM]** | LM74700-Q1 behaviour at **20 mA forward** — controllers regulate a small forward drop and some specify a minimum current for regulation |
| **[CONFIRM]** | MF-NSHT050KX I<sub>hold</sub> derating — 0.50 A must stay above the switch's 250 mA limit at worst-case cabin ambient, or it nuisance-trips |
| **[CONFIRM]** | TPS2H160B-Q1 specs are characterised at V<sub>VS</sub> = 13.5 V. 5 V is inside the 3.4–40 V operating range but not where the tables were taken — verify current-limit accuracy at 5 V |
| ~~**[CONFIRM]**~~ | ~~TR sensor on VREF~~ — **closed**: Ford's diagrams show the DTR is a switch array returning on SIGRTN, not a VREF load. Speed-control switches still open |

The `THER` decision is worth thinking about rather than defaulting. **Auto-retry**
keeps the engine running through a transient short, which is what you want from
a sensor supply — losing VREF loses TPS and idle control. **Latch** stops a hard
short from thermally cycling the part indefinitely. Auto-retry with firmware
counting the retries and latching in software gets both, and the always-on MCU
domain means there is something awake to do the counting.
