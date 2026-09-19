#!/usr/bin/env python3
"""Dwell limits from the MEASURED coil primary.

L = 1.48 mH and R = 1.8 ohm, measured on an LCR meter, 2026-09-18.
Driver: ISL9V3040, E_AS = 300 mJ single-pulse avalanche.
"""
import math
L      = 1.48e-3          # MEASURED
R_MEAS = 1.8              # MEASURED on the same meter - but see section 5:
                          # DCR or ESR at the meter's test frequency?
E_AS   = 0.300            # ISL9V3040 avalanche energy rating, J
V_NOM, V_HI = 13.5, 14.4

def I_for(E): return math.sqrt(2*E/L)
def E_at(I):  return 0.5*L*I*I
def t_for(I, R, V):
    """Time to reach I through L-R from V. None if V/R never gets there."""
    if I >= V/R: return None
    return -(L/R)*math.log(1 - I*R/V)

print("="*74); print("1. THE HEADROOM IS MUCH BETTER THAN THE DOC ASSUMED")
print("="*74)
print(f"""
  output-drivers.md reasoned from "a COP primary of ~5 mH" and warned that
  "6 mH at 10 A is 300 mJ, exactly at the limit and therefore not
  acceptable". The measured coil is {L*1e3:.2f} mH - roughly a QUARTER of that -
  and energy goes as L, so the whole worry evaporates:
""")
print(f"  {'peak current':>13} {'at 5 mH (assumed)':>19} {'at 1.48 mH (measured)':>23}  margin")
for I in (8,10,12,14,16,20,20.13):
    e5, e = 0.5*5e-3*I*I, E_at(I)
    tag = "  <- AT THE RATING" if abs(e-E_AS) < 0.002 else ""
    print(f"  {I:>11.1f} A {e5*1e3:>16.0f} mJ {e*1e3:>20.1f} mJ  {E_AS/e:>5.2f}x{tag}")
print(f"""
  ** The 300 mJ rating is reached at {I_for(E_AS):.1f} A. ** A COP spark wants
  {I_for(0.050):.1f} A for 50 mJ or {I_for(0.080):.1f} A for 80 mJ, so the operating point sits
  {E_AS/E_at(I_for(0.080)):.1f}x under the rating on energy.""")

print("\n"+"="*74); print("2. DWELL  --  and R is the other half of the measurement")
print("="*74)
print(f"""
  I(t) = (V/R)(1 - e^(-tR/L)).  Primary resistance was NOT measured, so the
  table sweeps it. Note how little it matters at the operating point: early
  in the charge curve the rise is set by L, not R.

      di/dt at t=0  =  V/L  =  {V_NOM/L:.0f} A/s  =  {V_NOM/L/1000:.2f} A/ms at {V_NOM} V
""")
for tgt,lab in ((I_for(0.050),"50 mJ"),(I_for(0.080),"80 mJ"),(I_for(E_AS),"300 mJ - THE RATING")):
    print(f"  to reach {tgt:5.2f} A ({lab})")
    print(f"      {'R':>6} {'dwell at 13.5 V':>17} {'dwell at 14.4 V':>17}")
    for R in (0.3,0.4,0.5,0.6,0.7):
        a,b = t_for(tgt,R,V_NOM), t_for(tgt,R,V_HI)
        fa = f"{a*1e3:.2f} ms" if a else "never"
        fb = f"{b*1e3:.2f} ms" if b else "never"
        print(f"      {R:>5.1f}R {fa:>17} {fb:>17}")
    print()
print(f"""  ** Spread across R = 0.3-0.7 is ~10 % at the operating point and ~60 % at
  the rating. ** So the dwell you would actually run is nearly independent of
  the resistance, and the FAULT margin is not. Measure it.""")

print("="*74); print("3. THE FAULT CASE IS STUCK-ON, AND IT EXCEEDS THE RATING")
print("="*74)
print(f"""
  A stuck-on output does not climb forever - current saturates at V/R:
""")
print(f"  {'R':>6} {'I_sat at 14.4 V':>17} {'stored energy':>15} {'vs 300 mJ':>11} {'coil dissipates':>17}")
for R in (0.3,0.4,0.5,0.6,0.7):
    isat = V_HI/R; e = E_at(isat)
    print(f"  {R:>5.1f}R {isat:>15.1f} A {e*1e3:>13.0f} mJ {e/E_AS:>9.1f}x {isat*isat*R:>15.0f} W")
print(f"""
  ** At any plausible resistance a stuck-on coil stores MORE than the IGBT's
  avalanche rating, ** and turning it off then dumps that into the device.
  The coil is cooking at hundreds of watts by then too.

  This is the argument for the OE2 watchdog that v1-scope.md currently
  carries as "footprint yes, strap OE2 low for v1". The firmware dwell limit
  is the first line; the hardware watchdog is what covers a firmware hang,
  and now there is a number behind it rather than a principle.""")

