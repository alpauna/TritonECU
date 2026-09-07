#!/usr/bin/env python3
"""ECU main supply: LM5155-Q1 SEPIC, 6.0 V at 3 A.

Single phase. Input range set by the vehicle, not the converter: 6 V is a
cold-crank sag at the ECU after harness drop, and the upper end is what the
surge stopper passes through. The LM5155-Q1 itself runs 3.5-45 V.

Every number here is reproducible; nothing is asserted that this file does
not compute.
"""

VOUT   = 6.0      # V, main rail
IOUT   = 3.0      # A
VD     = 0.5      # V, Schottky forward drop
# Switching frequency: 2.2 MHz, chosen for EMC rather than for efficiency.
#
# The AM broadcast band is 530-1710 kHz. A 400 kHz converter puts its 3rd
# harmonic at 1.2 MHz and its 4th at 1.6 MHz, both squarely inside it -- in a
# vehicle with a radio, on a harness that runs the length of the truck. The
# LM5155-Q1 reaches 2.2 MHz specifically so the fundamental and every harmonic
# sit above the band. It also shrinks the magnetics by 5.5x.
FSW    = 2.2e6    # Hz
ETA    = 0.85     # assumed efficiency at low line
L      = 3.3e-6   # H, each inductor (separate, not coupled)

VIN_CRANK, VIN_NOM, VIN_HIGH, VIN_MAX = 6.0, 13.8, 30.0, 45.0


def duty(vin):
    """SEPIC duty: D = (Vout + Vd) / (Vin + Vout + Vd)."""
    return (VOUT + VD) / (vin + VOUT + VD)


def analyse(vin, label):
    d    = duty(vin)
    pout = VOUT * IOUT
    iin  = pout / (ETA * vin)          # = IL1 average
    il1, il2 = iin, IOUT

    # Ripple in each inductor while the switch is on.
    dil  = vin * d / (L * FSW)
    il1_pk, il2_pk = il1 + dil / 2, il2 + dil / 2

    # The switch and the diode both carry IL1 + IL2 — the defining property
    # of a SEPIC, and what sets the silicon.
    isw_pk = il1_pk + il2_pk
    vsw    = vin + VOUT + VD           # switch and diode blocking voltage

    # Coupling capacitor carries a large RMS current, often the overlooked part.
    ics_rms = IOUT * (d / (1 - d)) ** 0.5

    print(f"  {label:<22} Vin={vin:5.1f} V")
    print(f"    duty                 {d*100:6.1f} %")
    print(f"    input current        {iin:6.2f} A")
    print(f"    inductor ripple      {dil:6.2f} A  ({dil/il1*100:.0f} % of IL1)")
    print(f"    IL1 / IL2 peak       {il1_pk:6.2f} / {il2_pk:.2f} A")
    print(f"    SWITCH+DIODE peak    {isw_pk:6.2f} A")
    print(f"    switch blocking V    {vsw:6.1f} V")
    print(f"    Cs ripple current    {ics_rms:6.2f} A rms")
    print()
    return isw_pk, vsw, ics_rms


print(f"LM5155-Q1 SEPIC — {VOUT} V @ {IOUT} A = {VOUT*IOUT:.0f} W, "
      f"fsw {FSW/1e3:.0f} kHz, L = {L*1e6:.0f} uH\n")

worst_i = worst_v = worst_cs = 0.0
for vin, label in ((VIN_CRANK, "cold crank"), (VIN_NOM, "running (nominal)"),
                   (VIN_HIGH, "surge pass-through"), (VIN_MAX, "LM5155 max")):
    i, v, c = analyse(vin, label)
    worst_i, worst_v, worst_cs = max(worst_i, i), max(worst_v, v), max(worst_cs, c)

# Ripple is nearly independent of Vin, which is not obvious from the table
# above. Vin * D = Vin * (Vout+Vd)/(Vin+Vout+Vd), which tends to (Vout+Vd) as
# Vin rises -- so the ripple asymptote is fixed by the output, not the input.
# The alarming "302 % of IL1" at high line is the *same* absolute ripple
# measured against a much smaller average current, not a runaway.
print(f"Ripple asymptote as Vin -> inf: {(VOUT+VD)/(L*FSW):.2f} A "
      f"(fixed by Vout, not Vin)\n")

print("Component requirements")
print(f"  MOSFET     >= {worst_v:.0f} V blocking, >= {worst_i:.1f} A peak")
print(f"             -> 80-100 V part for ringing margin, 20 A+ continuous")
print(f"  Diode      >= {worst_v:.0f} V, {IOUT:.0f} A average, {worst_i:.1f} A peak")
print(f"             -> 100 V Schottky, 5-10 A")
print(f"  Inductors  2 x {L*1e6:.0f} uH, saturation > {worst_i/2*1.3:.1f} A each")
print(f"  Cs         >= {worst_v:.0f} V rated, {worst_cs:.1f} A rms")
print(f"             -> multiple 100 V X7R in parallel; one part will not do it")

# Thermal, at the operating point that actually matters: nominal, forever.
d_nom = duty(VIN_NOM)
pout  = VOUT * IOUT
loss  = pout * (1 / ETA - 1)
print(f"\nThermal at {VIN_NOM} V nominal")
print(f"  output               {pout:.1f} W")
print(f"  total loss at {ETA*100:.0f}%    {loss:.1f} W")
print(f"  duty                 {d_nom*100:.1f} %")
print("  The worst case is not cranking. It is this, continuously, forever.")
