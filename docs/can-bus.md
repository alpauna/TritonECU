# CAN for external devices

**Decision: add one CAN channel.** It costs 2 pins and it closes the telemetry gap
that dropping Ethernet opened — see [`carrier-board.md`](carrier-board.md).

## This is not the CAN that was rejected

[`v1-scope.md`](v1-scope.md) dismissed CAN as an **internal inter-board** link,
when the plan was to split engine and transmission across two MCUs. The single
board made that moot, and the rejection was of *the split*, not of CAN.

**CAN as an external device bus is a different question and had never been asked.**

## Three reasons it is the right bus here

**1. No factory conflict — it is a private bus.** A 1999 F-150 has **no CAN**;
Ford used SCP (J1850 PWM) until roughly 2003. So there is no OEM traffic to share
with, no ID space to avoid, and free choice of bit rate.

**2. Precedent on this exact vehicle.** The prior MegaSquirt build ran an MS3Pro
PNP plus a MicroSquirt over CAN —
[`f150-1999-target.md`](f150-1999-target.md). The truck has been CAN-wired before,
and any surviving dash or logger already speaks it.

**3. It is the bus externals actually come with.** Aftermarket dashes, gauges and
loggers speak CAN natively. USB does not survive an engine bay, and a laptop is
not a dashboard.

## The split this creates

| bus | carries | pins |
|---|---|--:|
| **SCP / J1850 PWM** | the **factory** cluster and OEM modules | 4 — already budgeted |
| **CAN** | **new** externals: dash, logger, telemetry, tuning dongle | **+2** |
| **USB** | flashing, bench tuning, console | 0 — on-board |

Each bus for what it is good at, and none of them overlapping.

## Pin and peripheral cost

```
CAN_TX + CAN_RX + STB = 3 pins       41 spare -> 38
```

`STB` **must be a GPIO, not strapped** — it is what makes the 20 µA standby
reachable, and what the host drives to return to Normal after a wake-up.

The F767 carries **3 × bxCAN**, so a second or third channel is available if a
reason ever appears. One is enough: at 500 kbit/s a full ECU dataset at 50 Hz is a
few percent of bus load.

> **bxCAN is CAN 2.0B, not CAN-FD.** Ample for telemetry. FD would mean an H743 —
> a platform change, and not worth it for this.

## What it needs beyond the two pins

### Transceiver: NOT the TJA1051T/3 — it has no low-power mode

The TJA1051T/3 was recommended first and it is the wrong variant. Verified against
its datasheet (`VCC` = 5 V):

| mode | min | typ | max |
|---|--:|--:|--:|
| **Silent** | 0.1 | **1** | 2.5 mA |
| **Normal, recessive** | 2.5 | **5** | 10 mA |
| Normal, dominant | 20 | 50 | 70 mA |

> *"In Silent mode the transmitter is disabled... **All other IC functions,
> including the receiver, continue to operate as in Normal mode.**"*

**Silent is not a power-saving state.** Against the 184 µA parked budget in
[`always-on-domain.md`](always-on-domain.md), Normal recessive is **27×** and Silent
is still **5.4×**. And it *would* be powered when parked, because the always-on
decision keeps the 5 V rail up to feed the TLV62085.

**Use the TJA1042T/3.** Same family, same `/3` meaning a `VIO` pin for 3.3 V logic,
same ±58 V bus fault rating — plus a real **Standby mode at ~10 µA**, which fits
the budget instead of destroying it, and **remote wake-up on bus activity**, which
an always-on design actively wants. A dash or logger powering up can wake the ECU.

**CONFIRMED against the TJA1042T/3 datasheet — a genuine drop-in.**

```
1 TXD   2 GND   3 VCC   4 RXD   5 VIO   6 CANL   7 CANH   8 STB
```
Identical to the TJA1051T/3 in all eight positions; only pin 8's meaning differs,
`S` (Silent) → `STB` (Standby). And the numbers justify the swap outright:

| | TJA1051T/3 | **TJA1042T/3** |
|---|--:|--:|
| low-power `ICC` | 1 mA (Silent) | **10 µA typ, 15 µA max** |
| `VIO` in that mode | — | 5–14 µA |
| **total parked** | ~1000 µA | **~20 µA typ** |
| Normal recessive | 5 mA | 5 mA — *identical* |
| Normal dominant | 50 mA | 45 mA |
| `VCANH`/`VCANL` | ±58 V | ±58 V |

