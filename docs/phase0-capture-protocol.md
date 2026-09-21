# Phase 0 — how to take a capture that is actually usable

[`f150-1999-target.md`](f150-1999-target.md) says *what* Phase 0 is: plug into
the DLC with the OEM PCM still installed, record the bus, catalogue what it
transmits. This is the *how*, because a recording of a warm idle tells you almost
nothing — you cannot find the RPM bytes in a stream where RPM never changed.

## Short answer: yes, a capture is required — but for a short list

The cluster does not poll OBD-II PIDs. The PCM **broadcasts** proprietary SCP
frames and the cluster listens. OBD-II modes are documented; these broadcasts are
not, so they have to be observed.

**Two different jobs, often confused:**

| | Direction | Needed for |
|---|---|---|
| **Broadcast** | ECU → bus, unsolicited, periodic | The dash. This is the Phase 0 capture |
| **Request / response** | Tool → ECU → tool | A scan tool. OBD-II mode 01/03, already documented, no capture needed |

## What must be reproduced — and what must not

The cluster sheets settle most of this, and the list is smaller than it looks:

| Function | Source | Over SCP? |
|---|---|---|
| **Tachometer** | no discrete PCM pin | **yes** |
| **Speedometer** | PCM pin 68 feeds cruise, GEM and rear air suspension — *not* the cluster | **yes** |
| **MIL** | disputed — [`source-conflicts.md`](source-conflicts.md) | **probably** |
| Oil pressure | switch → cluster C236 pin 20, `WHT/RED` | no — discrete |
| Coolant temperature | sensor → cluster, direct | no — discrete |
| Fuel level | sender → cluster, direct | no — discrete |
| 4×4 high / low | GEM | no |
| ABS, airbag, brake, charge | their own modules | no |
| O/D OFF lamp | **C174 pin 12**, truck-confirmed | no — discrete |

So the SCP transmit job is roughly **three signals**, not a protocol port.

## The capture is only as good as the states you exercise

Vary **one thing at a time**, and mark each event. A byte that tracks one varied
quantity across a dozen steps is not a coincidence; a byte that changes during a
drive where everything changed is unidentifiable.

| Step | Hold steady | Vary | Finds |
|---|---|---|---|
| 1 | — | key off → on, engine off | prove-out frames, what the bus does at wake |
| 2 | — | crank | cranking/run state, and whether anything is suppressed |
| 3 | parked, in P | **RPM**: idle, 1200, 1500, 2000, 2500, 3000, back to idle | **tachometer bytes** — the cleanest correlation available, because road speed stays zero |
| 4 | steady throttle | **road speed**: 15, 25, 35, 45 mph, GPS as reference | **speedometer bytes** |
| 5 | idle | induce a fault — see *On-demand MIL* below | the **MIL** bit, and the transition in both directions |
| 6 | idle | press O/D OFF | whether the switch state appears on the bus at all |
| 7 | — | key cycle with a valid key | the **PATS** exchange |

**Record a reference channel alongside the bus.** RPM from the crank sensor and
speed from GPS, on the same timebase. Without one, correlation is guesswork.

### On-demand MIL, without breaking anything

The 2003 truck has a **disconnected EGR** setting a code, which makes it a
controllable MIL source rather than a broken one.

The valuable recording is not the lamp being *on* — it is the moment it **goes**
on, with everything else held still:

1. Reconnect the EGR and clear the code.
2. Idle the engine, warm, parked. Start recording.
3. **Unplug the EGR connector while it is running.**
4. Record through the lamp coming on.

RPM, coolant, road speed and engine state are all steady across that boundary, so
the bits that change are the MIL and whatever carries DTC state. Nothing else in
the capture isolates a single bit that cleanly.

**Two traps:**

- **One-trip vs two-trip.** A circuit fault (open solenoid, DPFE) usually sets on
  the trip it happens. A *flow* fault such as P0401 is two-trip and will not
  light until the next key cycle — still usable, just record both trips and note
  where the key cycle falls.
- **Do not use the key-on prove-out.** The lamp lights for ~3 s at key-on, which
  looks like a free transition — but the cluster may perform that self-test
  **internally**, in which case nothing appears on the bus and the honest
  conclusion "the MIL is not on SCP" would be wrong. Only a *fault-driven*
  transition proves anything.

While the lamp is lit, that is also the window for the back-probe test in
[`source-conflicts.md`](source-conflicts.md): if no PCM pin is being sunk, it is
SCP.

> **The 2003 is a hint, not proof, for the 1999.** The Chilton set that started
> the MIL disagreement spans 1997–2003, and "the architecture changed partway
> through that span" is the leading explanation for it. If the 2003 has a
> discrete MIL wire, that may be *why* Chilton drew one — and the 1999 could
> still be SCP. Confirm on the truck being converted.

## Finding the bytes

1. **Diff frames with the same header.** Within one header ID, most bytes are
   constant. The ones that move are the payload you care about.
2. **Look for monotonic tracking**, then for a linear fit. RPM is commonly a
   16-bit big-endian value with a fixed divisor — check adjacent byte pairs, not
   single bytes.
3. **Rate matters as much as content.** Note each header's period. A cluster that
   receives a correct message too slowly shows a needle that sags or a lamp that
   flickers.
4. **Do not assume one message per quantity.** A single frame often carries
   several.

## Verify on the bench, not in the truck

The decisive test costs nothing and risks nothing: **pull the cluster, power it
on a bench** — 12 V, ground, illumination — and transmit candidate frames at the
captured rate. If the needle moves, the message is right. If it does not, no
amount of re-reading the log will tell you why.

Do this before the ECU ever transmits in the vehicle.

## Two cautions

**Listen only while the OEM PCM is installed.** Two devices transmitting the same
headers will corrupt each other's frames. Phase 0 is receive-only — hold the
transceiver's TX in its idle state, and confirm with a scope before connecting.

**PATS.** The cluster's theft micro drives the MIL on the sheets, which hints the
two are entangled. With TritonECU as the PCM, PATS cannot immobilise anything —
start enable is ours — but the cluster may flash its theft indicator forever if
the handshake never comes. Capture step 7 so that is a decision rather than a
surprise.

## Tools

The board's own front end — DRV8837 H-bridge TX, TLV7031 comparator RX, per
[`review-scp-chain.md`](review-scp-chain.md) — is the right instrument, because
Phase 0 then validates the hardware that ships. An STN2120-based sniffer is
worth having as a cross-check: if the two disagree, the front end is the suspect.

Avoid cheap ELM327 clones. J1850 PWM is the mode they implement worst, and a
clone that silently drops frames looks exactly like a quiet bus.
