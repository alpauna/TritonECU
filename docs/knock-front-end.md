# Knock front end — differential charge amplifier

Next build after the VR board. The sensor is a **two-wire differential piezo** on
pins 57 (YEL/RED) and 32 (DK GRN/VIO), and the front end is common to both
detection routes (HIP9011-class IC or DSP on the F767), so it is worth building
before that choice is made. See
[`oem-connectors.md`](1999-Ford-F150-4wd-5.42v/oem-connectors.md) for the routes.

---

## Why charge mode and not voltage mode

A piezo is a charge source with its own capacitance — around 1 nF, **measure the
real one**. At 6 kHz that is a 26.5 kΩ source impedance, and it sits at the end of
a metre or two of harness.

Read as a **voltage**, the cable capacitance appears in parallel with the sensor
and divides the signal down. A metre of harness is maybe 100 pF against the
sensor's 1 nF — a 10 % error that **changes if the harness is rerouted**.

Read as **charge**, both sensor terminals are held at a virtual ground, so the
cable capacitance never sees a voltage swing and contributes nothing. Sensitivity
stops depending on how the loom was dressed.

**Schematic:** [`Schematics/knock-front-end-schematic.md`](Schematics/knock-front-end-schematic.md)
— net list, BOM and layout notes, ready to transcribe.

## Topology — and it fills a quad exactly

```
        pin 57 ──┬── Cf ──┐
                 │        │
                 └─[A1]───┴──┐          Cf, Rf in parallel on each leg
                  (virtual   │          both inputs held at VMID
                   ground)   ├──[A3]──► to ADC / knock IC
        pin 32 ──┬── Cf ──┐  │          difference + anti-alias
                 │        │  │
                 └─[A2]───┴──┘
                              [A4] ──► VMID buffer, from the 2.5 V MAX6070
```

| | |
|---|---|
| **A1, A2** | charge amps, one per leg. Charge leaves one terminal and enters the other, so the outputs are equal and opposite |
| **A3** | difference amplifier, `2Q/Cf`, plus the anti-alias pole |
| **A4** | buffers a **dedicated 2.5 V reference** for this block to VMID — the ADC's reference is left alone |

**So yes to a quad — but it is already full.** The knock chain wants exactly four
amplifiers, and the fourth is not spare.

**A dedicated reference does not free A4 up.** It removes the loading concern, but
the buffer was never only about loading: `A3`'s reference leg is one arm of a
resistor bridge, and **CMRR depends on that bridge staying balanced**. Driving
`R8` from the reference IC directly puts the reference's output impedance in
series with that arm and unbalances it. The buffer stays.

## Do not share the package with other inputs

The question was whether to use a quad to pick up other inputs too. **No**, for
three reasons beyond the count:

- **Channels in one package share supply and substrate.** They are not isolated.
  Putting a slow sensor buffer next to a microvolt-sensitive kHz charge amp buys
  crosstalk into the one path that cannot tolerate it.
- **Layout pulls in opposite directions.** The knock path wants to be short and
  guarded, right where the sensor pair enters the board. Other analog inputs come
  from elsewhere on a 104-pin connector.
- **Op amps are cheap.** Separating them costs nothing now and is impossible
  later.

If other inputs do want buffering, **the narrowband O₂ sensors are the real
candidate** — their source impedance is high and rises sharply when cold. Give
them their own package near their own pins.

---

## Part: TLV9064-Q1

Quad, 10 MHz, rail-to-rail in and out, **CMOS input**, AEC-Q100 Grade 1, 1.8–5.5 V.

**The CMOS input is the requirement, not a preference.** `Rf` is 1 MΩ, and input
bias current flows through it as a DC offset:

| input stage | I_bias | offset across 1 MΩ |
|---|--:|--:|
| **CMOS (TLV9064)** | 10 pA | **0.01 mV** |
| bipolar | 100 nA | **100 mV** |

100 mV of drifting offset on a 5 V single supply, on a stage whose whole job is
resolving small signals around a 2.5 V midpoint, is not recoverable by trimming —
it moves with temperature.

Bandwidth is not the constraint: a gain of ~10 flat to 25 kHz needs 250 kHz, and
10 MHz is 40× that. If 36 V robustness is wanted instead, **OPA4197-Q1** is the
same shape of part at higher supply and higher cost.

## Component values

Starting point, with the sensor assumed at 1 nF:

| | value | sets |
|---|--:|---|
| `Cf` | **220 pF** | sensitivity, `Vout_diff = 2Q/Cf` |
| `Rf` | **1 MΩ** | DC path for bias current, and the high-pass corner |

That gives a **723 Hz high-pass** and a noise gain of 5.5, with roughly **0.9 V
differential** for a sensor producing 100 mV open-circuit.

The high-pass is doing real work: engine block vibration is strongest at low
frequency, so a corner around 700 Hz rejects mechanical noise well below the
5–6.5 kHz knock band while leaving it untouched.

| `Cf` | high-pass | noise gain | out for 100 mV oc |
|--:|--:|--:|--:|
| 100 pF | 1592 Hz | 11.0 | 2.00 V |
| **220 pF** | **723 Hz** | **5.5** | **0.91 V** |
| 1 nF | 159 Hz | 2.0 | 0.20 V |

### Three things that will bite

**`Cf` must be C0G/NP0.** Gain is `Q/Cf`, so the feedback capacitor *is* the
calibration. An X7R part drifts ±15 % over temperature and loses capacitance
under bias — knock sensitivity would wander with under-hood temperature, which is
the worst possible way to lose it.

**Guard the summing nodes.** They are megohm-impedance. Surface leakage across a
dirty or fluxy board shows up directly as drift; a guard ring at VMID around each
inverting input costs nothing.

**The floating source needs a DC return, and here it gets one for free.** A
capacitive source into a high-impedance input has no path for bias current and
drifts to a rail. In this topology `Rf` provides it on each leg — which is part of
why the charge-amp form is the right one, not just a sensitivity choice.

## Anti-alias

Target a **25 kHz corner** on A3 and sample at **200 kSPS** on the F767's own ADC.
Two poles then give about −24 dB at the 100 kHz Nyquist. If the DSP route shows
aliased content, add a third pole rather than slowing the sampler — the MCU's ADC
reaches 2.4 MSPS and the headroom is free.

## [MEASURE] before committing values

- **Sensor capacitance.** Everything above scales off the assumed 1 nF.
- **Open-circuit output under real knock.** Sets whether `Cf` should be 100 or
  470 pF. Log it before fixing the gain.
