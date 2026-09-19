#!/usr/bin/env python3
"""Pin 55 as the battery-voltage sense input. Reproduces schematic-findings.md 19."""
TOP,BOT = 180e3, 30e3
RATIO = (TOP+BOT)/BOT
NOM   = 14.0
I     = NOM/(TOP+BOT)

print("="*74); print("1. THE OBJECTION TO PIN 55 DOES NOT SURVIVE THE CURRENT")
print("="*74)
print(f"""
  Pin 55 was ruled out as a POWER source because it reaches the PCM through
  the Central Junction Box, and the divider has to read TRUE battery. That
  reasoning was about carrying SUPPLY current. As a SENSE-ONLY input the
  divider draws {I*1e6:.1f} uA, and the CJB path stops mattering:
""")
print(f"  {'assumed CJB path resistance':>32} {'drop at 66.7 uA':>18}")
for r,lab in ((0.05,"fuse alone"),(0.16,"fuse + contacts + wire, realistic"),
              (1.00,"absurdly corroded"),(10.0,"a fault, not a path")):
    print(f"  {r:>8.2f} ohm  {lab:<22} {I*r*1e6:>12.1f} uV")
print(f"""
  ** Even a fully corroded ohm of path costs 67 microvolts. ** The reading
  is battery voltage. The objection applied to amps and there are none.

  Circuit 729 RD/WH runs C242 -> C160 -> pin 55 with no other load drawn on
  the sheet, so there is no shared-segment current to create a drop either.
  [CONFIRM] nothing else sits on that 5 A CJB fuse.""")

print("\n"+"="*74); print("2. WHAT THE SPLIT BUYS")
print("="*74)
print(f"""                     supplies            senses
   dedicated lead      the always-on rail   -            2 A at the post
   pin 55              -                    battery      5 A in the CJB

  ** SEPARATELY FUSED, AND THAT IS THE POINT. ** Power and measurement no
  longer share a failure. It also finally gives pin 55 a job: it is live at
  our connector whether we use it or not, and "unconnected" was always the
  weaker answer for a permanently hot 12 V pin.

  Parked drain does not change - {I*1e6:.0f} uA moves from our lead to pin 55:
      our lead   117 uA   (converter chain only)
      pin 55      {I*1e6:.0f} uA   (divider)
      total      184 uA   as before""")

print("\n"+"="*74); print("3. THE FAILURE MODE THIS CREATES  --  and it is the whole design")
print("="*74)
print(f"""
  Sense and supply are now independent, so ONE CAN FAIL WITHOUT THE OTHER.

    CJB fuse blows, or 729 opens
      -> pin 55 floats, the {BOT/1e3:.0f}k leg pulls the node to 0 V
      -> battery reads 0.0 V
      -> THE ECU IS STILL RUNNING, happily, off the dedicated lead

  Left alone, the low-battery self-disable sees 0 V and parks the ECU on a
  perfectly good battery - the exact failure the divider was moved upstream
  to avoid, reintroduced by a different route.

  ** THE CROSS-CHECK IS ALREADY ON THE BOARD. ** The INA238 reads the
  PROTECTED RAIL, which is fed by our lead when parked and by VPWR when the
  key is on. It is never fed by 729. So:
""")
print(f"  {'pin 55':>10} {'protected rail':>16}   diagnosis")
print("  " + "-"*62)
for a,b,d in ((">11 V",">11 V","normal"),
              ("<2 V",">11 V","** 729 OPEN / CJB FUSE BLOWN ** - not a flat battery"),
              ("<11.5 V","<11.5 V","genuinely low battery -> self-disable"),
              (">11 V","<2 V","our lead's fuse blown - but then nothing is running")):
    print(f"  {a:>10} {b:>16}   {d}")
print(f"""
  ** The self-disable must require AGREEMENT, not just a low reading. **
  Disagreement is a wiring fault and should set a code, not park the ECU.
  Allow ~1 V of slack: parked, the rail sits {0.48:.2f} V below the lead through
  D3 and R7.""")

print("\n"+"="*74); print("4. PROTECTION, AND WHY THIS CHANNEL KEEPS WHAT THE O2 CHANNELS LOST")
print("="*74)
for v,lab in ((35,"ISO 7637-2 pulse 5b, suppressed"),(69.4,"SMDJ43A clamp equivalent"),
              (-100,"ISO 7637-2 pulse 1")):
    print(f"  {lab:<34} {v:>6} V  ->  {v/(TOP+BOT)*1e6:>7.1f} uA,  node {v/RATIO:>6.2f} V")
print(f"""
  ** The {TOP/1e3:.0f}k top leg IS the protection. ** Nothing in the harness can push
  more than half a milliamp into this node.

  And unlike the four O2 channels, THIS ONE IS UNBUFFERED - so it still sits
  behind the ADS8588H's 9 kV input clamp. o2-input-stage.md had to add a
  BAT54S precisely because a buffer relocated that boundary; here it never
  moved. Half a milliamp is nothing to a clamp rated for ESD.

  Add an SMBJ30A at the pin anyway - SAME PART as TVS3 on the always-on
  lead, so no new line item - and the node worst case becomes {36/RATIO:.1f} V.

  Ratio stays {RATIO:.3f} (180k/30k). One LSB is {20/2**16*RATIO*1e3:.1f} mV referred to the
  battery against a 0.1 V target; {NOM/RATIO:.3f} V at {NOM:.0f} V nominal.""")
