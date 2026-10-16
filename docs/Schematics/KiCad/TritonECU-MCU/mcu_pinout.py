#!/usr/bin/env python3
"""TritonECU MCU module: the STM32F767ZIT6 (LQFP144) on a 44 x 44 mm board that
replaces the Nucleo-144 on the carrier. Single source of truth for the module's
four edge headers; the carrier footprint (TritonECU-Main/gen_floorplan.py) and
the module's own PCB both read it.

Headers: four 2x18, 1.27 mm pitch, one per side of the QFP. Samtec TFM-118-22
on the module mates with SFM-118-02 on the carrier at 9.91 mm, matching the
10 mm M3 standoffs. Pad geometry below is the generic 1.27 mm through-hole
pattern; check it, and the -A alignment-pin holes, against Samtec's footprint
before layout. Each header carries the pins of the QFP side it
faces, in package order, so the module escape is a straight fan-out:

  A  left    package 1-36,    top -> bottom
  B  bottom  package 37-72,   left -> right
  C  right   package 73-108,  bottom -> top
  D  top     package 109-144, right -> left

Slot k (0..35) is position k // 2 along the header; even slots are the inner
row (nearer the QFP), odd slots the outer. Pad name = side letter + (k + 1),
so odd pad numbers are the inner row.

Mapping rules, applied in package order:
  Pxx           -> the port pin, broken out   (except the crystal pins below)
  VSS, VSSA     -> GND
  VDD, VDDUSB, VDDSDMMC -> +3.3V (fed by the carrier; the module has no regulator)
  NRST, VBAT, BOOT0 -> broken out (carrier watchdog drives NRST; carrier decides VBAT)
  PC14/PC15 (LSE 32.768 kHz), PH0/PH1 (HSE 8 MHz) -> crystals on the module
  VDDA, VREF+   -> on the module: ferrite from VDD, VREF+ tied to VDDA
  VCAP_1/2      -> 2.2 uF each on the module
  PDR_ON        -> VDD on the module (internal supervisor on)
Unused slots are filled with GND, alternately at the start and end of the header.

Usage:  python3 mcu_pinout.py           prints the pinout as a markdown table
"""

LQFP144 = """
    PE2 PE3 PE4 PE5 PE6 VBAT PC13 PC14 PC15 PF0 PF1 PF2
    PF3 PF4 PF5 VSS VDD PF6 PF7 PF8 PF9 PF10 PH0 PH1
    NRST PC0 PC1 PC2 PC3 VDD VSSA VREF+ VDDA PA0 PA1 PA2
    PA3 VSS VDD PA4 PA5 PA6 PA7 PC4 PC5 PB0 PB1 PB2
    PF11 PF12 VSS VDD PF13 PF14 PF15 PG0 PG1 PE7 PE8 PE9
    VSS VDD PE10 PE11 PE12 PE13 PE14 PE15 PB10 PB11 VCAP_1 VDD
    PB12 PB13 PB14 PB15 PD8 PD9 PD10 PD11 PD12 PD13 VSS VDD
    PD14 PD15 PG2 PG3 PG4 PG5 PG6 PG7 PG8 VSS VDDUSB PC6
    PC7 PC8 PC9 PA8 PA9 PA10 PA11 PA12 PA13 VCAP_2 VSS VDD
    PA14 PA15 PC10 PC11 PC12 PD0 PD1 PD2 PD3 PD4 PD5 VSS
    VDDSDMMC PD6 PD7 PG9 PG10 PG11 PG12 PG13 PG14 VSS VDD PG15
    PB3 PB4 PB5 PB6 PB7 BOOT0 PB8 PB9 PE0 PE1 PDR_ON VDD
""".split()   # STM32F767ZITx, package pin 1..144 (KiCad MCU_ST_STM32F7, = DS11532)
assert len(LQFP144) == 144

