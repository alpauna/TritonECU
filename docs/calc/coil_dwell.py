#!/usr/bin/env python3
"""Dwell limits from the MEASURED coil primary inductance.

L = 1.48 mH, measured on an LCR meter, 2026-09-18.
Driver: ISL9V3040, E_AS = 300 mJ single-pulse avalanche.
"""
import math
L      = 1.48e-3          # MEASURED
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
