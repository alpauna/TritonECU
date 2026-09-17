# Electric cooling fans

Two fans, staged, replacing the clutch fan bolted to the water pump.

The clutch fan is driven by engine speed, which is exactly the wrong variable:
it roars at 3000 rpm on a cold morning and barely turns at a hot idle in
traffic, which is the one moment cooling actually matters. Electric fans move
that decision to the ECU, where the head temperature is already known.

**The control side is nearly free.** Everything this needs is in the design
already except one expander output — see [What it costs](#what-it-costs). The
work is in the strategy and the wiring, not the pin count.

---

## 1. What it costs

| Signal | Direction | Where it already lives | New? |
|---|---|---|---|
| Fan 1 relay | out | MCP23S17 expander | — *(the existing "cooling fan" output)* |
| **Fan 2 relay** | out | MCP23S17 expander | **yes — one output** |
| A/C request | in | expander input, `sensors-to-run.md` | — |
| A/C clutch | out | expander output, EEC-V 69 | — |
| CHT | in | AD7606B, EEC-V 66 | — |
| Road speed | derived | OSS on MAX9926, EEC-V 84 | — |
| 4x4 low indicator | in | expander input, EEC-V 14 | — |
| Cranking state | internal | engine position | — |
| Battery voltage | in | AD7606B | — |

One expander bit. The expander chain is on the board regardless and has spare
bits, so the board cost of this feature is a relay driver channel and a
connector pin.

---

## 2. The connector pin conflict

The MegaSquirt sheet transcribed in
[`1999-Ford-F150-4wd-5.42v/eec-v-pinout.md`](1999-Ford-F150-4wd-5.42v/eec-v-pinout.md)
already anticipated this job and annotated two pins *"Electric Fan 1"* and
*"Electric Fan 2"*:

| Pin | MS function | '99 F-150 pin | Verdict |
|---|---|---|---|
| 19 | Low Cool Fan | **—** *(no wire)* | ✅ **use it — Fan 1** |
| 46 | High Cool Fan | **IMCC** (BRN, C118) | ❌ **taken** |

**Pin 46 cannot carry Fan 2.** On this truck it is the intake manifold runner
control, which the design keeps — it is listed as an output in
[`f150-1999-target.md`](f150-1999-target.md) and in `sensors-to-run.md`. The
MegaSquirt mapping was free to reuse it because that build dropped IMCC. This
one does not.

**Use pin 18 for Fan 2.** It has no wire in this truck's harness and it is
adjacent to pin 19, so the two fan drives leave the connector as a neighbouring
pair and harness together.

There are **28 pins with no wire** in this truck's harness — 2, 4, 5, 8, 9, 10,
17, 18, 19, 23, 24, 28, 30, 31, 33, 38, 42, 43, 44, 45, 48, 58, 63, 70, 76, 82,
86, 102 — so pin choice is not scarce. Adjacency is the only reason to prefer 18.

None of this is OEM wiring in any case: **the truck has no fan wires at all**,
because it has a clutch fan. Both fan drives are new harness from the ECU to the
relays whatever pins they use.

> **[CONFIRM]** the flat 1–104 numbering against Ford's connector-relative
> numbering (A-13, B-17…) before crimping. That caveat is already on the pinout
> document and applies here.

---

## 3. Temperature source: CHT, not ECT

**This truck has no coolant temperature sensor.** EEC-V pin 66 is *Cyl Head
Temp* (YEL/LT GRN), and the MegaSquirt build jumpered its own ECT input across
to it precisely because there was nothing else to connect.

That is not a detail to gloss over when setting fan thresholds:

- **Head metal runs hotter than coolant** and responds faster. Thresholds
  carried over from a coolant-sensor engine will run the fans late.
- **CHT keeps reading when coolant is gone.** This is the sensor Ford's
  fail-safe cooling strategy is built on — a coolant sensor in an empty head
  reads air. Fan logic keyed to CHT still does something useful during a coolant
  loss, which is a genuine argument for the fans being on this sensor rather
  than an added aftermarket coolant probe.
- **The defaults below are CHT numbers.** They are not coolant numbers.

> **[CONFIRM ON TRUCK]** the CHT sensor curve and what this engine actually
> stabilises at, at idle and at speed, before trusting the defaults. Every
> threshold in this document is a starting point to be measured against.

---

## 4. Control strategy

### 4.1 Staging

Two relays, staged on/off. Stage 1 carries normal traffic; stage 2 is for
grades, towing and heat.

| | On | Off | |
|---|--:|--:|---|
| **Fan 1** | 96 °C | 91 °C | 205 / 196 °F |
| **Fan 2** | 103 °C | 98 °C | 217 / 208 °F |

The 5 °C hysteresis band is the point. At idle airflow that is minutes of run
time, not seconds, so the relays are not cycling and the fans are not surging
the electrical system every few seconds.

Two further guards:

- **`stageDelayMs` (3 s)** — never start both fans into the same inrush. If a
  hot restart crosses both thresholds at once, stage 2 still waits. Two 60–80 A
  inrush events three seconds apart are a far smaller disturbance than one
  160 A event.
- **`minRunMs` (10 s)** — once a fan starts it runs at least this long,
  whatever the temperature does. Relay contacts have a finite number of
  operations and a fan motor does not enjoy being stalled and restarted.

### 4.2 A/C

**A/C pulls a fan on by itself, regardless of head temperature.** The condenser
sits in front of the radiator and needs airflow at idle; head temperature is
not a proxy for condenser pressure, and waiting for the engine to heat up is
how you get warm vents in a parking lot and a high-pressure cutout on a hot day.

Stage 1 is enough for a condenser. `acFanStage` can raise it to 2.

> **[CONFIRM]** which input to key on. There are two distinct A/C signals and
> they are not interchangeable:
>
> | | | |
> |---|---|---|
> | **A/C request** | C139/C170, listed in `sensors-to-run.md` | the driver asked for A/C |
> | **A/C cycle switch** | EEC-V 41, BLK/YEL | the low-pressure cycling switch |
>
> The *request* is the right trigger — it is true whenever the system is trying
> to cool. The cycling switch drops out every time the compressor cycles, which
> would chatter the fan. Use the request; log the cycle switch.

A third signal exists and is worth wanting: **A/C high-side pressure**, listed
as an analog channel in `f150-1999-target.md`. If it is fitted, high head
pressure should command stage 2 directly. Without it, stage 2 is temperature-only.

### 4.3 Highway cutoff — a permissive, never an override

Above roughly 45 mph, ram air through the grille exceeds what the fans move.
Running them is wasted alternator load and noise for no cooling.

**But the cutoff is a permission to stop, not an instruction to stop.** The
fans are switched off at speed *only while the head is already cool*. It is
structured as:

```
fans_allowed_off_at_speed  =  highwayCutoff enabled
                          AND road_speed > highwayCutoffKph  (sustained)
                          AND CHT         < highwayMaxC
                          AND A/C not requested
                          AND not in 4x4 low
```

Any one of those failing and the fans run on their normal thresholds. The
temperature term is the important one: `highwayMaxC` defaults to 91 °C, the same
as the stage 1 off threshold, and **the config loader clamps it so it can never
exceed `fan1OnC`**. A speed signal cannot override a thermal limit — that is the
one thing this feature must not be able to do. A stuck-high speed reading should
cost you some fan noise, not a head.

`highwayHoldMs` (5 s) requires the speed to be sustained, so a noisy OSS edge or
a brief downhill run does not toggle the fans.

Default is **off**. Turn it on once the truck's real highway CHT has been
measured and is comfortably below 91 °C. On a truck that runs hotter than that
at speed, this option does nothing except add a failure mode.

### 4.4 Road speed is not free on a 4WD

Road speed comes from **OSS** (EEC-V 84, VR, on a MAX9926) — the transmission
*output shaft*, upstream of the transfer case.

**In 4-LO that reading is wrong by the transfer case ratio** (roughly 2.64:1 on
this truck). OSS would indicate ~45 mph at ~17 mph of actual road speed, and the
cutoff would switch the fans off crawling up a trail — which is the worst
possible moment, with no ram air at all and the engine working hard.

Hence the `4x4 Low Indicator` term. It is a discrete input on **EEC-V pin 14**
(LT BLU/BLK) that was already found in the pinout and is not otherwise used, and
it inhibits the cutoff outright. Cheap insurance.

> **[CONFIRM]** whether OSS or the **transfer case speed sensor** (C199, 4x4
> only) feeds the speedometer. `sensors-to-run.md` already flags this as open.
> If the transfer case sensor is the real road-speed source, prefer it for the
> cutoff — it is downstream of the range box and correct in both ranges, and the
> 4x4-low inhibit becomes belt-and-braces rather than load-bearing.

### 4.5 Cranking

**Fans off while cranking.** A starter on a cold morning is already the largest
load the battery will see; adding 20 A of fan to it drops the rail, for no
cooling benefit at an engine that has not run yet. `crankInhibit`, default on.

### 4.6 Run-on after key-off

Peak head temperature after a hard pull happens *after* shutdown, when coolant
stops circulating and the water pump stops with the engine. Heat soak is real
and it is what warps things.

The [always-on MCU domain](always-on-domain.md) makes run-on possible: the MCU
survives key-off, so it can keep a fan relay energised and decide when to stop.

Guards, all configurable:

| | Default | |
|---|--:|---|
| `runOnMaxS` | 300 s | hard ceiling regardless of temperature |
| `runOnUntilC` | 95 °C | stop once the head is back under this |
| `runOnMinVolts` | 12.2 V | **stop immediately below this** |

The voltage floor is not optional. A cooling fan must never be the reason the
truck will not start, and with the engine off there is nothing replacing the
charge. 300 s of a single 18 A fan is roughly 1.5 Ah — a few percent of a group
65 battery, acceptable once, and the floor catches the case where it is not.

> **Requires** the fan relay feed to be on a permanent B+ circuit, not switched
> ignition. See §5.

---

## 5. Electrical

Sized for an **aftermarket dual 12–13″ setup, ~30–40 A total**.

| | Per fan | Note |
|---|---|---|
| Running current | 15–20 A | |
| Locked-rotor / inrush | 60–80 A | brief, but it is what welds contacts |
| Relay | **40 A SPST**, one per fan | |
| Fuse | **30 A**, one per fan | at the battery end of the feed |
| Feed | **10 AWG** | fuse → relay → fan |
| Ground | **10 AWG to the block or battery**, not a body screw | |
| Relay coil | **TBD62083AFNG**, direct from the expander | §5.2 |
| Coil suppression | **built into the driver** | TBD62083AFNG clamps every channel to COMMON — no external diodes |

### 5.1 Feed and the run-on requirement

The fan relay contacts must be fed from **permanent B+ through their own
fuses**, not from switched ignition — otherwise §4.6 run-on cannot work, because
the power disappears with the key.

The *coils* are ECU-driven, so nothing runs unless the ECU commands it, and the
ECU is the thing that de-energises them at the end of run-on or at the voltage
floor.

### 5.2 Relay coil driver — **Toshiba TBD62083AFNG**

Settled. An 8-channel DMOS sink array, ULN2803-pin-compatible, chosen for the
whole slow low-side group at once rather than per feature. Full reasoning and
the thermal numbers are in
[`output-drivers.md`](output-drivers.md#relays-and-lamps-toshiba-tbd62083afng).

What it means for the fans:

- **Direct from the expander.** V<sub>IN(ON)</sub> is 2.5 V at 100 µA, so an
  MCP23S17 pin drives a channel with nothing in between — no level shift, no
  base resistor, and nowhere near the expander's 25 mA.
- **No flyback diodes to fit.** Every channel has a clamp diode to COMMON built
  in, which satisfies `harness-protection.md`'s requirement for relay coils.
- **Both fans plus the fuel pump, A/C clutch and MIL fit one package**, five
  channels of eight, three spare. At 200 mA coils that is 0.23 W against a
  0.69 W budget at a 60 °C cabin ambient — not close to any limit.
- **COMMON forces one supply rail for the whole package.** All eight clamp
  diodes share it, so every relay coil on the chip is fed from **permanent B+**.
  That is what §4.6 run-on needs anyway, so the constraint costs nothing here.

The 400 mA operating limit is comfortable for a relay coil and is *not* enough
for the HO2S heaters or the transmission solenoids. Those are covered by the
**NCV8405ASTT1G** in
[`output-drivers.md`](output-drivers.md#solenoids-and-heaters-onsemi-ncv8405astt1g),
which does not touch the fan path either way.

### 5.3 Alternator headroom

40 A of fan against the OEM alternator, at idle, with headlights and blower
already running, is the case to check. The OEM unit self-regulates and
[alternator control is explicitly deferred](v1-scope.md), so the ECU has no
influence over output — it can only decide not to ask.

The staging already helps: stage 1 alone is 15–20 A, and stage 2 only joins
under real thermal load.

> **[CONFIRM ON TRUCK]** the alternator's rating and its actual idle output.
> Idle output is typically a fraction of the rated figure, and the rated figure
> is what gets quoted.

---

## 6. Configuration

All thresholds and options are in `/config.json` on the SD card, under
`cooling`, and are read at boot. Defined in
[`../firmware/ecu/include/Config.h`](../firmware/ecu/include/Config.h).

```json
{
  "cooling": {
    "enabled": true,

    "fan1OnC": 96.0,
    "fan1OffC": 91.0,
    "fan2OnC": 103.0,
    "fan2OffC": 98.0,

    "acFanOn": true,
    "acFanStage": 1,

    "highwayCutoff": false,
    "highwayCutoffKph": 72,
    "highwayMaxC": 91.0,
    "highwayHoldMs": 5000,

    "stageDelayMs": 3000,
    "minRunMs": 10000,
    "crankInhibit": true,

    "runOn": true,
    "runOnMaxS": 300,
    "runOnUntilC": 95.0,
    "runOnMinVolts": 12.2
  }
}
```

| Key | Default | |
|---|--:|---|
| `enabled` | true | master switch for the whole feature |
| `fan1OnC` / `fan1OffC` | 96 / 91 | stage 1, **CHT** °C |
| `fan2OnC` / `fan2OffC` | 103 / 98 | stage 2, **CHT** °C |
| `acFanOn` | true | A/C request pulls a fan on by itself |
| `acFanStage` | 1 | which stage A/C commands (1 or 2) |
| `highwayCutoff` | **false** | opt in — read §4.3 first |
| `highwayCutoffKph` | 72 | ~45 mph |
| `highwayMaxC` | 91 | cutoff does not apply above this. **Clamped to ≤ `fan1OnC`** |
| `highwayHoldMs` | 5000 | speed must be sustained |
| `stageDelayMs` | 3000 | minimum gap between stage 1 and stage 2 starting |
| `minRunMs` | 10000 | minimum fan run once started |
| `crankInhibit` | true | fans off while cranking |
| `runOn` | true | run-on after key-off |
| `runOnMaxS` | 300 | hard ceiling |
| `runOnUntilC` | 95 | stop once back under |
| `runOnMinVolts` | 12.2 | **stop immediately below this** |

### Sanity correction, not rejection

`config::sanitiseCooling()` runs after every load. A hand-edited config that
would leave the engine with no cooling gets corrected and logged rather than
refused — the same principle as the rest of `Config.cpp`, where a config that
will not parse is a reason to fall back, not a reason to leave the engine
without a controller.

| Condition | Correction |
|---|---|
| `fanNOffC` within 2 °C of `fanNOnC` | off pulled down to a 2 °C band — otherwise it is a latch, not a hysteresis |
| `fan2OnC` ≤ `fan1OnC` | stage 2 pushed 5 °C above stage 1 — inverted stages fight and stage 2 means nothing |
| `highwayMaxC` > `fan1OnC` | clamped — **a speed signal must never override a thermal limit** |
| `acFanStage` outside 1–2 | forced to 1 |

Each correction prints to the console at boot, so a config that is being quietly
fixed does not stay quiet.

---

## 7. Status

**Config is in.** The `cooling` block loads, saves, validates and reports today
— thresholds can be edited on the card and read back, which is testable on the
bench right now.

**The control logic is not**, and cannot be yet: it needs CHT, which arrives
with **M7 (sensors → fuel)**, and an expander output layer, which does not exist
in the rebuilt tree. See [`roadmap.md`](roadmap.md).

That ordering is deliberate rather than an omission. Fan control written against
a temperature that nothing reads would be untestable fiction, and
[`roadmap.md`](roadmap.md)'s rule is that nothing enters the tree until it has
been proven on hardware.

### Open items

| | Where |
|---|---|
| **[CONFIRM]** EEC-V flat vs connector-relative pin numbering | §2 |
| **[CONFIRM ON TRUCK]** CHT curve and real operating temperatures | §3 |
| **[CONFIRM]** A/C *request* vs *cycle switch* as the trigger | §4.2 |
| **[CONFIRM]** whether A/C high-side pressure is fitted | §4.2 |
| **[CONFIRM]** whether OSS or the transfer case sensor feeds the speedo | §4.4 |
| ~~Choose the relay coil driver~~ — **resolved: TBD62083AFNG** | §5.2 |
| **[CONFIRM ON TRUCK]** alternator rating and idle output | §5.3 |
