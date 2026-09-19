#!/usr/bin/env python3
"""In-circuit O2 cell impedance by modulating the shared bias node.

Reproduces every number in o2-input-stage.md section 10.
The stage already has the injection path: R2 = 22M from each channel's
high-Z node to the SHARED 455 mV bias node. Move that node and you have
driven a known current into every cell at once.
"""
import math

R2    = 22e6      # bias resistor per channel        (o2-input-stage.md sec 3)
R1    = 10e3      # series fault resistor, in the measured path   (sec 2)
RBIAS = 8.3e3     # bias divider source impedance                  (sec 3)
RDAC  = 1e3       # NEW: DAC drives the bias node through this
C1    = 1e-9      # node capacitance                               (sec 1)
FC    = 159.0     # post-buffer filter corner                      (sec 4)
LSB   = 20.0/2**16          # ADS8588H on +/-10 V
FS    = 500e3

print("=" * 72)
print("1. THE ALGEBRA  --  the sensor's own EMF cancels out")
print("=" * 72)
print("""
  node = (E/Rt + Vb/R2) / (1/Rt + 1/R2),   Rt = Rs + R1

  Take two bias states and subtract:

      dV / dVb  =  Rt / (R2 + Rt)        <-- E is gone
      Rt        =  R2 . k / (1 - k),     k = dV/dVb

  E cancels exactly. So this does not need a stable mixture, a warm
  engine or a known lambda -- only that the cell's EMF does not move
  much between the two samples. Op-amp offset, offset drift and the
  bias divider's tolerance cancel with it.
""")

def k_of(Rs):  return (Rs+R1)/(R2+Rs+R1)

print("=" * 72)
print("2. DRIVING IT  --  one DAC pin, no per-channel parts")
print("=" * 72)
print(f"""
  The divider STAYS. A DAC pin drives the bias node through {RDAC/1e3:.0f}k:

     +5VA --[91k]--+--[9.1k]-- AGND        455 mV, Zsrc {RBIAS/1e3:.1f}k
                   |
      DAC --[1k]---+--[100n]-- AGND

  DAC disabled (reset state, high-Z) -> node sits at 455 mV exactly as
  today. Nothing about the parked or open-circuit behaviour changes if
  the firmware never touches it. FAIL-SAFE BY OMISSION.

  With the DAC driving, the divider attenuates it by a known constant:""")
att = RBIAS/(RDAC+RBIAS)
dVdac = 3.0-0.455
dVb   = dVdac*att
print(f"    dVb_node / dVdac = {RBIAS/1e3:.1f}k/({RDAC/1e3:.0f}k+{RBIAS/1e3:.1f}k) = {att:.4f}")
print(f"    DAC swings 0.455 -> 3.000 V  ({dVdac:.3f} V)  ->  dVb = {dVb*1e3:.0f} mV at the node")

print("\n" + "=" * 72)
print("3. RESOLUTION AND PERTURBATION  --  they scale the right way")
print("=" * 72)
print(f"\n  dVb = {dVb*1e3:.0f} mV, R2 = 22M, R1 = 10k, LSB = {LSB*1e6:.0f} uV\n")
print(f"{'cell Rs':>10} {'Rt':>9} {'dV seen':>11} {'LSBs':>8} {'I into cell':>12}"
      f" {'perturbs 0-1V':>14} {'node tau':>10}")
print("-"*80)
rows=[]
for Rs,lab in ((10e3,"hot, new"),(30e3,"hot, typical"),(100e3,"warm/aged"),
               (300e3,"aged - review sec1 FAIL row"),(1e6,"cool or failing"),
               (10e6,"cold"),(float('inf'),"OPEN / unplugged")):
    if math.isinf(Rs):
        dV, I, tau = dVb, 0.0, R2*C1
        Rt=float('inf')
    else:
        Rt = Rs+R1
        dV = dVb*Rt/(R2+Rt)
        I  = dVb/(R2+Rt)
        tau = (Rt*R2/(Rt+R2))*C1
    rows.append((Rs,lab,dV))
    rt = "  open" if math.isinf(Rt) else f"{Rt/1e3:>7.0f}k"
    print(f"{lab.split(',')[0][:10]:>10} {rt:>9} {dV*1e3:>9.2f}mV {dV/LSB:>8.0f}"
          f" {I*1e9:>10.0f}nA {dV/1.0*100:>12.1f}% {tau*1e3:>8.2f}ms")
print("""
  Read the last two columns together, because that is the whole argument:

  * The step is SMALLEST on a healthy cell -- 0.5 % of a 1 V swing at 30k,
    and it is transient -- and LARGEST on a sick one, where the reading was
    worthless anyway. The disturbance self-scales inversely with how much
    you care about the reading underneath it.
  * Injected current peaks at ~115 nA. A zirconia cell does not notice
    115 nA. There is no polarisation and nothing to damage.
  * An unplugged channel gives the full dVb -- a saturated, unmistakable
    signature, not an inference from "it is sitting near 455 mV".""")

