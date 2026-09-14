# Onboard barometric sensor

**Yes — and it is one of the cheapest additions on the board, because it needs
nothing from the harness.**

---

## This truck has no pressure sensor at all

The EEC-V pinout carries **DPFE** (EGR differential pressure, pin 65) and nothing
else. There is no MAP and no BARO input. The factory MAF strategy either infers
barometric pressure or assumes sea level.

So this is **new capability, not duplication** — and the only absolute pressure
reference the system would have.

## It needs no harness change, which is the real argument

Barometric pressure is just **ambient static pressure**. Unlike MAP it needs no
vacuum line, no connector, no cavity in the 104-pin shell, and no wire. It is a
part on the board and nothing else.

That sits exactly inside the project's standing principle: **leave the factory
harness alone**. Capability that costs zero harness modification is the cheapest
kind there is.

## What it actually buys — and what it does not

```
altitude   pressure   density
    0 ft   101.3 kPa    1.000
  3000 ft   90.8 kPa    0.896
  5000 ft   84.3 kPa    0.832
  8000 ft   75.3 kPa    0.743
```

Weather alone moves it about **8 %** at fixed altitude (96–104 kPa).

**It does not help fuelling.** A MAF measures *mass* directly, so the fuel
calculation is already correct at altitude — that is the entire point of mass
airflow. Anyone arguing BARO is needed for fuel on a MAF truck is describing a
speed-density system.

**It does help spark.** At 5000 ft the charge is **17 % less dense**, so peak
cylinder pressure and knock tendency fall with it. Without a barometric reading
the calibration must assume the worst case everywhere — which means **advance
left on the table at altitude**, or knock risk at sea level. With the knock
channel arriving too, the two work together: BARO sets the expected margin, knock
detection confirms it.

**It does not give speed-density limp-home.** That needs *manifold* pressure, and
this truck has no MAP either. A BARO sensor is a plausibility check on the MAF,
not a replacement for it.

## Digital, not analog — the ADC is full

All eight AD7606B channels are allocated
([`adc-front-end.md`](adc-front-end.md)), and the eighth is spent on VREF sense
for ratiometric correction, which is not negotiable.

Barometric pressure changes on the timescale of weather and hills. It has no
business on a 200 kSPS simultaneous-sampling converter. **Put it on I²C or SPI**,
read it once a second, and it costs **no analog channel at all**.

## The one thing that makes or breaks it: vent the enclosure

**A sealed box measures its own temperature, not the weather.** Trapped air
follows the gas law, so a sealed enclosure's internal pressure tracks under-hood
heating and tells you nothing about altitude.

The sensor is only as good as the vent. A **Gore-type vent membrane** — standard
on automotive housings, and wanted anyway to stop the enclosure breathing
moisture through its seals — makes the internal pressure track ambient while
keeping water out.

**Heat is a parts problem, not an accuracy problem.** Once vented, internal
pressure equals external pressure regardless of how hot the box gets. Temperature
only decides what the sensor must be *rated* for.

## Part selection

| | |
|---|---|
| **[VERIFY] first** | the ECU's mounting location and its ambient temperature |
| ≤ 85 °C | **BMP390** (Bosch) or **DPS368** (Infineon) class — I²C/SPI, few-pascal resolution, ~2 × 2 mm |
| under-hood hot | needs an automotive-grade part; **MPXAZ6115A** (NXP) is the classic −40 to +125 °C option, but it is **analog** and would cost an ADC channel — displacing something slow onto the MCU's own ADC |

Most precision digital barometers stop at +85 °C, so the mounting location
decides the part. Confirm the rating against the datasheet rather than the
marketing table.

**Do not use its temperature output as ambient or IAT.** It sits next to warm
electronics inside a box. It reads the board, not the air. The truck already has
a real IAT sensor.

## Recommendation

**Put the footprint down now, populate later.** Two pads on an existing bus and a
2 × 2 mm land cost nothing at layout time and are impossible to add afterwards.
Leave it DNP if the calibration never uses it.

It is **not needed to run** — the engine will start, idle and drive without it,
which is the standing test for whether something belongs in the current scope. It
earns its place because the marginal cost is a footprint.
