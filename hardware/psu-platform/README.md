# PSU mounting platform

A Z-bracket that stands a supply module off a surface and offsets it sideways.
The module bolts down onto the **upper flange** through four 2 mm holes; the
**lower flange** is the foot.

**The four holes now carry Ø5 × 3 mm standoffs** on the flange's top face, so
the module sits 3 mm clear of it. Overall height is **54 mm** to the standoff
tips; the bracket itself is still 51. Bores run through standoff and flange
together at Ø2.30 — nominal M2 plus 0.30 for what a printed bore loses.
`standoff = false` returns the flat flange.

```
             TOP VIEW                            SIDE VIEW
   |<-- 44.5 -->|<---- 30 ---->|
   +------------+--------------+          +-------------+          ---
   |  o      o  |              |          |             |           |
   |            |              |          +----------+--+          48
 92|            |              |                     |##|           |
   |            |              |                     |##|          51
   |  o      o  | (  ) <- O14  |             +-------+##+-------+  ---
   +------------+--------------+             +-----------------+    3
    upper flange  lower flange               |<----- 74.5 ---->|

   holes:  34.9 apart across,  73.1 apart along the 92,  centred in the flange
   O14:    clearance for the module's ~13 mm standoff, in the FOOT, tangent to
           the fold, centre 10 mm from the end of the 92
   O3.5:   a pair through the WEB, 25.4 apart, at z 8.5 and 33.9, y 15 —
           the same fixing holes hardware/l-bracket carries in its upright
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
| Standoff clearance cut | **Ø14** through the foot at x 51.5, y 10 |
| Ø3.5 pair in the web | z 8.5 / 33.9, y 15 — modelled **3.80** |

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

## The ~13 mm standoff cutout

The module has a boss on its underside that lands where the **foot** is, so the
foot is holed rather than made to sit on it. **Ø14 = the 13 mm standoff plus 1 mm
on diameter**, through the 3 mm lower flange, centred at **x 51.5, y 10**.

How that position comes off the sketch of 2026-09-19:

- **x is derived, not dimensioned.** The drawn circle *touches the fold line*, so
  its centre is one radius outboard of it: 44.5 + 7 = **51.5**. The web hangs
  below the upper flange, from 41.5 to 44.5, so a cut tangent to the fold takes
  nothing off the web. `psu_cut_x` overrides this with an absolute x.
- **y was scaled off the sketch** at about 8 mm from the end of the 92, which
  would leave ~1 mm of plate outboard of the bore — a sliver. It is set to
  **10**, so 3 mm remains. `psu_cut_y` is the one number to change once the
  module is on the bracket; the render echoes the margin and flags it under 2 mm.

The cut interrupts the foot's joint to the web for **14 mm of the 92**; the other
78 still carry it, and the foot is not the loaded member anyway — the web is.

> The sketch is a **top view**, so the circle's plan position says *which plate*
> it falls in, and it falls in the 30 mm lower flange, clear of the 44.5 one. If
> what you actually want is relief in the **upper** flange — a boss on the module
> that fouls the plate it bolts to — that is a different cut and this is the wrong
> one; say so and it moves.

## The Ø3.5 pair in the web

The same fixing holes `hardware/l-bracket` carries in its upright, and the same
**25.4** between centres — but placed differently, because this web has no free
end to measure from and they are not on the midline.

| | |
|---|--:|
| Centres up from the **underside of the foot** | **8.5** and **33.9** |
| Across the 92, from the y = 0 end | **15.0** |
| Modelled bore | **3.80** — 3.5 nominal + 0.30 |

The z numbers are the L bracket's unchanged: there the 8.5 ran from the leg's
free end, here from the bottom of the foot, which is the same plane in both
parts. The lower bore clears the foot's **top** face by 3.6 mm, so a washer sits
flat; the upper bore has 12.2 mm to the underside of the upper flange.

> **Which end is "the right side".** The instruction was *15 mm from the right,
> looking at the face straight on*, which needs a side to stand on. It is read
> here as standing on the **upper flange's side** and looking at the web — the
> viewer's right is then y = 0, so `side_y = 15` puts them at the **same end of
> the 92 as the Ø14 standoff cut**. If the intended face was the other one, the
> whole answer is `side_y = 77`; nothing else in the part changes, and the render
> echoes both the current value and its mirror.

`side_holes = false` removes them.

## Read this before you order screws

> **The inboard pair of holes clears the web by 0.65 mm.**

The hole centres sit 39.70 from the tip and the web's inner face is at 41.50, so
the *bore* clears comfortably. **The fastener's head or nut does not**: Ø3.8
across the flats reaches 41.6 and fouls the web by 0.1 mm. This is a consequence
of centring a 34.9 pattern in a 44.5 flange — what the drawing shows, and tight
by construction rather than by mistake.

> ⚠ **Clarified: the obstruction is on the UNDERSIDE.** The flange's top face is
> flat and clear right out to 44.5 — the web hangs *below* it — so nothing on top
> can foul. It is the **nut** (or the head, if you drive from below) that meets
> the web at the flange's lower face. **The standoffs do not help with this**,
> because they are on the other side.

Four ways out, in order of preference:

1. **Measure the module's real pattern.** If it is not actually centred, set
   `hole_x0` and re-render; nothing else changes.
2. ⭐ **Tap it and use no nut at all** — *newly practical because of the
   standoffs*. Standoff plus flange is **6 mm** of stack, three diameters of M2
   engagement, which is a respectable thread in PETG. Drop `hole_comp` and model
   the bore at a **1.6 mm tapping pilot** instead of 2.30 clearance. **This
   dissolves the clash outright** rather than working around it.
3. **Countersunk screws.** An M2 flat head is Ø3.65 and sits *in* the plate.
4. **Move the pattern outboard** by a millimetre and accept 2.65 mm to the tip.

## Printing

**Stand it on end — 92 mm tall, the 74.5 × 51 Z outline on the bed.**

> ⚠ **The standoffs cost this orientation its best property.** The argument
> below rests on the part being a **constant cross-section prism**. Four Ø5
> bosses are not part of that prism: stood on end they become **horizontal
> stubs off a vertical wall**, and their M2 bores print on their sides, where a
> bore sags at the crown and comes out elliptical — the 0.30 mm compensation
> was sized for a *vertical* bore.
>
> **Stand it on end anyway.** The prism argument is about the web and the
> corners, which carry the load; the stubs are 3 mm long and their tips only
> have to be flat. Either let them bridge and clean the bores with a 2 mm drill,
> or drop four scraps of support under them. **Do not flip the part flat to
> please the standoffs** — that puts the corners back into the interlayer
> direction that delaminated the VR rig's bearing blocks, and trades a load-path
> problem for a cosmetic one.
>
> ✅ **Or set `standoff = false`, print the prism, and use four M2 washers or
> nylon spacers** for the 3 mm. That keeps the orientation perfect and costs
> pennies — worth considering, since the standoffs are the only thing in this
> part that is not a prism.

> ⚠ **The Ø3.5 pair is the one thing that prints *better* on end.** Its bores
> run along X, so with the depth vertical they come out as ordinary horizontal
> bores in a vertical wall — same as the Ø14 below, crown bridged, clean them
> with a 3.5 mm drill.

> ⚠ **The Ø14 cut breaks the prism too, in a smaller way.** Stood on end the
> foot is a vertical wall and the cut is a horizontal-axis hole through it, so
> its **crown bridges** and droops a few tenths — the usual elliptical top of a
> printed sideways bore. It is a clearance hole, so that is tolerable; if the
> standoff still fouls, raise `psu_cut_clear` to 1.5-2.0 rather than reaming.

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
