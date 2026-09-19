# GEM — what it is wired to, and what it wants from the PCM

Read from `GEM1.png` – `GEM4.png`. The GEM is the module the PCM replacement has
to coexist with most carefully, because it owns 4×4, wipers, interior lighting
and several cluster tell-tales.

## ✅ CLOSED — the GEM ↔ PCM interface is **one wire, and it points at us**

[`oem-connectors.md`](oem-connectors.md#correction-the-gem-is-not-on-the-scp-bus)
predicted the answer was *"nothing over a bus"*. **Correct, and `GEM4.png` names
the one hardwired discrete:**

```
  GEM pin 16   "4X4 LOW RANGE OUTPUT TO PCM"   784 LB/BK   ──►   PCM pin 14
```

[`eec-v-pinout.md`](eec-v-pinout.md) has PCM pin 14 as *"4x4 Low Indicator Sw,
LT BLU/BLK"* — **LB/BK is LT BLU/BLK, the same circuit.** Two sources, and now
the direction is unambiguous.

**So the GEM does not need anything *from* the PCM. It needs the PCM to accept
one input**, telling it the transfer case is in low range — which
[`../cooling-fans.md`](../cooling-fans.md) already uses and
[`sensors-to-run.md`](sensors-to-run.md) already lists.

**That is the whole interface.** Nothing to emulate, nothing to originate.

## Circuit 679 — the topology fills in, the level does not

`GEM3.png` shows **679 GY/BK on three GEM pins**:

| GEM pin | Goes to |
|--:|---|
| 14 | Engine controls |
| 21 | Engine controls |
| 22 | **Rear air suspension** |

The two "engine controls" arrows cite diagrams 23-8 / 24-8 / 25-8 / 26-8, which
are the **engine-variant sheets** (4.2 / 4.6 / 5.4), so those two pins are most
likely alternates by application rather than two live connections. **[CONFIRM]**
if it ever matters — it does not change our end.

> ⚠ **The level question stays open.** `schematic-findings.md` §asks what the
> speed-control servo, GEM and RAS expect on 679 — 12 V, 5 V or open-drain — and
> **these sheets do not answer it.** They show topology, not thresholds.
>
> One weak observation, offered as such: **no pull-up is drawn** on pins 14/21/22,
> where `GEM4.png` *does* draw resistor symbols inside the module on pins 8 and 13.
> That is consistent with 679 not being pulled up at the GEM, but a wiring diagram
> is not a schematic and this is not evidence to design on.
>
> **The open-drain default with an unpopulated pull-up pad remains the right
> call** — [`../Schematics/schematic-ecu-v1.txt`](../Schematics/schematic-ecu-v1.txt) §8a.

## The GEM's own supplies — it is fully independent of us

`GEM1.png`, all through the Central Junction Box:

| GEM pin | | Fuse |
|--:|---|---|
| **4, 16** | Battery — hot at all times | CJB 15, 5 A |
| **3** | Ignition RUN | CJB 6, 5 A |
| **13** | Ignition ACC or RUN | CJB 8, 5 A |
| **5** | Ignition START — *"ground in park or neutral or with clutch depressed"* | CJB 20, 5 A |
| **14, 26** | Ground, `875 BK/LB` → S208 → **G201** | — |
| 20 | Tone request input, `1083 TN/YE` ← restraints module C208-26 | — |
| 10 | Key-in-ignition input, `158 BK/PK` ← key warning switch | — |
| 25 | `70 LB/WH` → S229 → **DLC pin 7** — ISO 9141, as already recorded | — |

**Nothing here comes from the PCM.** Pull our module out and the GEM still has
power, ground, diagnostics and its own inputs.

## Cluster tell-tales the GEM drives directly — not us

`GEM2.png`:

| GEM pin | | To |
|--:|---|---|
| 9 | Door ajar indicator control | `433 DG/OG` → cluster pin 5 |
| 12 | Fasten safety belt indicator control | `450 DG/LG` → cluster pin 10 |

Worth having, because
[`schematic-findings.md`](schematic-findings.md) §10 established the cluster has
**no discrete PCM pins** and takes everything over SCP. These two are the
exception that proves it: **they are discrete, and they come from the GEM, not
from us.**

## What else is on the GEM, for context

| Sheet | |
|---|---|
| `GEM2` | Interval wipers and washer, park/headlamp sense, door-ajar switches, safety-belt switch |
| `GEM3` | Battery saver, one-touch-down, accessory delay and interior lamp relays; power windows; courtesy lamps. The one-touch-down uses a **15 mΩ shunt** on pins 7/17 to sense driver-window motor current |
| `GEM4` | Electric shift 4×4 in full — mode switch, contact plates A–D, centre axle solenoids, L2H/H2L relays, transfer-case clutch, range indicator to the cluster |
