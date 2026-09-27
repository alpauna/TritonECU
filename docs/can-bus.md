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
CAN_TX + CAN_RX = 2 pins       41 spare -> 39
```

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

**Expected drop-in:** same SO8, pins 1–7 identical, only pin 8 changes meaning —
`S` (Silent) on the 1051, `STB` (Standby) on the 1042. **Route pin 8 to a GPIO** and
the footprint serves either part, so layout need not wait on the decision.
**[CONFIRM]** against the TJA1042T/3 datasheet before ordering.

### What it needs beyond the two pins

- **`VCC` must be 5 V, not 3.3 V** (4.5–5.5 V). CAN's differential levels are
  defined around a 5 V supply, so the bus side runs from the MAX25239's rail.
- **`VIO` = 3.3 V, tied to the same rail the STM32 uses** — its only job is matching
  the MCU's logic levels, so it must track them. `VIO` draw is small: 200 µA max
  recessive, 500 µA dominant.
- **Local decoupling matters.** Normal-mode dominant is **50 mA typ, 70 mA max**, so
  100 nF hard against `VCC` plus local bulk — this is a pulsed load, not a static one.
- **Absolute limits:** `VCANH`/`VCANL` −58 V to +58 V, differential ±27 V.
- **Termination as a fitted option, not hardwired.** 120 Ω belongs at the two
  *physical ends* of the bus, and whether this ECU is an end depends on topology
  that is not decided yet. Use a jumper or a 0 Ω link — same reasoning as making
  a ground tie a component: the decision stays visible and reversible.
- **Harness-facing protection.** CAN_H/CAN_L leave the box, so they fall under
  [`harness-protection.md`](harness-protection.md) like any other external pin.

## Open

- [ ] Decide bit rate and whether this ECU terminates. Both follow from the device
      list, so they wait on it.
- [ ] **[CONFIRM]** the TJA1042T/3 pinout and standby current against its own
      datasheet — the drop-in claim is from family architecture, not the document.
- [ ] Confirm the transceiver's ground treatment against
      [`grounding-architecture.md`](grounding-architecture.md) — it is harness-facing.
- [ ] Decide whether `STB` is GPIO-driven or strapped. GPIO costs 1 pin (83 of ~114)
      and is what makes the standby saving reachable at all.
