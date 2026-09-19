# What the factory wiring diagrams settled

Read from the Ford diagrams now in this directory — `4R70W-*.png`,
`EngineControls2-8.png`, `Electronic-Shift-Control.png`. These are **Ford's own
sheets**, so where they disagree with
[`eec-v-pinout.md`](eec-v-pinout.md) — which is a transcription of a MegaSquirt
PNP mapping — the diagrams win.

Several questions that had been open for weeks close here.

---

## 1. VREF is **one** pin, not two

**Circuit 351 BN/WH → PCM pin 90**, spliced at **S136** and **S137** to reach the
DPFE sensor (C122), the TP sensor (C123) and C150.

That closes the question `vref-supply.md` opened at the top and
`eec-v-pinout.md` §2 flagged: the Ford power-pin sheet's "A-20 *and* C-20" is
connector-relative numbering for a different vehicle or a different thing. **On
this truck there is a single VREF.**

Nothing needs redesigning — the chosen switch is dual-channel — but the second
feed is now a **stuffing option**, not a requirement.

## 2. Sensor ground is **one** pin, heavily spliced

**Circuit 359 GY/RD → PCM pin 91**, via splices **S135** and **S138**, reaching
TP, DPFE, IAT, knock, both HO2S pairs, OSS, TFT and the transfer case sensor.

`oem-connectors.md` describes "**three** separate signal returns (A-17, B-17,
C-17) … meeting only inside the module". **The diagrams do not show that.** They
show one sensor ground at pin 91 with harness splices doing the joining.

> **This weakens a premise in [`vref-supply.md`](../vref-supply.md) § Grounds**,
> which reasoned about SIGRTN-to-PGND offsets partly from there being three
> independent returns. The grounding *decision* is unaffected — TVS to PGND,
> divider to AGND — but the offset it guards against is now a single shared
> return carrying every sensor on the truck, which makes keeping it clean more
> important, not less.

## 3. HO2S heaters are power-fed and PCM-grounded — **confirmed**

This was tagged `[CONFIRM ON TRUCK]` and **the entire low-side NCV8405A case
rested on it.**

| | Feed | Heater ground → PCM |
|---|---|---|
| Upstream, HO2S 11 / 21 | **391 RD/YE** | pins **93**, **94** |
| Downstream, HO2S 12 / 22 | **1138 VT/WH** | pins **95**, **96** |

Note the two pairs are on **different supply circuits**. Signal wires are
separate throughout.

## 4. EVAP and EGR pins — found, and they were missing entirely

Neither appeared in the transcribed pinout.

| Load | Connector | Circuit | PCM pin | Feed |
|---|---|---|--:|---|
| EVAP canister purge | C164 | 191 LG/BK | **56** | 391 RD/YE |
| EGR vacuum regulator | C121 | 360 BN/PK | **47** | 391 RD/YE |
| **Canister vent solenoid** | C413 | 91 VT/WH | **67** | 361 RD |
| IMCC | C118 | 367 BN | 46 | 391 RD/YE |

**A third EVAP solenoid exists** — the canister vent solenoid, C413 — which is
in no list in this tree. It is low-side like the others.

Two diagram notes settle the drive types:

- EGR: *"PCM controls EGR by **varying voltage** applied to the solenoid"* — PWM,
  confirmed.
- EVAP: *"When PCM **grounds** valve, fuel vapors … are released"* — low-side,
  confirmed.
- **IMCC carries no such note**, unlike EGR. That leans **on/off**, though it is
  not proof.

## 5. The transmission solenoids share one feed — and it does not reach the PCM

This is the answer to
[`review-solenoid-chain.md`](../review-solenoid-chain.md) finding 4.

```
BJB fuse 24, 15 A  ──► 1138 VT/WH ──► S140 ──► C183 pin 4
                                                 ├── TCC solenoid   ──► 480 VT/YE ──► PCM 54
                                                 ├── EPC solenoid   ──► 925 WH/YE ──► PCM 81
                                                 ├── SSA            ──► 237 OG/YE ──► PCM 27 (*6)
                                                 └── SSB            ──► 315 VT/OG ──► PCM 1  (*11)
```

1138 comes off the **PCM power relay** output (1140 VT) through BJB fuse 24.

