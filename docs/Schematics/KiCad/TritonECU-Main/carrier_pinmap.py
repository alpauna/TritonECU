#!/usr/bin/env python3
"""TritonECU carrier pin map: every carrier function on an STM32F767ZIT6 port
pin, and through mcu_pinout.py, on a module header pad. The source of truth for
the carrier schematic and for firmware's Board.h.

Checked on every run:
  * the pin is a port pin broken out on the module, and not reserved
    (SWD/SWO on the STDC14, the ST-Link VCP)
  * no pin is used twice (the CAN RXD net deliberately lands on two pins)
  * the function exists on that pin, from stm32f767zi_af.json (CubeMX data,
    gen_af_table.py) plus the WKUP pins from the datasheet
  * signals that need an interrupt sit on distinct pin numbers: the STM32 has
    one EXTI line per pin NUMBER, shared across ports
  * a timer runs in one mode only: free-running for scheduling and capture, or
    fixed-period PWM; the two cannot share a counter
  * the J1850 TX pair shares a port, so one BSRR write switches both

Usage:  python3 carrier_pinmap.py          check, print a summary
        python3 carrier_pinmap.py --md     the pin table as markdown (docs/carrier-pinmap.md)

Decided 2026-10-17 with the user. The full demand was 115 signals against 105
usable pins (the pin-budget.md figure of 83 left out the internal ADC inputs, the
SD card, USB, the wake pins and most of the power-board signals). Trimmed with no
loss of function:
  - console UART dropped: the STLINK-V3 VCP on the module's STDC14 (USART3) is it
  - ADS8588H OS0-2 and RANGE strapped (0R options), FRSTDATA not wired
  - SD card on SDMMC2 1-bit (config and logs only)
  - power board 3_GOOD not wired: if 3.3 V fails the MCU cannot read it
  - TPS2H160B DIAG_EN tied high
  - the 8 slow diagnostic analog channels (6 drain senses, 2 solenoid supply
    senses) behind a 74HC4051, analog-mux-scan.md: 8 ADC pins -> 1 + 3 selects
"""
import json, os, re, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'TritonECU-MCU'))
import mcu_pinout as mp

# Standby wake-up pins (DS11532 / RM0410 PWR_CSR2); PI8/PI11 are not on LQFP144
WKUP = {'PA0': 'WKUP1', 'PA2': 'WKUP2', 'PC1': 'WKUP3', 'PC13': 'WKUP4'}
RESERVED = {'PA13': 'SWDIO (STDC14)', 'PA14': 'SWCLK (STDC14)', 'PB3': 'SWO (STDC14)',
            'PD8': 'USART3 TX, ST-Link VCP (STDC14)', 'PD9': 'USART3 RX, ST-Link VCP (STDC14)'}

# Timer modes. 'sched': free-running counter, output compare / input capture at
# arbitrary times. 'pwm': fixed period, the channels share it.
TIMER_MODE = {'TIM1': 'sched', 'TIM2': 'sched', 'TIM3': 'sched', 'TIM4': 'sched', 'TIM8': 'sched',
              'TIM12': 'sched', 'TIM5': 'sched', 'TIM9': 'pwm', 'TIM10': 'pwm', 'TIM11': 'pwm',
              'TIM13': 'pwm'}

