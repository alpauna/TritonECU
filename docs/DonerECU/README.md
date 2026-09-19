# Donor PCM — the source of the 104-pin connector

![the donor board](1998-ExplorerECUBoard.jpg)

The EEC-V board-mount header cannot be bought — see
[`../1999-Ford-F150-4wd-5.42v/connector-sourcing.md`](../1999-Ford-F150-4wd-5.42v/connector-sourcing.md).
This board is where ours comes from, and it is also the **dimensional datum**
for the carrier outline.

## What the label says

```
EEC-V   MP2-113   00L08   KLB2
1L2F-12A650-ANC     G
6B*A113A05-AC       71958-593
```

| | |
|---|---|
| **`1L2F-12A650-ANC`** | Ford part number. `12A650` is the PCM family; **`1L2F`** is the prefix |
| `KLB2` | calibration / strategy code |
| `MP2-113` | hardware variant |

> ⚠ **The prefix and the filename disagree.** The file is named
> `1998-ExplorerECUBoard.jpg`, but Ford's prefix scheme reads **`1L2F`** as
> **2001 model year**, `L2` being the Explorer/Mountaineer platform. The board
> may well carry a © 1998 design date while the assembly is later.
> **[CONFIRM]** the donor year — it does not change the connector, but a
> mis-named file will mislead later.

## Does an Explorer header fit an F-150 harness?

**It should** — the 104-pin EEC-V header is common across EEC-V applications,
which is the whole reason salvage works. **But confirm the pin field against the
rusEFI geometry before designing to it:**

| | |
|---|---|
| Arrangement | 4 rows × 26 |
| Pitch within a row | 3.4 mm |
| Row-to-row | 3.0 mm |
| **Stagger** | **1.7 mm** — alternate rows offset half a pitch |
| Drill / pad | 1.143 / 1.778 mm |
| Pin field | 101.4 × 9.0 mm |

## ✅ 158 × 174 is the bare PCB

The photo shows no housing, and the board outline's aspect ratio measures
**0.901** against the stated **158/174 = 0.908** — within 1 %. So the envelope
in [`../carrier-envelope.md`](../carrier-envelope.md) is the **board**, not a
case.

> ### ⚠ Then what was the 31 mm measured across?
>
> If it is **board plus connector**, the **connector is the tallest thing on the
> assembly** — not the Nucleo's RJ45 at 27.7 mm — and the height analysis was
> solving the wrong constraint. A standard EEC-V header stands roughly 25–30 mm
> off the board, which is consistent with 31 mm over a 1.6 mm PCB.
>
> **This does not change the 35 mm target or the 46.5 mm ceiling**, both of which
> clear either reading. It changes *which component sets the floor*.

## How to capture the datum properly

**Do not measure this off a photograph.** Perspective and lens distortion make
hole patterns untrustworthy, and the hole pattern is the entire point.

> **Put the bare board on a flatbed scanner at 600 dpi**, glass-down, connector
> included. A scan is orthographic and dimensionally accurate: import it into
> CAD, scale it with a known reference (the 3.4 mm pin pitch across all 26
> positions is an excellent one — 85 mm over 25 gaps averages out error), and
> trace directly.

What has to come out of it:

| | |
|---|---|
| **PCB outline** | including any notches or cutouts |
| **Mounting holes** | centres and diameters. The photo shows holes at the corners plus at least one centre boss below the connector |
| **Pin field position relative to the outline** | ⭐ **the datum everything else places from** |
| Connector body height above the board | settles the question above |
| Board thickness | probably 1.6 mm, worth confirming |
