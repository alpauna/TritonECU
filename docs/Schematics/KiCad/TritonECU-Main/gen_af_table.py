#!/usr/bin/env python3
"""Extract the STM32F767ZIT6 (LQFP144) pin functions from STM32duino's generated
PeripheralPins.c (CubeMX data) into stm32f767zi_af.json, so carrier_pinmap.py
can check every assignment against the silicon without the toolchain installed.

Usage:  python3 gen_af_table.py [path/to/PeripheralPins.c]
"""
import json, os, re, sys

SRC = os.path.expanduser('~/.platformio/packages/framework-arduinoststm32/variants/STM32F7xx/'
                         'F765Z(G-I)T_F767Z(G-I)T_F777ZIT/PeripheralPins.c')

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else SRC
    text = open(src).read()
    af = {}
    for table, body in re.findall(r'PinMap PinMap_(\w+)\[\] = \{(.*?)\n\};', text, re.S):
        for line in body.splitlines():
            line = line.strip()
            if line.startswith('//'):
                continue
            m = re.match(r'\{(P[A-K])_(\d+)(?:_ALT\d)?,\s*(\w+),.*?\}(?:,\s*//\s*(.*))?', line)
            if not m:
                continue
            pin = f'{m.group(1)}{int(m.group(2))}'
            periph, comment = m.group(3), (m.group(4) or '').strip()
            if table == 'TIM':
                fn = comment                                  # TIM2_CH1, TIM1_CH1N
            elif table in ('ADC', 'DAC'):
                fn = comment.split()[0] if comment else periph   # ADC1_IN0, DAC_OUT1
            else:
                kind = table.replace('UART_', '').replace('SPI_', '').replace('I2C_', '')
                fn = f'{periph}_{kind}'                       # SPI2_SCLK, USART2_TX, CAN1_RD
            if fn:
                af.setdefault(pin, [])
                if fn not in af[pin]:
                    af[pin].append(fn)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stm32f767zi_af.json')
    json.dump({'source': 'STM32duino ' + os.path.relpath(src, os.path.dirname(src) + '/../..'),
               'pins': dict(sorted(af.items(), key=lambda kv: (kv[0][1], int(kv[0][2:]))))},
              open(out, 'w'), indent=1)
    print(f'{len(af)} pins -> {out}')

if __name__ == '__main__':
    main()
