# Dash indicators — speaking Ford's language

Two driver-facing lamps, and the rule for both is the same: **the truck should
behave the way the person looking at it expects.** A mechanic who has seen a
hundred F-150s reads these lamps fluently. Inventing new meanings for them
throws that away for nothing.

| Lamp | Stock meaning | Driven by |
|---|---|---|
| **Oil pressure** | Below ~12 psi | `hardware/oil-pressure/` — see that doc for the driver and the watchdog |
| **O/D OFF** | **Steady:** overdrive cancelled. **Flashing:** transmission fault | This document |

## The O/D OFF lamp is the transmission's MIL

That is the part worth preserving carefully. On these trucks a **flashing O/D OFF
lamp is how Ford reports a transmission fault** — a stored DTC, a failed solenoid
circuit, a lost speed signal, limp mode. Engine faults go to the MIL; transmission
faults go here. They are two separate indicators and must not be merged.

So the lamp has three states, not two:

| State | Means |
|---|---|
| Off | Overdrive available, no faults |
| **Steady** | Overdrive cancelled — by the driver's button, or by strategy (tow/haul, overheat, warm-up) |
| **Flashing ~1 Hz** | **Transmission fault.** Takes precedence over steady |

> **To verify on the truck**, rather than trusted from memory: the exact flash
> cadence, and whether this indicator proves out at key-on. That it flashes for
> faults at all is now confirmed by the EVTM — see below.

### Where the lamp actually is — settled

**Not in the instrument cluster.** `InstramentCluster2/3/4.png` carry the low
fuel, low oil pressure / high coolant, MIL, 4×4 low and high range, fuel reset,
door ajar and anti-lock indicators — and no overdrive one. `dash-modules.md` has
it: **C251, the transmission control switch assembly, is "29 in, 12 out" — the
O/D switch *and* its indicator lamp.** The lamp is in the switch on the column.

That matters, because `schematic-findings.md` establishes the cluster's only PCM
connection is **SCP**, and the MIL is driven by the cluster's own micro with no
wire to it. Had the O/D lamp been a cluster indicator it would have been an SCP
message, there would be no wire to grab, and the watchdog design below would be
impossible. It is not — it is a **discrete ground-switched LED**, which is also
where the resistor in that circuit lives (the LED's own, per `eec-v-pinout.md`),
so the ECU sinks milliamps.

**PCM pin 79 — settled by the EVTM itself.** `4R70W-Transmission.png` draws the
whole circuit, and it is unambiguous:

```
  12V (START OR RUN) ─ C243 ─ 640 RD/YE ─ S225 ─ C251M/F ─┬─[ 820 OHMS ]─ TCIL ─┐
                                                          │                     │
                                                          └─ O/D OFF switch ─┐  │
                                                                             │  │
                          224 TN/WH ── C251 ── PCM pin 29  ◄─────────────────┘  │
                          911 WH/LG ── C251 ── C158 ── PCM pin 79  ◄────────────┘
```

| | |
|---|--:|
| Switch in, "12 V when closed" | **pin 29**, `224 TN/WH` |
| **Indicator lamp out, PCM sinks it** | **pin 79**, `911 WH/LG` |
| Series resistor, inside the TCS assembly | **820 Ω** |
| Lamp current the ECU must sink | **12.2 mA** at 12 V, **15.1 mA** at 14.4 V |

> **Correction.** An earlier version of this file chose pin **12**, on the
> grounds that two derived notes said 12 against one saying 79. That was
> counting sources instead of weighing them — `eec-v-pinout.md` has the right
> circuit colour (WHT/LT GRN = `911 WH/LG`) with the wrong pin, and
> `schematic-findings.md` had it right all along. The EVTM sheet outranks both,
> which is exactly the rule [`source-conflicts.md`](source-conflicts.md) sets out.

**The EVTM also confirms the flashing behaviour** in its own callout, rather than
leaving it to memory: *"Indicates that 4th gear has been disengaged. **May also
flash if monitored sensors/actuators or circuits have failed.**"*

At 15 mA the driver is trivial — any SOT-23 logic-level FET, and the 820 Ω means
the ECU never sees more than that even with the output shorted to the 12 V rail.

> **The cluster's house style is open-to-warn**, which is worth knowing for
> everything else on that connector: the oil pressure switch is *closed* for
> normal, and the anti-lock indicator "receives an **open** from the ABS module
> when there is a fault". The O/D lamp is the opposite — ground-switched to
> illuminate — because it is an LED in a switch pod, not a cluster input.

## What the ECU is missing today

Nothing in the repo touches this. Checked:

- **No lamp output** and **no O/D cancel switch input** anywhere in `src/` or
  `include/`.
- **`TransmissionManager` detects no faults at all.** `_limpMode` exists and
  `setLimpMode()` is public, but it is only ever called from outside — there is
  no internal detection that would ever call it.
- **`TransmissionState` exposes no fault or limp field**, so the dashboard, the
  `/state` JSON and MQTT cannot report one either.

That last point matters more than the lamp: **a lamp that flashes for faults
needs faults to exist first.** The lamp is the cheap half of this job.

## Three layers of work

### 1. The O/D cancel input — 12 V, not switch-to-ground

**Corrected.** `4R70W-Transmission.png` labels PCM pin 29 *"12 V (switch
closed)"*: the switch feeds **battery** down `224 TN/WH`, it does not pull to
ground. An earlier version of this section assumed a `CPIN_INPUT_POLL` with an
internal pull-up, which would have been wrong in both polarity and voltage.

