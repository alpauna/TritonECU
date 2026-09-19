#!/usr/bin/env python3
"""Dwell limits from the MEASURED coil primary.

L = 1.48 mH and R = 0.5 ohm (DCR, good leads), measured 2026-09-18.
Driver: ISL9V3040, E_AS = 300 mJ single-pulse avalanche.
"""
import math
L      = 1.48e-3          # MEASURED
R_MEAS = 0.5              # MEASURED, DCR, with good leads. An earlier 2-wire
                          # reading gave 1.8 ohm - that was the leads. See s.5.
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
print("5. SETTLED: L = 1.48 mH, R = 0.5 ohm  --  and the 1.8 was the leads")
print("="*74)
R = R_MEAS
print(f"""
  A first 2-wire reading gave 1.8 ohm. With good leads it is {R} ohm, which is
  also what published DG508-family figures predict. At half an ohm the leads
  ARE most of a 2-wire reading, so this is the expected failure and worth
  remembering next time a small resistance is measured.

  It matters, because 1.8 ohm would have meant the coil CURRENT-LIMITED
  ITSELF at 8 A and could never reach the IGBT's rating. At {R} ohm it can:
""")
for V in (13.5, 14.4):
    isat = V/R; tau = L/R
    print(f"  at {V} V:  I_sat = {isat:.1f} A   tau = {tau*1e3:.2f} ms"
          f"   stuck-on energy {E_at(isat)*1e3:.0f} mJ = {E_at(isat)/E_AS:.2f}x THE RATING")
t300 = t_for(I_for(E_AS), R, 14.4)
print(f"""
  ** THE STUCK-ON CASE IS REAL AGAIN. ** {E_at(14.4/R)*1e3:.0f} mJ against a 300 mJ rating,
  and the device reaches that rating after {t300*1e3:.2f} ms of dwell - about
  {t300/0.00133:.1f}x the nominal. The OE2 watchdog is protecting the IGBT, not just
  the coil. Firmware dwell limiting remains the first line.

  ** BUT THE OPERATING POINT IS COMFORTABLE. ** We charge to {I_for(0.080):.1f} A for
  80 mJ, which is {E_AS/0.080:.1f}x under the rating, and tau is {L/R*1e3:.2f} ms so the ramp
  is still in its near-linear region - dwell is predictable and not
  sensitive to small errors in R.""")

print("\n"+"="*74)
print("6. THE DWELL TABLE  --  this is the deliverable")
print("="*74)
print(f"""
  Target {I_for(0.080):.1f} A / 80 mJ. Dwell must track battery voltage, and across the
  real range it varies by more than half:
""")
print(f"  {'V_batt':>8} {'I_sat':>8} {'dwell for 80 mJ':>17} {'dwell for 50 mJ':>17}")
for V in (9.0,9.5,10.0,11.0,12.0,12.6,13.5,14.4,15.0):
    a = t_for(I_for(0.080), R, V); b = t_for(I_for(0.050), R, V)
    fa = f"{a*1e3:.2f} ms" if a else "UNREACHABLE"
    fb = f"{b*1e3:.2f} ms" if b else "UNREACHABLE"
    print(f"  {V:>7.1f}V {V/R:>7.1f}A {fa:>17} {fb:>17}")
print(f"""
  ** {t_for(I_for(0.080),R,9.0)*1e3:.2f} ms at 9 V cranking against {t_for(I_for(0.080),R,14.4)*1e3:.2f} ms at 14.4 V - a {t_for(I_for(0.080),R,9.0)/t_for(I_for(0.080),R,14.4):.1f}x span. **
  A fixed dwell would either waste energy and heat the driver at high line
  or miss the target entirely while cranking, which is exactly when spark
  energy matters most. The dwell-vs-voltage table is not optional.

  Overlap: at {t_for(I_for(0.080),R,9.0)*1e3:.2f} ms the 90-degree event spacing collides above
  {90/360*60/t_for(I_for(0.080),R,9.0):.0f} rpm - and that is the CRANKING dwell, at 9 V, where the
  engine is turning 200 rpm. At the 14.4 V dwell of {t_for(I_for(0.080),R,14.4)*1e3:.2f} ms it is
  {90/360*60/t_for(I_for(0.080),R,14.4):.0f} rpm. ** Overlap is not a constraint anywhere the engine
  actually runs. **""")
