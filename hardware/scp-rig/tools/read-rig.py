#!/usr/bin/env python3
"""Read the SCP rig's console.

Exists because `cat /dev/ttyACM0` silently returns nothing. The arduino-pico
USB-CDC stack discards writes until the host raises DTR, and cat never does, so
a perfectly healthy rig looks dead. This asserts DTR and then just prints.

    ./tools/read-rig.py              # follow until Ctrl-C
    ./tools/read-rig.py -s 20        # stop after 20 seconds
    ./tools/read-rig.py -p /dev/ttyACM1
"""
import argparse
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("pyserial missing. Try: ~/.platformio/penv/bin/python tools/read-rig.py")

ap = argparse.ArgumentParser()
ap.add_argument("-p", "--port", default="/dev/ttyACM0")
ap.add_argument("-b", "--baud", type=int, default=115200)
ap.add_argument("-s", "--seconds", type=float, default=0, help="0 = follow forever")
args = ap.parse_args()

try:
    port = serial.Serial(args.port, args.baud, timeout=0.5)
except serial.SerialException as e:
    sys.exit(f"cannot open {args.port}: {e}")

port.dtr = True          # the whole reason this script exists
port.rts = True

start = time.time()
seen = False
try:
    while args.seconds == 0 or time.time() - start < args.seconds:
        chunk = port.read(4096)
        if chunk:
            seen = True
            sys.stdout.write(chunk.decode("utf-8", "replace"))
            sys.stdout.flush()
except KeyboardInterrupt:
    pass
finally:
    port.close()

if not seen:
    print(f"\n[no data in {args.seconds or time.time() - start:.0f}s]", file=sys.stderr)
    print("The rig prints every 5 s unconditionally, so silence means it is not "
          "running setup() to completion — not that the bus is quiet.", file=sys.stderr)
    sys.exit(1)
