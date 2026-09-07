# Battery sensing and alternator control

## First: the OEM PCM does not control the alternator

The EEC-V 104-pin pinout has **no generator, field, or charging pin**. The
generator's own connectors (C176–C178) appear in the engine bay component
locations, and nothing routes to the PCM for it.

That means the '99 F-150's alternator is **self-regulating** — a voltage
regulator integrated in the alternator, as Ford used before PCM-controlled
"smart charging" arrived on later platforms. Removing the PCM does not affect
charging at all.

**So ECU charging control is an addition, not a replacement.** Worth being
clear about, because the design implications are very different:

- **If the alternator keeps self-regulating** — nothing to do. Battery voltage
  is still needed for injector dead-time and coil dwell compensation, but only
  to ordinary accuracy.
- **If the ECU takes over charging** — that is a real upgrade with real
  benefits, and it makes battery voltage a **precision absolute measurement**.

Both are legitimate. The rest of this document covers the second case, because
it is the demanding one.

## Taking over charging changes the accuracy class

Every other analog input on this ECU is **ratiometric** — a TPS reports a
fraction of VREF, and the channel-7 VREF correction cancels absolute error
entirely. Battery voltage for charging control is different: it is an
**absolute** measurement against a real volt, and errors in it become errors in
delivered charging voltage.

The consequences are not subtle:

| Sustained charging voltage | Effect on a lead-acid battery |
|---|---|
| Above ~14.8 V | gassing, water loss, plate corrosion |
| 14.2 – 14.7 V | correct, temperature-dependent |
| Below ~13.8 V | chronic undercharge, sulfation |

Holding ±0.1 V at 14.4 V is **±0.7 %**, end to end, across temperature and
years. That is a tighter requirement than anything else on the board.

### Use the ADR4525 as an external ADC reference

The AD7606 defaults to its internal 2.5 V reference, selected by tying **REF
SELECT (pin 34) high**. Tie it **low** instead and feed **REFIN/REFOUT (pin 42)**
from an external precision reference.

The **ADR4525** already in `~/Documents` is exactly that part: 2.5 V,
±0.02 % initial accuracy, 2 ppm/°C. Against a ±0.7 % budget, that makes the
reference's contribution negligible instead of a dominant term.

This is the single highest-value change if charging control is adopted, and it
costs one IC and a decoupling capacitor.

### The divider is the other half

- **0.1 % resistors**, and more importantly **low temperature coefficient** —
  25 ppm/°C across a 100 °C swing is 0.25 % of drift on its own. 10 ppm/°C
  parts are worth the difference here.
- **Both resistors should be the same type in the same package**, so their
  tempcos track and partially cancel in the ratio.

### Calibrate once, then rely on stability

Initial tolerance can be measured out; drift cannot. So:

1. At build, apply a known voltage measured with a good meter.
2. Store gain and offset in `/config.json` — the config already round-trips to a
   PC, which is exactly what this needs.
3. From then on, only *drift* matters — which is why the precision reference and
   low-tempco divider earn their place.

This handles the ADC's own gain error too, which would otherwise be an
uncharacterised term.

## Where you sense matters as much as how well

Voltage at the ECU is not voltage at the battery. Harness resistance between
alternator, battery and ECU means regulating to 14.4 V *at the ECU* delivers
something else at the battery — and the error grows with charging current,
exactly when it matters most.

**A dedicated battery sense wire** run to the battery positive post gives a
Kelvin measurement: it carries no current, so it has no drop. That is one extra
wire for the thing the whole loop is trying to control.

If a dedicated wire is not run, the regulation target has to be raised to
compensate for a drop that varies with current — which is guesswork, and it
guesses worst at high load.

## Temperature compensation is not optional

Lead-acid charging voltage should fall as temperature rises, roughly
**−3 to −5 mV/°C per cell**, so **−18 to −30 mV/°C** for a 12 V battery. Across
a −20 °C winter start and a +50 °C summer engine bay, that is well over a volt
of correct variation.

Regulating to a fixed 14.4 V year-round overcharges in summer and undercharges
in winter. If the ECU takes over charging it must take over this too.

**[CONFIRM]** what temperature to compensate against. Battery temperature is
the correct input but needs a sensor at the battery; IAT is a poor proxy in an
engine bay. This is worth resolving before committing to ECU-controlled
charging, because getting it wrong is worse than leaving the alternator's own
regulator alone.

## Two measurements, two purposes — recap

| Measurement | Sense point | Accuracy needed | For |
|---|---|---|---|
| **INA238-Q1** | ECU protected rail | ordinary | ECU self-diagnostics, current draw |
| **Battery voltage** | raw battery, ideally at the post | ordinary → **precision if charging is controlled** | injector dead-time, coil dwell, **charging regulation** |
