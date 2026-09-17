# SCP / J1850 PWM chain review — pre-schematic

Review of the SCP front end now that it has
[moved onto the v1 board](v1-scope.md), against the design in
[`f150-1999-target.md`](f150-1999-target.md) §5.3 and its source,
`~/Claude/LxScanner/docs/j1850_multiprotocol.md`.

```
STM32 TX_P ─┐
STM32 TX_N ─┴─► DRV8837 H-bridge ─► SCP+ / SCP−  (EEC-V 16 / 15)
                    ▲                    │
                 nSLEEP              100k:100k divider
                                          ▼
STM32 RX ◄────────────────────── TLV7031 comparator @ 3.3 V
```

**The single most important thing about this chain is where it came from.** The
reference is a **USB-powered scan tool that plugs into the DLC**. We are putting
it in a harness, on a bus we transmit on continuously. Three of the four
findings come straight out of that difference.

---

## 1. IMPORTANT — `nSLEEP` is a fourth pin, and it is not optional

Every pin count in the tree says **three**: `pin-budget.md` has
*"J1850: TX_P, TX_N, RX | 3"*, and `v1-scope.md` repeats *"only three GPIOs and
a transceiver."*

The reference is explicit that the DRV8837 has a fourth control:

> `nSLEEP`/enable pin: **LOW = Hi-Z/RX-only, HIGH = driver enabled**

On a point-to-point scanner that is a nicety. **On a multi-master bus it is the
mechanism by which you release the bus** — without it the H-bridge drives the
lines whenever it is powered, and no other node can talk.

**Four pins, not three.** The budget absorbs it without comment; the count being
wrong is the problem, not the pin.

---

## 2. IMPORTANT — the H-bridge has no arbitration story, and an ECU is not a scanner

J1850 PWM is **multi-master CSMA/CD with bitwise arbitration**: nodes monitor
the bus while transmitting and the loser backs off. That requires a driver where
one node can **override** another — dominant over recessive.

**A push-pull H-bridge cannot be overridden.** Two nodes driving opposite states
short into each other through their output stages. The reference works anyway
because a **scan tool transmits a request and then listens** — contention is
rare and brief.

**An ECU on this bus is a continuous periodic transmitter**, sharing it with the
cluster, the GEM and anything a technician plugs in. Collisions stop being
exceptional and become routine.

The reference carries its own warning, which now reads differently:

> *"PWM IMPLEMENTATION IS EXPERIMENTAL AND MAY REQUIRE FIRMWARE OR HARDWARE
> TUNING FOR SPECIFIC VEHICLES."*

**This is the risk that justifies Phase 0 existing**, and it should be Phase 0's
explicit objective rather than a hoped-for side effect:

> **[PHASE 0]** With the OEM PCM still installed and transmitting, **transmit
> from our node into live traffic** and confirm arbitration behaves — not merely
> that we can *listen*. Listening proves the RX path. It proves nothing about
> whether we can share the bus.

A likely mitigation, if it does not: drive `nSLEEP` **within the bit period** so
the stage presents high-impedance during the window where arbitration is
resolved, making it behave as open-drain. That is firmware, and it is why
`nSLEEP` being a real pin (finding 1) matters beyond bookkeeping.

---

## 3. IMPORTANT — the TX outputs face the harness, and the part is low-voltage

The DRV8837's `OUT1`/`OUT2` connect **directly to SCP+ and SCP−**, which run the
length of the truck. The reference runs its `VM` from **5 V**, and the DRV8837
family is a low-voltage motor driver — its supply and output ratings are in the
**single digits**, not battery territory.

`harness-protection.md` currently says of this bus:

> *already has its own protection network in the transceiver design*

**That claim inherits a scan tool's threat model.** A scanner sees the DLC, on a
short cable, briefly. An ECU sees a harness that can chafe, and a
short-to-battery on SCP+ puts 14 V onto a driver output rated for far less.

**This is the same pattern as the VREF blind spot** —
[`review-vref-chain.md`](review-vref-chain.md) — and the same one the
[protection sweep](review-protection-sweep.md) went looking for: protection
specified against the expected fault, not against the harness.

> **[CONFIRM]** the DRV8837's `VM` and output absolute maximums, then decide:
> series resistance ahead of the outputs, a clamp, or a different driver. The
> 100 kΩ series resistors already protect the **RX** side; the **TX** side has
> nothing, because a motor driver is meant to drive a motor, not a harness.

---

## 4. Do not copy the upstream reference's RX divider — it has a known bug

`j1850_multiprotocol.md` records a **real functional defect** in the original
OpenJ1850 circuit, found and fixed during that board's bring-up:

> the original 10k:100k input divider only attenuated to ~91 %, so a normal ~5 V
> PWM HIGH landed around **4.5 V** at the comparator — **over absolute max
> during ordinary bit reception**, not just during faults.

TLV7031's input abs-max is only V<sub>CC</sub> + 0.3 V ≈ **3.6 V** at 3.3 V.
The fix is a symmetric **100 k : 100 k** divider, putting a 5 V bus HIGH at
**2.5 V**.

There is a second trap recorded alongside it: the reference's
`R_PWM_P_BIAS` goes to **3.3 V, not ground**. That was harmless at the original
10:1 ratio and becomes destructive at 1:1 — it pulls half the node instead of a
tenth.

**Carry the corrected values, not the reference schematic.** This is the most
likely way to introduce a known-and-already-solved bug into a new board.

---

## 5. Checked and clear

| | |
|---|---|
| **Bus polarity** | The reference warns polarity varies and to swap DLC pins 2/10 if nothing decodes. **Not a risk here** — this truck is documented: EEC-V **pin 16 = SCP+** (TAN/ORG, circuit 914), **pin 15 = SCP−** (PNK/LT BLU, 915), matching DLC pins 2 and 10 |
| **One connection serves both jobs** | The DLC and the cluster are the same bus, so wiring to EEC-V 15/16 reaches a scan tool *and* the cluster |
| **Bit timing** | 41.6 kbps is a 24 µs bit. Against a 216 MHz STM32F767 with hardware capture/compare, unremarkable |
| **Wake-on-bus falls out for free** | The **5 V rail is gated** but **3.3 V is always on**, so in sleep the DRV8837 is unpowered (bus released) while the TLV7031 still receives. A scan tool plugging in can wake the ECU — a capability, not a compromise, and it comes from the [always-on domain](always-on-domain.md) rather than from anything added here |
| **Supply rails** | PWM needs no boost. The reference's +7 V rail is for **VPW**, the GM flavour, which this truck does not use |

---

## Summary

| # | Finding | Action |
|---|---|---|
| 1 | `nSLEEP` uncounted — every pin count says three | **four pins**; it is how the bus is released |
| 2 | H-bridge has no arbitration mechanism; ECU duty cycle ≠ scanner's | make **transmitting into live traffic** an explicit Phase 0 objective |
| 3 | TX outputs face the harness on a low-voltage driver | **[CONFIRM]** abs-max, then protect or replace |
| 4 | Upstream reference has a known RX abs-max bug | carry the **corrected** divider, not the reference |

Findings 2 and 3 are the same observation in two places: **the reference design
was validated as a scan tool, and we are using it as a node.** Its warning about
being "experimental" was written about *vehicle variation*; for us it is also
about *role*.