**~50× less parked current for no operational penalty** — 20 µA is ~11 % of the
184 µA budget rather than 27× it.

### `RXD` must land on an EXTI-capable pin

Wake-up is signalled **on `RXD`**, not on a dedicated pin, and §*Standby mode* is
explicit that a transition to Normal "will not be triggered until `STB` is" driven
low by the host. So the sequence is: the MCU sleeps, `RXD` asserts on bus activity,
an interrupt wakes it, **then** firmware releases `STB`.

A **bus-dominant time-out** in Standby stops a stuck-dominant bus generating a
permanent wake request — worth knowing, because without it a shorted bus would hold
the ECU awake indefinitely.

### The `/3` trades `SPLIT` for `VIO`

On the plain TJA1042T, pin 5 is `SPLIT` — a common-mode stabilization output
intended for exactly the split termination suggested below. **The `/3` uses that pin
for `VIO`.** You cannot have both on an SO8, and 3.3 V logic is essential where
`SPLIT` is a nicety.

So split termination here is **passive** — 2 × 60 Ω with a capacitor to ground at
the midpoint — not actively driven. In Standby the bus lines are biased to ground
regardless.

### What it needs beyond the two pins

- **`VCC` must be 5 V, not 3.3 V** (4.5–5.5 V). CAN's differential levels are
  defined around a 5 V supply, so the bus side runs from the MAX25239's rail.
- **`VIO` = 3.3 V, tied to the same rail the STM32 uses** — its only job is matching
  the MCU's logic levels, so it must track them. `VIO` draw is small: 200 µA max
  recessive, 500 µA dominant.
- **Local decoupling matters.** Normal-mode dominant is **50 mA typ, 70 mA max**, so
  100 nF hard against `VCC` plus local bulk — this is a pulsed load, not a static one.
- **Absolute limits:** `VCANH`/`VCANL` −58 V to +58 V, differential ±27 V.
- **Termination: DECIDED — this ECU is a bus end and terminates.** Fit passive
  split termination, not a single 120 Ω:

  ```
  CANH --[ 60.4R 1% ]--+--[ 60.4R 1% ]-- CANL
                       |
                   [ 4.7nF ]
                       |
                      GND
  ```

  **Why split.** The midpoint capacitor shunts common-mode noise to ground, which
  matters in a bay where eight coils fire past the harness. Corner is about
  `1/(2*pi*30R*4.7nF) = 1.1 MHz` — well above 500 kbit/s signalling, so it filters
  without distorting bits. The `/3` has no `SPLIT` pin to bias the midpoint, so
  this is passive; in Standby the transceiver biases the bus to ground anyway.

  **The resistors must be matched, 1 % or better.** Mismatch converts common-mode
  into differential noise — the exact thing the network exists to prevent, so an
  unmatched split termination is *worse* than a single 120 Ω. `60.4 Ω` is the
  standard E96 value and 2× gives 120.8 Ω, inside CAN's ±10 %.

  **Keep it an identifiable schematic block.** The decision is made, but if the
  device list ever puts this ECU mid-bus the whole network has to come out — much
  easier to find if it was drawn as one thing.

  **Sizing for bus faults:** with the midpoint capacitor there is no DC path to
  ground, so a sustained CANH-to-B+ short drives ~117 mA through both resistors in
  series — about **0.8 W each**, which will cook an 0805 or a 1206. It fails *open*,
  costing termination quality rather than the node, and the transceiver survives on
  its own ±58 V rating. Use 2512 only if surviving a sustained bus short matters.
- **Harness-facing protection.** CAN_H/CAN_L leave the box, so they fall under
  [`harness-protection.md`](harness-protection.md) like any other external pin.

## Open

- [ ] Decide bit rate — it follows from the device list. Termination is settled:
      this ECU is a bus end.
- [ ] Confirm the transceiver's ground treatment against
      [`grounding-architecture.md`](grounding-architecture.md) — it is harness-facing.
- [ ] Assign `RXD` to an **EXTI-capable** pin — bus wake-up depends on it.