**It also cannot be a plain digital input.** With a 47k/10k divider — the same
pair the board already uses for VBAT — the pin sits in the ESP32's undefined
band across the normal operating range:

| Battery | At the pin | ESP32 sees |
|--:|--:|---|
| 11.0 V | 1.93 V | **undefined** (V<sub>IH</sub> = 2.47, V<sub>IL</sub> = 0.82) |
| 12.0 V | 2.11 V | **undefined** |
| 14.4 V | 2.53 V | high |
| 16.0 V | 2.81 V | high |

A ratio that clears V<sub>IH</sub> at 11 V would exceed 3.3 V at 16. There is no
plain divider that works, which is why this gets read as an **analog** value with
the threshold in software — a `SensorDescriptor` on the MCP3204, where 14.4 V
lands at 2.53 V, comfortably mid-scale against a 5 V reference.

**Front end**, matching the oil sender's pattern:

| Part | Value | Doing |
|---|--:|---|
| Series / top leg | **47 kΩ** | scaling, and limiting a fault to 0.63 mA at 35 V |
| Bottom leg | **10 kΩ** | scaling, **and defining the open state** — the switch is a source, so with no pull-down the pin would float |
| Clamp | BAT54 to the 5 V rail | load dump |
| Filter | 100 nF | debounce in hardware, the rest in firmware |

> **No three-state here, unlike the DTR.** The 270 Ω on the DTR sensor gives the
> PCM distinguishable positions; this circuit's **820 Ω is on the lamp side**, so
> it buys the switch input nothing. Switch-not-pressed and broken-wire both read
> 0 V and cannot be told apart. Detecting a broken O/D switch wire would need a
> series resistor added at the switch end.

The state machine is unchanged and is firmware:

- Each press **toggles** the cancel state.
- **It resets to "overdrive enabled" on every key cycle** — stock Ford behaviour,
  and a driver who expects it will be surprised by anything else. Deliberately
  *not* persisted to config.

If ADC channels are tight, the alternative is a **2N7002 with the same 47k/10k on
its gate** pulling a digital pin down: inverting, immune to the threshold
problem, and the gate sees 6.1 V at a 35 V load dump against a ±20 V rating.

### 2. The lamp driver

