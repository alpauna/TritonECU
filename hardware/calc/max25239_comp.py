#!/usr/bin/env python3
"""MAX25239 loop compensation and output capacitor sizing, TritonECU 5 V rail.

Equations 8-15 from the MAX25239/MAX25240 datasheet (Rev 14, 7/26).
Compensation is designed at the worst case the datasheet specifies: minimum
input and heavy load, i.e. deepest boost, where the RHP zero is lowest.
"""
import math

# --- part constants (datasheet) ---
RI    = 0.050      # ohm, internal current-sense
GM    = 100e-6     # A/V, error-amp transconductance
VREF  = 0.800      # V, FB regulation point
FSW   = 2.1e6      # Hz

# --- design point ---
VOUT  = 5.0        # V, MAX25239AFFA fixed option
IOUT  = 1.0        # A, 5 V rail total (TLV62085 + ADC/VR + logic + VREF out)
VIN_M = 4.2        # V, LTC4364 cutoff -> deepest boost we must stay stable at
L     = 2.2e-6     # H
ETA   = 0.90

# --- output capacitor candidates: (label, nominal, effective after DC bias) ---
CANDS = [
    ("2 x 22 uF, 0805 16 V  (-45 % bias)", 44e-6, 24e-6),
    ("2 x 22 uF, 1206 25 V  (-25 % bias)", 44e-6, 33e-6),
    ("3 x 22 uF, 0805 16 V  (-45 % bias)", 66e-6, 36e-6),
    ("4 x 22 uF, 0805 16 V  << DECIDED  ", 88e-6, 66e-6),
]
ESR      = 0.005   # ohm, bank
DIOUT    = 0.5     # A, load step
DVUS     = 0.100   # V, allowable undershoot

D      = 1 - VIN_M / VOUT
RLOAD  = VOUT / IOUT
fzrhp  = RLOAD * (1 - D) ** 2 / (2 * math.pi * L)
fc     = fzrhp / 5

print(f"MAX25239 @ {VOUT} V / {IOUT} A, L = {L*1e6:.1f} uH, fsw = {FSW/1e6:.1f} MHz")
print(f"worst case: Vin = {VIN_M} V  ->  D = {D:.3f} (boost), Rload = {RLOAD:.1f} ohm\n")
print(f"  RHP zero        {fzrhp/1e3:8.1f} kHz")
print(f"  target fc       {fc/1e3:8.1f} kHz   (fsw/{FSW/fc:.0f})\n")

# Eq 11 - output cap rms ripple, boost mode
irms = IOUT * math.sqrt((VOUT - VIN_M) / VIN_M)
# Eq 10 - transient requirement
c_tr = DIOUT / (2 * math.pi * DVUS * fc)
print(f"  Cout rms ripple {irms:8.2f} A     (boost corner)")
print(f"  Cout for {DIOUT} A step, {DVUS*1e3:.0f} mV undershoot: {c_tr*1e6:.1f} uF (Eq 10)\n")

print(f"{'output bank':<38} {'Ceff':>7} {'ripple':>8} {'transient':>10}  {'Rc':>8} {'Cc':>7} {'Cp':>7}")
for label, cnom, ceff in CANDS:
    # Eq 8 - output ripple voltage, boost mode
    dv = (VOUT * IOUT * ESR) / (VIN_M * ETA) + IOUT * (1 - VIN_M / VOUT) / (FSW * ceff)
    # Eq 15
    rc = 2 * math.pi * RI * ceff * VOUT * fc / ((1 - D) * GM * VREF)
    cc = RLOAD * ceff / (2 * rc)
    cp = 1 / (2 * math.pi * rc * fzrhp)
    fp = 1 / (math.pi * RLOAD * ceff)
    ok = "OK " if ceff >= c_tr else "LOW"
    print(f"{label:<38} {ceff*1e6:6.0f}u {dv*1e3:7.1f}mV {ok:>10}  "
          f"{rc/1e3:7.1f}k {cc*1e9:6.2f}n {cp*1e12:6.1f}p   fp={fp:.0f} Hz")

print("\nNote: compensation is designed in deep boost, so buck-mode transient")
print("response is slower than it could be. That is the datasheet's own guidance")
print("and it is the right trade -- one network stable across the whole range.")
