# Harness modernization label

A printed plate that zip-ties to the engine harness beside the EEC-V connector.

It exists for **one** reason, and the rest is context around it:

> **This truck now has an always-hot lead straight off the battery post.**
> Nothing else in the engine bay says so. The ECU is live with the key off, and
> the only fuse protecting that wire is at the battery, not in any fuse box
> anyone would think to check.

Someone working on this vehicle in ten years — quite possibly not the person who
built it — has to be able to discover that **before** they start cutting.

```
   +--------------------------------------------------+
   | []            TRITON  ECU                     [] |
   |          NOT A STOCK PCM - 99 F-150 5.4L         |
   |  ----------------------------------------------  |
   |         ! ALWAYS-HOT LEAD TO BATTERY +           |
   |              2 A FUSE AT THE POST                |
   |          ECU IS LIVE WITH THE KEY OFF            |
   |  ----------------------------------------------  |
   |      ADDED PINS - unused on a stock truck        |
   |            18 FAN 2      19 FAN 1                |
   |            48 FRW 391    82 FRW 1138             |
   |  ----------------------------------------------  |
   |          github.com/alpauna/TritonECU            |
   +--------------------------------------------------+
        []  zip-tie slots, 6.5 x 2.2, one per end
```

## What is on it, and where each line comes from

| Line | Source |
|---|---|
| **Always-hot lead, 2 A fuse at the post** | [`always-on-domain.md` § The KAPWR feed](../../docs/always-on-domain.md#the-kapwr-feed-where-the-constant-12-v-comes-from) — the feed is a dedicated battery lead, fused within 150–300 mm of the post, because the fuse protects the *wire* and the run before it is unprotected by definition |
| **18 FAN 2, 19 FAN 1** | [`cooling-fans.md`](../../docs/cooling-fans.md) — both pins are empty in this truck's harness; the OEM sheet had already annotated 19 *"Electric Fan 1"* |
| **48 FRW 391, 82 FRW 1138** | [`output-drivers.md`](../../docs/output-drivers.md) — circuits 391 RD/YE and 1138 VT/WH brought into the ECU as **freewheel returns** rather than left floating, so recirculation does not loop out across the Battery Junction Box |

All four added pins are listed in
[`eec-v-pinout.md` § Pins this design allocates](../../docs/1999-Ford-F150-4wd-5.42v/eec-v-pinout.md).

**The pin numbers are flat 1–104**, which is this truck's scheme. Do not
cross-reference them against Ford's `EEC-V-Power-Pins.png` — that chart is a
**three-connector PCM** and is not this vehicle. See
[`oem-connectors.md`](../../docs/1999-Ford-F150-4wd-5.42v/oem-connectors.md#-eec-v-pcm--power-ground-and-reference-pins--not-this-trucks-pcm).

## Printing

```bash
./render.sh          # -> stl/{label,plate,text,warn}.stl
```

### Multi-material — the warning in red

Four STLs come out. Use **one** of these two routes:

| Route | Files | How |
|---|---|---|
| **Multi-material (AMS/MMU)** | `plate` + `text` + `warn` | Load **all three as one object**. They share an origin, so they land aligned. Assign `warn` red, `text` white, `plate` black |
| Single extruder | `label` | One file, plus a colour change at **2.4 mm** |

**Why the split exists.** A colour change at 2.4 mm colours *all* the text at
once — including the URL, which does not matter, and the warning, which does.
The three warning lines are the only reason this label exists, so they get their
own filament:

```
   ! ALWAYS-HOT LEAD TO BATTERY +      <- warn
        2 A FUSE AT THE POST           <- warn
    ECU IS LIVE WITH THE KEY OFF       <- warn
```

Which rows belong to which group is the fourth field in `rows` — `"w"` for the
warning, `"t"` for everything else. The horizontal rules stay `"t"` so they
**bracket** the warning rather than joining it.

**The glyphs sink `embed` = 0.2 mm into the plate.** Exactly coincident faces
confuse some slicers; a small overlap makes the union unambiguous. It is buried,
so it never shows.

| | |
|---|---|
| **Material** | **PETG, ASA or ABS.** Not PLA |
| Size | **98 × 78 × 3.2 mm** — verified off the STL, and the height follows the text, see below |
| Colours | **red** warning, white text, black plate — see below |
| Layer | 0.2 mm |
| Supports | **none** — flat plate, raised text, nothing overhangs |
| Infill | 20 % is plenty; this is a label, not a bracket |

**Why not PLA.** It creeps at engine-bay temperatures. A label that has slumped
off its zip ties is *worse* than no label, because the next person will not know
it was ever there.

### Two-colour without multi-material

**Every glyph sits in one Z plane** — text starts at `plate_t` and is `text_h`
tall — so a single filament change at **2.4 mm** prints `label.stl` two-colour
with no other setup. White or yellow on black reads well under a bonnet light.

One colour works too; the raised text just relies on shadow, so pick a light
filament.

## The plate sizes itself

`rows` in the `.scad` is a list of `["text", size, advance]`. **Plate height is
the sum of the advances plus the margins**, so adding or removing a line
re-sizes the plate instead of silently overflowing it.

Width is fixed at `plate_w`, and four `assert()`s run before any geometry:

| Assert | Catches |
|---|---|
| Widest line ≤ usable width | Text running off the plate. Estimated from `CHAR_W`, because OpenSCAD 2021.01 has no `textmetrics()` |
| Slot inner edge ≥ text column | **This one fired during design** — the zip slots sat under the last two characters of the widest line |
| Slot inside the plate edge | A slot that breaks out into thin air |
| Slot length ≤ plate height | A slot longer than the plate is tall |

The text-fit assert is deliberately **conservative**: `CHAR_W = 0.62` over-states
Liberation Sans Bold slightly, so it complains a little early rather than letting
a line escape.

## Fitting it

Two zip ties through the end slots, onto the harness loom **beside the EEC-V
connector** — not on the ECU itself, which may be replaced, and not somewhere it
can chafe a wire. The slots run along the plate's short axis so the tie pulls it
flat against the loom instead of cocking it.

The back is flat, so VHB tape is an alternative on a clean surface. Zip ties are
better: adhesive in an engine bay has a worse life than the label does.

## If you change the truck, change the label

The whole point is that it matches reality. If a pin assignment moves, edit
`rows`, re-render, reprint. It is a twenty-minute part.
