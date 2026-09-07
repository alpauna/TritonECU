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
| 3 | 570 | BK/WH | Sensor ground (PCM signal-return network) |
| 4 | 968 | TN/LB | **MAF signal return** |
| 5 | 967 | LB/RD | **MAF signal out** |
| 6 | — | — | not used |

### What this tells the design

**1. The MAF is a differential measurement, and that settles the ADC choice.**

The sensor has a dedicated **signal return** (968) that is a separate circuit
from the ground it runs on (570). Ford does that because the MAF's hot-wire
supply current — hundreds of milliamps, varying with airflow — returns on 570
and drops millivolts along it on the way back to the ECU. 968 carries no
current, so it is a true Kelvin sense of the sensor's own reference. Measure
the signal against local ECU ground and the 570 drop lands directly on the
reading as an airflow-dependent error. Measure 967 against 968 and it cancels.

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
| 570 (BK/WH) | ECU sensor-ground network | see the circuit 570 note below |
| 967 (LB/RD) | AD7606C channel +IN | |
| 968 (TN/LB) | AD7606C channel −IN | sense return — keep separate |


---

## C228 (BLACK) — Data Link Connector (DLC)

Source: `data-link-connector.png`

| Pin | Circuit | Colour | Function |
|---|---|---|---|
| 2 | 914 | TN/OG | **J1850 BUS (+)** |
| 4 | 57 | BK | Ground (chassis) |
| 5 | 570 | BK/WH | Ground (signal return) |
| 7 | 70 | LB/WH | **ISO 9141 link** |
| 10 | 915 | PK/LB | **J1850 BUS (−)** |
| 13 | 107 | VT | PCM input |
| 16 | 40 | LB/WH | Power (hot at all times) |

1, 3, 6, 8, 9, 11, 12, 14, 15 not used.

### What this confirms

**1. J1850 PWM, two-wire differential — as designed for.**

Both BUS (+) on pin 2 and BUS (−) on pin 10 are populated. That is Ford SCP:
**differential PWM at 41.6 kbps**. It also independently confirms why the
MC33390 cannot be used here — that part is single-wire VPWM and would only ever
touch pin 2.

The transceiver plan stands: DRV8837 driving TX_P/TX_N complementary into
914/915, TLV7031 comparator reading across them.

**2. There is also an ISO 9141 K-line (pin 7, circuit 70).**

Unexpected, and worth knowing before assuming J1850 is the whole story. Some
modules on this truck may answer on the K-line rather than SCP. It does not
change the ECU design — the PCM's own bus is J1850 — but if a module goes quiet
after the swap and is not on SCP, this is where to look. **[CONFIRM ON TRUCK]**
which modules, if any, actually use it.

**3. Pin 13 is a PCM input, not a bus line.**

Circuit 107 (VT) runs to the PCM. On Ford of this era pin 13 is normally the
self-test input used to command KOEO/KOER self-test — **[CONFIRM ON TRUCK]**
against the schematic before wiring it. Either way it is an input the
replacement ECU can choose to honour or ignore; it is not required for running.

**4. The DLC can power the Phase 0 sniffer.**

Pin 16 is hot at all times and pins 4/5 are grounds, so the bus-capture rig
needs no separate supply and no splicing — it plugs in like a scan tool. That
keeps Phase 0 completely non-invasive.

---

## Circuit 57 vs circuit 570 — two different grounds

The DLC carries both, on separate pins, and the distinction matters when the
PCM is replaced:

- **57 (BK)** — chassis/battery ground. High current, noisy.
- **570 (BK/WH)** — the **signal-return network sourced by the PCM**. Appears
  at the DLC *and* at the MAF (C141 pin 3), which is what shows it is a
  distributed sensor-ground net rather than a local ground at each device.

So circuit 570 originates at the PCM. **When the ECU is replaced, the new ECU
becomes the origin of 570.** It must not simply be strapped to chassis ground —
bonding it to chassis at more than one point puts engine-bay ground currents
through the sensor return network, which is exactly the noise the split was
designed to avoid. Bond 57 and 570 at a single star point inside the ECU.

**[CONFIRM]** how many sensors sit on 570 as more connector sheets arrive; two
data points establish the pattern but not its extent.
