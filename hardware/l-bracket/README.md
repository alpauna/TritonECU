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

   top holes: 21.8 across the 30, 44.5 along the 50, centred.  Ø2 on Ø5 bosses.
```

Render: `./render.sh` → `stl/bracket.stl`.

## Dimensions

| | |
|---|--:|
| Outside | **30 × 50 × 50** mm (53 to the standoff tips) |
| Short leg (the platform) | 30 × 50 |
| Tall leg (the upright) | 50 × 50, inner face at x 27 |
| Plate and wall thickness | **3** — *a decision, not on the drawing* |
| Top hole pattern | 21.8 × 44.5, centred |
| Top hole centres | x 4.10 / 25.90, y 2.75 / 47.25 |
| Top bore, modelled | **2.30** — 2.0 nominal + 0.30 print compensation |
| Standoffs | Ø5 × 3, on the top face |
| Side hole centres | z 8.5 / 33.9 up from the free end, y 25 (midline) |
| Side bore, modelled | **3.80** — 3.5 nominal + 0.30 |

`openscad` echoes every one of these on each render, so they follow the
parameters rather than this table. Re-read them after changing anything. The
rendered STL has been measured back: 30.000 × 50.000 × 53.000, every side bore
at r 1.9000 exactly, every top bore at 1.150 and every boss at 2.500, on
(4.10, 2.75) and the three that follow.

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
- **The short leg was 25.8 on the sketch, opened to 30.** The pattern was then
  23.8, and 23.8 in 25.8 puts each centre 1 mm from an edge: a Ø2.3 bore would
  open *onto* the edge rather than through the plate, and a Ø5 boss would hang
  1.5 mm in mid-air.
- **The pattern was 23.8 on the sketch, corrected to 21.8** off the module
  itself. Each centre is now 4.1 in from the tip — 2.95 mm of plate to the tip,
  1.6 mm outboard of each boss — and, more usefully, it opens the nut window
  below. 25.8 would *almost* take the narrower pattern (2.0 to each centre, boss
  overhanging 0.5), but `leg_x` is left at 30, because the extra 4.2 mm is
  exactly what makes a nut possible under the inboard pair.

The 50 is taken as **overall height**, top face to the free end, and the 30 as
**tip to the outer face of the upright** — the same convention as the 44.5 on
hardware/psu-platform.

## ⚠ Two screw sizes, and the part now says so

**M2 in the standoffs. M3 clearance in the upright.** One bracket, two threads —
which is how an M3 came to be driven into an M2 boss and split it.

| | Modelled | Finishes | Screw |
|---|--:|--:|---|
| Four standoffs, short leg | **1.90** | ~1.6 | **M2 self-tapping — a PILOT** |
| Pair in the upright | 3.80 | ~3.5 | M3 clearance |

### Clearance and pilot are opposite holes

`top_mode` picks which, and the difference is not a detail:

| Mode | Bore vs screw | For |
|---|---|---|
| `"clearance"` | **bigger** than the screw — 2.0 for M2 | a machine screw passing through to a nut or a tapped part |
| **`"selftap"`** ⭐ as built | **smaller** than the screw — 1.6 for a 2 mm screw | a thread-forming screw cutting into the boss |

A self-tapper driven into a *clearance* hole has nothing to bite and everything
to wedge, and splits the boss exactly as an oversized machine screw does. **The
hole looks correct in both cases; only the number differs**, which is why this is
worth a mode rather than a comment.

The pilot is `selftap_ratio × selftap_major`, default **0.80** — right for PETG
and PLA. Drop it to 0.75 in stiffer material, raise it to 0.85 if a boss still
splits.

### The three ratios the render checks

| | As built | Rule |
|---|--:|---|
| Boss OD ÷ screw major | **2.5×** | 2× is the floor, 2.5× comfortable. Below 2× the hoop stress splits it |
| Thread engagement ÷ major | **3.0×** | 2× minimum or it strips |
| Wall around the pilot | **1.55 mm** | vs 1.35 mm with a clearance bore — the smaller hole is also the stronger boss |

**This is why a 3 mm self-tapper cannot go in this boss**: Ø5 ÷ 3 = 1.67×, under
the 2× floor, regardless of pilot size.

An M3's major diameter is **3.0 mm going into a ~2.0 mm hole**, against a boss
wall of only **1.35 mm**. It acts as a wedge; the boss splits. Nothing about the
print was wrong.

**And if that screw was self-tapping, it was doubly wrong** — a clearance hole is
the wrong hole for a thread-former even at the right diameter.

**The part is now marked**: `M2` debossed on the short leg's top face between the
hole columns, `M3` on the upright's inner face between the two bores, 0.6 mm
deep. `mark = false` removes them.

### If M3 really is wanted, the plate has to grow

The binding constraint is not the boss — it is that **a 44.5 pattern in a 50 mm
deep plate leaves 2.75 mm of edge**, so no boss above Ø5.5 fits without
overhanging.

| Option | `deep` | Bore | Wall | Boss to edge |
|---|--:|--:|--:|--:|
| **1. As built — just use M2** | 50 | 2.30 | 1.35 | 0.25 |
| 2. Tougher M2: `standoff_d = 6` | **51** | 2.30 | **1.85** (+37 %) | 0.25 |
| 3. M3: `top_d = 3.5`, `standoff_d = 6.5` | **52** | 3.80 | 1.35 | 0.50 |
| ~~M3 on the existing 50 plate~~ | 50 | 3.80 | 1.35 | **−0.50 ⛔** |

That last row is the one to avoid: an M3 boss on the current depth **overhangs
the edge by half a millimetre**, so enlarging the bore alone is not a fix — it
trades a split boss for one hanging in mid-air.

## Read this before you order screws

> **A nut fits under all four holes — but only if you move the pattern off
> centre.**

What is under the short leg at the inboard holes is upright, not air, so a nut
or a screw head driven from below has to clear the upright's inner face at
x 27.00. With the pattern at 21.8 there is now a window where that works *and*
each Ø5 boss still lands fully on plate:

| | |
|---|--:|
| A Ø3.8 nut under the inboard pair needs | `top_x0` ≤ **3.30** |
| A Ø5 boss on plate at the tip needs | `top_x0` ≥ **2.50** |
| Centred, which is what the model ships with | `top_x0` = **4.10** |

**The default is outside that window by 0.8 mm.** Centring the pattern is what
costs the nut: at 4.10 the inboard centres sit 1.10 mm from the upright, and a
nut wants 1.90. The model ships centred because that is what the drawing shows
and because tapping is the better fastening anyway — but the choice is now real,
and it is one parameter:

1. ⭐ **Tap the plate and use no nut at all.** Plate plus standoff is **6 mm** —
   three diameters of M2, a respectable thread in PETG. Set `hole_comp = 0` and
   model the bore at a **1.6 mm tapping pilot** instead of 2.30 clearance. Keeps
   the pattern centred and dissolves the question.
2. **Set `top_x0 = 3.0`** and use ordinary nuts on all four. That puts the boss
   0.5 mm from the tip and the nut 0.9 mm clear of the upright. The render
   echoes both margins and tells you which side of the window you are on.
3. **Fasten the inboard pair from above** into the module's own threads, and
   leave everything else alone.

*(Before the pattern came down to 21.8 this section said no such window existed.
At 23.8 that was true: a nut needed `top_x0` ≤ 1.3 and a boss needed ≥ 2.5. The
2 mm bought the overlap.)*

The bore itself is fine at any of these — at the centred default it reaches just
**0.05 mm** into the upright's plan area, against 1.05 mm before.

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
