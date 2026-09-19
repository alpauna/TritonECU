#!/usr/bin/env python3
"""The KAPWR always-on feed. Reproduces always-on-domain.md "The KAPWR feed"."""

print("="*74)
print("1. WHERE IT JOINS  --  and why that kills the biggest sleep load")
print("="*74)
print("""
  always-on-domain.md already says the tapping point is AFTER the LTC4364.
  Take that literally for the INPUT too and KAPWR joins the PROTECTED RAIL,
  downstream of the ideal-diode FET, not the LTC4364's input:

   VPWR 71,97 --[F1]--[SMDJ43A]--+ LTC4364-2 +-------+
                                 | pass FET          |
                                 | ideal-diode FET --+--+--> PROTECTED RAIL
                                                        |    |
   KAPWR A-44 --[F2]--[SMDJ43A]--[D3]--[R7 470R]--------+    +--> MAX25239 -> 5V
                                        |                    +--> NCV8772 -> VREF
                                     [TVS3]                  +--> 150k/33k divider
                                        |
                                       PGND

  Three things fall out, and the first is the whole argument:

  * THE LTC4364 IS UNPOWERED WHEN PARKED. It was 750 uA - 80 % of the old
    budget - and it is now zero, because nothing feeds its input with the
    key off.
  * BACK-FEED INTO VPWR IS BLOCKED FOR FREE by the ideal-diode FET that is
    already in the design. Joining at the LTC4364's INPUT instead would
    push KAPWR back out through pins 71/97 into the open relay contact.
  * THE 'SECOND TRANSIENT CHAIN' IS A RESISTOR AND A TVS, because this
    branch carries microamps. always-on-domain.md dismissed a second chain
    as not worth it - but it was costing a full protection circuit against
    a drain saving. Here it buys the source itself, and it is two parts.
""")

print("="*74)
print("2. THE NEW SLEEP BUDGET")
print("="*74)
old = [("LTC4364 quiescent",750),("MAX25239 standby, skip mode",95),
       ("TLV62085 quiescent",17),("STM32F767 Standby + RTC + backup SRAM",3),
       ("INA238 shutdown",2),("Battery-sense divider 150k/33k",77)]
new = [(n,(0 if "LTC4364" in n else v)) for n,v in old]
print(f"\n  {'':<40} {'was':>8} {'now':>8}")
for (n,a),(_,b) in zip(old,new):
    tag = "   <-- unpowered" if a!=b else ""
    print(f"  {n:<40} {a:>6} uA {b:>6} uA{tag}")
ta, tb = sum(v for _,v in old), sum(v for _,v in new)
print(f"  {'TOTAL':<40} {ta:>6} uA {tb:>6} uA")
BATT=70.0
for lab,t in (("was",ta),("now",tb)):
    ah = t*1e-6*720
    print(f"    {lab}: {ah:.3f} Ah/month on a {BATT:.0f} Ah battery"
          f"  = {ah/BATT*100:.2f} %/month, {ah*6/BATT*100:.1f} % over six months")
print(f"\n  {ta/tb:.1f}x better, and it came from moving a junction, not adding parts.")

print("\n"+"="*74)
print("3. R7  --  it does three jobs at once")
print("="*74)
R7=470.0; I=tb*1e-6
print(f"""
  R7 = {R7:.0f} ohm.

  a) IT MAKES THE OR ASYMMETRIC, WITHOUT AN OR CONTROLLER.
     The LTC4364 path is a 10 mohm shunt plus a pass FET - call it 20 mohm.
     R7 is {R7/0.020:.0f}x that. So when VPWR is up, KAPWR cannot take the load
     even though it sits at a similar potential:""")
for ld,drop in ((0.5,0.010),(1.0,0.020)):
    print(f"       rail sags {drop*1e3:.0f} mV at {ld:.1f} A  ->  KAPWR contributes {drop/R7*1e6:.0f} uA")
print(f"""     ** Run current can never flow through the keep-alive fuse. ** That
     was the failure mode a plain diode-OR would have had, because KAPWR
     is if anything HIGHER than VPWR - VPWR comes through a relay contact.

  b) IT LIMITS KAPWR FAULT CURRENT to {14.0/R7*1e3:.0f} mA at 14 V into a dead short,
     so a downstream failure cannot open the keep-alive fuse and take the
     truck's other keep-alive loads with it.

  c) IT MAKES TVS3 WORK. Without series impedance a shunt clamp has to
     absorb the whole surge; with it, the clamp only has to sink what R7
     lets through.

  COST: {I*1e6:.0f} uA x {R7:.0f} ohm = {I*R7*1e3:.0f} mV of drop when parked. The MAX25239
  runs down to 2 V, so this is irrelevant to operation - but see sec.5,
  because it is NOT irrelevant to the battery-voltage reading.""")

