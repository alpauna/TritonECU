# VREF supply design

The replacement ECU must source the buffered 5 V sensor reference the OEM PCM
provides on two pins (A-20, C-20). See
`1999-Ford-F150-4wd-5.42v/oem-connectors.md`.

**Originally specified:** separate supply, isolated from the internal 5 V,
outbound resettable fuse, **3 A** output.

**Decided:** separate 5 V linear supply, common ground, feeding a
**TPS2H160B-Q1** dual-channel smart high-side switch — one channel per VREF
feed, current limit set at **250 mA**, per-channel current sense, fault
reporting, and a 40 V output rating that survives a short to battery. See
[§ The output stage](#the-output-stage-tps2h160b-q1).

The separation was right and matters. The current figure moved, and the
protection scheme had a hole in it.

**No longer open — one VREF pin or two.** The EEC-V pinout shows one (pin 90,
BRN/WHT); Ford's power-pin sheet lists two (A-20, C-20). That mattered when the
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
| TR sensor | ~5 mA | resistive ladder **[CONFIRM]** |
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
  12 V ──► [ separate 5 V linear regulator ]  ← own regulator, not the logic rail
                        │
                        │   ┌─────────── TPS2H160B-Q1, dual channel ───────────┐
                        └──►│  ch1  limit 250 mA ├──► PTC ──► A-20             │
                            │  ch2  limit 250 mA ├──► PTC ──► C-20             │
                            │  FAULT ──► GPIO    CS ──► STM32 ADC   SEL ──► GPIO│
                            └──────────────────────────────────────────────────┘
```

- **Separate regulator from the internal 5 V.** As originally specified.
  Sensor-supply noise and harness fault current never reach the logic rail or
  the ADC supply. A linear regulator is sufficient and preferable at this load.
- **Per-feed current limit at 250 mA**, set by one resistor. Ten times the
  ~25 mA real load, and it matches what Ford's own VREF is rated at across both
  pins. A 22 AWG wire is untroubled by it.
- **Fault flag into a GPIO** so a VREF short becomes a logged DTC — "VREF
  circuit A shorted" — rather than a truck that mysteriously will not run.
- **PTC keeps a job, but not the one it was given.** See
  [§ What the PTC is actually for](#what-the-ptc-is-actually-for).

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

**Sizing R<sub>CS</sub>.** K(CS) = 290, so I<sub>CS</sub> = I<sub>OUT</sub>/290:
25 mA gives 86 µA, and the 250 mA limit gives 862 µA. At **R<sub>CS</sub> =
3.3 kΩ** that is 0.28 V normally and 2.84 V at the limit — a 3.3 V ADC span with
the resolution where the fault case is. The CS pin tolerates 7 V and 30 mA, so
there is ample margin.

### CS does not belong on the AD7606

Two VREF-related analog signals exist and only one is precision-critical.
Conflating them is easy and wrong:

| Signal | Converter | Why |
|---|---|---|
| **VREF sense** — the 5.00 V rail itself | **AD7606** | it is the ratiometric divisor; measuring it on the same converter as the sensors lets errors cancel |
| **CS** — diagnostic current | **STM32 internal ADC** | ±17% inherent accuracy, static, fault detection only |

Putting CS on the precision converter would be measuring a ±17% signal with a
16-bit instrument. The internal ADC's own error is a rounding difference against
the sense ratio's tolerance.

There is no shortage of native channels to worry about, either. The four-channel
limit noted in the firmware's `Board.h` was an **ESP32-P4** constraint — the C6
radio link occupied ADC1 channels 0–3. On the STM32F767ZI there are three ADCs,
against a pin budget of 37 used out of ~114.

---

## What the PTC is actually for

The original scheme gave the PTC a job it could not do — see
[§ The blind spot](#the-blind-spot-short-to-battery) — and the switch now does
that job properly. But the PTC is not redundant, because **running the switch
from 5 V creates a reverse-current path the datasheet requires you to limit.**

§8.3.6.3: on a short to battery, if V<sub>OUT</sub> − V<sub>S</sub> exceeds the
body-diode drop, reverse current flows and **must be externally limited to below
I<sub>R(1)</sub> = 2.5 A**.

At V<sub>S</sub> = 13.5 V a 14 V short is a 0.5 V differential and nothing
happens. **At V<sub>S</sub> = 5 V it is a 9 V differential**, so real current
flows. Harness resistance plus the PTC is what keeps it under 2.5 A.

So the PTC stays, and its sizing rationale is unchanged — a **16 V part**, not
the 2920L030/150GR 150 V devices freed up from the input, for the reason that
disqualified them upstream: **high-voltage PPTCs trip in 8–16 seconds**, because
a 120–150 V element needs a thick polymer body and thickness is thermal mass.

| | 150 V part | 16 V part |
|---|---|---|
| Trip time | **8–16 s** | 0.1–0.5 s |
| Resistance | 1–3 Ω | lower for the same hold current |

Size the hold current at ~100–150 mA: below the switch's 250 mA limit, above the
~25 mA real load.

### The accuracy problem this document used to have is gone

Earlier revisions argued at length that VREF must be *sensed downstream of the
PTC*, because a PPTC is a thermistor by construction — its resistance rises with
current and ambient and roughly doubles after each trip, putting 75 mV of
wandering error on a 5.00 V ratiometric reference.

**That argument is retired.** The fix it proposed — take the regulator's
feedback from the far side of the PTC — never worked for two feeds anyway: there
are two far sides and one loop. What actually removes the problem is the switch's
**4 mV** drop at 25 mA, which is 20× smaller than the PTC's and stable.

Take the sense at the regulator, one channel, covering both feeds. If a PTC
trips, the `FAULT` and `CS` path is what reports it — not a drifting voltage
nobody can calibrate out.

## On "isolated"

Worth being explicit: this should be a **separate regulator with a common
ground**, not galvanic isolation.

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

## Still open

**The 5 V regulator itself has no part number.** Its sizing case is not the
25 mA normal load — it is **a fault on one feed while the other keeps working**:

```
250 mA (channel in current limit)  +  25 mA (healthy channel)  =  275 mA
```

**It is fed from the 6.0 V SEPIC rail, not from battery**, so the drop is 1 V:

```
(6.0 V − 5.0 V) × 275 mA  =  0.275 W   in fault
(6.0 V − 5.0 V) ×  25 mA  =  0.025 W   normally
```

That makes the thermal question a non-question, and the linear choice trivially
correct — the argument against a buck here was never dissipation, it was ripple
on a ratiometric reference. See
[§ Why the number fights itself](#why-the-number-fights-itself).

The ~275 mA does come out of the 6.0 V rail's budget, which
[`power-supply.md`](power-supply.md) settled at **2 A**. (Note
[`v1-scope.md`](v1-scope.md) still says 3 A in its board table — stale.)

| | |
|---|---|
| **[DECIDE]** | `THER` pin: latch or auto-retry on thermal shutdown |
| **[DECIDE]** | PTC part — 16 V, ~100–150 mA hold |
| **[CONFIRM]** | TPS2H160B-Q1 specs are characterised at V<sub>VS</sub> = 13.5 V. 5 V is inside the 3.4–40 V operating range but not where the tables were taken — verify current-limit accuracy at 5 V |
| **[CONFIRM ON TRUCK]** | one VREF pin or two. Not blocking — the part is dual-channel either way |
| **[CONFIRM]** | TR sensor and speed-control switches really are on VREF (load table above) |

The `THER` decision is worth thinking about rather than defaulting. **Auto-retry**
keeps the engine running through a transient short, which is what you want from
a sensor supply — losing VREF loses TPS and idle control. **Latch** stops a hard
short from thermally cycling the part indefinitely. Auto-retry with firmware
counting the retries and latching in software gets both, and the always-on MCU
domain means there is something awake to do the counting.
