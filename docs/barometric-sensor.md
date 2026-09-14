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

## Part: Infineon KP497 (KP497XTMA1)

**Datasheet:** [`Datasheets/infineon-kp497-datasheet-en.pdf`](Datasheets/infineon-kp497-datasheet-en.pdf)
— Rev 1.01, 2025-12-04.

This settles the temperature question that was the open item above.

| | |
|---|---|
| Range | **20–250 kPa** absolute |
| Accuracy | **±2 kPa** absolute, **±1 kPa** on differences |
| Temperature | **−40 to +105 °C** |
| Humidity | **0–100 % RH** |
| Qualification | **AEC-Q100 Grade 1**, ISO 26262 SEooC to **ASIL A** |
| Interface | I²C or 3-pin SPI |
| Supply | **2.5–3.6 V** |
| Autonomous current | **5.1 µA** at 300 ms intervals, 44 µA at 50 ms |
| Extras | z-axis accelerometer ±100 g, 3 kB NVM |
| Package | PG-DSOSP-14-84 |

### Why it fits this board specifically

**It is a 3.3 V part, so it belongs on the always-on rail.** VDD tops out at
3.6 V — this is not a 5 V device. That places it alongside the sleeping MCU on
the always-on domain, where its **5.1 µA autonomous draw is 0.5 % of the ~950 µA
sleep budget**. It can keep tracking ambient while the truck is parked, so
barometric pressure is already known at key-on rather than acquired after it.

**−40 to +105 °C and AEC-Q100 Grade 1** removes the mounting-location dependency
entirely. The BMP390/DPS368 class stops at +85 °C and would have forced a decision
about where the box lives; this does not.

### The trade: it is coarse for a barometer, and that is fine here

±2 kPa is **25× worse than a consumer barometer** like the BMP390. In useful
units:

| error | altitude equivalent | density error |
|--:|--:|--:|
| ±2 kPa absolute | ±166 m (**±546 ft**) | **2.0 %** |
| ±1 kPa on differences | ±83 m (±273 ft) | 1.0 % |

**The reason is the range.** Barometric pressure of interest spans 67–104 kPa —
only **16 % of this part's 20–250 kPa full scale**. It is a MAP-range sensor being
used as a barometer, and the accuracy follows from that.

**2 % density error is inside spark calibration margin**, and fuelling does not
use it at all on a MAF truck. So the coarseness costs nothing for the actual job.
It would be useless as an altimeter, which is not the job.

### The wide range is an asset, not just a compromise

250 kPa is **36 psia — 21.6 psi of boost**. The same part number, and the same
driver code, would serve as a **MAP sensor** if a manifold reference is ever
plumbed in. That is a genuine option kept open for the price of nothing.

### The accelerometer is not a gimmick

±100 g on z, 0.0625 g/LSB, ±2 g error. The real use is **rough-road detection to
suppress the misfire monitor** — OBD-II misfire diagnostics have to be inhibited
on rough roads because driveline shock reads as crank-speed irregularity, and the
usual workaround is inferring it from wheel-speed variance. A real accelerometer
measures it directly.

**[VERIFY]** the accelerometer's sampling bandwidth against the datasheet before
counting on that — rough-road content is a few Hz to tens of Hz, and the
autonomous-mode intervals quoted are 10 ms and slower.

It is **not** a knock sensor. Nowhere near the bandwidth, and the knock channel is
already designed.

### Two limits worth writing down

**The NVM is good for 100 write cycles per block.** 3 kB sounds like somewhere to
log, and it is not — it is for configuration and provisioning. Logging belongs on
the SD card.

**Configuration writes need −20 to +90 °C.** Narrower than the operating range, so
any field reconfiguration has to happen when the box is not hot.

**[VERIFY] availability.** The datasheet is Rev 1.01 dated December 2025, so this
is a new part. Check stock and lifecycle before committing the footprint — being
new is a different sourcing risk from being old, but it is still a risk.

## Recommendation

**Put the footprint down now, populate later.** A 14-pin SOP and two pads on an
existing bus cost little at layout time and are impossible to add afterwards.
Leave it DNP if the calibration never uses it.

**And vent the enclosure regardless of part choice.** No sensor fixes a sealed
box. That requirement is now recorded against the housing itself in
[`enclosure.md`](enclosure.md), along with the note that venting is better
practice anyway — a sealed box pumps moisture past its own seals — and that the
vent should be sited out of ram air, which biases the reading by 0.43 kPa at
60 mph.

It is **not needed to run** — the engine will start, idle and drive without it,
which is the standing test for whether something belongs in the current scope. It
earns its place because the marginal cost is a footprint.