**But the PCM's own VPWR is circuit 361 RD, on pins 71 and 97 — a different
branch.** Neither 1138 nor 391 arrives at the PCM at all.

So a freewheel diode returned to VPWR inside the ECU would recirculate
**out through the connector, across the Battery Junction Box, over two fuses,
and back** — a long loop switching at PWM rates.

**The better option is now visible:** 28 EEC-V pins are unused, so **bring 1138
and 391 into the ECU as two dedicated freewheel returns.** Two wires buys a
local, tight recirculation loop for all five PWM solenoids.

## 6. Only **two** shift solenoids appear, not three

The 4R70W connector C183 shows **SSA and SSB only**. `eec-v-pinout.md` lists a
third — CSS, coast clutch, pin 20 BRN/ORG — sourced from the MegaSquirt sheet.

> **[CONFIRM]** whether this transmission has a coast clutch solenoid at all.
> It changes the NCV8405A channel count.

## 7. Road speed: the transfer case sensor is a separate input

| Sensor | Connector | Circuit | PCM pin |
|---|---|---|--:|
| Output shaft speed (OSS) | C187 | 136 DB/YE | **84** |
| **Transfer case speed** | C199 | 1496 PK | **7** |

And the PCM's **road-speed output is pin 68**, circuit 679 GY/BK, feeding the
speed control servo (C157), the GEM (C267) and the rear air suspension module.

The OSS note says it is used for *"shift scheduling, torque converter engagement
schedule and EPC pressure"* — transmission control. **The transfer case sensor
is the road-speed source**, and it sits downstream of the range box.

> **This improves [`cooling-fans.md`](../cooling-fans.md) §4.4.** The highway fan
> cutoff should key on the **transfer case sensor (pin 7)**, which is correct in
> both ranges. The 4×4-low inhibit becomes belt-and-braces rather than
> load-bearing.

## 8. There is no separate "A/C request" — and that matters

| | Circuit | PCM pin |
|---|---|--:|
| A/C clutch **cycling pressure switch**, C139 | 347 BK/YE | **41** |
| **WOT relay** drive | 331 PK/YE | **69** |

The PCM does **not** drive the A/C clutch directly. It drives a **wide-open-
throttle cutout relay** whose output (321 GY/WH) goes to the A/C/heater circuit.
The only A/C input it has is the **cycling pressure switch** on pin 41, annotated
*"Used to adjust EPC pressure in transmission."*

> **This forces a change in [`cooling-fans.md`](../cooling-fans.md) §4.2.** That
> section says to key fan-on to the *A/C request* and explicitly not to the
> cycling switch, because the cycling switch chatters as the compressor cycles.
> **The request signal does not exist at the PCM.** The cycling switch is the
> only A/C input, so the chatter has to be handled in firmware with a hold-on
> timer rather than avoided by choosing a different signal.

## 9. Odds and ends confirmed

| | |
|---|---|
| **4×4 low indicator** | PCM pin **14**, circuit 784 LB/BK, C189 — as assumed by the fan cutoff inhibit |
| **Brake pedal position** | PCM pin **92**, 810 RD/LG, hot at all times via a 5 A fuse — a 12 V switch input |
| **TFT sensor** | C183 pin 2 → 923 OG/BK → PCM **37**, returning on 359 GY/RD |
| **Fuel pump relay** | PCM pin **80** grounds the coil via 926 LB/OG |
| **Transmission control switch (O/D off)** | pin **29** (224 TN/WH); indicator lamp pin **79** (911 WH/LG) — in no output list in this tree |

---

# Instrument cluster sheets

`InstramentCluster1-5.png`. These settle the tach/VSS driver question that
[`review-ignition-injection.md`](../review-ignition-injection.md) left open, and
the answer is not the one the scope assumed.

## 10. There is no discrete tach output, and no discrete MIL output

Across five cluster sheets, **the cluster's only connection to the PCM is SCP** —
circuits **914 TN/OG** and **915 PK/LB** at C237 pins 1 and 2, marked
*"MULTIPLEX COMMUNICATION NETWORK"*.

The **MIL lives inside the cluster**, driven by the cluster's own microprocessor
via the *"theft indicator micro cluster"*. No wire runs to it from the PCM. And
`grep -niE 'tach|MIL'` over [`eec-v-pinout.md`](eec-v-pinout.md) returns
**nothing** — neither has a PCM pin.

