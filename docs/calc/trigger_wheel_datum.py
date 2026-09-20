#!/usr/bin/env python3
"""36-1 trigger wheel keyway datum. Reproduces the "Corrected: the keyway is NOT
on the gap" section of hardware/vr-test-rig/README.md.

The observation (physical wheel, 2026-09-19, corrected the same day after the
first look turned out to be from the BACK of the wheel): the keyway lines up with
THE GAP BETWEEN THE MISSING TOOTH AND THE NEXT TOOTH. Everything below turns that
into degrees and asks how well it can be known."""

import math

PITCH = 360.0 / 36          # 10.00 deg, 36-1

print("=" * 74)
print("1. THE GAP CENTRE  --  and why the tooth width CANCELS")
print("=" * 74)
print(f"tooth pitch                    {PITCH:.2f} deg")
print("The keyway sits in the gap between the missing tooth and the next tooth.")
print("That gap runs from one tooth's edge to the next tooth's edge, so its")
print("centre is the MIDPOINT OF TWO TOOTH CENTRES -- and w cancels:\n")
print("    gap spans  w/2 .. pitch-w/2")
print("    centre   = (w/2 + pitch - w/2)/2 = pitch/2\n")
print(f"{'duty':>6} {'tooth_w':>9} {'gap centre':>12} {'gap width':>11}")
for duty in (0.40, 0.50, 0.60):
    w = PITCH * duty
    print(f"{duty:>6.0%} {w:>8.2f}d {PITCH/2:>11.2f}d {PITCH-w:>10.2f}d"
          + ("   <-- assumed" if duty == 0.50 else ""))
print(f"\nkey_to_gap = {PITCH/2:.2f} deg EXACTLY, for any tooth width.")
print("The first reading of this part gave 7.5 deg -- the FAR EDGE of this same")
print("gap -- and needed the duty to say so. Tooth width now only bounds the")
print(f"uncertainty: the keyway is somewhere in a {PITCH-PITCH*0.5:.1f} deg gap, so +/-{(PITCH-PITCH*0.5)/2:.2f} deg.")

print()
print("=" * 74)
print("2. SIGN  --  define it by EVENTS, and it cannot be mirrored")
print("=" * 74)
print("The first reading was taken with the wheel FACE-DOWN, which mirrors any")
print("geometric convention (clockwise/anticlockwise, forward/back). So:")
print()
print("    key_to_gap = crank rotation from THE GAP PASSING THE SENSOR")
print("                 until THE KEYWAY PASSES THE SENSOR.")
print()
print(f"Always positive. +{PITCH/2:.2f} deg. An order of events has no handedness.")
print("It is also how the part reads on the engine: the missing tooth goes by,")
print("and TDC is coming up.")

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
print("4. WHAT 5.00 deg IS NOT: IT IS NOT CKP_GAP_TO_TDC_DEG")
print("=" * 74)
print("    CKP_GAP_TO_TDC_DEG = key_to_gap + angle(sensor, keyway-at-TDC)")
print(f"                       = {PITCH/2:.2f} deg   + set by where the sensor BOLTS")
print("                                     TO THE BLOCK -- not a wheel property")
print()
print("The gap is detected when it passes THE SENSOR; TDC happens when the crank")
print("reaches an orientation. They coincide only if the sensor sits exactly")
print("where the keyway points at TDC, which would be luck.")
print()
print("So the SEQUENCING (gap first, TDC second) is right and is the useful half.")
print("The magnitude needs the engine -- and one look supplies it: bring #1 to TDC")
print(f"on a piston stop and see if the gap has just gone past by ~{PITCH/2:.0f} deg.")
print()
print("Readings of this wheel so far, all sighted outward FROM the keyway:")
for label, v in (("vendor photo", 2.3), ("part, face-down", 7.5), ("part, corrected", PITCH/2)):
    print(f"    {label:<18}{v:>5.1f} deg")
print("At 2.6-4.1 deg of noise per mm (section 3) all three look like 'on the gap'.")

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
print("6. THE OD  --  a ratio, not a proof")
print("=" * 74)
plate_long, vendor_od = 173.0, 171.45
frac = 0.92          # wheel span / frame width, EYEBALLED from the photo
print("The first version of this argument claimed the wheel 'sits inside the")
print("157 mm plate'. WRONG -- the plate runs off both edges of both photos, so")
print("grid beside the wheel bounds nothing. What survives needs a pixel ratio:")
print()
print(f"  plate spans MORE than the frame, and is at most {plate_long:.0f} mm")
print(f"  wheel spans LESS than the frame, about {frac:.2f} of it")
print(f"  ->  OD < {plate_long:.0f} x {frac:.2f} = {plate_long*frac:.0f} mm")
print()
print(f"vendor OD (6-3/4\")               {vendor_od:.2f} mm  -- excluded, but by")
print("                                 a measurement OF the photo, not a fact")
print(f"                                 about it. Treat as a strong hint.")
print()
print(f"THE GRID SETTLES IT: {vendor_od:.2f} mm is {vendor_od/10:.1f} squares. Count them.")