print("=" * 72)
print("4. THE ONE REAL PROBLEM  --  E drifts while you measure")
print("=" * 72)
sw = 1.0/0.020     # 1 V in 20 ms, a brisk narrowband transition
print(f"""
  E cancels only if it is the SAME in both samples. A switching narrowband
  slews ~1 V in 20 ms = {sw:.0f} V/s. Two samples 2 ms apart see {sw*2e-3*1e3:.0f} mV of
  drift -- {sw*2e-3/ (rows[1][2]) :.0f}x the {rows[1][2]*1e3:.1f} mV signal at 30k. A single before/after
  pair is not good enough.

  Fix: SQUARE-WAVE the bias node and synchronously detect. Drift becomes a
  common-mode term that the +1/-1 demodulation rejects.

  The modulation frequency is boxed in from both sides:""")
for f in (5,10,50,100,200,500):
    a = 1/math.sqrt(1+(f/FC)**2)
    print(f"    {f:>4} Hz  ->  post-filter gain {a:.3f}   ({(1-a)*100:>4.1f}% loss)"
          f"{'   <-- too near the cell swing' if f<=10 else ''}"
          f"{'   <-- PICK' if f==50 else ''}")
print(f"""
  Below ~10 Hz it collides with the cell's own 1-10 Hz switching; above
  {FC:.0f} Hz the R3/C2 filter of section 4 eats it. 50 Hz sits in the gap with
  {(1-1/math.sqrt(1+(50/FC)**2))*100:.1f} % loss and is 5-50x above anything the cell does.

  50 Hz = 10 ms per half period. Budget inside one half period:
    settle R3/C2  (tau = {1/(2*math.pi*FC)*1e3:.2f} ms)  -> discard 5 tau = {5/(2*math.pi*FC)*1e3:.1f} ms
    settle node   (tau <= {(1e6*R2/(1e6+R2))*C1*1e3:.2f} ms up to Rs = 1M)  -> covered by the same wait
    sample the remaining {10-5/(2*math.pi*FC)*1e3:.1f} ms at 500 kSPS   -> {int((10-5/(2*math.pi*FC)*1e3)*1e-3*FS)} samples""")
n = int((10-5/(2*math.pi*FC)*1e3)*1e-3*FS)*2*25   # both halves, 25 cycles = 0.5 s
print(f"""    25 cycles (0.5 s) -> {n} samples -> noise / {math.sqrt(n):.0f} = {LSB/math.sqrt(n)*1e6:.1f} uV

  Against the {rows[1][2]*1e3:.2f} mV worst case (30k, the healthiest cell and so the
  smallest signal) that is {LSB/math.sqrt(n)/rows[1][2]*100:.2f} % -- better than the sensor is.""")

print("\n" + "=" * 72)
print("5. ABOVE Rs = 1M THE TIME CONSTANT ITSELF IS THE SIGNAL")
print("=" * 72)
print(f"""
  Node tau = (Rt || R2) . C1 reaches {(10e6*R2/(10e6+R2))*C1*1e3:.1f} ms at Rs = 10M and {R2*C1*1e3:.0f} ms open,
  so a 10 ms half period no longer fully settles. That is not a failure --
  incomplete settling at a KNOWN excitation is itself monotonic in Rt, and
  the regime where it happens is the one where the amplitude has already
  saturated. Report "> 1 M" and stop; nothing downstream needs the
  difference between 4 M and 9 M.""")

print("=" * 72)
print("6. WHAT IT REPLACES  --  the heater strategy stops being open loop")
print("=" * 72)
print("""
  This is the same measurement a CJ125 makes on the LSU's Nernst cell at
  its UR pin, and that the legacy firmware read through the ADS1115 to
  run the heater PID. Applied to narrowband it gives:

  1. LIGHT-OFF, MEASURED. Cell impedance falls steeply with temperature,
     so "the sensor is hot enough to believe" becomes a threshold on Rs
     instead of a timer or a coolant-temperature guess. Closed loop can
     start when the sensor says so.

  2. HEATER RAMP, CLOSED LOOP. The PWM ramp from commit e06a6df exists to
     spare the ceramic from thermal shock. Ramping against measured
     impedance targets the ceramic's actual temperature rather than an
     assumed heating curve.

  3. AGEING, TRENDED. review-o2-chain.md sec 1 is an IMPEDANCE table --
     300k is the row that fails the 0.7 V OBD-II amplitude threshold.
     Logging Rs per sensor per trip turns that row from a hazard into a
     scheduled replacement.

  4. FAULT DISCRIMINATION. A lean-looking reading now separates into
     "lean mixture" (Rs normal), "tired sensor" (Rs high), "unplugged"
     (Rs open) and "shorted" (Rs ~ 0) without moving a wire.

  INTEGRATION NOTE, and it is the one that constrains firmware:
  measure in the heater PWM's OFF window. Heater current shares harness
  ground with the cell, and 50 Hz modulation against a PWM'd heater will
  otherwise beat. PWMing the heaters -- already decided -- is what makes
  the off-windows exist, so the two decisions fit together rather than
  competing.""")

print("=" * 72)
print("7. COST")
print("=" * 72)
print("""  One DAC pin (PA4 or PA5, of 35 spare), one 1k, one 100n.
  ZERO per-channel parts -- the bias node is already shared, and the
  ADS8588H samples all channels SIMULTANEOUSLY, so all four cells are
  excited and measured in the same 0.5 s window.
  The two downstream sensors on the STM32's internal ADC share the same
  bias node and get the same measurement for free.""")
