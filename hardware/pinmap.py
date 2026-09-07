#!/usr/bin/env python3
"""ESP32-P4 pin budget for the ECU. Definitive count, not an estimate."""

ALL = set(range(55))                       # ESP32-P4: GPIO0-54

COMMITTED = {
    "ESP32-C6 SDIO (Wi-Fi)": [14, 15, 16, 17, 18, 19],
    "ESP32-C6 reset":        [54],
    "Boot strapping":        [35, 36],
    "UART0 console/flash":   [37, 38],
    "SD card, SDMMC 4-bit":  [39, 40, 41, 42, 43, 44, 45],
}

CORE = {
    "Coils 1-8":             [46, 47, 48, 49, 50, 51, 52, 53],
    "Injectors 1-8":         [26, 27, 28, 29, 30, 31, 32, 33],
    "VR: CKP, CMP, OSS":     [20, 21, 22],
    "SPI SCK/MOSI/MISO":     [34, 23, 2],
    "SPI CS: ADC, expander": [3, 6],
    "AD7606 CONVST, BUSY":   [4, 5],
    "I2C SDA, SCL":          [1, 24],
    "PWM: TCC, EPC, IAC":    [10, 11, 12],
    "Tach out, VSS out":     [13, 0],
    "Ignition arm (OE1)":    [25],
}

DEFERRED_BUT_ROUTED = {
    "J1850 TX_P/TX_N/RX":    [7, 8, 9],
    "Watchdog kick (OE2)":   [],           # strap low in v1
}


def show(title, groups):
    total = 0
    print(f"\n{title}")
    for name, pins in groups.items():
        if pins:
            print(f"  {name:24} {len(pins):2d}  {sorted(pins)}")
            total += len(pins)
    print(f"  {'':24} {total:2d}  total")
    return total


c = show("COMMITTED (cannot be reused)", COMMITTED)
k = show("CORE — engine + transmission", CORE)
d = show("DEFERRED but routed on v1", DEFERRED_BUT_ROUTED)

free = ALL - {p for g in COMMITTED.values() for p in g}
used = {p for g in CORE.values() for p in g} | {p for g in DEFERRED_BUT_ROUTED.values() for p in g}

# Sanity: no pin assigned twice, and nothing assigned to a committed pin.
from collections import Counter
dup = [p for p, n in Counter([p for g in list(CORE.values()) + list(DEFERRED_BUT_ROUTED.values())
                              for p in g]).items() if n > 1]
clash = sorted(used & {p for g in COMMITTED.values() for p in g})

print(f"\n{'='*52}")
print(f"  GPIOs on the P4                {len(ALL):3d}")
print(f"  Committed                      {c:3d}")
print(f"  Available                      {len(free):3d}")
print(f"  Core (engine + transmission)   {k:3d}")
print(f"  Deferred but routed            {d:3d}")
print(f"  ASSIGNED                       {k+d:3d}")
print(f"  SPARE                          {len(free)-(k+d):3d}")
print(f"{'='*52}")
print(f"  duplicate assignments : {dup if dup else 'none'}")
print(f"  clashes with committed: {clash if clash else 'none'}")
print(f"  spare pins            : {sorted(free - used)}")
print(f"\n  Levers if more is ever needed:")
print(f"    SD in 1-bit SDMMC (drop D1-D3)          +3")
print(f"    Semi-sequential injection (8 -> 4)      +4")
print(f"    Tach/VSS over SCP instead of discrete   +2")