print("="*74)
print("4. TVS3  --  the window is narrower than it looks")
print("="*74)
print("""
  It has to stand OFF a jump start and clamp BELOW the MAX25239:

    jump start / LTC4364 regulated output        27 V   must not conduct
    MAX25239 transient absolute maximum          42 V   must clamp below
""")
print(f"  {'part':>10} {'standoff':>9} {'Vbr min':>9} {'verdict'}")
for part,so,vbr in (("SMBJ24A",24,26.7),("SMBJ26A",26,28.9),("SMBJ30A",30,33.3),("SMBJ33A",33,36.7)):
    if so < 27: v = "NO - conducts at a 27 V jump start"
    elif vbr > 42: v = "NO - above the MAX25239 limit"
    else: v = f"OK  ({so} V standoff, clamps from {vbr} V)"
    print(f"  {part:>10} {so:>7} V {vbr:>7} V   {v}")
VC=34.5
for lab,V,note in (("ISO 7637-2 pulse 5b, suppressed alternator",35,
                    "TVS3 barely conducts; the MAX25239's own 42 V rating already covers it"),
                   ("SMDJ43A clamping at full rated current",69.4,"the unsuppressed worst case")):
    i=(V-VC)/R7
    if i<0: i=0.0
    print(f"\n  {lab} = {V} V   ({note})")
    print(f"    through R7: {i*1e3:>6.1f} mA    R7 dissipates {i*i*R7:>5.2f} W    TVS3 {i*VC:>5.2f} W")
print(f"""
  400 ms of pulse 5 at the worst case is {((69.4-VC)/R7)**2*R7*0.4:.2f} J in R7. Use a 1206 or
  larger, or two 1k in parallel. ** DECIDED: SMBJ30A, R7 = 470R 1206. **

  Note the realistic case does nothing at all: a modern alternator's
  centralised suppression holds pulse 5b to 35 V, which is inside the
  MAX25239's own transient rating. TVS3 exists for the unsuppressed case.""")

print("\n"+"="*74)
print("5. THE CONSEQUENCE NOBODY WOULD LOOK FOR  --  the voltmeter now lies")
print("="*74)
VF=0.42
print(f"""
  The 150k/33k battery-sense divider hangs on the protected rail, which
  when parked is KAPWR minus D3 minus R7:

     D3 forward drop at {I*1e6:.0f} uA   {VF:.2f} V
     R7 drop                {I*R7:.3f} V
     ------------------------------
     total offset           {VF+I*R7:.2f} V   LOW, and ONLY when parked

  always-on-domain.md's low-battery self-disable trips at 11.5 V. Uncorrected
  it would actually trip at {11.5+VF+I*R7:.2f} V of real battery - it would give up on a
  healthy battery. Firmware must add the offset back whenever VPWR is absent,
  and the offset is load-dependent, not a constant, because R7's drop tracks
  the sleep current.

  ** This is the kind of error that reads as a weak battery for a year. **""")

print("="*74)
print("6. WHAT STILL NEEDS CONFIRMING")
print("="*74)
print("""  1. [CONFIRM] A-44's number in the 1-104 scheme. The wiring diagrams give
     VPWR as 'pins 71 and 97'; oem-connectors.md gives it as 'A-32, A-33'.
     Two numbering systems, no mapping recorded anywhere in the repo.
  2. [CONFIRM] the LTC4364 tolerates OUT held at battery while IN is at 0 V.
     That is the parked state by construction here. The ideal-diode FET
     blocks the current; what is unverified is the part's own rating for a
     reverse IN-OUT differential with the die unpowered.
  3. [CONFIRM] the keep-alive fuse rating on this truck, to size F2 under it.
  4. [CONFIRM] D3 reverse leakage at 125 C. It is reverse-biased only when
     the key is on and the MCU is awake, so it costs nothing in the sleep
     budget - but a Schottky would leak tens of uA and is the wrong choice
     here for exactly that reason. Silicon, and take the 0.42 V.""")
