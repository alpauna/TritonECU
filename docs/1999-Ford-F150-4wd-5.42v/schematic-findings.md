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
