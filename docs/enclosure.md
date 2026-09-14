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

## [CONFIRM] Where the ECU lives — still open, and it now decides two things

The OEM PCM on this truck sits in the **cabin**, which is the strong hint. It has
not been confirmed, and it settles:

| | if cabin | if under-hood |
|---|---|---|
| **ADC choice** | the 200 kSPS part (−40…+85 °C) is fine | **ruled out** — needs the AD7606B/C at −40…+125 °C. [`adc-front-end.md`](adc-front-end.md) |
| **Barometric** | no constraint | fine either way — KP497 is −40…+105 °C |
| Vent siting | sheltered by default | must dodge ram air and washing |

**Confirm the mounting location before committing to a housing.** It is the one
input that changes part selection rather than just packaging.

## Other constraints already implied by the board

- **The EEC-V 104-pin connector** sets the mating face and its orientation. The
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