Electrically identical to the oil lamp: cluster feeds +12 through the bulb, the
ECU sinks it to ground through a low-side FET. Reuse that design.

**But the flash cannot be an `OutputRule`.** Rules evaluate a threshold to a
boolean — there is no cadence in them. This needs a small piece of firmware that
owns the lamp and takes a mode:

```
    LAMP_OFF
    LAMP_STEADY
    LAMP_FLASH(period_ms)
```

driven from the existing 10 ms task. Worth writing generically, because the MIL
will eventually want the same thing.

### 3. Something for it to flash about

The fault list `TransmissionManager` should detect and latch, each setting a bit
and any of them lighting the flash:

| Fault | Detect by |
|---|---|
| Solenoid circuit open or shorted | Current sense, or a flyback-clamp voltage check on each of SS A–D, TCC, EPC |
| **OSS or TSS lost** | Pulses stop while the engine is running and the trans is in gear |
| OSS/TSS implausible | Ratio outside anything the gear set can produce — the check that catches a sensor lying rather than dying |
| Excessive slip | `slipRpm` beyond threshold with TCC commanded locked |
| **Over temperature** | `overTemp` already exists in `TransmissionState` and currently lights nothing |
| MLPS invalid | Position decodes to a combination the switch cannot produce |
| Commanded gear not achieved | Target vs actual disagree for N shifts |

Each should set a fault bit, latch until cleared, and the serious ones should
call the `setLimpMode()` that is already sitting there unused.

## CEL severity tiers — and the one convention this collides with

Implemented: `FAULT_ACT_PREFAULT` joins `FAULT_ACT_CEL` and `FAULT_ACT_LIMP`, and
`LampDriver` owns the cadence.

| Tier | Action | Lamp | Anything acts? |
|---|---|---|---|
| **Pre-fault** | `FAULT_ACT_PREFAULT` | **blink**, 300 ms every 4 s | No — advisory only |
| **Full fault** | `FAULT_ACT_CEL` | **steady** | No |
| **Critical** | `FAULT_ACT_LIMP` / `SHUTDOWN` | **steady** | Limp mode: rev limit, advance cap, trans lock |

Severity outranks, so a steady lamp beats a blinking one and a real fault is
never downgraded to a flash by an unrelated advisory.

> ⚠ **On any OBD-II vehicle, a MIL flashing at about 1 Hz means a
> catalyst-damaging misfire** — the most severe thing that lamp can say, "stop
> driving now". Using a blink for the *least* severe tier inverts that, which is
> the opposite of the rule this document opens with.
>
> The pre-fault flash is therefore deliberately **slow and short — 300 ms every
> 4 seconds** — so it cannot be read as the 1 Hz misfire cadence. It looks like a
> heartbeat, not an alarm. If it ever needs to be unmistakable, the alternative
> is to move *critical* to a 1 Hz flash, which puts the fastest cadence at the
> top where every mechanic already expects it. Both are one constant in `ECU.h`.

`LampDriver` is deliberately generic — off / steady / blink with an asymmetric
duty — because the O/D OFF lamp needs exactly the same thing, and an `OutputRule`
cannot express a cadence.

## Audible annunciation — a buzzer, not the stock chime

**Do not hijack the seatbelt chime.** `gem-module.md` shows the chime is a
GEM/CTM function driven by *its own inputs* — pin 10 key-in-ignition
(`158 BK/PK`), the safety-belt switch, the door-ajar switches — with pin 12
driving the belt indicator out to the cluster. There is no "sound the chime"
input, so making it chime means asserting one of those, and none of them is a
private wire:

| Assert | What else the truck then believes |
|---|---|
| Belt switch | the belt is unbuckled — lights the belt lamp, and it is shared with restraint logic |
| Key-in-ignition | the key is in — courtesy lighting, theft logic |
| Door ajar | a door is open — interior lamps, the door-ajar indicator |

