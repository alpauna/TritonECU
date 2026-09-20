# L bracket

A right-angle bracket. A module bolts down onto the **short leg** through four
holes carrying **Ø5 × 3 mm standoffs**; the **tall leg** is the upright, and a
pair of **Ø3.5** holes on its midline fixes the bracket to whatever it hangs on.
Overall **30 × 50 × 50**, or 53 to the standoff tips.

```
            SIDE VIEW                         THE TALL LEG, face on
   |<------- 30 ------->|
   +--------------------+  ---              +-----------------+   ---
   | I                I |   3               |                 |    |
   +-----------------+--+  ---              |        o        |   33.9
                     |##|                   |                 |    |    50
                     |##|                   |        o        |   8.5
              50     |o#|                   |                 |    |
                     |##|                   +-----------------+   ---
                     |o#|                   |<----- 50 ------>|
                     +--+                    the two are on the midline,
                                             8.5 and 33.9 up from the end

   top holes: 23.8 across the 30, 44.5 along the 50, centred.  Ø2 on Ø5 bosses.
```

Render: `./render.sh` → `stl/bracket.stl`.

## Dimensions

| | |
|---|--:|
| Outside | **30 × 50 × 50** mm (53 to the standoff tips) |
| Short leg (the platform) | 30 × 50 |
| Tall leg (the upright) | 50 × 50, inner face at x 27 |
| Plate and wall thickness | **3** — *a decision, not on the drawing* |
| Top hole pattern | 23.8 × 44.5, centred |
| Top hole centres | x 3.10 / 26.90, y 2.75 / 47.25 |
| Top bore, modelled | **2.30** — 2.0 nominal + 0.30 print compensation |
| Standoffs | Ø5 × 3, on the top face |
| Side hole centres | z 8.5 / 33.9 up from the free end, y 25 (midline) |
| Side bore, modelled | **3.80** — 3.5 nominal + 0.30 |

`openscad` echoes every one of these on each render, so they follow the
parameters rather than this table. Re-read them after changing anything. The
rendered STL has been measured back: 30.000 × 50.000 × 53.000, every side bore
at r 1.9000 exactly, every top bore at 1.150 and every boss at 2.500.

## How the drawing was read

The sketch of 2026-09-20 has two views: the L in profile, and the short leg in
plan. Three of its numbers needed work.

- **The Ø3.5 pair.** The profile labels them 25.4 and 8.5 with no statement of
  which is which. The two leaders land on the upright **88 px apart in a 175 px
  leg**, which scales to 25.1 mm against the 50 — so **25.4 is centre to centre**
  and **8.5 is the lower centre up from the free end**. Centres at 8.5 and 33.9.
- **The row spacing was 70 on the sketch, corrected to 44.5.** 70 cannot fit in
  a 50 deep plate; 44.5 leaves 2.75 mm of plate outboard of each row, and the
  drawn proportion (0.72 of the plate) sits between the two.
- **The short leg was 25.8 on the sketch, opened to 30.** A 23.8 pattern in 25.8
  puts each centre 1 mm from an edge: a Ø2.3 bore would open *onto* the edge
  rather than through the plate, and a Ø5 boss would hang 1.5 mm in mid-air. At
  30 each centre is 3.1 in, which leaves 1.95 mm of plate to the tip and 0.6 mm
  outboard of each boss. `leg_x` is the one number to change if the real leg
  differs.

The 50 is taken as **overall height**, top face to the free end, and the 30 as
**tip to the outer face of the upright** — the same convention as the 44.5 on
hardware/psu-platform.

## Read this before you order screws

> **Nothing can go under the inboard pair of top holes.**

Their centres are at x 26.90 and the upright's inner face is at x 27.00, so each
bore reaches **1.05 mm into the upright's plan area**. The bore itself is fine —
it passes through 3 mm of plate like the others — but what is *below* that plate
is upright, not air. A nut, or a screw head driven from below, has nowhere to go.

This is inherent to the numbers: the clear span beyond the upright is 27 mm and
the pattern is 23.8, so there is 3.2 mm of slack in total, and no position exists
where a Ø3.8 nut clears the wall and a Ø5 boss still lands on the plate.

Three ways out, in order of preference:

1. ⭐ **Tap the plate and use no nut at all.** Plate plus standoff is **6 mm** of
   stack — three diameters of M2, a respectable thread in PETG. Set
   `hole_comp = 0` and model the bore at a **1.6 mm tapping pilot** instead of
   2.30 clearance. This dissolves the problem rather than working around it.
2. **Fasten the inboard pair from above** into the module's own threaded
   standoffs, and keep clearance bores.
3. **Measure the module's real pattern.** If it is not centred, set `top_x0`;
   every millimetre outboard buys back a millimetre of nut clearance, at the cost
   of the 0.6 mm the boss already has to the tip.

The outboard pair is clear to the tip and takes an ordinary nut.

## Printing

**Stand it on end — 50 mm tall, the 30 × 50 L outline on the bed.**

In that orientation the bracket is a **constant cross-section prism**, so it is
entirely self-supporting, every layer is a complete L, and the load path from the
short leg round the corner into the upright runs *within* layers instead of
across them. Printed the other way — short leg flat on the bed, upright rising —
the corner loads the interlayer bond in exactly the direction that delaminated
the VR rig's bearing blocks.

> ⚠ **Both hole families become sideways bores in that orientation**, and so do
> the standoffs. A bore printed on its side sags at the crown and comes out
> slightly elliptical; the 0.30 mm compensation was sized for a *vertical* bore.
> Let them bridge and clean them with a 2 mm and a 3.5 mm drill, or drop scraps
> of support under the four bosses.
>
> ✅ **Or set `standoff = false`, print the prism, and use four M2 washers or
> nylon spacers** for the 3 mm. The bosses are the only thing in this part that
> is not a prism.

The footprint is an L, so it is tippy along the upright: **print it with a brim**,
and in PETG or ABS rather than PLA if it will sit anywhere warm.

## What is not on the drawing

- **Thickness.** Set to 3 mm. The upright is the loaded member: as a 50 × 3 plate
  its section modulus is 75 mm³, and a load in the middle of the short leg acts
  at a 15 mm offset, so at a conservative 20 MPa for printed PETG it carries
  **100 N — about 10 kg**. Height does not enter that, which is why `gusset` is
  off by default.
- **Fixing holes in the upright beyond the two.** The drawing has two; add more
  once the mounting surface is known.
- **`gusset = true`** adds triangular ribs in the corner. Worth turning on only
  if the load is ever *sideways*, which is the case a flat plate is poor at. In
  the print orientation above the ribs are in-layer and cost nothing in strength.
