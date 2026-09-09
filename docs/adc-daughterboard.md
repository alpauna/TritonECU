# ADC daughterboard

**Decided 2026-09-09.** The AD7606C-16, its reference and the analog front end
move to a separate board, joined to the carrier by a board-to-board connector.

## Be honest about which argument justifies it

**Not proximity.** "The MAX6070 must be close to REFIN" is solved by placing
them next to each other on one board. That constraint is real — a 30 mm OUTF run
puts a 514 kHz resonance inside the reference's feedback loop, see
[`always-on-domain.md`](always-on-domain.md) — but it does not need a second
board.

**Two things do justify it:**

1. **Analog ground plane control.** This board low-side switches **eight
   ignition coils**. Sharing a plane between that and a 16-bit converter is the
   hardest mixed-signal problem in the design, and physical separation is the
   most reliable answer available — more reliable than plane splits, guard
   traces or careful placement, all of which depend on getting the return paths
   right by inspection.
2. **Iteration.** [`carrier-board.md`](carrier-board.md) already makes this
   argument for the carrier: *"most first-board mistakes are in the analog and
   driver sections anyway."* The analog front end is the part most likely to
   need revision and the part where mistakes are subtle rather than obvious —
   a bad reading looks like a bad sensor. Respinning a small board beats
   respinning the main one.

## The trap: the analog signals must not traverse the noisy board

**A daughterboard buys nothing if the sensor inputs still run past the coil
drivers to reach it.** That would add a connector without removing the noise
path.

So the layout question that decides whether this works is **where the analog
harness pins land**:

| Arrangement | Verdict |
|---|---|
| Harness → carrier connector → long traces past the drivers → daughterboard | **defeats the purpose** |
| Harness → carrier connector, **daughterboard mounted directly over that region** | **the practical answer** |
| Harness → daughterboard's own connector | cleanest electrically, two harness entries |

**Place the analog input pins of the EEC-V connector and the daughterboard
footprint adjacent**, so the traverse on the carrier is a few millimetres of
short, direct trace on the far side from the drivers. Decide this before the
carrier's placement is fixed — it is not something to retrofit.

## What goes on it

| On the daughterboard | Why |
|---|---|
| **AD7606C-16** + REFIN caps | the reason for the board |
| **MAX6070** + C<sub>FILTER</sub>, input RC, OUTS tap | must be within ~10 mm of REFIN |
| **Input scaling and protection** for every analog channel | the dividers and clamps belong with the converter, not across a connector |
| **MAX9926 ×2** (crank and cam VR) | small differential signals; losing them stops the engine. Their outputs are comparator-level and cross a connector safely |
| Local analog rail decoupling, after the ferrite | |

| Stays on the carrier | Why |
|---|---|
| MCU, SD, buses | digital |
| All switchers | the noise source |
| Injector and coil drivers | the other noise source |
| 74HCT541, MCP23S17 | digital, and part of the driver chain |

## What crosses the connector, and what it costs

| Signal class | Risk |
|---|---|
| SPI + CONVST / BUSY / RESET / FRSTDATA | low — digital, moderate rate |
| MAX9926 outputs to timer inputs | low — comparator-level |
| 5 V analog, 3.3 V | low — DC, decoupled locally at both ends |
| **Analog sensor inputs** | **this is the one that matters** — see above |

**The ground tie is now connector inductance, not a plane stitch.** A single pin
is 5–20 nH. **Use many ground pins, interleaved between signals**, not a row of
grounds at one end — the return path wants to be adjacent to its signal.

## Mechanical

**A vehicle vibrates.** A daughterboard supported only by its connector is a
fatigue failure waiting to happen, and an intermittent ADC reads as a bad
sensor. **Standoffs at minimum two corners**, and prefer a connector rated for
vibration over a plain 0.1" header.

## What this defers

Nothing on the carrier. The power design in
[`always-on-domain.md`](always-on-domain.md) is unaffected — the 3.3 V and 5 V
rails simply appear on the connector instead of at a local pin. The reference's
placement constraint moves onto the daughterboard, where it is easy to satisfy.
