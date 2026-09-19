# Carrier template — a measurement jig for the donor case

**This is not a check of a finished layout.** It is the instrument that
*captures* the numbers the layout is waiting on. The one thing we do not have is
**where the case's mounting bosses sit relative to the board outline** — drop
this in the case floor, read the boss centres off the grid, and the carrier can
be drawn.

```
./render.sh          # -> stl/template.stl, stl/ring.stl
```

## Two parts, print the ring first

| | |
|---|---|
| **`ring.stl`** | A 16 mm perimeter frame. **Print this one first** — if the centre pan or the bosses foul a full plate, the ring still sits on the rails and still gives you the outline and the connector check |
| `template.stl` | The full plate with the complete grid. More useful *if* it sits flat |

Both are **157 × 173 × 2 mm** — deliberately **0.5 mm undersized per side**, so
they drop in rather than jam. Add that back when reading the outline.

## ⚠ Print in PLA

**The opposite of the harness label.** That one bans PLA; this one wants it.
A 158 × 174 flat plate is the most warp-prone shape there is, this jig never
leaves room temperature, and **a curled datum is worthless**. PETG and ABS will
lift the corners.

0.2 mm layers, 15 % infill, no supports, and a brim if the bed is at all marginal.

## What is on it

| Feature | Status |
|---|---|
| **10 mm engraved grid**, bolder every 50 mm, axes numbered every 20 mm | the measuring scale |
| **Origin at the plate centre**, readings signed | so a boss reads as e.g. `(−62, +71)` |
| **Corner key** — a 45° chamfer at **+X +Y** | ⭐ **orientation.** Without it the plate reads identically rotated 180° and every sign inverts |
| **Connector pin field**, cut through, 101.4 × 9.0 | geometry **known** (rusEFI); **position ESTIMATED** |
| **Edge-cooling band**, 12 mm, engraved outline | where power devices must sit to reach the rails |

## What to send back

Lay it in, key to a corner you can describe, and read off:

1. **Mounting boss centres** — `(x, y)` from the grid, and their diameters
2. **Does the outline fit?** If it fouls, where and by how much
3. **Does the connector cut line up** with the case opening? The `pin_x` and
   `pin_edge` parameters are guesses — this is what corrects them
4. **Does the plate sit flat on the rails**, or does the centre pan hold it up?
   That answers the pan's sign — see
   [`../../docs/DonorECU/README.md`](../../docs/DonorECU/README.md)

Those four turn `carrier-envelope.md` from an envelope into a layout.

## Everything is parametric

`carrier_template.scad` carries the envelope, the grid, the pin field and the
band as named parameters, with five `assert()`s that run before any geometry.
When the real numbers come back, change them and re-render — **the estimated
ones are commented `** ESTIMATED **` so they are easy to find.**
