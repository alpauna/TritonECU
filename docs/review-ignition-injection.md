# Ignition and injection chain review — pre-schematic

Review of the eight coil and eight injector channels as specified in
[`output-drivers.md`](output-drivers.md), now that Ford's own diagrams are in
the tree. Same discipline as
[`review-vref-chain.md`](review-vref-chain.md) and
[`review-solenoid-chain.md`](review-solenoid-chain.md).

```
STM32 ──► 74HCT541 @ 5 V ──► 470 R ──► ISL9V3040 ──► coil ──► 12 V   (x8)
STM32 ──────── direct 3.3 V ──► 470 R ──► ZXMS6005DGQ ──► injector ──► 361 RD  (x8)
                                            └─► Schottky to ground, both stages
```

**This chain came out well.** Two findings, both about things missing from it
rather than wrong within it.

---

## 1. IMPORTANT — the IAC valve has no driver assigned

| | |
|---|---|
| PCM pin | **83** |
| Circuit | 264 WH/LB, C110 |
| Feed | **361 RD** — the same circuit as the PCM's own VPWR |
| Drive | **PWM** — *"Duty cycle signals … control a solenoid that opens or closes air bypass"* |
| Current | ~1–2 A (Ford IAC, ~6–13 Ω) |

`grep -rn IAC docs/output-drivers.md docs/v1-scope.md` returns **nothing**. The
NCV8405A channel budget lists twelve loads and IAC is not among them.

**This is the third instance of the same gap** — EPC and TCC were missing for
the same reason, and both were listed in `pin-budget.md` as *"IAC | 1 | PWM"*,
which allocates a **pin** and reads like an allocated **driver**.

`sensors-to-run.md` is blunt about what it costs: *"Without it there is no idle
control at all — the engine will only idle on the throttle stop."*

**Fix:** NCV8405A, SOT-223 (1.82 A on a minimum pad covers 1–2 A), driven
through the **74HCT541** buffer alongside the other PWM channels — it has four
spare and this makes five. Channel count goes **12 → 13**.

**And it needs a freewheel diode, but uniquely no new connector pin.** Its feed
is **361 RD**, which *is* the ECU's VPWR at pins 71 and 97 — already inside the
box. Unlike 1138 and 391, the return node is free.

---

## 2. The injector stage has no interlock equivalent to the ignition stage's

The ignition stage has a deliberate two-key interlock: the **74HCT541's `OE1`
and `OE2`, both pulled up**, so the outputs are high-impedance at power-on, plus
the IGBT's internal 10–26 kΩ gate-emitter resistor. And because
[`always-on-domain.md`](always-on-domain.md) **gates the 5 V rail**, the buffer
is *unpowered* in sleep — the coils cannot fire, by construction.

**The injectors have none of that.** They are driven **direct from 3.3 V GPIOs**,
which live in the always-on domain and are therefore *live in sleep*. Their
default-off rests entirely on the specified **10 kΩ pulldown** plus firmware
holding the pins low.

That asymmetry is not obviously wrong, but it should be a decision rather than
an accident. **The system-level answer already exists:** the fuel pump relay is
on the TBD62083AFNG, whose expander defaults off, so an injector opened in sleep
sees no rail pressure. Ford relies on the same interlock.

> **Recorded rather than fixed.** Adding an `OE`-style interlock to the injector
> stage would mean a buffer the drivers do not otherwise need — the
> ZXMS6005DGQ's whole appeal is that it runs direct from 3.3 V. The pulldown
> plus the fuel pump relay is a reasonable answer; it just was not written down
> as one.

---

## 3. The coil supply circuit is not in the tree

The injector feed is confirmed as **361 RD** from S127/S129. The **coil** feed is
not: Ford's ignition sheets are DIA 21-1 and 21-4, which are not among the
diagrams provided.

It does not block anything — the coils need the 400 V clamp, not a freewheel
return, so no supply node is wanted inside the ECU. But *"dumb coils, 12 V one
side, driver grounds the other"* is still an inference rather than something
read off a diagram.

> **[CONFIRM]** the coil supply circuit and whether all eight share one feed,
> from ignition diagram 21-1 or 21-4.

---

## 4. Checked and clear

| | |
|---|---|
| **PCM pins 21 and 22** | Ford's sheet groups ten pins under "IGNITION SYSTEM", which looked like two more drivers than the design has. They are **CKP+ and CKP−** — the crank sensor lives on the ignition diagram. Eight coil drivers confirmed at pins 26, 104, 52, 53, 27, 1, 78, 79 |
| **Injectors are low-side** | Confirmed: each fed 361 RD, PCM grounds them — pins 75, 101, 74, 100, 73, 99, 72, 59 |
| **Direct 3.3 V injector drive** | Legitimate here, and **explicitly characterised**: the ZXMS6005DGQ specifies R<sub>DS(on)</sub> **at V<sub>IN</sub> = 3 V**. This is the exact contrast with [`review-solenoid-chain.md`](review-solenoid-chain.md) §2, where the solenoid drivers are only specified at 5 V and therefore need the buffer |
| **Schottky to ground per output** | [`harness-protection.md`](harness-protection.md) already reasons this through for *both* stages, including the IGBT case — the ISL9V3040 specifies only **30 V emitter-to-collector**, so it needs the negative-transient path more than the MOSFET does, not less |
| **Buffer supply during cranking** | The 5 V rail is a MAX25239 **buck-boost**, so it holds through a crank sag, and the LTC4364's UV is set to **4.47 V** — below the sag, as `surge-stopper.md` insists |
| **Buffer propagation delay** | Tens of ns against **27.8 µs per crank degree** at 6000 rpm, and a fixed delay is calibratable regardless |
| **Load-dump clamp energy** | Covered by [`review-protection-sweep.md`](review-protection-sweep.md) §A1: the injector clamp energy rises 1.8× at a 35 V supply, against 7.5 mJ stored versus a 490 mJ rating. The 400 V ignition clamp barely notices |
| **Battery sense shares the injector feed** | V<sub>BAT</sub> is measured at the LTC4364's shunt, on **361 RD** — the same circuit feeding the injectors, so it dips slightly during injection. At ~1–2 A through harness resistance that is sub-1 %, but dwell and dead-time compensation both consume V<sub>BAT</sub>, so **sample it away from injection events** rather than averaging through them |

---

## Summary

| # | Finding | Action |
|---|---|---|
| 1 | **IAC valve has no driver** — third instance of pin-allocated-reads-as-driver-allocated | NCV8405A via the buffer; freewheel to VPWR, no new pin |
| 2 | Injector stage has no `OE`-style interlock | recorded: the fuel pump relay is the system answer |
| 3 | Coil supply circuit not in the tree | **[CONFIRM]** from ignition diagram 21-1/21-4 |

**The recurring defect is not electrical.** Three times now a load has been
listed in `pin-budget.md` as *"N | PWM"* and read as though a driver had been
assigned, when only a pin had. EPC, TCC and now IAC. Worth a pass over that
table asking, for every row, **which part switches it.**