> ### This invalidates the J1850 deferral rationale
>
> [`v1-scope.md`](../v1-scope.md) defers SCP on the grounds:
>
> > *Needed for the cluster and OBD-II, not to run. **Tach and speedo can be
> > discrete outputs.***
>
> **They cannot.** The cluster has no discrete inputs for them. Without SCP this
> truck has **no tachometer, no speedometer and no check-engine lamp** — the
> dash simply does not work.
>
> That does not make SCP required *to run the engine*, which was the deferral's
> real point. But "defer it, the cluster can be driven discretely" was wrong,
> and the cost of deferring is larger than recorded.

## 11. The MIL channel has nothing to drive

[`output-drivers.md`](../output-drivers.md) allocates a TBD62083AFNG channel to
the MIL. There is no MIL circuit to switch. **Five channels used becomes four**,
and four spare becomes five.

Lighting the check-engine lamp is an **SCP message**, not an output.

## 12. The VSS output is real — but not to the cluster

PCM **pin 68**, circuit **679 GY/BK**, reaches the **speed control servo**
(C157), the **GEM** (C267) and the **rear air suspension module** (C277). Not
the cluster.

So `pin-budget.md`'s *"Tach out, VSS out | 2"* should read **VSS out | 1**. The
fourth no-driver instance narrows to a single frequency output feeding three
module inputs.

> **[CONFIRM]** what level those three modules expect on 679 — 12 V, 5 V or
> open-drain. It decides whether a spare NCV8405A channel does it or whether it
> needs push-pull.

## 13. Oil pressure and fuel level go to the cluster, not the PCM

| Signal | Circuit | Goes to |
|---|---|---|
| **Engine oil pressure switch**, C101 | 31 WH/RD | **cluster** C236 pin 20 |
| **Fuel level sender** | 29 YE/WH | **cluster** C236 pin 3 |

Both appear in this tree's input lists —
[`f150-1999-target.md`](../f150-1999-target.md) has *"oil pressure switch"* among
the digital inputs and *"Fuel level"* on an ADC channel — **as though the PCM
sees them. It does not.**

The oil pressure switch is *"closed with normal oil pressure"*, so the cluster
reads it directly and drives its own gauge.

If the ECU wants either, the circuits must be **tapped** — both pass through
C120/C158 in the engine harness, so the tap is physically easy. But it is added
wiring, not an existing PCM input, and nothing in the tree said so.

## 14. Minor — the 4×4 low input holds up

Pin **14** reads the **4x4 low and high indicator *switch*** (C189, 784 LB/BK),
so it is an input, as the cooling-fan cutoff inhibit assumes. The *indicator
lamp* is PCM-commanded, but over SCP — the cluster note says *"LOW Range
indicator is controlled by the PCM"* with no wire to it.

---

## 15. Pin 25 is the CMP shield drain, not a power ground

[`eec-v-pinout.md`](eec-v-pinout.md) has pin 25 as *"GND | Power Ground | Same |
BLK"*, from the MegaSquirt sheet. **Ford's `EngineControls6.png` shows
`567 LB/YE`, marked 0 V, carrying the camshaft sensor's cable shield** — drained
through splices S199 and S101.

