# Latching relay driver — 5 V standby, mains relay for the 36 V supply

A soft power switch. The **5 V module is always live**; a momentary button
toggles a **5 V latching relay** that switches **mains ahead of the 36 V
supply**. Push on, push off, and the relay holds its own state with **zero
coil current** in between.

> ## ✅ Outcome, 2026-09-22 — the PSU is working on a bought module
>
> An off-the-shelf **5 V latching relay module** is in service and doing the job.
> This board is therefore **not needed to switch the supply** — only if the
> behaviours listed below are wanted.
>
> ### The 12 V → 5 V conversion, found by comparing the two boards
>
> The vendor builds both variants on **one PCB**. The 5 V version is the 12 V
> version with the on-board **5 V LDO omitted** and a **0 Ω 0805 link** fitted in
> its place, feeding the input straight to the rail. The rest of the circuit is
> already 5 V.
>
> So a 12 V module bought by mistake converts by bridging the LDO's in/out pads
> with a 0 Ω 0805 — or a solder blob — and feeding it 5 V.
>
> > ⚠ **Check the relay coil before assuming this generalises.** It works because
> > the logic *and the coil* are 5 V on both variants. A 12 V board fitted with a
> > **12 V coil** would get 5 V on that coil after the bypass and simply not pull
> > in, and would need the relay swapped as well. Measure the coil, or read the
> > relay's part number, first.
>
> ### What the bought module does not do
>
> | | Bought module | This board + ATtiny |
> |---|---|---|
> | Toggle a latching relay from a button | ✅ | ✅ |
> | **Fail-safe off after a blackout** | ❌ | ✅ reset pulse at boot |
> | Brown-out interlock | ❌ | ✅ BOD fuse |
> | State sense — where the relay actually is | ❌ | ✅ spare pole |
> | A line to the ECU | ❌ | ✅ |
>
> **The second row is the one that matters**, and it is where this whole thread
> started: a latching relay *remembers*, so after a power cut the 36 V supply
> switches itself back on when the mains returns. If that is acceptable on a
> bench supply, the bought module is the right answer and this board stays on the
> shelf — a legitimate outcome, not a failed one.

**Nothing on this board is ever mains.** The relay lives in the PSU enclosure
with the mains wiring; the board carries 5 V, the button contacts and two coil
wires. It is SELV end to end, which is the main reason the relay is on a header.

```
   5V always-on module
        │
        ├── this board ── coil wires ──► LATCHING RELAY ──► mains ──► 36 V PSU
        │                                (in the PSU enclosure)
     button (remote, on a header)
```

## Final version — bleed the 36 V output so "off" means off

Today the supply **fades** rather than switching off: its output capacitance
holds charge with nothing to discharge it. The fix is a **bleed resistor across
the output, connected by a normally-closed contact** — open while the supply
runs, closed when it is switched off, so the discharge is automatic and needs no
logic. A latching relay's off position is stable, so an NC pole genuinely means
"off".

### Size it for the stuck-closed case, not for the discharge

The discharge itself is trivial — **0.65 to 3 J** depending on capacitance, which
any resistor absorbs as a pulse. What decides the value is the failure: **if that
contact ever closes while the supply is on, the resistor sees V²/R
continuously.**

| R | τ at 2200 µF | 36 V → 5 V | Peak I | **P if stuck closed** |
|--:|--:|--:|--:|--:|
| 220 Ω | 0.48 s | 0.96 s | 164 mA | **5.9 W** 🔥 |
| 470 Ω | 1.03 s | 2.04 s | 77 mA | 2.8 W |
| **1 kΩ** | **2.20 s** | **4.3 s** | 36 mA | **1.3 W** |
| 2.2 kΩ | 4.84 s | 9.6 s | 16 mA | 0.6 W |

**1 kΩ in a 3 W package** is the pick: a few seconds to safe, and a stuck contact
is a warm resistor rather than a fire. A 220 Ω would discharge in under a second
and burn 5.9 W forever if the relay failed closed — the wrong trade for a
difference nobody notices.

**Measure the real capacitance first.** The supply's own output caps plus
whatever the 36 V feeds downstream both sit across the bleed, and the total is
what sets the time.

### Two alternatives worth knowing

- **No relay at all:** a permanent 10 kΩ across the output bleeds it in ~20 s and
  wastes 0.13 W while running. Zero moving parts; often enough for a bench.