# (net, pin, function needed, irq, group, note)
#   function: an AF name from the table (TIM4_CH1, SPI3_SCLK, ...), 'ADC' (any
#   ADCx_INy), 'ADC1' (on ADC1, for the fast knock path), 'DAC_OUT1', a WKUPn,
#   or 'GPIO'.
SIGNALS = [
    # --- ignition: 8 x COP, 74HCT541 #1 -> ISL9V3040. Cylinder numbers.
    ('COIL1', 'PD12', 'TIM4_CH1', False, 'ignition', ''),
    ('COIL2', 'PD13', 'TIM4_CH2', False, 'ignition', ''),
    ('COIL3', 'PD14', 'TIM4_CH3', False, 'ignition', ''),
    ('COIL4', 'PD15', 'TIM4_CH4', False, 'ignition', ''),
    ('COIL5', 'PC6',  'TIM8_CH1', False, 'ignition', ''),
    ('COIL6', 'PC7',  'TIM8_CH2', False, 'ignition', ''),
    ('COIL7', 'PC8',  'TIM8_CH3', False, 'ignition', ''),
    ('COIL8', 'PC9',  'TIM8_CH4', False, 'ignition', ''),
    ('COIL_ARM', 'PD11', 'GPIO', False, 'ignition', '74HCT541 #1 OE1: engine position known, ignition armed'),
    ('WDI', 'PD10', 'GPIO', False, 'ignition', 'TPS3823A-33 kick; its RESET drives OE2 of #1 and OE of #3. NO pull resistor'),
    # --- injection: 8 x ZXMS6005DGQ, direct
    ('INJ1', 'PE9',  'TIM1_CH1', False, 'injection', ''),
    ('INJ2', 'PE11', 'TIM1_CH2', False, 'injection', ''),
    ('INJ3', 'PE13', 'TIM1_CH3', False, 'injection', ''),
    ('INJ4', 'PE14', 'TIM1_CH4', False, 'injection', ''),
    ('INJ5', 'PB4',  'TIM3_CH1', False, 'injection', ''),
    ('INJ6', 'PB5',  'TIM3_CH2', False, 'injection', ''),
    ('INJ7', 'PB14', 'TIM12_CH1', False, 'injection', ''),
    ('INJ8', 'PB15', 'TIM12_CH2', False, 'injection', ''),
    # --- position and speed: 3 x MAX9926
    ('CKP', 'PA15', 'TIM2_CH1', False, 'vr', '36-1 crank; capture on the 32-bit TIM2 timebase'),
    ('CMP', 'PB10', 'TIM2_CH3', False, 'vr', 'cam; capture on TIM2'),
    ('OSS', 'PB6', 'GPIO', True, 'vr', 'output shaft; EXTI + timestamp'),
    ('TSS', 'PB7', 'GPIO', True, 'vr', 'turbine shaft, pin 59; EXTI + timestamp'),
    ('TC_SPEED', 'PE0', 'GPIO', True, 'vr', 'transfer case, pin 7; EXTI + timestamp'),
    # --- ADS8588H, SPI3
    ('ADC_SCK', 'PC10', 'SPI3_SCLK', False, 'adc', ''),
    ('ADC_MISO', 'PC11', 'SPI3_MISO', False, 'adc', 'DOUTA'),
    ('ADC_CS', 'PD2', 'GPIO', False, 'adc', 'software chip select'),
    ('ADC_CONVST', 'PB11', 'TIM2_CH4', False, 'adc', 'CONVSTA+B; compare output on the crank timebase'),
    ('ADC_BUSY', 'PD3', 'GPIO', True, 'adc', 'falling edge = data ready'),
    ('ADC_RESET', 'PD4', 'GPIO', False, 'adc', 'active high; OS0-2, RANGE strapped, FRSTDATA not wired'),
    # --- internal ADC, analog (3.3 V full scale)
    ('KNOCK', 'PC3', 'ADC1', False, 'analog', '200 kSPS on ADC1, adc-front-end.md'),
    ('DPFE', 'PF3', 'ADC', False, 'analog', ''),
    ('TFT', 'PF4', 'ADC', False, 'analog', 'tft-sensor.md'),
    ('O2_DN1', 'PF6', 'ADC', False, 'analog', 'HO2S #12, buffered'),
    ('O2_DN2', 'PF7', 'ADC', False, 'analog', 'HO2S #22, buffered'),
    ('FP_MON', 'PF10', 'ADC', False, 'analog', 'fuel pump monitor'),
    ('TR3A', 'PC0', 'ADC', False, 'analog', 'three-state, 4R100 270R; 4r100-deltas.md'),
    ('VREF_CS', 'PC1', 'ADC', False, 'analog', 'TPS2H160B current sense, via 4.7k + Schottky'),
    ('VREF_STB', 'PC2', 'ADC', False, 'analog', 'VREF feed short-to-battery divider'),
    ('MUX_OUT', 'PA2', 'ADC', False, 'analog', '74HC4051 COM: drain sense x6 (HO2S x4, EVAP, vent), supply sense 1138, 391'),
    ('MUX_S0', 'PB0', 'GPIO', False, 'analog', '74HC4051 select'),
    ('MUX_S1', 'PB1', 'GPIO', False, 'analog', '74HC4051 select'),
    ('MUX_S2', 'PA7', 'GPIO', False, 'analog', '74HC4051 select'),
    ('O2_BIAS', 'PA4', 'DAC_OUT1', False, 'analog', 'DAC -> 1k -> 455 mV bias node, o2-input-stage.md'),
    # --- solenoids and heaters: 74HCT541 #3 @ 5 V -> NCV8405A x8 (full)
    ('HTR11', 'PG2', 'GPIO', False, 'solenoid', 'HO2S #11 heater, software PWM (ramp, stagger)'),
    ('HTR21', 'PG3', 'GPIO', False, 'solenoid', 'HO2S #21 heater'),
    ('HTR12', 'PG4', 'GPIO', False, 'solenoid', 'HO2S #12 heater'),
    ('HTR22', 'PG5', 'GPIO', False, 'solenoid', 'HO2S #22 heater'),
    ('VENT', 'PG6', 'GPIO', False, 'solenoid', 'canister vent, pin 67'),
    ('IMCC', 'PG7', 'GPIO', False, 'solenoid', 'pin 46'),
    ('SSA', 'PG8', 'GPIO', False, 'solenoid', 'pin 27'),
    ('SSB', 'PB12', 'GPIO', False, 'solenoid', 'pin 1'),
    # --- PWM loads: 74HCT541 #2 @ 5 V
    ('EVAP', 'PE5', 'TIM9_CH1', False, 'pwm', 'purge, pin 56; shares TIM9 period with EGR'),
    ('EGR', 'PE6', 'TIM9_CH2', False, 'pwm', 'EVR, pin 47'),
    ('EPC', 'PB8', 'TIM10_CH1', False, 'pwm', 'NCV8408B, pin 81, >= 200 Hz, own timer'),
    ('TCC', 'PB9', 'TIM11_CH1', False, 'pwm', 'pin 54, own timer'),
    ('IAC', 'PF8', 'TIM13_CH1', False, 'pwm', 'pin 83, own timer'),
    ('VSS_OUT', 'PA3', 'TIM5_CH4', False, 'pwm', 'pin 68 open drain via NCV8405A #13; frequency by compare toggle'),
    ('CCS', 'PB13', 'GPIO', False, 'pwm', 'coast clutch, pin 20, #2 ch7'),
    ('PWM_OE', 'PA8', 'GPIO', False, 'pwm', '74HCT541 #2 OE, software-releasable'),
    # --- relays: TBD62083AFNG, direct at 3.3 V
    ('FPUMP', 'PE7', 'GPIO', False, 'relay', ''),
    ('FAN1', 'PE12', 'GPIO', False, 'relay', ''),
    ('FAN2', 'PE15', 'GPIO', False, 'relay', ''),
    ('ACC', 'PG0', 'GPIO', False, 'relay', 'A/C clutch'),
    # --- switch inputs, conditioned
    ('TR1', 'PF11', 'GPIO', True, 'input', 'pin 34'),
    ('TR2', 'PF12', 'GPIO', True, 'input', 'pin 49'),
    ('TR4', 'PF14', 'GPIO', True, 'input', 'pin 50'),
    ('BRAKE', 'PF15', 'GPIO', True, 'input', ''),
    ('ACP', 'PE10', 'GPIO', True, 'input', 'A/C pressure'),
    ('4X4L', 'PE8', 'GPIO', True, 'input', '4x4 low'),
    # --- VREF: TPS2H160B-Q1, DIAG_EN tied high
    ('VREF_EN', 'PB2', 'GPIO', False, 'vref', ''),
    ('VREF_IN1', 'PF13', 'GPIO', False, 'vref', ''),
    ('VREF_IN2', 'PC4', 'GPIO', False, 'vref', ''),
    ('VREF_SEL', 'PC5', 'GPIO', False, 'vref', ''),
    ('VREF_FAULT', 'PF9', 'GPIO', True, 'vref', ''),
    # --- SCP / J1850 PWM: DRV8837 + TLV7031
    ('J1850_TXP', 'PG13', 'GPIO', False, 'j1850', 'same port as TXN: one BSRR write'),
    ('J1850_TXN', 'PG14', 'GPIO', False, 'j1850', ''),
    ('J1850_NSLEEP', 'PG15', 'GPIO', False, 'j1850', ''),
    ('J1850_RX', 'PA1', 'TIM2_CH2', False, 'j1850', 'capture on the TIM2 timebase'),
    # --- CAN: TJA1042T/3
    ('CAN_RX', 'PD0', 'CAN1_CAN_RD', False, 'can', ''),
    ('CAN_TX', 'PD1', 'CAN1_CAN_TD', False, 'can', ''),
    ('CAN_STB', 'PD5', 'GPIO', False, 'can', 'not strapped: standby is what reaches 20 uA'),
    ('CAN_RX_WAKE', 'PA0', 'WKUP1', False, 'can', 'SAME NET as CAN_RX: Standby wakes only on a WKUP pin'),
    # --- wake, power board, I2C
    ('IGN_WAKE', 'PC13', 'WKUP4', True, 'power', 'key-on sense, conditioned; also key-off detect'),
    ('I2C_SDA', 'PF0', 'I2C2_SDA', False, 'power', 'power board, INA238, baro'),
    ('I2C_SCL', 'PF1', 'I2C2_SCL', False, 'power', ''),
    ('M_SYNC', 'PE3', 'GPIO', False, 'power', 'MAX25239 SYNC; 10k pull-down on the power board'),
    ('U_SHDN', 'PF2', 'GPIO', False, 'power', ''),
    ('ENOUT', 'PE2', 'GPIO', True, 'power', '3.3_ENOUT, LTC4364 enable'),
    ('FLT', 'PE4', 'GPIO', True, 'power', ''),
    ('VIN_ALERT', 'PF5', 'GPIO', True, 'power', ''),
    ('5_GOOD', 'PG1', 'GPIO', True, 'power', ''),
    # --- storage, USB
    ('SD_CK', 'PD6', 'SDMMC2_SD_CK', False, 'storage', '1-bit'),
    ('SD_CMD', 'PD7', 'SDMMC2_SD_CMD', False, 'storage', ''),
    ('SD_D0', 'PG9', 'SDMMC2_SD_DATA0', False, 'storage', ''),
    ('USB_DM', 'PA11', 'USB_OTG_FS_USB_OTG_FS', False, 'usb', 'tuning path'),
    ('USB_DP', 'PA12', 'USB_OTG_FS_USB_OTG_FS', False, 'usb', ''),
    ('USB_VBUS', 'PA9', 'USB_OTG_FS_USB_OTG_FS', False, 'usb', 'via divider'),
    # --- test header, 3.3 V, stops at the header
    ('TACH', 'PA5', 'GPIO', False, 'test', 'software square wave'),
    ('SPEED', 'PA6', 'GPIO', False, 'test', 'software square wave'),
]


