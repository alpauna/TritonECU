# Low-side driver board

One transistor, two resistors, two headers. Switches a grounded load from a
3.3 V logic output. Built for the [PSU enclosure fan](../psu-enclosure/fan-controller).

```
In --[R1 220R]--+-- Q1 pin 1        H1: 1 = GND, 2 = In
                |                   H2: 1 = GND, 2 = Load
             [R2 10k]               Q1: 2 = GND, 3 = Load
                |
               GND
```

The load goes between an external **+V** and `H2` pin 2; `H2` pin 1 ties that
supply's return to board ground.

## Fit an SS8050, not the 2N7002

The board is named for a part that should not go in it. **The 2N7002 is the
wrong device for a 3.3 V gate** and the datasheet says so by omission — it
characterises `Rds(on)` at `Vgs` = 10 V and 5.0 V, and **nothing below 5 V**.
`Vgs(th)` is 1.0/1.6/2.0 V, so at 3.3 V the worst-case part has 1.3 V of
overdrive, sitting on the knee of its own `Rds(on)`-vs-`Vgs` curve where it
goes vertical just under 3 V. The manufacturer will not put a number there, and
neither should we.

The current rating is worse than the headline. `Id` is 115 mA at 25 °C but
**75 mA at Tc = 100 °C**, against a fan drawing ~100 mA. The derating and the
demand are coupled the wrong way round: the transistor is hottest exactly when
the box is hottest, which is when the fan must run. The rating collapses as the
load arrives.

**This applies to `L2N7002LT1G` too.** The leading `L` is LRC — Leshan Radio
Company, the manufacturer — not a logic-level suffix. Marking is `702`, same as
any other 2N7002. It is not onsemi's logic-level `2N7002L`.

### Why a BJT rather than a better MOSFET

A BJT is current-driven, so the gate-threshold problem does not exist. Through
the existing R1 it is comfortably saturated, and it beats every MOSFET on hand:

| | 2N7002 @ 3.3 V | **SS8050** |
|---|---|---|
| drop at 100 mA | ~0.5 V, on the knee | **~0.15 V** `Vce(sat)` |
| dissipation | 40–60 mW | **~15 mW** |
| current rating | 115 mA, 75 mA hot | **1.5 A** |
| package | 225 mW | **1 W** |

```
Ib = (3.3 - 0.7) / 220 = 11.8 mA          inside the ESP32's ~20 mA
forced beta = 100 / 11.8 = 8.5            vs hFE min 85 -> hard saturation
```

SOT-23 NPN is base/emitter/collector on pins 1/2/3 — the same order as
gate/source/drain — so it drops into the footprint unchanged. Marking `J3Y`.

An **AO3400A** or **SI2302** would also work and keeps it a MOSFET, `Rds(on)`
specified down to 2.5 V. Either is fine; the SS8050 was to hand.

## The fail-safe pull-up is NOT on this board

`R2` is a pulldown to GND, so a floating input means the load is **off**. For
the fan that is the wrong default — see the fan controller's README. It cannot
be fixed here: **there is no 3.3 V rail on the board.** `H1` brings in GND and
the signal only, so converting R2 to a pull-up would need a cut trace and a
flying lead.

It does not need to be here. The pull-up only has to be on the **In** net, so
put it at the controller end and leave this board alone:

```
3V3 --[470R]--+-- GPIO --> H1 pin 2
```

470 Ω, not 10 k, and that difference is the whole point of using a BJT: a
MOSFET gate needs *voltage*, a BJT base needs *current*. Through 10 k you get
0.26 mA — a forced beta of 385 against an hFE that may be 85. The transistor
would never saturate, the fan would turn at half speed, and it would dissipate
a third of a watt doing it, all while looking like it worked.

With 470 Ω: floating gives 3.8 mA of base drive (forced beta 26, saturated),
and driving low sinks 7 mA and holds the base at ~0.1 V. R2's 10 k only shunts
70 µA at `Vbe` and changes nothing. Cost is 7 mA standing current while the
load is off.

## No flyback diode, deliberately

A 2-wire brushless fan commutates its windings internally, behind its own input
capacitor, so switching its supply does not interrupt inductive current the way
a relay coil or brushed motor does. What is left is lead inductance — roughly
0.5 µH at 100 mA, about **2.5 nJ** — turned off over microseconds by R1, into a
part with 13 V of headroom on a 12 V rail.

Fit one if the load is a relay, a solenoid, or a brushed motor, or if you switch
this fast enough to matter. For this fan it is not needed.

## Naming

The folder, the BOM and the schematic PNG disagree with each other and with
reality: the folder says `2N7002 Driver`, the schematic file says `2N2004`, the
title block says `2n2002 Driver board`, and what belongs in Q1 is an SS8050.
Left alone rather than renamed, because the board itself is fine — only the part
in it changed.