- **Spare pole:** if the mains relay has one, its NC contact does this for free —
  but that pole was also the candidate for **state sense**. Two jobs, one pole:
  either a DPDT latching relay, or accept the choice.

## One layout, either relay

The relay is on order and the coil type is not settled, so the board is laid out
as a **full bridge with a 3-pin coil header (A / +5V / C)** and populated to suit:

| Relay | Coil wiring | Populate | Components |
|---|---|---|--:|
| **Dual coil** (separate set + reset) | coil 1 across **A–B**, coil 2 across **B–C** | the two **low-side** FETs only | 90 mm² |
| **Single coil** (reverses polarity) | coil across **A–C**, B unused | **all four** → full H-bridge | 107 mm² |

The two extra footprints cost 17 mm² of board and nothing at all if unpopulated,
which is cheaper than guessing wrong and re-spinning.

> **Gate defaults are safe in both populations.** Pull-downs on both legs mean
> that with the bridge fitted, *both* midpoints idle high — the coil sees no
> differential — and with only the low-side FETs fitted, both coils idle off.

**If it turns out to be single coil, the IRF7319 is finally the right part**: a
matched complementary pair per leg, both halves specified at ±4.5 V gate drive,
so a 5 V rail drives it with no bootstrap. Two SO-8s replace four SOT-23s. It
costs 37 mm² more and about 40× the money, so it is a preference, not an
improvement — but it is a legitimate one.

