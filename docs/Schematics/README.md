# Board files — which revision is which

| Board | Rev | State | Files |
|---|---|---|---|
| **Power** | **V1** | 🔒 **RELEASED — frozen, do not edit** | `*_Power_V_1.*`, `TritonECU_Power_V_1_Gerber.zip`, `TritonECU_Power_InteractiveBOM-V1.html` |
| **Power** | **V2** | 🟢 **current** | `*_Power_V_2.*`, `TritonECU_Power_V_2_Gerber.zip`, `TritonECU_Power_InteractiveBOM-V2.html` |
| **VR** | V1 | 🟢 current | `TritonECU_VR_*_V_1.*` |

**V1 is frozen because it has been released.** Design changes go to V2. The only
edits V1 should ever receive are **corrections to its own record** — see below.

## Power V2 — the delta is one part

A part census (immune to designator renumbering) gives **exactly one addition**:

| | |
|---|---|
| **C1** | **100 nF, `CGA1206X7R104K201MT`** — 1206 X7R, automotive CGA, **200 V** |

Everything else is identical. The capacitor designators *appear* to have changed
wholesale between the two BOMs, but that is the tool **renumbering the sequence**
when C1 was inserted — every part shifted up, none changed.

### Why it is there

`B+` had **no capacitor at all** in V1 — it touched only CN1, D1, Q1 and three
divider resistors, with the nearest component of any kind 8 mm away. A TVS is a
slow device dressed as a fast one: **D1 does nothing until 43 V and then has to
turn on, while a capacitor has no threshold.** The cap takes the *edge*, the TVS
takes the *energy*. See [`../review-power-v1-bom-gerbers.md`](../review-power-v1-bom-gerbers.md).

### ✅ And it is placed properly, which is what actually decides the benefit

Measured off the V2 netlist:

```
  CN1_1 B+   (12.19, 6.22)        C1_2 B+   (13.39, 9.91)
  CN1_2 PGND (17.27, 6.22)        C1_1 PGND (16.58, 9.91)
```

| | Loop | vs D1 |
|---|--:|--:|
| **C1** | **5.08 × 3.69 mm = 19 mm²** | **7× smaller** |
| D1 | 17.7 × 7.4 mm = 131 mm² | — |

Which is worth **2.4–2.7×** on fast-edge overshoot — 33–75 V on ISO 7637-2 pulse
3a/3b where D1 alone gives 80–200 V. **200 V is more headroom than the 100 V that
was asked for**, and 1206 is what a 200 V X7R at 100 nF needs; its extra ~0.2 nH
of ESL is nothing against a 7–18 nH loop.

## ⚠ One thing to check on any V1 boards already built

The V1 BOM was re-exported and **corrected** — the original export was
column-shifted, which put the manufacturer in the part field, leaked a footprint
string into the designator column as a phantom part, and listed `D2` twice with
two different components. Correcting that is legitimate on a frozen revision,
because it makes V1's record match the V1 *board*.

**But two entries are part substitutions rather than corrections**, and if V1
hardware was assembled from the original BOM it will not match:

| Ref | Original V1 BOM | V1 BOM now, and V2 |
|---|---|---|
| **R1** | `FRM252WJR010TN` | `FPM253WFR010TM` |
| **Q4** | `BS170FTA` | `BSS123` |

**[CONFIRM]** which parts are actually fitted to any assembled V1 board. Both
swaps keep the footprint, so either part fits — the BOM cannot tell you which one
went on.

## Recovering an exact released state

The filenames carry the revision, but **a git tag is the reliable handle**:

```bash
git tag -l 'power-v*'            # what has been released
git show power-v1                # the tree as released
```
