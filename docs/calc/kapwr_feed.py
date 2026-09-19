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
       ("INA238 shutdown",2),("Battery-sense divider 180k/30k, ON THE BATTERY LEAD",67)]
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
R7=470.0; I=(tb-67)*1e-6   # the divider sits UPSTREAM of R7 now
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
print("5. THE DIVIDER MOVES TO THE BATTERY LEAD  --  and re-ratios")
print("="*74)
RIN,SP,CLAMP,NOM,FS = 1e6,0.15,69.4,14.0,10.0
def spread(z):
    lo,hi = RIN*(1-SP), RIN*(1+SP)
    return abs(z/(z+lo) - z/(z+hi))   # FULL span of RIN, as adc-front-end.md quotes it
print("""
  Downstream of D3 and R7 the divider would read 0.51 V low when parked,
  with a LOAD-DEPENDENT correction - an error that reads as a weak battery
  for a year. Upstream of them it reads TRUE battery voltage and the
  correction disappears entirely.

  But it also leaves the LTC4364's 27 V clamp behind. adc-front-end.md
  sized 150k/33k against "the LTC4364's 27 V clamp"; on the battery lead
  the worst case is the SMDJ43A's clamping voltage, 69.4 V.
""")
print(f"{'divider':>16} {'ratio':>7} {'at 14V':>8} {'at 69.4V':>9} {'sleep':>8} {'Zsrc':>7} {'spread':>8} {'at 14V':>8}")
for top,bot in ((150e3,33e3),(160e3,27e3),(180e3,30e3),(200e3,30e3),(220e3,33e3)):
    r=(top+bot)/bot; z=top*bot/(top+bot); sp=spread(z)
    flag="  CLIPS" if FS*r<CLAMP else ""
    print(f"{top/1e3:>8.0f}k/{bot/1e3:<6.0f}k {r:>7.3f} {NOM/r:>7.3f}V {CLAMP/r:>8.3f}V"
          f" {NOM/(top+bot)*1e6:>6.1f}uA {z/1e3:>5.1f}k {sp*100:>7.2f}% {sp*NOM*1e3:>6.0f}mV{flag}")
print(f"""
  ** 180k / 30k, ratio exactly 7.000. ** It beats the incumbent on every
  axis at once rather than trading one against another:

    headroom   69.4 V -> 9.914 V, INSIDE the +/-10 V range. 150k/33k would
               read 12.5 V - over range, losing the measurement during
               exactly the event you would want it for.
    drain      66.7 uA vs 76.5 uA
    Zsrc       25.7k vs 27.0k, so the uncalibratable spread improves too,
               105 mV vs 110 mV at 14 V
    clipping   at {FS*7.0:.0f} V, just above where the SMDJ43A clamps. The ADC range
               covers the whole survivable envelope and nothing beyond it.

  One LSB is {20/2**16*7*1e3:.1f} mV referred to the battery, against a 0.1 V target.
  Not close to binding.""")

print("="*74)
print("6. WHAT STILL NEEDS CONFIRMING")
print("="*74)
print("""  1. ~RETIRED~ A-44's number in the 1-104 scheme. A dedicated battery lead
     uses no EEC-V pin, so the unmapped A-xx / 1-104 question no longer
     blocks this drawing. It is still a real gap for every OTHER pin.
  2. [CONFIRM] the LTC4364 tolerates OUT held at battery while IN is at 0 V.
     That is the parked state by construction here. The ideal-diode FET
     blocks the current; what is unverified is the part's own rating for a
     reverse IN-OUT differential with the die unpowered.
  3. ~RETIRED~ the truck's keep-alive fuse rating. The lead has its own
     fuse at the battery post and shares nothing with the vehicle.
  4. [CONFIRM] D3 reverse leakage at 125 C. It is reverse-biased only when
     the key is on and the MCU is awake, so it costs nothing in the sleep
     budget - but a Schottky would leak tens of uA and is the wrong choice
     here for exactly that reason. Silicon, and take the 0.42 V.""")

print("\n"+"="*74)
print("7. WHAT THE TRUE BATTERY LEAD CHANGES BESIDES ACCURACY")
print("="*74)
print(f"""  a) R7 MATTERS MORE, NOT LESS. A lead off the post has LESS drop than the
     OEM keep-alive circuit, so it sits even further above VPWR - which
     arrives through a relay contact. Without R7 the ECU would run entirely
     off the always-on lead. At 1 A of load against the LTC4364 path's
     ~20 mohm, R7 = 470R holds its contribution to {0.020/470*1e6:.0f} uA.

  b) A DIAGNOSTIC FALLS OUT FOR FREE. The divider now reads the BATTERY;
     the INA238 reads the PROTECTED RAIL. The difference is the drop across
     the EEC relay contact and the 361 RD harness run, under whatever load
     the ECU is drawing. Corroded contacts and a tired harness become
     measurable instead of inferred. Neither reading gave that before,
     because both sat on the same side of the relay.

  c) THE FUSE MOVES AND F2 GOES AWAY. The fuse protects the WIRE, so it
     belongs within 150-300 mm of the battery post - the run between post
     and fuse is unprotected by definition. Once it exists, a board fuse
     protects nothing: R7 already caps fault current at {14.0/470*1e3:.0f} mA.
     ONE FUSE, AT THE SOURCE. 2 A blade.

  d) IT IS AN ALWAYS-HOT WIRE IN AN ENGINE BAY, and it bypasses every
     switch in the vehicle. Gauge is set by mechanical durability, not
     ampacity - the lead carries 184 uA. 18 AWG minimum, loomed, grommeted
     at the firewall, clear of heat and edges.

  e) GROUND STAYS SINGLE-POINT. Positive from the post; return stays on the
     EEC-V PWRGND pins. Do NOT run a second ground to the battery negative -
     that makes a loop with PWRGND. The consequence is that the reading
     includes the ground-path drop and so reads low while cranking. That is
     the right thing to measure: it is what the ECU's supply actually sees.""")
