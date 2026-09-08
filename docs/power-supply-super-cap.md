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

## What still needs solving

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
| Inrush | handled by the LTC4364 | **becomes our problem** |
| Noise near the ADC | controlled | unknown if a module is used |

Not a decision. But the layout row is the one that matters most, and it is the
part of the current design most likely to cause trouble on a first spin.
