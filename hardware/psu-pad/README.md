# PSU pad

A flat plate, not a bracket — nothing bends. Stepped outline: a full-width body
with a raised centre section. The module bolts onto it through four **Ø5 × 3 mm
standoffs**; two **Ø3.5** holes at the bottom corners fix the pad down.
**164.4 × 71.5 × 3**, or 6 mm to the standoff tips.

```
   |<-45->|<-------- 108 -------->|<-11.4->|
          +-----------------------+            ---
          |   I               I   |             |
   +------+                       +---------+   |   71.5
   |                                        |  50.8
   |  o    I               I             o  |   |
   +----------------------------------------+  ---
   |<---------------- 164.4 --------------->|

   I = Ø2 bore on a Ø5 × 3 standoff, pattern 100 × 63.5
   o = Ø3.5 through, 152.4 apart, 6.4 up from the bottom edge
```

Render: `./render.sh` → `stl/pad.stl`.

## Dimensions

| | |
|---|--:|
| Outline | **164.4 × 71.5** |
| Thickness | **3** — *a decision, not on the drawing* |
| Body (full width) | y 0 … 50.8 |
| Raised section | y 50.8 … 71.5, over x 45 … 153 |
| Standoff pattern | 100 × 63.5 |
| Standoff centres | x 49.00 / 149.00, y 4.00 / 67.50 |
| Standoff bore, modelled | **2.30** — 2.0 nominal + 0.30 print compensation |
| Ø3.5 centres | x 6.00 / 158.40, y 6.40 |
| Ø3.5 bore, modelled | **3.80** — 3.5 nominal + 0.30 |

`openscad` echoes every one of these on each render. Measured back off the STL:
164.400 × 71.500 × 6.000, both fixing bores at r 1.9000, all four standoff bores
at 1.150 and all four bosses at 2.500, with the step landing at y 50.800 either
side of the raised section.

## How the drawing was read

**The width closes exactly, and that is what fixes everything else.**
45 + 108 + 11.4 = **164.4**, the overall width to the decimal. So the three top
dimensions are a decomposition of the width: 45 to the step, 108 of raised
section, 11.4 to the right edge. The raised part is **not centred** — it sits
11.4 from the right and 45 from the left. The render re-checks that sum and says
so if it ever stops closing.

The sketch is not to scale — it stretches both ends and squeezes the middle, so
the drawn raised section measures 65 mm where the label says 108. Positions were
taken from the labels; only where the labels are silent do the proportions get a
vote, and those places are called out below.

- **The Ø3.5 pair.** 164.4 − 152.4 = 12, so **6.0 from each side edge**, and 6.4
  up from the bottom. The drawing puts them at 7.2 and 6.2 from the edges, which
  is the same number within sketch error.
- **The standoff pattern is centred in the RAISED SECTION, not the plate.** The
  labels do not say where the 100 × 63.5 sits. Measured off the drawing, its
  centre lands **4 px from the raised section's centre and 86 px from the
  plate's** — no contest. That gives 4 mm to each step edge.
- **Vertically it is centred in the 71.5**, giving 4.0 top and bottom. Here the
  drawing is less decisive: it shows 5.8 above and 10.0 below, but those sum to
  16 where 71.5 − 63.5 leaves only 8, so they cannot both be right. Centred is
  what the other patterns on this rig turned out to be. `pat_y0` moves it.

## Margins — the whole part is tight by 1.5 mm

Everything lands 1.5 mm from an edge, by construction rather than by mistake:

| | |
|---|--:|
| Bottom row boss to the bottom edge | 1.5 mm |
| Top row boss to the top edge | 1.5 mm |
| Boss to the step's side edges | 1.5 mm |
| Plate round the Ø3.5 holes | 4.1 to the side, 4.5 to the bottom |

Nothing overhangs and the render checks each one, but there is no room to drift:
a millimetre of error in `pat_dy` or `pad_h` puts a boss over an edge. **If the
module's pattern is a caliper reading rather than a tape reading, set it before
printing** — this is not a part with slack in it.

Tapping is available here as on the other two: plate plus standoff is **6 mm**,
three diameters of M2. Set `hole_comp = 0` and model a 1.6 mm pilot.

## Printing

**Flat on the bed, as modelled.** This is the easy one of the three — every bore
is vertical, the standoffs are vertical bosses, and there is no bending load and
no interlayer question. No support.

The footprint is 164.4 × 71.5, so:

- **Brim.** A long thin plate is exactly the shape that lifts at the corners.
- **PETG or ABS if it will sit anywhere warm**, as with the rest of the rig.
- The two re-entrant corners at the step are the only stress risers in the
  outline. `step_fill` puts a fillet in them — off by default, because the
  drawing shows square corners and a pad carries its load in compression.
