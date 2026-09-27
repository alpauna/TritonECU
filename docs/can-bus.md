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

- **A 3.3 V-capable transceiver** — TJA1051T/3, TCAN1042, MCP2562FD. Prefer one
  rated for harness bus faults; the TJA1051 withstands ±58 V on CAN_H/CAN_L.
- **Termination as a fitted option, not hardwired.** 120 Ω belongs at the two
  *physical ends* of the bus, and whether this ECU is an end depends on topology
  that is not decided yet. Use a jumper or a 0 Ω link — same reasoning as making
  a ground tie a component: the decision stays visible and reversible.
- **Harness-facing protection.** CAN_H/CAN_L leave the box, so they fall under
  [`harness-protection.md`](harness-protection.md) like any other external pin.

## Open

- [ ] Decide bit rate and whether this ECU terminates. Both follow from the device
      list, so they wait on it.
- [ ] Choose the transceiver, and confirm its ground treatment against
      [`grounding-architecture.md`](grounding-architecture.md) — it is harness-facing.
