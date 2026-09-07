# Input protection — LTC4364-2

One part covers reverse polarity, load-dump clamping, overcurrent and brownout
holdup, and it is automotive-qualified.

| | |
|---|---|
| Operating range | **4 V to 80 V** |
| Surge withstand | **over 80 V** with the VCC clamp network |
| Output clamp | **adjustable** |
| **Reverse input protection** | **to −40 V** |
| Reverse output protection | to −20 V |
| Overcurrent | timed, current-limited circuit breaker |
| Brownout | **ideal diode holds the output up** |
| Qualification | **AEC-Q100** |
| Packages | 4 × 3 mm DFN-14, MSOP-16, SO-16 |

Its own datasheet headline application is a **4 A 12 V automotive regulator
withstanding a 200 V 1 ms transient**, clamping a 92 V surge to 27 V. That is
this application.

## What it replaces

| Previously planned | Now |
|---|---|
| Reverse-polarity P-FET | **the ideal diode controller** — same job, −40 V capable, and it actively regulates the forward drop instead of eating a diode drop |
| Resettable fuse as primary protection | **the timed circuit breaker** — electronic, fast, and it retries |
| Crowbar | **the output clamp** — regulates rather than shorting |

**Keep a physical fuse anyway**, but demote it: it is now the backstop for the
pass FET failing short, not the primary overcurrent protection. That is a real
if unlikely mode, and it is the one thing the LTC4364 cannot protect against by
definition.

**Keep the TVS too.** ISO 7637-2 pulses 3a and 3b are 0.1 µs events — far too
fast for any FET-based scheme to respond to. The TVS catches those; the
LTC4364 handles everything from microseconds upward.

## The ideal diode solves the cranking problem twice over

The datasheet notes the ideal diode controller **holds up the output voltage
during input brownouts**. That is exactly the cold-crank case: when the battery
sags, the output capacitance holds the SEPIC's input up and the ideal diode
blocks reverse current back into the sagging battery.

So cranking is now defended at two levels — the SEPIC works down to 3.5 V, and
the ideal diode plus bulk capacitance stops it ever getting there.

## Configuration

### Choose the −2, not the −1

**LTC4364-1 latches off. LTC4364-2 auto-restarts** at a 0.1 % retry duty cycle.

For a vehicle, take the **−2**. A latched shutdown after a transient means a
truck that has to be key-cycled — or towed, if the fault was momentary and has
already cleared. Auto-retry at 0.1 % duty is gentle enough to protect the FET
while still recovering on its own.

Note the datasheet's detail: **auto-retry is disabled during overvoltage**, so
the −2 does not repeatedly slam back into a sustained overvoltage. It retries
after a fault, not into one.

### Set UV below the cranking minimum

The external MOSFET is **held off in undervoltage**. The UV threshold is set by
a resistor divider, and it must sit **below the worst cranking sag** — around
**4.5–5 V** — or the protection circuit itself becomes the thing that kills the
ECU during a start. This is the single easiest way to get this part wrong.

### Set the output clamp around 27–30 V

Low enough to let the SEPIC use **80 V switching devices** (see
[`supply-layout.md`](supply-layout.md)), high enough to be clear of any normal
charging-system voltage.

### Size the fault timer against a real load dump — and the FET's SOA

This is the calculation that matters, and it is a thermal one.

While clamping, the pass FET drops the difference between input and clamp at
full load current. With the SEPIC drawing ~0.7 A from a 30 V clamped rail:

```
worst case:  (87 V − 30 V) × 0.7 A ≈ 40 W
duration:    load dump, up to 400 ms
energy:      ≈ 16 J into the pass FET
```

Two consequences:

1. **The fault timer must be long enough not to trip during a legitimate load
   dump.** A load dump is a normal event; shutting down for it defeats the
   purpose.
2. **The pass FET must survive 16 J in its safe operating area** for that
   duration. This is a SOA selection, not an R<sub>DS(on)</sub> one — the
   device spends the event in *linear* mode, which is the regime most modern
   low-R<sub>DS(on)</sub> FETs are worst at. A larger, older, more robust part
   is often the right answer here, and the datasheet's own example uses a
   D²PAK.

**[CONFIRM]** the actual load-dump level for this vehicle. A '99 Ford
alternator very likely has avalanche-rated rectifiers giving some clamping,
which would reduce the 87 V figure considerably and relax the FET requirement.
Worth establishing before over-specifying.

## Resulting input chain

```
Battery ─► fuse ─► TVS ─► LTC4364-2 ─► SEPIC (LM5155-Q1) ─► 6.0 V
                          │  ├─ pass FET (SOA-rated, linear mode during clamp)
                          │  └─ ideal diode FET (reverse protection, holdup)
                          └─ VCC clamp network for >80 V survival
```

| Element | Covers |
|---|---|
| Fuse | pass FET failed short — the one thing downstream cannot self-protect |
| TVS | sub-microsecond ISO 7637 pulses, faster than any FET can respond |
| **LTC4364-2** | **reverse polarity, load dump, overcurrent, brownout holdup, UV lockout** |
| LM5155-Q1 | 3.5–45 V in, 6 V out |
