# Grounding architecture: the fault plane is not a ground

Three distinct return domains, meeting only outside the board.
[`harness-protection.md`](harness-protection.md) covers the OEM precedent — three
signal returns and four power grounds, star point in the box. This document adds
the domain above those: **PGND, which is not a ground at all.**

| domain | carries | reaches the vehicle via |
|---|---|---|
| **PGND** — fault plane | D1 clamp current, only when D1 fires | **dedicated twisted pair with B+**, direct to battery negative |
| **GND** — real ground plane | the board's DC return | three header pins → 104-pin connector |
| signal returns | sensor and reference returns | separate 104-pin pins, star point in the box |

## PGND is a two-node net and is deliberately not tied to GND

```
GND    118 pins
PGND     2 pins  --  D1_2 and CN1_2, that is the entire net
```

**Confirmed on hardware 2026-09-26: no copper tie exists.** This closes
`schematic-review-power.md` §8, which asked to confirm the two were joined at
exactly one point and was carried unresolved through v1 and v2. The answer is
zero points, and that is correct.

Clamp current enters at `CN1_1`, crosses D1, and leaves at `CN1_2` without ever
touching the board's ground reference. **Do not "fix" this by merging the nets.**
Tying GND to PGND would turn a fault path into the board's DC trunk and put
operating current through it permanently — the opposite of its purpose.

## Why PGND gets its own wire and not a 104-pin pin

Two threats with opposite physics, both pointing the same direction.

**Load dump** (ISO 16750-2 test B) — high energy, *slow*: 5–10 ms rise in a 12 V
system, tens of amps until the 5 A fuse clears. **Current capacity** is the
constraint; inductance is irrelevant, since 40 A in 5 ms is 8000 A/s and even
1 µH develops millivolts.

**Fast transients** (ISO 7637-2 pulse 3a/3b) — nanosecond edges, low energy, a
few amps from a ~50 Ω source. **Inductance is the whole story.** At roughly
1 nH/mm unpaired, a metre of wire is ~1 µH, which against a 5 ns edge is an
impedance the transient simply will not take. It goes into the board instead.

> **A TVS on a long ground lead stops being a TVS.** It stays in the schematic
> and does nothing for the threat that arrives fastest.

Three reasons the main connector is the wrong route:

1. **Lead inductance decouples D1 from what it protects** — above.
2. **Pin rating.** EEC-V pins are good for single-digit amps; a load-dump clamp
   pushes tens through. Pin erosion from repeated arcing is cumulative and
   invisible until it isn't.
3. **It would drag surge current across the ECU.** The worst of the three. The
   entire reason PGND is isolated is so clamp current never traverses the board;
   routing its return through the 104-pin runs that current the length of the
   module, coupling into every adjacent conductor by mutual inductance.

**Route `CN1_1` and `CN1_2` as a twisted pair, as short as practical, to the
battery negative or the main engine ground stud** — the same reference the
charging system uses, because that is where a load dump originates. Twisting is
the highest-value single measure: paired go-and-return cancels most of the loop
inductance, which is exactly what the fast pulses see.

### The cost of the isolation, stated plainly

With PGND and GND separate, what the board sees during a clamp is D1's clamp
voltage **plus whatever PGND rises relative to GND**. Negligible for load dump;
for fast edges it is the inductance term above. Same argument for the short
twisted pair, arriving from the protected side instead of the source side.

## GND return budget: three header pins

Normal return leaves on **three header ground pins** — two on the power header,
one on the status/I²C header.

The loads are **off-board**: 5 V and 3.3 V leave through the headers to the rest
of the ECU and their return comes back through these pins. So the budget is the
**sum of the off-board rail currents**, not the input current:

```
header GND return  =  I(5V loads)  +  I(3.3V loads)
```

3 A per 2.54 mm post is the usual figure, so three pins give **6–9 A** against a
worst case set by the converters' combined capability. Adequate, with two
qualifications:

- **Sharing is by impedance, not by pin count.** Three pins do not mean three
  equal thirds; trace geometry decides, and one pin can take well over its share.
- **The status/I²C header's ground pin doubles as a power return.** That is the
  pin the status signals and the INA238's I²C reference against. It is one net so
  the division cannot be forced — only geometry keeps return current off it.
  Worth a look during layout, and worth measuring under load.

## Open items

- [ ] **Confirm which header carries the two ground pins.** The BOM has `U8` as
      the INA238 and the 6-pin power header as `U6`; the three-ground split was
      described as "U8 has two, U7 has one". Reconcile the designators before
      this is treated as settled.
- [ ] **Confirm the 104-pin connector allocates multiple pins to GND.** Three
      ground pins on the board accomplish nothing if they funnel into one harness
      pin downstream.
- [ ] **Measure the return split** across the three pins under load, to see
      whether the status header's ground is carrying power current.
