# Enclosure requirements

Not yet designed. This file collects the constraints the board has already
imposed, so the housing is specified rather than discovered.

---

## It must be vented — and not only for the barometric sensor

**Requirement: a gas-permeable, liquid-blocking vent membrane** (Gore-type or
equivalent), fitted to the housing.

### The barometric sensor is unusable without it

A **sealed** box contains a fixed mass of air, so its internal pressure follows
the gas law and tracks **under-hood temperature, not the weather**. The
[KP497](barometric-sensor.md) would faithfully report the inside of its own
enclosure. Once vented, internal pressure equals ambient regardless of how hot the
box gets — which is also why **heat is a parts-rating question, not an accuracy
one**.

### But venting is better practice anyway

This is not a concession made for one sensor. **A sealed automotive enclosure
pumps moisture past its own seals.** Every heat cycle raises internal pressure and
pushes air out; every cool-down lowers it and draws air — and whatever is around
the seal — back in. Over years that is a moisture pump aimed at the inside of the
box.

A vent membrane gives that breathing a deliberate path that passes water vapour
and blocks liquid water, which is why production ECUs have them. The barometric
sensor gets a correct reading as a **side effect of doing the enclosure properly**.

### Site the vent out of moving air

Ram air at the vent biases the reading:

| speed | dynamic pressure |
|--:|--:|
| 60 mph | 0.43 kPa |
| 80 mph | 0.77 kPa |

Against the KP497's ±2 kPa that is small, but it is a **speed-correlated** error
rather than noise — exactly the kind that looks like a real signal in a log. Put
the vent somewhere sheltered, and away from anything a pressure washer can reach
directly.

---

## RESOLVED — the ECU lives in the cabin, behind the glovebox

Upper right-hand side, behind the glovebox, matching the OEM PCM location.
Confirmed by the owner. That settles several things at once.

### The temperature constraint lifts

| | |
|---|---|
| **ADC** | the 200 kSPS option (−40…+85 °C) is **no longer ruled out**. The AD7606B already specified reaches 125 °C and is a populate-different-part change either way, so there is no reason to move — but the constraint is gone. [`adc-front-end.md`](adc-front-end.md) |
| **Barometric** | never constrained; the KP497 reaches 105 °C |
| Everything else | cabin ambient, not under-hood |

### The box straddles the firewall — one end is under-hood

**The 104-pin connector is accessed from the engine bay.** The housing sits in the
cabin but its connector face passes through the firewall, so the harness plugs in
from under the hood. That is how the OEM PCM does it, and it is why the factory
gets mild cabin air for the electronics without needing a bulkhead connector.

It means the enclosure has **two environments, not one**:

| | cabin side | connector face |
|---|---|---|
| Temperature | cabin ambient | under-hood |
| Water | none | spray, salt, washing |
| Pressure | cabin | engine bay |

**So the vent goes on the CABIN side.** This corrects the assumption above that
the location alone settles vent siting — it does not. A membrane on the connector
face would sit in exactly the ram air, spray and pressure-wash path the siting
rule exists to avoid. On the cabin side it is sheltered by the glovebox and sees
nothing worse than a footwell.

Fit the membrane regardless of side — the moisture-pumping argument does not
depend on location, and cabin humidity still cycles.

### The firewall seal is now a pressure boundary too

It was already the water barrier. With a barometric sensor inside, **a leak at
that seal also lets engine-bay pressure into the box** — and the bay runs a few
hundred pascals away from the cabin at speed. Same order as the blower effect
below, small against ±2 kPa, and **speed-correlated again**.

The seal earns its keep twice over: water out, and one pressure domain rather
than an average of two.

### But a cabin is not quite at ambient pressure

Worth knowing before a log gets misread:

- **The blower pressurises the cabin.** Cars carry pressure-relief vents
  specifically to limit this; the residual is on the order of **100–250 Pa** with
  the blower high. Against the KP497's **±2 kPa** that is roughly a tenth of the
  accuracy — negligible in magnitude, but **correlated with fan speed**, which is
  the kind of error that looks deliberate in a plot.
- **Door slams spike it.** A door closing in a near-sealed cabin is a real
  transient, which is what those relief vents exist to bleed. Harmless to a part
  rated 250 kPa, but a 1 Hz barometric sample can catch one. **Filter or reject
  outliers** rather than trusting a single reading.

Neither changes the part choice. Both argue for treating barometric pressure as a
slowly-filtered value, which it is anyway.

### Thermal deserves a second look, though

**Behind a glovebox is a confined space with poor convection.** Q2 dissipates
~2.7 W into board copper, and that analysis assumed air that carries heat away.
A closed cavity raises local ambient above cabin temperature.

**And the connector face is a heat path in, not out.** 104 terminals and their
copper run straight to a harness in the engine bay, so the pin field conducts both
ways rather than only away.

**[CHECK]** junction temperature against *measured* in-cavity ambient once the
enclosure exists, not against cabin air temperature. The fix, if needed, is
housing-side — a metal case bonded to the board's thermal copper, which the
no-wireless decision already permits.

## Other constraints already implied by the board

- **The EEC-V 104-pin connector** sets the mating face and its orientation, and
  that face is the **firewall penetration** — so it carries the gasket, and the
  donor shell dictates the opening, not the other way round.
  [`1999-Ford-F150-4wd-5.42v/connector-sourcing.md`](1999-Ford-F150-4wd-5.42v/connector-sourcing.md)
- **Q2 dissipates ~2.7 W** into 1.14 in² of board copper. Whatever the housing is,
  it must not trap that — the thermal path is board copper to air.
  [`review-power-v1-bom-gerbers.md`](review-power-v1-bom-gerbers.md)
- **The ADC daughterboard** is a separate PCB and needs volume and standoffs
  above the carrier. [`adc-daughterboard.md`](adc-daughterboard.md)
- **No wireless**, so no antenna window and no plastic radome requirement — the
  housing may be metal, which helps both shielding and the thermal path.
  [`platform-decision.md`](platform-decision.md)
