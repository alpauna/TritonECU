# 4R100 — what differs, now that the board is built for it

Read from
[`1999-Ford-F150-4wd-5.42v/4R100-ATSG-Service-Manual.pdf`](1999-Ford-F150-4wd-5.42v/4R100-ATSG-Service-Manual.pdf).
The board is built for the 4R100 and tested on the 4R70W —
[`review-vr-channel-count.md`](review-vr-channel-count.md).

## ✅ The driver sizing does not move, and the 4R70W stays the worst case

| Solenoid | 4R70W | **4R100** | Worst-case R | I at 14.4 V |
|---|---|---|--:|--:|
| SSA / SSB | 20–30 Ω | 20–30 Ω | 20 Ω | 0.72 A |
| TCC (PWM) | 10–16 Ω | **10–20 Ω** | 10 Ω | 1.44 A |
| EPC | **2.48–5.66 Ω** | 3.0–5.0 Ω | **2.48 Ω** | 5.81 A |
| **Coast clutch** | *none* | **20–30 Ω** | 20 Ω | **0.72 A** |

- **TCC** bottoms out at 10 Ω on both — the 1.44 A figure and the
  pour-the-copper recommendation stand unchanged.
- **EPC**'s 4R100 floor is **3.0 Ω, higher than the 4R70W's 2.48 Ω**, so the
  existing worst case already covers both.
- **CCS** is an ordinary shift-solenoid-class load. Nothing new to size.

**Every driver already chosen covers the 4R100.**

> The 4R100 also lists an **on/off TCC at 20–30 Ω** as an alternative to the PWM
> one. We PWM it, so 10–20 Ω is the row that applies.

### One consequence: the third clamping solenoid comes back

[`output-drivers.md`](output-drivers.md) was corrected from *"three on/off shift
solenoids can clamp"* to **two** when CSS turned out not to exist on a 4R70W.
**On a 4R100 it is three again** — SSA, SSB and the coast clutch. TCC and EPC
still recirculate through their freewheel diodes.

## ⚠ The speed sensors are a different story

| Sensor | 4R70W | **4R100** |
|---|---|---|
| OSS | 450–750 Ω | **781–1979 Ω** |
| TSS | *not specced* | **496–1244 Ω** (PTO) · **781–1979 Ω** (non-PTO) |

**Up to 2.6× the source impedance.** Against the MAX9926 network's balanced
5 kΩ legs that is **28 % of the signal dropped in the sensor**, against 7 % for
CMP's measured 371 Ω.

A higher-resistance VR coil usually has more turns and therefore puts out *more*
signal, so this may cancel entirely — **but that is an assumption, not a
measurement.**

> **[CONFIRM]** the MAX9926 input network against a ~2 kΩ source. The part is
> adaptive and will very likely cope; the point is that the network was sized
> against 371 Ω and has never been checked at five times that.

**The ATSG manual also confirms why the channel was worth adding:** *"The PCM
uses the TSS sensor signal to control EPC pressure and TCC strategy."*

## ⚠ TR3A is not a plain switch — there is a 270 Ω internal resistor

> *"The DTR sensor also opens or closes a set of four different switches that are
> monitored by the PCM… notice that **three positions read a 270 Ω resistor**,
> that is also internal."*

Testing is specified **across DTR pins 2 and 3** — signal return and **TR3A**.
So on the 4R100, TR3A appears to be **resistively coded**: open, short, or
270 Ω, depending on selector position.

**This design treats TR as four *digital* inputs**
([`pin-budget.md`](pin-budget.md)). A digital input cannot distinguish 0 Ω from
270 Ω unless the pull-up is chosen to make the difference a valid logic level —
and with a 10 kΩ pull-up to 5 V, 270 Ω gives **0.13 V** against a short's 0 V.
Both read as a low.

### ✅ CONFIRMED — the 4R100 handles the range switch differently. TR3A becomes an analog input.

**Three states on one wire: open, 270 Ω, short.** A digital input cannot see the
middle one — with a 10 kΩ pull-up, 270 Ω reads 0.087 V against a short's 0 V, and
both are a logic low.

| Pull-up | Open | 270 Ω | Short | Separation | I when shorted |
|--:|--:|--:|--:|--:|--:|
| 1 kΩ | 3.30 V | 0.702 V | 0 V | 871 LSB | 3.3 mA |
| **2.2 kΩ** | 3.30 V | **0.361 V** | 0 V | **448 LSB** | **1.5 mA** |
| 4.7 kΩ | 3.30 V | 0.179 V | 0 V | 223 LSB | 0.7 mA |

**2.2 kΩ.** 360 mV between the middle state and a short — 450 counts on a 12-bit
ADC, nowhere near marginal — and only 1.5 mA through a harness switch. A 270 Ω
pull-up would centre the middle state at mid-rail but draws **12 mA** for no
benefit.

> Harness-facing, so it keeps the usual series resistance and clamp. **The series
> resistor adds to the measured value** — 1 kΩ in series makes the middle state
> read 1270 Ω. That is a calibration constant, not a problem, but it has to be in
> the firmware's thresholds rather than assumed away.

**Budget:**

| | |
|---|---|
| Internal ADC | 15 used of 18 → **16 of 18**, two spare |
| **Moving all four TR to analog** | 19 of 18 — **one over. Do not** |
| Pin count | **unchanged** — TR3A was already one of the seven conditioned inputs; it just has to land on an **ADC-capable** pin |

**Only TR3A is resistively coded.** The ATSG manual tests TR1 across pins 2 and 4
as plain continuity, so **TR1, TR2 and TR4 stay digital**.

### ⭐ And it makes the input transmission-agnostic

A 4R70W's plain switches read **open or short**. A 4R100's read **open, 270 Ω or
short**. **Both decode in firmware off the same pin, with no hardware change** —
which is precisely what "build for the 4R100, test on the 4R70W" is supposed to
buy.

## The DTR's other jobs — unchanged from the 4R70W

*"The DTR sensor completes the start circuit in Park and Neutral, the backup lamp
circuit in Reverse, and the neutral sense circuit (4WD only) when in Neutral."*

All three match what C182 showed on the 4R70W — starter control, reversing lamps,
and the `463 RD/WH` neutral sense to the GEM. **Same architecture, and the
`[MEASURE]` list does not grow.**
