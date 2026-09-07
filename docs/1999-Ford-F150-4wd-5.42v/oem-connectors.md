# OEM connector reference — 1999 F-150 4WD, 5.4L 2V

Running catalogue built from the factory schematics, one connector at a time.
Ford circuit numbers are given because they are the stable identifier across
the wiring diagrams; wire colours are the field identifier.

---

## C141 — Mass Air Flow (MAF) sensor

Source: `oem-maf-pins.png`

| Pin | Circuit | Colour | Function |
|---|---|---|---|
| 1 | — | — | not used |
| 2 | 361 | RD | Power — hot in START or RUN |
| 3 | 570 | BK/WH | Ground |
| 4 | 968 | TN/LB | **MAF signal return** |
| 5 | 967 | LB/RD | **MAF signal out** |
| 6 | — | — | not used |

### What this tells the design

**1. The MAF is a differential measurement, and that settles the ADC choice.**

The sensor has a dedicated **signal return** (968) that is a separate circuit
from its **power ground** (570). Ford runs it that way because the MAF's hot-wire
supply current — hundreds of milliamps, varying with airflow — drops millivolts
across the power ground on its way back to the ECU. Measure the signal against
local ECU ground and that drop lands directly on the reading, as an airflow-
dependent error. Measure it against 968 and the error cancels.

This is exactly what the AD7606C-16's true differential bipolar inputs do, and
it is the strongest single argument for it over the P4's own ADC:

- **AD7606C:** 967 → +IN, 968 → −IN. The ground offset is common-mode and is
  rejected. 16-bit, and the ±10 V range covers the full 0–5 V swing with margin
  for transients.
- **P4 native ADC:** single-ended against chip ground only. There is no way to
  use 968 at all, so the ground-offset error is unrecoverable — and it is worst
  at high airflow, which is where fuelling errors hurt most.

Do not tie 968 to chassis ground at the ECU. It is a sense line, not a ground.

**2. There is no IAT in this connector.**

Pins 1 and 6 are explicitly unused, so this is a MAF-only sensor — not one of
the Ford 6-pin MAF/IAT combination units where IAT sits on 1 and 6. **Intake air
temperature is a separate sensor on this truck** and needs its own analog
channel and its own NTC pull-up. Previously carried as an assumption in the
target document; now confirmed from the schematic.

**3. Power is switched, not constant.**

Circuit 361 is hot in START or RUN. The MAF is dead with the key off, so the
ECU must not treat a zero reading at key-on as a sensor fault before the
run/start line is live.

### Wiring to the ECU

| OEM circuit | Goes to | Notes |
|---|---|---|
| 361 (RD) | switched 12 V feed | from the ECU's own main relay |
| 570 (BK/WH) | power ground | star point, not the analog ground |
| 967 (LB/RD) | AD7606C channel +IN | |
| 968 (TN/LB) | AD7606C channel −IN | sense return — keep separate |