> **This choice reaches outside this board.** The enclosure fan controller can
> use the 5 V rail as an interlock — lose the rail, the coil drops, the 36 V
> supply dies and there is nothing left to cool, so no thermal switch is needed.
> **That only holds with an ordinary relay.** A latching relay's stable off
> position means a 5 V loss leaves the contacts where they were and the supply
> running, which removes the interlock without changing anything visible here.
> See [`../fan-controller`](../fan-controller/README.md#the-5-v-rail-is-an-interlock--if-you-wire-it-that-way).

## Or use an ordinary 5 V relay

There are plain 5 V relays in the drawer, and they build today rather than
waiting on the post. The firmware covers them with `LATCHING 0`.

| | Latching | Ordinary |
|---|---|---|
| Drive | 30 ms pulse | coil **held** |
| Holding current | **zero** | 70–90 mA, ~0.4 W, for as long as the supply is on |
| After a blackout | comes back **on by itself** unless firmware resets it | **off**, by construction |
| FETs populated | 2 or 4 | **1** |
| Coil header | A / +5V / C | A / +5V |

The fail-safe-off behaviour that costs a boot pulse and a paragraph of reasoning
on a latching relay is simply free on an ordinary one — no power, no coil, no
contact. What you pay is 0.4 W sitting in the coil, and a standby module that
has to carry it continuously rather than in 30 ms bursts.

## Pulses, not levels

A latching relay is driven by a **20–50 ms pulse**, not a held signal. That is
the whole difference from an ordinary relay driver, and it is what makes the
microcontroller the sensible choice rather than a luxury:

| | Discrete logic | ATtiny |
|---|---|---|
| Pulse generation | two RC differentiators, ~10 µF caps, gates decaying through the linear region, width drifting with temperature | `pin high; delay 30 ms; pin low` |
| Debounce | RC + Schmitt inverter | firmware |
| Power-on state | RC on a clear pin | firmware, and it can be *decided* |
| Parts | ~14 | ~7 |

**Rail sag during the pulse.** 150 mA for 30 ms is 4.5 mC, which no practical
bulk cap can supply on its own — 1000 µF alone would sag 4.5 V. The 5 V module
sources the pulse; the cap (100–470 µF at the coil header) is there to stop the
rail dipping enough to disturb anything else sharing it. Size the 5 V module for
the coil's pull-in current, not its average.

## Firmware — what makes this better than the module you'd buy

| Behaviour | Why |
|---|---|
| **Fail-safe off on power return** | A latching relay *remembers*, so after a blackout the 36 V supply would come back by itself. Firing a reset pulse at boot makes it come up off. This is a deliberate decision, not a default — and it is the one a bought module gets wrong. |
| **Brown-out interlock** | Never start a pulse on a sagging rail. A half-energised coil can leave the armature indeterminate, which is what makes latching relays look unreliable. |
| **State sense** | A spare pole fed back to an input through a divider tells the board where the relay actually *is*, instead of assuming. |
| **Pulse width as a tunable constant** | Matched to the relay you actually have. |
| **Long press vs short press** | Short toggles; long forces off. |
| **A line to the ECU** | One spare I/O and the ESP32 can toggle or read the supply. |

Pin budget on an 8-pin tinyAVR — VDD, GND, UPDI and five I/O:

| Pin | Use |
|---|---|
| Leg A | both gates of leg A tied; high = midpoint low |
| Leg C | same for leg C |
| Button | to GND, internal pull-up, firmware debounce |
| State sense | from the relay's spare pole |
| ECU line | spare, bidirectional |

Package note: the ATtiny202 is an **8-pin** part. SOIC-8 is ~30 mm²; the 3 × 3
UDFN-8 is ~12 mm² and is what the areas above assume.

## No-firmware fallback

If the programmer is a problem, the discrete version still works: **SN74LVC1G74**
flip-flop with D tied to /Q, a **SN74LVC1G14** Schmitt inverter shaping the
button edge, and Q and /Q feeding the two gates through RC differentiators
(~10 µF + 4.7k ≈ 47 ms) so each transition fires one coil briefly. It gives up
fail-safe-off, the brown-out interlock, state sense and tunable pulse width —
which is most of the reason for building your own.

## Why there is no optocoupler in this

**The relay is the isolation.** Coil and contacts are galvanically separate
inside the part, typically 4–5 kV. The mains on the contacts is invisible to the
gate circuit, and there is no path back to the FETs. An opto would isolate
something the relay already isolated.

## The mains side (all of it off this board)

- **Inrush is what kills the contacts, and there is no way around it here.** A
  switch-mode supply pulls **30–60 A for under a millisecond** at turn-on, and
  repeated inrush welds contacts over time — the relay dies closed, with the
  36 V supply stuck on. An **NTC limiter (SL32-type, 5–10 Ω)** in series with
  the mains fixes it for pennies, and matters far more than the steady-state
  current rating you would otherwise shop on.
- **Remote inhibit was checked — this supply does not have one.** That closes the
  tidier option (a signal-level enable, no inrush, no contact wear) and makes
  mains switching the only route, so the NTC above is not optional, it is the
  design. If the supply is ever replaced, a model with a remote-on input turns
  this board into a signal driver and retires the relay.
- **Creepage at the relay**, not here: ≥ 6.4 mm between coil-side and
  contact-side copper on whatever board carries it, with a routed slot if the
  footprint allows.
- **Fuse the mains side**, ahead of the relay.
- Contact rating: switching AC sidesteps the DC derating trap entirely. Had this
  been the 36 V DC output instead, a "10 A / 250 VAC" relay is usually only
  10 A / **30 VDC** and would have been out of spec.

## Parts considered and rejected

| Part | Why not |
|---|---|
| **SN74AUC2G80** | V<sub>CC</sub> **0.8–2.7 V**, built for 1.8 V — cannot take the 5 V rail, and a ~1.2 V output will not drive a gate. **No preset or clear**, so no defined power-up state. Input transition limit 20 ns/V against a button's ~10⁶. Its one elegant trait: Q̄ is the only output, so the toggle is a single wire. |
| **CD4013** | SOIC-14 for one flip-flop, half of it unused, and its ~15 µs input transition limit is violated by any RC debounce just as badly as the alternatives. |
| **IRF7319PbF** | Not rejected any more — see the single-coil population above. |
| **Two-MOSFET soft latch** | Turning off with the *same* button needs a steering capacitor whose behaviour depends on press duration and on how far it discharged since the last press, with no defined power-up state and no debounce. A latching relay makes the whole question moot: the relay is the memory. |
| **Alternate-action pushbutton** in the coil line | With a *latching* relay and a spare changeover pole, the relay can steer its own next pulse and need no electronics at all. Genuinely the answer if you never want the ECU to touch it. |

## BOM

`BOM.csv` follows the column format of `hardware/2N7002 Driver`, UTF-8 BOM marker
included. It is the **dual-coil population** — the single-coil delta is two more
FETs, two more gate resistors and two more pull-downs. The relay and the button
are not in it; they are H3 and H2.

Supplier part numbers carried over from the 2N7002 driver board are known good
(the 220 Ω and 10 kΩ codes are the **0805** parts — re-pick for 0402). The rest
are blank deliberately rather than guessed: **fill them from LCSC before
ordering**, and prefer Basic parts to avoid feeder charges.
