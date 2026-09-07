# VREF supply design

The replacement ECU must source the buffered 5 V sensor reference the OEM PCM
provides on two pins (A-20, C-20). See
`1999-Ford-F150-4wd-5.42v/oem-connectors.md`.

**Specified:** separate supply, isolated from the internal 5 V, outbound
resettable fuse, **3 A** output.

The separation is right and matters. The current figure is worth revisiting.

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
current limit sits.

```
  12 V ──► [ separate 5 V regulator, ~500 mA ]  ← own regulator, not the logic rail
                        │
                        ├──► [ limit ~150 mA, fault flag ] ──► VREF feed A ──► PTC ──► A-20
                        │
                        └──► [ limit ~150 mA, fault flag ] ──► VREF feed B ──► PTC ──► C-20
```

- **Separate regulator from the internal 5 V.** As specified. Sensor-supply
  noise and harness fault current never reach the logic rail or the ADC supply.
  A linear regulator is sufficient and preferable at this load.
- **Per-feed electronic current limit at ~150 mA.** Well above the ~25 mA real
  load, well below anything that harms a 22 AWG wire. An electronic limit or
  load switch reacts in **microseconds**, not seconds.
- **PTC as a backstop only**, not the primary protection. It catches the case
  where the electronic limiter itself fails short.
- **Fault flag into a GPIO** so a VREF short becomes a logged DTC — "VREF
  circuit A shorted" — rather than a truck that mysteriously will not run.

### On "isolated"

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
AD7606C analog supply, the J1850 transceiver and any level shifting. If that is
the intent, the answer is the same diagram: build the rail at 3 A, and still
current-limit each VREF feed at ~150 mA on its way out of the box.

The rail can be as strong as you like. What leaves the connector and goes into
the truck's harness should not be.