print("="*74); print("4. SCHEDULER: DWELL OVERLAP IS NOT A CONSTRAINT HERE")
print("="*74)
CYL=8
for dwell_ms in (1.1,1.4,2.0):
    # spacing between spark events, 8 cyl 4-stroke = 90 deg crank
    for rpm in (6000,):
        spacing_ms = (90.0/360.0)*(60.0/rpm)*1000
        print(f"  dwell {dwell_ms:.1f} ms: event spacing at {rpm} rpm is {spacing_ms:.2f} ms"
              f"  -> {'OVERLAPS' if dwell_ms>spacing_ms else 'no overlap'}"
              f"   max rpm without overlap {90/360*60/ (dwell_ms/1000) :.0f}")
print(f"""
  With COP each coil has its own driver, so overlap is legal - it only means
  two coils charge at once, doubling the instantaneous supply draw. At
  {I_for(0.080):.1f} A that is ~21 A from the harness for a few hundred microseconds.
  SparkScheduler::maxRpmForDwell() already exposes this end of the trade.""")

print("\n"+"="*74)
print("5. THE MEASURED R = 1.8 OHM  --  and one check before trusting it")
print("="*74)
R = R_MEAS
for V in (13.5, 14.4):
    isat = V/R; tau = L/R
    print(f"\n  at {V} V:  I_sat = V/R = {isat:.2f} A   tau = {tau*1e3:.3f} ms"
          f"   max energy EVER {E_at(isat)*1e3:.1f} mJ  ({E_AS/E_at(isat):.1f}x under the rating)")
    for frac,lab in ((0.90,"90%"),(0.95,"95%"),(0.98,"98%")):
        I = isat*frac; t = -tau*math.log(1-frac)
        print(f"      {lab:>4} of saturation: dwell {t*1e3:5.2f} ms -> {I:5.2f} A, {E_at(I)*1e3:5.1f} mJ")
print(f"""
  ** THE COIL CURRENT-LIMITS ITSELF, AND SECTION 3 IS RETIRED. ** At
  0.3-0.7 ohm a stuck-on coil stored 1.0-5.7x the IGBT's rating. At 1.8 ohm
  it can never store more than {E_at(14.4/R)*1e3:.0f} mJ however long it is left on -
  {E_AS/E_at(14.4/R):.1f}x UNDER. The coil still cooks at {(14.4/R)**2*R:.0f} W; the IGBT never sees risk.

  ** THE COST IS SPARK ENERGY AND RPM HEADROOM. ** {E_at(14.4/R)*1e3:.0f} mJ is the ceiling,
  ~2 ms of dwell gets {E_at(0.9*14.4/R)*1e3:.0f} mJ, and 95% of saturation needs 2.46 ms - which
  collides with the 90-degree event spacing above {90/360*60/0.00246:.0f} rpm.""")

print(f"""
  1.8 ohm is HIGH for a Ford 5.4L COP primary; published DG508-family figures
  sit nearer 0.5 ohm. Two measurement effects explain that, and both take
  seconds to rule out:

  * AN LCR METER REPORTS AC SERIES RESISTANCE AT ITS TEST FREQUENCY, NOT
    DCR. An iron-cored ignition coil has real core loss at 1 kHz and it shows
    up as ESR. A coil reading 0.5 ohm on a DC ohmmeter reading several ohms
    on an LCR bridge is unremarkable.
      TEST: change the test frequency. If R moves, it is core loss. DCR does
      not care about frequency.

  * A 2-WIRE READING INCLUDES THE LEADS, and at half an ohm that is most of
    the reading.
      TEST: short the probes, note the reading, subtract.

  The dwell ramp is DC, so DCR is what the model needs.
""")
print(f"  {'if DCR is':>10} {'I_sat 14.4V':>13} {'max energy':>12} {'dwell for 80 mJ':>17} {'stuck-on vs rating':>20}")
I80 = I_for(0.080)
for Rx in (0.5,0.8,1.2,1.8):
    isat = 14.4/Rx; t = t_for(I80, Rx, 14.4)
    ft = f"{t*1e3:.2f} ms" if t else "UNREACHABLE"
    print(f"  {Rx:>8.1f}R {isat:>11.1f} A {E_at(isat)*1e3:>10.0f} mJ {ft:>17} {E_at(isat)/E_AS:>18.2f}x")
print("""
  ** THE PART CHOICE IS UNAFFECTED EITHER WAY. ** At 1.8 ohm the ISL9V3040 is
  6.3x under its rating; at 0.5 ohm the stuck-on case is 2.0x over it and the
  OE2 watchdog is what covers that. No resistance in this range argues for a
  different driver. What the number decides is the DWELL CONSTANT and whether
  overlap bites inside the rev range.""")