They disagree on the function *and* the wire colour. **The diagram wins**, as it
did on [pin 46](../cooling-fans.md#2-the-connector-pin-conflict): the MegaSquirt sheet is one
install's mapping, not Ford's.

This matters more than a label. Wiring pin 25 as a power ground would put
**engine-bay ground current into a sensor cable shield** — the precise inversion
of what a shield is for.

### Why CMP is shielded and CKP is not

Worth recording, because it is not arbitrary:

| | |
|---|---|
| **CKP** | **differential**, pins 21/22 — rejects pickup by construction. No shield |
| **CMP** | **single-ended**, one signal wire returning on the shared sensor ground. **No common-mode rejection of its own** — the shield does that job instead |

Our design wires CMP *pseudo*-differentially (`IN2+` on pin 85, `IN2−` on sensor
ground, balanced 5 kΩ legs), which recovers rejection of noise **common to pins
85 and 91**. It does nothing about noise picked up on the CMP conductor itself.
**The shield still does real work.**

---

## 16. The PCM's grounds, and there is no case ground

`Engine-Controls.png`, read for the first time in this pass.

**Four ground pins — 3, 51, 77, 103 — all circuit `570 BK/WH`, all marked 0 V,
all joining at splice `S100` and going to body ground `G101`.** Ford draws them
in one row. That is the PCM's complete ground complement.

| Consequence | |
|---|---|
| **No `CSEGND`** | There is no case- or chassis-ground pin on this connector. The chart's `A-43` belongs to the other PCM. The ECU's shield bond is a *mechanical* question, not a connector pin |
| **Four, not five** | `oem-connectors.md` §3 briefly said five, counting pin 24. **Pin 24 carries no wire on this truck** — the MegaSquirt sheet lists it, its F-150 column is blank, and Ford does not draw it |
| **Pin 25 is separate** | The CMP shield drains to `S199`/`S101`, a different path from `S100`/`G101`. §15 |

### The MAF is wired as a Kelvin measurement, and that is worth keeping

The MAF's own 0 V is **`570 BK/WH` — the same circuit, same splice `S100`, same
ground `G101` as the PCM's power grounds.** Its return to the PCM, `968 TN/LB` on
**pin 36**, is therefore a *sense* wire, not a current path: ground current goes
to G101 on 570, and 968 lets the PCM measure the MAF signal against the sensor's
**local** ground.

**That is a four-wire measurement**, and it is the strongest evidence yet for the
differential-measurement argument in [`../adc-front-end.md`](../adc-front-end.md).
Tying pin 36 to our AGND at the connector would throw the whole benefit away.

> Signal is `967 LB/RD` on **pin 88** — checked, because the sheet's pin label is
> easy to misread as 38, and pin 38 is unused on this truck.

---

## 17. VPWR is key-switched — confirmed at the relay coil, not inferred

The always-on work assumed VPWR dies at key-off. `Engine-Controls.png` proves it:

```
  BJB "HOT AT ALL TIMES" ── 554 YE/BK ──► PCM POWER RELAY pin 30
  CJB "HOT IN START OR RUN" ── 16 RD/LG ──► PCM POWER DIODE ── 20 WH/LB ──► coil 86
                                                          coil 85 ──► 57 BK ──► S106 ──► G104
  relay 87 ──► 1140 VT ──► S1003 ──┬── BJB fuse 23, 15 A ──► 391 RD/YE ──► S155
                                   ├── BJB fuse 18, 15 A ──► 361 RD    ──► S127   (VPWR)
                                   └── BJB fuse 24, 15 A ──► 1138 VT/WH ──► C172
```

**The coil is energised straight from "hot in start or run" and grounded at
G104. No PCM output touches it.** So the relay opens the moment the key does —
there is no PCM-held afterrun on this circuit, and nothing keeps VPWR alive.

**And the three circuits the output-driver work cared about all come off that one
relay** through three *separate* 15 A fuses. `361 RD` (VPWR, pins 71/97),
`391 RD/YE` and `1138 VT/WH` are siblings, which is exactly why a freewheel diode
returned to VPWR inside the ECU would loop out across the Battery Junction Box —
see [`../output-drivers.md`](../output-drivers.md).

---

## 18. Keep-alive power exists, on pin 55

`Engine-Controls.png`: **Central Junction Box, "HOT AT ALL TIMES", 5 A fuse →
C242 → `729 RD/WH` → C160 → PCM pin 55, marked 12 V.**

[`eec-v-pinout.md`](eec-v-pinout.md) has had it all along as
**"B+ KAM | 12V KAM | RED/WHT"**. **KAM is Keep Alive Memory — it is KAPWR**, and
nothing in the repo made that connection while `oem-connectors.md` §5 asserted
twice that this truck did not need it.

It does not overturn the dedicated battery lead — that was chosen so the
battery-sense divider reads **true** battery voltage, which a feed through the
Central Junction Box cannot do. But it makes that a **trade** rather than a
consequence of not finding the pin, and it leaves one thing open:

> **[DECIDE]** what the board does with pin 55. It is a permanently hot 12 V pin
> that will be present at our connector whether we use it or not.
