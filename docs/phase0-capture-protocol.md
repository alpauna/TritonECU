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

### Choosing which sensor to unplug — quieter is better

The point of the transition capture is that **only the MIL changes**. A fault
that also changes how the engine runs moves half the bus with it, and then the
MIL bit is buried among genuine data changes.

| Unplug | Sets a code | Side effects at idle | Verdict |
|---|---|---|---|
| **IAT** | yes, promptly | PCM substitutes a default air temp; fuelling barely moves | ⭐ **quietest** |
| **EGR / DPFE** | yes | EGR is closed at idle anyway | ⭐ also good |
| HO2S | yes | drops to open loop, fuelling shifts | usable, noisier |
| **TPS** | yes, promptly | **PCM's whole air/fuel and shift strategy changes** | works, but noisy — see below |

**TPS is a poor first choice and a good second one.** The 4R70W sheet lists TP as
an input to *"EPC pressure, shift and torque converter clutch scheduling"*, so
unplugging it moves idle, fuelling and the transmission at once. The MIL bit will
be in there, but so will a dozen other changing bytes.

Where it *is* useful is as a deliberate second run: if TP is broadcast on SCP,
pulling the sensor pegs those bytes, which helps identify them. Do that as its
own experiment, not as the MIL capture.

> ⛔ **Do not drive with the TPS unplugged.** Shift scheduling and EPC line
> pressure both depend on it.

**Suggested order on the 2001:**

1. **Baseline** — no faults, engine idling, five minutes. This is the reference
   every later diff is taken against, and it exists only because this truck
   currently has no codes.
2. **RPM sweep in park** — tach bytes, against that baseline.
3. **Pull the IAT while idling** — the clean MIL transition.
4. Reconnect, clear, confirm the lamp goes out and the bus returns to the
   baseline pattern. *A transition that only works in one direction has not been
   identified.*
5. Optionally, pull the TPS as a separate run to find the TP bytes.

Record which sensor was pulled, and when, in the log notes. Six months from now
the capture will be unreadable without it.

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

## Capturing more than one truck

Three vehicles are available — a **2001** with no codes, a **2003** with a
standing EGR code, and the **1999** being converted. Capturing more than one is
worth the time, and what it buys depends on how they come out:

| Outcome | Means |
|---|---|
| MIL bit in the same place on 2001 and 2003 | The format is stable across the span. Raises confidence for the 1999 — still not proof |
| They differ | **The year-variation hypothesis is confirmed**, which is the leading explanation for the Chilton/EVTM disagreement in [`source-conflicts.md`](source-conflicts.md) |
| A header exists on one and not the other | Architecture, not data. Note it and move on |

### The sharper version: make one truck look like the other

The 2003 already stands with a code set; the 2001 stands clean. That is a
**between-vehicle** difference of the same nominal state as the 2001's
**within-vehicle** transition.

So: capture the 2001 clean, induce the IAT fault, and capture it again. The bytes
that **change on the 2001 and also differ from the 2003's clean-state values in
the same direction** are the strongest MIL/DTC candidates available — two
independent lines of evidence crossing at one byte.

It may also find the **DTC count or status** field, which a single-vehicle
transition cannot isolate on its own.

### The timing constant is a different target, and two engines check it

Separate from byte-hunting: the same capture rig can settle
`CKP_GAP_TO_TDC_DEG` electrically, by logging **commanded spark advance from the
bus** alongside **gap-to-spark from the VR channels**:

```
CKP_GAP_TO_TDC = gap-to-spark + advance_reported
```

That holds at *any* operating point, so it averages over a hundred of them
rather than resting on one careful reading with a degree tape. See
[`measurements-wanted.md`](measurements-wanted.md).

**Two engines make it check itself.** A **5.4** and a **4.6**, both 2V modular,
both EEC-V. They share the 36-1 wheel, so `key_to_gap = 5.00°` — the wheel's
half — is common to both. What need *not* be common is the other half: where the
CKP sensor bolts is a **block** property, and these are different blocks.

| Outcome | Means |
|---|---|
| The two agree | It is a **family constant**. Trust it for any 2V modular |
| They differ | It is **engine-specific**. The 5.4 is the number that matters — it is the truck being converted; the 4.6 was the control |

Either result is worth having, which is the mark of a measurement worth taking.

**And the 4.6 validates the decoder, not just the constant.** Two PCMs of the
same family broadcasting the same PIDs: if the decoder reads both consistently,
that is evidence about the *decoder*. If it reads one cleanly and garbles the
other, the fault is in the decode rather than in either truck — a distinction a
single vehicle cannot offer.

### Discipline, or the diff is noise

- **Run the identical scripted states on each truck.** Same idle duration, same
  RPM points, same order. A diff between a five-minute idle and a two-minute one
  is mostly about duration.
- **Record the metadata in the log header**: year, engine, transmission, 2WD/4WD,
  odometer, and which sensor was pulled. A 4.6 and a 5.4, or a 4R70W and a
  4R100, put different modules on the bus and different values in the frames.
- **Do not chase the bytes that are supposed to differ**: VIN and module IDs,
  calibration IDs, odometer-derived values, engine hours, adaptive fuel trims.
  Those differ between any two trucks and will eat an evening.
- **Different calibrations can change content without changing format.** Two
  trucks disagreeing on a value is not evidence the field moved.

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
