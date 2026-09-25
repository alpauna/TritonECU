# SCP scanner schematic — review

Against `schematics/SCP-Schematic-V1.zip`, three pages, 2026-09-25.

## Fixed since the first draft

**The front-end RC was comparable to the bit time.** `100k/100k` gives a 50 kΩ
Thevenin source, and the original `MM3Z3V3BW` clamps are *high-capacitance*
parts — a 3.3 V zener runs 200–600 pF:

| | RC | 8 µs pulse reaches | 16 µs reaches |
|---|---|---|---|
| MM3Z3V3BW, ~350 pF | 17.5 µs | **37 %** | 60 % |
| **BAT54S, ~23 pF total** | **1.15 µs** | **99.9 %** | 100 % |

The differential arrangement survives *symmetric* filtering — both inputs are
filtered alike and a matched delay cancels. What it does not survive is the two
pulses settling to **different amplitudes**, which puts the comparator crossing
at different fractions of full swing and distorts exactly the widths the rig
exists to measure.

Fixed with BAT54S rather than by dropping the divider, which keeps the
high-impedance tap: **35 µA** of bus loading instead of the 625 µA a 5.6k/5.6k
divider would have drawn. That matters on a live vehicle bus you do not own.

**The loopback sense was ambiguous and is now correct.** `H1` grounds the Bus−
divider, `H3` injects `LOOP` into Bus+ through 1 kΩ. Driving `LOOP` high puts
`+` above `−` and the output goes high — non-inverting, so the firmware's
8.000/16.000 µs calibration carries over unchanged.

**And it says so on the drawing:**

> *Strapped on Bench but must be removed when connected to vehicle. Both H1 and
> H3 should be open when on vehicle!!!*

That is the failure worth annotating — injecting a test pattern onto a live SCP
bus while the PCM is talking on it.

## C15 — confirmed on the clamp rail

**Confirmed: clamp-rail decoupling for transients**, which is the right place
for it and settles the only blocking question on this page.

It matters because an **LDO can only source, never sink**. When a transient
arrives down the 100 kΩ and the BAT54S upper diode dumps it into the 3.3 V rail,
that current has nowhere to go but the rail's capacitance. `C7` 22 µF and `C8`
10 µF have the *charge* to absorb it — 367 µA of injection for 100 µs moves a
32 µF rail by about 1 mV — but they are across the board with trace inductance
between, so they do not have the *bandwidth* for the edge. `C15` local to the
clamp takes the fast part; the bulk takes the energy.

The alternative was the one worth ruling out. On an **input** node instead:

```
50k Thevenin x 100 nF = 5 ms.  An 8 us pulse reaches 0.16%.
```

Not a degraded signal — no signal, presenting as a dead comparator rather than
as a filter.

## Verified correct

- **`GP2 = RX`, `GP3 = LOOP`** match the firmware. The loopback that validated at
  8.000/16.000 µs runs on this board unchanged.
- **Differential Bus+ vs Bus−** into the comparator, not a single-ended tap.
- **SD in SPI mode**: SPCS→CD/DAT3, MOSI→CMD, MISO→DAT0, SCLK→CLK, pull-ups on
  all five including the unused DAT1/DAT2.
- **`R10` 100 Ω + `D7` SMF3.3** on RX — series limit plus clamp into the Pico.
- **`D2` STTH112A** reverse protection on the OBD feed, and a buck + LDO so the
  Pico's own switcher is not sitting beside the GNSS front end.

## Still open

- **`3V3_EN` on the Pico socket.** With 3.3 V supplied externally the Pico's own
  regulator should be *disabled* — that pin wants grounding, not feeding.
- **`D3` SMAJ3.3A on the 3.3 V rail.** Its standoff is 3.3 V, i.e. exactly the
  rail, so it sits at the top of its leakage curve. Not wrong, but a 3.6 V part
  would idle cooler.