def af_table():
    return json.load(open(os.path.join(HERE, 'stm32f767zi_af.json')))['pins']


def module_pads():
    """{port pin: header pad} for every port pin on the module."""
    out = {}
    for pad, _, _, net in mp.module_pins():
        if re.fullmatch(r'P[A-K]\d+', net):
            out[net] = pad
    return out


def has_function(af, pin, need):
    fns = af.get(pin, [])
    if need == 'GPIO':
        return True
    if need == 'ADC':
        return any(f.startswith('ADC') for f in fns)
    if need == 'ADC1':
        return any(f.startswith('ADC1_') for f in fns)
    if need.startswith('WKUP'):
        return WKUP.get(pin) == need
    return need in fns


def check():
    af, pads = af_table(), module_pads()
    errors = []
    used = Counter(p for _, p, *_ in SIGNALS)
    for net, pin, need, irq, group, note in SIGNALS:
        if pin not in pads:
            errors.append(f'{net}: {pin} is not a port pin on the module')
        if pin in RESERVED:
            errors.append(f'{net}: {pin} is reserved ({RESERVED[pin]})')
        if used[pin] > 1:
            errors.append(f'{net}: {pin} used {used[pin]} times')
        if not has_function(af, pin, need):
            errors.append(f'{net}: {pin} has no {need} (has {af.get(pin)})')
    lines = defaultdict(list)
    for net, pin, need, irq, *_ in SIGNALS:
        if irq:
            lines[int(pin[2:])].append(f'{net}({pin})')
    for n, nets in sorted(lines.items()):
        if len(nets) > 1:
            errors.append(f'EXTI{n} shared: {", ".join(nets)}')
    timers = defaultdict(list)
    for net, pin, need, *_ in SIGNALS:
        m = re.match(r'(TIM\d+)_CH\d', need)
        if m:
            timers[m.group(1)].append(net)
            if m.group(1) not in TIMER_MODE:
                errors.append(f'{net}: {m.group(1)} has no mode in TIMER_MODE')
    chans = Counter(need for _, _, need, *_ in SIGNALS if re.match(r'TIM\d+_CH\d$', need))
    errors += [f'{c} used twice' for c, k in chans.items() if k > 1]
    port = {net: pin[1] for net, pin, *_ in SIGNALS}
    if port['J1850_TXP'] != port['J1850_TXN']:
        errors.append('J1850 TX pair on different ports')
    return errors, pads, timers, lines


