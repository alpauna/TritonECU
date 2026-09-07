# What it actually takes to make the 5.4L run

1999 F-150 4WD, 5.4L 2V, 4R70W. Grouped by what happens if it is missing,
because that is what decides build order.

Connector refs are from `oem-connectors.md`. Anything not yet confirmed from a
schematic is tagged.

---

## Tier 1 — will not run at all without these

| Sensor | Type | Signal | Notes |
|---|---|---|---|
| **CKP** — crankshaft position | 36-1 **variable reluctance**, C102 | self-generated sine, mV at cranking to tens of V at speed | The one irreplaceable input. Position *and* rpm. **Needs a VR conditioner** — cannot drive a GPIO |
| **CMP** — camshaft position | **variable reluctance**, C100 | 1 pulse/cam rev | Identifies which stroke. With coil-on-plug and sequential injection this is mandatory, not optional. Also needs VR conditioning |
| **MAF** — mass air flow | hot wire, C141 | 0–5 V **differential** (967 signal / 968 return) | The load signal. Fuelling is computed from it |
| **TPS** — throttle position | potentiometer, C123 | 0–5 V ratiometric to VREF | Idle/WOT detection, transient (accelerator-pump) fuel |

Plus one thing that is not a sensor but belongs in Tier 1:

| | | |
|---|---|---|
| **VREF** — buffered 5 V | ECU **output**, 2 feeds | powers TPS and every other 3-wire sensor | Must be current-limited and short-to-ground survivable |

**Minimum to get combustion:** CKP + CMP + MAF + TPS + VREF. Everything below
this line affects how *well* it runs, not whether it runs.

---

## Tier 2 — will start, but runs badly or damages itself

| Sensor | Type | Why it matters |
|---|---|---|
| **CHT** — cylinder head temperature | NTC, C179 | Warm-up enrichment. Without it the engine either floods when cold or leans out when hot. **Note: CHT, not ECT** — different curve, mounted in the head, faster and hotter than coolant |
| **IAT** — intake air temperature | NTC, C107 | Air density correction. Separate sensor on this truck — confirmed, C141 pins 1/6 unused |
| **Battery voltage** | divider, internal | Injector dead-time compensation. At 10 V cranking an injector opens measurably slower than at 14 V; ignore it and cranking mixture is wrong exactly when it matters |
| **Knock sensor**, C103 | piezo | Not needed to *start*, but it is what stops the engine destroying itself under load on pump fuel. Needs a charge amp and windowed detection — see `oem-connectors.md`. Until it works, run conservative timing |

---

## Tier 3 — closed-loop fuelling and emissions

| Sensor | Type | Notes |
|---|---|---|
| **HO2S upstream ×2** | narrowband heated, C109 = #11, C108 = #21 | Closed-loop trim. Replaceable with LSU 4.9 wideband + CJ125, which the firmware already supports and which is far better for tuning |
| **HO2S downstream ×2** | narrowband heated | Catalyst efficiency monitoring only. Not needed to run; needed for a clean OBD-II readiness set |
| **DPFE** — EGR differential pressure | 0–5 V, C122 | Only if EGR is retained |

---

## Tier 4 — transmission (4R70W)

| Sensor | Type | Notes |
|---|---|---|
| **TSS** — turbine shaft speed | speed sensor | Present on '99 4R70W. Slip calculation and shift quality. **[CONFIRM]** VR or Hall |
| **OSS** — output shaft speed | speed sensor | Road speed. Also the cluster's speedometer source |
| **TR** — transmission range | multi-position switch | Park/neutral/gear. Also gates cranking |
| **TFT** — trans fluid temperature | NTC | Blocks converter lockup when cold |

---

## Digital inputs (switches, not sensors)

| Input | Notes |
|---|---|
| **Oil pressure switch**, C101 | **Binary, not a sender.** Warning lamp only. Fit a real sender if pressure logging is wanted |
| **Brake switch** | Unlocks the torque converter. Safety-relevant |
| **A/C request**, C139/C170 | Idle-up and compressor cutout |

---

## Outputs required to run

Listed because "what makes it run" is not only sensors.

| Output | Count | Notes |
|---|---|---|
| **Coil-on-plug drivers** | **8** | C1011–C1018. Individually timed. **[CONFIRM]** dumb coils needing an IGBT each, or smart coils with logic input |
| **Injector drivers** | 8 | C125–C132. High-impedance saturated, low-side |
| **IAC valve**, C110 | 1 PWM | Without it there is no idle control at all — the engine will only idle on the throttle stop |
| **Fuel pump relay** | 1 | |
| **VREF supply** | 2 feeds | see Tier 1 |
| **IMCC**, C118 | 1 | Intake manifold runner control. **[CONFIRM]** on/off or PWM |
| **Cooling fan, A/C clutch (C106), MIL** | 3 | Slow — expander chain |
| **EVAP purge valve**, C164 | 1 PWM | Not needed to run |
| **EGR vacuum regulator**, C121 | 1 PWM | Only if EGR retained |
| **Speed control servo**, C157 | — | Cruise control is a PCM function on this truck; it stops working unless the replacement drives it |
| **HO2S heaters** | 4 | Needed before the O2 sensors read at all |
| **Tach + road speed to cluster** | 2 | Or over SCP, if Phase 0 shows the cluster takes them that way |
| **4R70W: SSA, SSB, TCC, EPC** | 4 | Two on/off, two PWM |

---

## Build order this implies

1. **VREF supply and the analog front end.** Nothing else can be tested
   without a working sensor reference.
2. **VR conditioning, then CKP + CMP sync.** Prove 36-1 decode and cam sync on
   a signal generator before the engine, then cranking with fuel and spark
   disabled. This is the highest-risk item — VR amplitude is weakest at
   cranking speed, exactly when sync must be established.
3. **MAF + TPS + CHT + IAT.** Now fuelling can be computed, open loop.
4. **Injectors and coils.** First combustion.
5. **IAC.** First usable idle.
6. **O2 closed loop.**
7. **Transmission.**

Tiers 1 and 2 plus injectors, coils and IAC are the whole "make it run" set.
Everything else is refinement.