Same shape as the oil lamp polarity: these are shared signals, and faking one
lies to every module listening. A dedicated buzzer also lets the driver tell
*"that's the ECU"* from *"that's my seatbelt"*, which a borrowed chime never can.

### Patterns, and why bursts rather than a tone

| Tier | Lamp | Buzzer |
|---|---|---|
| Pre-fault | blink, 300 ms / 4 s | **silent** — an advisory that beeps is an advisory that gets disconnected |
| Full fault | steady | 2 × 150 ms, repeating every **60 s** |
| **Critical** | steady + limp | **3 × 150 ms, repeating every 10 s** |

`LampDriver` gained a `BURST` mode for this: *n* pulses, then quiet until the
repeat window comes round. A continuous tone is worse than useless — it gets
unplugged, and then nothing annunciates ever again. Three beeps every ten
seconds says "attend to me" and stays tolerable long enough to drive somewhere.

Verified on the host (`test/host/lampdriver_test.cpp`): 6 beeps and 900 ms of
sounding in 20 s for the critical pattern, a 0.5 % duty cycle for the full-fault
one, and re-arming with identical parameters does not retrigger the phase.

### Wired: MCP23S17 #0 P4 (pin 204)

`DEF_PIN_BUZZER 204`, driven from the same tiers as the CEL in
`ECU::checkLimpMode()`, plus one 150 ms chirp in `begin()` as a key-on
self-test.

> **A note on the pin map.** CLAUDE.md still describes an **I²C MCP23017 at
> 0x20** with injectors 4–8 on P3–P7. The board has since moved to **SPI
> MCP23S17** chips addressed as `200 + (chip × 16) + pin`, and injectors live on
> chip **#5** (280+). So P4 was free after all — but the stale doc made it look
> occupied. Chip #0 now holds fuel pump (200), tach (201), CEL (202), **buzzer
> (204)**, and the CJ125 chip selects (208/209); P3 and P5–P7 remain free.

### Policy worth deciding before it is wired

- ✅ **Silence/acknowledge — built.** `AlarmPolicy`: sounds for **5 minutes**,
  then goes quiet, and re-arms on any **new fault bit** or an **escalation in
  severity**. A bit that flaps in and out deliberately does *not* re-arm — that
  is the behaviour which makes real alarms unsilenceable and gets them
  disconnected. Clearing every fault ends the episode, so the next one is fresh.
  The **lamp never silences**; only the noise does. `buzzerSilenced` is published
  in `/state` so the UI can say why it is quiet.
- **Never sound while cranking**, or during a sensor's `settleMs` window — the
  masking work already suppresses the faults themselves, so this comes free as
  long as the buzzer follows the fault masks rather than raw readings.
- **Critical should also sound once at key-on** as a self-test, the same way the
  lamps prove out. A buzzer that has failed silent is indistinguishable from one
  with nothing to say.

## The ECU-is-dead signature

The heartbeat-gated watchdog in `hardware/oil-pressure/` should drive **this lamp
too**. If the ECU stops pulsing, the transmission is uncontrolled — so lighting
O/D OFF is not a guess, it is the truth.

The watchdog's output is static, so a dead ECU gives **both lamps steady**, which
is a recognisable signature and distinct from either fault on its own:

| Oil | O/D OFF | Means |
|---|---|---|
| on | off | Genuine low oil pressure, ECU alive and reporting |
| off | flashing | Transmission fault, ECU alive and reporting |
| off | steady | Driver cancelled overdrive |
| **on** | **steady** | **ECU is dead** — no heartbeat, nothing is controlling anything |

## What goes in `/state` and MQTT

`TransmissionState` gains `odCancelled`, `limpMode` and a `faultBits` mask, so
the dashboard and `ecu/fault` can say *which* fault is flashing the lamp. A
flashing lamp tells the driver something is wrong; the ECU should be able to tell
the mechanic what.
