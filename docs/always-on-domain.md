# Always-on MCU domain

**Proposal:** the MCU never fully powers down. It sleeps on a constant 3.3 V
supply and brings the 5 V rails up only when the engine needs to run.

This is how production ECUs are built, and it is a better answer than anything
in [`power-supply-super-cap.md`](power-supply-super-cap.md).

## What it retires

| Open thread | Status |
|---|---|
| Graceful shutdown before the rails collapse | **gone** — nothing collapses |
| KAPWR replacement for fuel trims and DTCs | **gone** — RAM never loses power |
| Supercapacitor hold-up | **gone** — the requirement that justified it is removed |
| Boot delay at key-on | **gone** — already running |

And it fixes something the review had written off. `schematic-review-power.md`
§"auto-retry" concluded that firmware retry-limiting "cannot be the primary fix,
because the MCU loses its rail." **With an always-on domain the MCU survives the
fault and can count retries, latch SHDN#, and log what happened.** The auto-retry
thermal problem becomes solvable in software after all.

Same for FLT#: the 44 ms warning stops being a race against the MCU's own death
and becomes an ordinary interrupt with plenty of time to shed loads and record
the event.

## The number that decides it: parasitic drain

A parked vehicle tolerates roughly **25–50 mA** total, and the truck has its own
draws before ours.

| Item | Sleep current |
|---|---|
| LTC4364 quiescent | **750 µA** |
| STM32F767 Standby + RTC + backup SRAM | **3 µA** |
| Always-on 3.3 V converter, quiescent | ~20 µA |
| INA238 in shutdown | ~2 µA |
| **Total** | **≈ 780 µA** |

```
780 µA × 720 h  =  0.56 Ah/month
group 65 battery ≈ 70 Ah  →  0.8 %/month,  ~5 % over six months
```

Comfortable. **Note what dominates: the LTC4364, at 250× the MCU's draw.**

### Standby, not Stop

| STM32F767 mode | Current | Retained |
|---|---|---|
| Stop, RAM retained | ~350 µA | all 512 KB, instant wake |
| **Standby + backup SRAM** | **~3 µA** | 4 KB + RTC, wakes via reset |

Fuel trims, DTCs and adaptive tables are small — **4 KB is ample**, and Standby
is 100× cheaper. Waking through a reset costs milliseconds, which is nothing
against a key turn. Use Standby; keep anything larger in SD or flash.

## The part: MAX25239AFFA

Datasheet: [`Datasheets/max25239-max25240.pdf`](Datasheets/max25239-max25240.pdf).
It fits the role better than the generic requirement written above.

| | MAX25239AFFA | Why it matters here |
|---|---|---|
| Topology | **H-bridge buck-boost, one inductor** | the "not a plain buck" requirement, met |
| Input | **2 V to 36 V**, 42 V transient | 2 V is far below the 4.2 V system floor |
| Switching | **2100 kHz** | AM-clear, same rationale as the SEPIC |
| Quiescent | **95 µA** no-load, auto skip mode | the always-on number |
| Shutdown | **5 µA** typ, EN low | for the *switched* rail |
| Spread spectrum | ±6 %, SPS pin | the SEPIC design has none |
| Qualification | **AEC-Q100 Grade 1**, −40 to +125 °C | ✓ |
| Current limit | 8.2 A, 6 A continuous | 20× the MCU load |
| Extras | PGOOD, 2.5 ms soft-start, PLL SYNC | |

### Catch: AFFA's *fixed* output is 5 V — 3.3 V needs adjustable mode

From the ordering table:

```
                     ILIM    FIXED VOUT    ADJ VOUT    fSW
MAX25239AFFA/VY+     8.2 A      5 V         < 6.5 V    2100 kHz
```

The **fixed** option on this variant is 5 V. What makes it usable at 3.3 V is
the **adjustable** column: this variant covers anything **below 6.5 V** with an
external feedback divider. So wire it for adjustable mode, not the fixed option.

That same column is the interesting part — see below.

### It must sit behind the LTC4364, not on raw B+

```
MAX25239 transient rating      42 V
SMDJ43A clamp                  69.4 V      ← what raw B+ actually sees
LTC4364 regulated output       27 V        ✓
```

**42 V is below the TVS clamp**, so an always-on rail tapped ahead of the
LTC4364 would be destroyed by the first transient the TVS passes. Behind the
LTC4364 it never sees more than 27 V, and the part's 2 V minimum means the
LTC4364's 4.2 V cutoff remains the system floor — as intended.

### Revised drain budget

| Item | Sleep current |
|---|---|
| LTC4364 quiescent | 750 µA |
| MAX25239 #1, 3.3 V, skip mode | **95 µA** |
| MAX25239 #2, 6 V rail, EN low | **5 µA** |
| STM32F767 Standby + backup SRAM | 3 µA |
| **Total** | **≈ 853 µA** → 0.61 Ah/month |

Unchanged conclusion: comfortable, and still dominated by the LTC4364.

### Package is the practical objection

**FC2QFN, 4.25 × 4.25 mm, 22 pins** — flip-chip QFN, no visible joints, not
hand-solderable. That is a real problem for bench work.

**MAX25239EAFNA/VY+** is the same silicon and same options (8.2 A, <6.5 V adj,
2100 kHz) in an **18-pin FCQFN at 5.00 × 5.00 mm** — fewer, larger pads.
Prefer it for anything hand-assembled.

## Architecture: cascade, not two independent rails

**Decided:** MAX25239 makes the main rail, TLV62085 makes 3.3 V from it.

```
B+ ─ TVS ─ LTC4364 ─► MAX25239 ─► 5.5 V ─┬─► TLV62085 ──► 3.3 V   (MCU, SD, peripherals)
                       (always on)        ├─► LDO ───────► 5 V digital
                                          ├─► LDO ───────► 5 V analog
                                          └─► LDO ───────► 5.00 V VREF
```

