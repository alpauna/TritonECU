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

## Architecture: two 3.3 V rails, no ORing

## Architecture: two 3.3 V rails, no ORing

The rail tree in [`power-supply.md`](power-supply.md) takes 3.3 V from the 6 V
main. That has to split, and the clean split avoids ORing two supplies:

```
protected rail ─┬─ always-on buck ─► 3.3 V MCU        (MCU only, low-Iq)
                │
                └─ LM5155-Q1 SEPIC ─► 6.0 V ─┬─ buck ─► 3.3 V peripherals
                     (enabled when running)   ├─ LDO ──► 5 V digital
                                              ├─ LDO ──► 5 V analog
                                              └─ LDO ──► 5.00 V VREF
```

- **The MCU's supply is sized for its full running current**, not just sleep, so
  there is never a handover and no ORing device. Everything else 3.3 V — SD
  card, peripherals — stays on the switched buck.
- **The SEPIC is off when parked.** The hardest converter in the design no
  longer runs 24/7, and ENOUT already sequences it (§9 of the review).
- The always-on converter must work down to the same ~3.9 V floor, so it wants
  to be a **buck-boost or SEPIC**, not a plain buck. At 3.9 V in, 3.3 V out, a
  buck is at ~85 % duty with no margin for its own dropout.

**[verify]** the STM32F767ZI's actual run current at the intended clock before
sizing that converter — it sets whether this is a 300 mA or a 600 mA part.

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
