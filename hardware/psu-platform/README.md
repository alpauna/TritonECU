# PSU mounting platform

A Z-bracket that stands a supply module off a surface and offsets it sideways.
The module bolts down onto the **upper flange** through four 2 mm holes; the
**lower flange** is the foot.

```
             TOP VIEW                            SIDE VIEW
   |<-- 44.5 -->|<---- 30 ---->|
   +------------+--------------+          +-------------+          ---
   |  o      o  |              |          |             |           |
   |            |              |          +----------+--+          48
 92|            |              |                     |##|           |
   |            |              |                     |##|          51
   |  o      o  |              |             +-------+##+-------+  ---
   +------------+--------------+             +-----------------+    3
    upper flange  lower flange               |<----- 74.5 ---->|

   holes:  34.9 apart across,  73.1 apart along the 92,  centred in the flange
```

Render: `./render.sh` → `stl/platform.stl`.

## Dimensions

| | |
|---|--:|
| Outside | **74.5 × 92 × 51** mm |
| Upper flange (the platform) | 44.5 × 92 |
| Lower flange (the foot) | 30 × 92 |
| Plate and web thickness | **3** — *a decision, not on the drawing* |
| Hole pattern | 34.9 × 73.1, centred |
| Hole centres | x 4.80 / 39.70, y 9.45 / 82.55 |
| Modelled hole diameter | **2.3** — 2.0 nominal + 0.30 print compensation |

`openscad` echoes every one of these on each render, so they follow the
parameters rather than this table. Re-read them after changing anything. The
rendered STL has been measured back: 74.500 × 92.000 × 51.000, and all four bore
centres land on their nominal to within 0.001 mm.

## How the drawing was read

The two dimensions on the side view run **flange tip to web**, and the web is
counted inside the 44.5. That is the only reading that satisfies both views at
once: the top view shows two rectangles meeting at **one** line, so their widths
must sum to the outside width, and 44.5 + 30 = 74.5 with no third piece left
over. Had the web been extra, the top view would need a third band.

The 51 is taken as **overall height**, outer face to outer face.

Only the 44.5 flange can hold the holes — 34.9 does not fit inside 30.

## Read this before you order screws

> **The inboard pair of holes clears the web by 0.65 mm.**

The hole centres sit 39.70 from the tip and the web's inner face is at 41.50, so
the *bore* clears comfortably. A **screw head does not**: an M2 pan head is
Ø3.8, which would reach 41.6 and foul the web by 0.1 mm. This is a consequence of
centring a 34.9 pattern in a 44.5 flange — it is what the drawing shows, and it
is tight by construction rather than by mistake.

Three ways out, in order of preference:

1. **Measure the module's real pattern.** If it is not actually centred, set
   `hole_x0` and re-render; nothing else changes.
2. **Countersunk screws.** An M2 flat head is Ø3.65 and sits *in* the plate.
3. **Move the pattern outboard** by a millimetre and accept 2.65 mm to the tip.

## Printing

**Stand it on end — 92 mm tall, the 74.5 × 51 Z outline on the bed.**

The part is a constant cross-section prism, so in that orientation it is
**entirely self-supporting** and every layer is a complete Z. The load path from
the upper flange, through the web, into the foot then runs *within* layers
instead of across them. As drawn — 51 mm tall, flanges horizontal — the 44.5 mm
upper flange is a full overhang starting 48 mm up and needs support under all of
it, and the corners load the interlayer bond in exactly the direction that
delaminated the VR rig's bearing blocks.

The footprint is a thin ribbon, so it is tippy: **print it with a brim**, and in
PETG or ABS rather than PLA if it will sit anywhere warm.

## What is not on the drawing

- **Thickness.** Set to 3 mm. The web is the loaded member: as a 92 × 3 plate its
  section modulus is 138 mm³, and a load in the middle of the upper flange acts
  at a 22.25 mm offset, so at a conservative 20 MPa for printed PETG it carries
  **124 N — about 12 kg**. The height does not enter that; a vertical load's
  moment at the root is set by the offset, not by how tall the web is. 3 mm is
  not the weak part, which is why `gusset` is off by default.
- **Fixing holes in the lower flange.** The drawing has none, so the foot is
  plain. Add them once the mounting surface is known.
- **`gusset = true`** adds triangular ribs at both corners. Worth turning on only
  if the load is ever *sideways*, which is the case a flat web is poor at. In the
  print orientation above the ribs are in-layer and cost nothing in strength.
