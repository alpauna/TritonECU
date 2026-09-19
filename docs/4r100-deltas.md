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

> **[CONFIRM] whether the PCM actually decodes the 270 Ω, or only switch
> closure.** If it decodes it, TR3A wants an **ADC channel rather than a digital
> input** — one channel, and the ADS8588H has the range.
>
> Two reasons to think it may not matter: on the 4R70W, TR3A's other job is the
> **start signal**, where 270 Ω in series with a logic input is irrelevant. And
> the resistor may exist for the *start circuit's* benefit rather than the PCM's.
> **But this is exactly the kind of assumption that has been wrong twice today.**

## The DTR's other jobs — unchanged from the 4R70W

*"The DTR sensor completes the start circuit in Park and Neutral, the backup lamp
circuit in Reverse, and the neutral sense circuit (4WD only) when in Neutral."*

All three match what C182 showed on the 4R70W — starter control, reversing lamps,
and the `463 RD/WH` neutral sense to the GEM. **Same architecture, and the
`[MEASURE]` list does not grow.**
