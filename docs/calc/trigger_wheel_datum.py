#!/usr/bin/env python3
"""36-1 trigger wheel keyway datum. Reproduces the "Corrected: the keyway is NOT
on the gap" section of hardware/vr-test-rig/README.md.

The observation (physical wheel, 2026-09-19): the keyway lines up with the REAR
EDGE of the tooth immediately forward of the missing tooth -- i.e. with the
FORWARD EDGE OF THE GAP. Everything below turns that into degrees and asks how
well it can be known."""

import math

PITCH = 360.0 / 36          # 10.00 deg, 36-1

print("=" * 74)
print("1. THE EDGE, IN DEGREES  --  and what the tooth width does to it")
print("=" * 74)
print(f"tooth pitch                    {PITCH:.2f} deg")
print("keyway sits at the rear edge of the tooth one pitch forward:")
print("    key_to_gap = pitch - tooth_w/2\n")
print(f"{'duty':>6} {'tooth_w':>9} {'key_to_gap':>12}")
for duty in (0.40, 0.50, 0.60):
    w = PITCH * duty
    print(f"{duty:>6.0%} {w:>8.2f}d {PITCH - w/2:>11.2f}d"
          + ("   <-- assumed" if duty == 0.50 else ""))
span = (PITCH - PITCH*0.60/2) - (PITCH - PITCH*0.40/2)
print(f"\nwhole 40-60 % duty range spans {abs(span):.1f} deg.")
print("So the UNMEASURED tooth width costs +/-0.5 deg. The observation itself is")
print("worth much more than the assumption riding on it.")

print()
print("=" * 74)
print("2. SIGN  --  the one thing that is NOT small")
print("=" * 74)
k = PITCH - PITCH*0.5/2
print(f"forward  = direction of rotation  ->  key_to_gap = +{k:.1f} deg")
print(f"backward                          ->  key_to_gap = -{k:.1f} deg")
print(f"getting it wrong moves the datum by {2*k:.0f} deg = {2*k/PITCH:.1f} PITCHES,")
print(f"which is {2*k/k:.0f}x the error of simply leaving key_to_gap at its old 0"
      f" ({k:.1f} deg).")

print()
print("=" * 74)
print("3. WHY THE KEYWAY IS THE NOISY END OF THE SIGHT-LINE")
print("=" * 74)
print("A radial line's angular error from a linear error d is  atan(d/r).")
print("The keyway is the INNERMOST feature on the wheel, so it pays the most.\n")
d = 1.0                     # mm, a generous eyeball
print(f"{'feature':<22}{'radius':>9}{'1 mm costs':>13}{'in pitches':>12}")
for name, r in (("keyway, 28 mm bore", 14.0),
                ("keyway, 43.4 mm bore", 21.7),
                ("tooth, 129 mm OD", 64.5),
                ("tooth, 171.45 mm OD", 85.7)):
    a = math.degrees(math.atan(d / r))
    print(f"{name:<22}{r:>8.1f}mm{a:>12.2f}d{a/PITCH:>11.2f}")
print("\nSo the keyway end is 3-5x noisier than the tooth end. Sighting FROM the")
print("keyway OUT to the rim puts the worst error at the start of the lever.")

print()
print("=" * 74)
print("4. THE OLD PHOTO SAID 2.3 deg. THAT DISAGREEMENT IS NOT NOISE")
print("=" * 74)
old, new = 2.3, k
print(f"photo (Dorman 917-060 listing)   {old:.1f} deg")
print(f"the part in hand                 {new:.1f} deg")
print(f"difference                       {new-old:.1f} deg"
      f"  = {(new-old)/PITCH:.2f} PITCH = {(new-old)/(PITCH*0.5):.2f} tooth widths")
print("Half a pitch -- one whole tooth -- is the signature of two different EDGES")
print("being read, not of random scatter. Such disagreements are never random.")

print()
print("=" * 74)
print("5. WHAT THE RIG CAN DO ABOUT IT")
print("=" * 74)
step_full, micro = 1.8, 16
res = step_full / micro
print(f"stepper {step_full} deg/step at {micro}x microstep -> {res:.4f} deg, 1:1 to the crank")
print(f"eyeball, optimistically                          -> ~{math.degrees(math.atan(1/21.7)):.1f} deg")
print(f"ratio                                            -> {math.degrees(math.atan(1/21.7))/res:.0f}x better")
print("\nAnd it needs no correct flute to start: cut the flute anywhere, home on")
print("it, log teeth, and key_to_gap falls out. The flute must be KNOWN, not RIGHT.")

print()
print("=" * 74)
print("6. THE OD, WITHOUT MEASURING ANYTHING")
print("=" * 74)
plate_w, vendor_od = 157.0, 171.45
print(f"carrier template width           {plate_w:.0f} mm")
print(f"vendor OD (6-3/4\")               {vendor_od:.2f} mm")
print(f"overhang a {vendor_od:.2f} wheel MUST show   {(vendor_od-plate_w)/2:.1f} mm per side")
print("The photo shows grid on BOTH sides of the wheel. No overhang ->")
print(f"the OD is under {plate_w:.0f} mm and the vendor listing does not describe this part.")