ON_MODULE = {'PC14', 'PC15', 'PH0', 'PH1', 'VDDA', 'VREF+', 'VCAP_1', 'VCAP_2', 'PDR_ON'}
TO_NET = {'VSS': 'GND', 'VSSA': 'GND', 'VDD': '+3.3V', 'VDDUSB': '+3.3V', 'VDDSDMMC': '+3.3V'}

BOARD = 44.0          # module outline, square, centred on the QFP
STANDOFF = 10.0       # board-to-board, M3, same as the power board V3
HEADER_MPN = 'TFM-118-22-L-D-A'   # module side: Samtec 2x18 1.27 mm shrouded header, through-hole, alignment pins
SOCKET_MPN = 'SFM-118-02-L-D-A'   # carrier side: Samtec 2x18 1.27 mm socket
STACK_NOTE = '9.91 mm mated (Samtec TFM-xx-22 + SFM-xx-02)'
SLOTS = 36            # 2 x 18
PITCH = 1.27
ROW_IN = 15.5         # inner-row distance from the module centre
ROW_OUT = ROW_IN + PITCH
HOLES = [(-17.5, -17.5), (17.5, -17.5), (17.5, 17.5), (-17.5, 17.5)]  # M3 standoffs
HOLE_DRILL, HOLE_PAD = 3.2, 6.0  # as the power board V3 mounting holes
PIN_DRILL, PIN_PAD = 0.65, 1.0   # through-hole 1.27 mm header, as KiCad PinHeader_2x18_P1.27mm

SIDES = 'ABCD'


def side_signals(side):
    """Signal list for one header, in slot order."""
    i = SIDES.index(side)
    sig = []
    for name in LQFP144[i * 36:(i + 1) * 36]:
        if name in ON_MODULE:
            continue
        sig.append((TO_NET.get(name, name), LQFP144.index(name) + 1 if name not in TO_NET else None))
    assert len(sig) <= SLOTS, (side, len(sig))
    front = True
    while len(sig) < SLOTS:
        if front: sig.insert(0, ('GND', None))
        else: sig.append(('GND', None))
        front = not front
    return sig


def slot_xy(side, k):
    """Pad centre relative to the module centre, KiCad axes (y down), top view."""
    along = (k // 2 - (SLOTS // 2 - 1) / 2) * PITCH
    d = ROW_IN if k % 2 == 0 else ROW_OUT
    if side == 'A': return (-d, along)
    if side == 'B': return (along, d)
    if side == 'C': return (d, -along)
    return (-along, -d)


def module_pins():
    """[(pad, x, y, net)] for all 144 header pins."""
    out = []
    for s in SIDES:
        for k, (net, _) in enumerate(side_signals(s)):
            x, y = slot_xy(s, k)
            out.append((f'{s}{k + 1}', round(x, 4), round(y, 4), net))
    return out


def check():
    pins = module_pins()
    ports = [n for _, _, _, n in pins if n.startswith('P')]
    assert len(ports) == len(set(ports)), 'port pin on two headers'
    want = {n for n in LQFP144 if n.startswith('P') and n not in ON_MODULE}
    assert set(ports) == want, want ^ set(ports)
    for n in ('NRST', 'VBAT', 'BOOT0'):
        assert sum(p[3] == n for p in pins) == 1, n
    return pins


if __name__ == '__main__':
    pins = check()
    print('| pad | net | pad | net |\n|---|---|---|---|')
    for s in SIDES:
        sp = [p for p in pins if p[0][0] == s]
        for a, b in zip(sp[0::2], sp[1::2]):
            print(f'| {a[0]} | {a[3]} | {b[0]} | {b[3]} |')
    io = sum(p[3].startswith('P') for p in pins)
    print(f'\n{io} port pins, {sum(p[3] == "GND" for p in pins)} GND, '
          f'{sum(p[3] == "+3.3V" for p in pins)} +3.3V, plus NRST, VBAT, BOOT0')