def markdown(pads):
    sides = {s: [] for s in mp.SIDES}
    by_pin = {pin: (net, need, group, note) for net, pin, need, _, group, note in SIGNALS}
    for pin, pad in pads.items():
        sides[pad[0]].append((int(pad[1:]), pad, pin))
    out = ['| pad | pin | net | function | group | note |', '|---|---|---|---|---|---|']
    for s in mp.SIDES:
        for _, pad, pin in sorted(sides[s]):
            if pin in RESERVED:
                out.append(f'| {pad} | {pin} | — | reserved | module | {RESERVED[pin]} |')
            elif pin in by_pin:
                net, need, group, note = by_pin[pin]
                out.append(f'| {pad} | {pin} | **{net}** | {need} | {group} | {note} |')
            else:
                out.append(f'| {pad} | {pin} | *spare* | | | |')
    return '\n'.join(out)


if __name__ == '__main__':
    errors, pads, timers, lines = check()
    if '--md' in sys.argv:
        print(markdown(pads))
        sys.exit(1 if errors else 0)
    for e in errors:
        print('ERROR', e)
    free = sorted(set(pads) - {p for _, p, *_ in SIGNALS} - set(RESERVED), key=lambda p: (p[1], int(p[2:])))
    print(f'{len(SIGNALS)} signals on {len({p for _, p, *_ in SIGNALS})} pins; '
          f'{len(pads)} port pins, {len(RESERVED)} reserved, {len(free)} spare: {" ".join(f"{p}({pads[p]})" for p in free)}')
    print('EXTI lines used:', ' '.join(f'{n}:{v[0]}' for n, v in sorted(lines.items())),
          f'- {16 - len(lines)} free')
    for t in sorted(timers, key=lambda s: int(s[3:])):
        print(f'  {t:5s} {TIMER_MODE.get(t, "?"):5s} {", ".join(timers[t])}')
    sys.exit(1 if errors else 0)