This replaces the earlier "two independent 3.3 V rails" sketch. Both converters
stay powered when parked; the MCU's Standby mode does the saving.

### TLV62085RLTR

Datasheet: [`Datasheets/TLV62085RLTR-Datasheet.pdf`](Datasheets/TLV62085RLTR-Datasheet.pdf).

| | |
|---|---|
| Input | **2.5 V to 6.0 V** ← the number that sets the main rail |
| Output | 0.8 V to V<sub>IN</sub>, adjustable, **3 A** |
| Switching | 2.4 MHz (DCS-Control, load-dependent) |
| **Quiescent** | **17 µA** no load |
| Shutdown | **0.7 µA**, EN low |
| Light load | **Power Save Mode**, automatic |
| Dropout | **100 % duty cycle** capable |
| Fault | **Hiccup short-circuit protection** |
| Package | VSON-HR (RLT), **2 × 2 mm**, 7 pins |
| Temperature | −40 to +125 °C |

### Set the main rail at 5.5 V, not 6.0 V

The TLV62085's **6.0 V absolute input maximum** collides with the 6 V main rail
that [`power-supply.md`](power-supply.md) chose for LDO headroom:

```
6.0 V nominal ± 2 % regulation  →  6.12 V     over the TLV62085's rating ✗
5.5 V nominal ± 2 % regulation  →  5.61 V     7 % margin                ✓
```

**5.5 V satisfies both constraints:**

- TLV62085 input stays inside 2.5–6.0 V with real margin
- The 5 V LDOs keep **0.5 V of headroom** — enough for low-dropout parts at the
  25–150 mA these rails draw, where 1 V was never actually required
- MAX25239AFFA's adjustable range is "< 6.5 V", so 5.5 V is in range

Do **not** use the part's fixed 5.0 V option: it leaves the 5 V LDOs no headroom
at all, and VREF in particular has to be a regulated 5.00 V isolated from the
switcher.

### This largely defuses MAX25239 Note 5

[`power-supply.md`](power-supply.md) flags *"output short circuit not allowed"*
as the blocking question for using the MAX25239 more widely. In **this**
topology it matters much less: the MAX25239's output faces **three LDOs and one
buck, every one of them internally current-limited**, and never a connector,
harness or anything a fault can reach. The TLV62085 brings its own hiccup
protection, and VREF's harness exposure sits behind an LDO plus a PTC.

The question still needs answering before the MAX25239 drives anything external.
It is no longer blocking for this arrangement.

### Revised drain budget

| Item | Sleep current |
|---|---|
| LTC4364 quiescent | 750 µA |
| MAX25239, 5.5 V, skip mode | 95 µA |
| **TLV62085, Power Save Mode** | **17 µA** |
| 5 V LDO quiescents (or disabled) | ~10 µA |
| STM32F767 Standby + backup SRAM | 3 µA |
| **Total** | **≈ 875 µA** → 0.63 Ah/month |

Cascading costs 17 µA over the parallel arrangement. Irrelevant against the
LTC4364's 750 µA.

### Two notes, neither blocking

- **Not AEC-Q100.** Every other part in this chain is automotive-qualified —
  LTC4364, MAX25239 Grade 1, LM5155-Q1. The TLV62085 is rated −40 to +125 °C,
  which is the Grade 1 *temperature* range, but without the qualification,
  PPAP or change control. For a one-vehicle build that is a reasonable trade;
  it should be a stated choice rather than an oversight.
- **2.1 MHz and 2.4 MHz beat at 300 kHz**, which is inside CISPR 25's band. It
  mostly stays internal — the TLV62085 is a point-of-load, so its switching
  appears as load modulation that the MAX25239's output capacitors absorb rather
  than as harness current. DCS-Control is also not rigidly fixed-frequency, so
  there is no clean tone to beat against. Worth a look on the bench, not worth
  designing around.
- Power Save Mode drops the switching frequency at light load, potentially into
  the AM band — but that only happens with the MCU asleep and the vehicle
  parked, when the radio is off too.

## Tapping point: after the LTC4364, not before

Simplest and protected. The cost is the LTC4364's 750 µA running permanently,
which the budget above absorbs.

The alternative — tapping raw B+ so the MCU can shut the LTC4364 down via SHDN#
— would cut the parasitic to tens of microamps, but it needs a **second
transient-protection chain** for a rail that must survive load dump and reverse
battery on its own. **Not worth it at 0.56 Ah/month.** Revisit only if the truck
sits for many months at a time.

## The new requirement this creates: low-battery self-disable

An always-on load is a permanent path to a flat battery. The design has to be
able to give up.

**Firmware does this for free**, using the INA238 already on the shunt:

```
bus voltage < ~11.5 V for N seconds
  → write learned state to SD
  → enter Standby (3 µA)
  → wake only on ignition, never on the RTC
```

Below that threshold the battery is already too weak to be worth defending, and
3 µA is close enough to nothing that it cannot be what fails to start the truck.
The LTC4364's UV pin cannot serve here — it is set at 4.47 V, which is a
brownout threshold, not a battery-protection one.

**This is not optional.** Without it, a slow parasitic drain plus a marginal
battery becomes a no-start that looks like a dead ECU.

## Open questions

- **Wake source wiring.** Switched ignition into an MCU pin needs level shifting
  and its own transient protection — it is a harness-facing input.
- **Whether the SD card stays on the switched rail.** It probably should; it is
  a large sleep load otherwise, and nothing needs it while parked.
- **Watchdog behaviour in Standby**, so a hung MCU cannot sit awake drawing
  hundreds of milliamps in a parked truck.
