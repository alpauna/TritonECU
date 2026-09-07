# Getting a Nucleo-144 (STM32F767ZI) live on Linux

Written from an actual first-time bring-up, including the two things that
stopped it. Total time once you know them: a few minutes.

The only genuine blocker is **step 3**. Everything else works first try.

---

## 1. Prerequisites

PlatformIO Core. If `pio` is not on your PATH it usually lives at
`~/.platformio/penv/bin/pio`.

```bash
~/.platformio/penv/bin/pio --version
```

The STM32 platform installs itself on first build — no separate step. For
reference, this bring-up used `ststm32 19.7.1`.

## 2. Minimal `platformio.ini`

```ini
[env:nucleo]
platform = ststm32
board = nucleo_f767zi
framework = arduino

upload_protocol = stlink
debug_tool = stlink
monitor_speed = 115200

build_flags = -Wall
```

`nucleo_f767zi` ships with the platform; nothing to add.

First build pulls the toolchain and framework (~50 s, one time):

```bash
pio run -e nucleo
```

Downloads `toolchain-gccarmnoneeabi`, `framework-cmsis`, `framework-cmsis-dsp`
and `framework-arduinoststm32`.

## 3. The udev rule — this is the one that stops you

Out of the box, uploading fails with:

```
Error: libusb_open() failed with LIBUSB_ERROR_ACCESS
Error: open failed
** OpenOCD init failed **
```

That is **not** a board or wiring fault. The ST-Link enumerates fine, but its
raw USB device is owned `root:root` with mode `crw-rw-r--`, so OpenOCD cannot
claim it for SWD:

```bash
lsusb | grep 0483:374b          # ST-LINK/V2.1 is present
ls -la /dev/bus/usb/001/0NN     # ...but crw-rw-r-- root root
```

Note the **serial port works from the start** if you are in `dialout` — only
the SWD interface is blocked. That is what makes the failure confusing.

### Fix

```bash
curl -fsSL https://raw.githubusercontent.com/platformio/platformio-core/develop/platformio/assets/system/99-platformio-udev.rules \
  | sudo tee /etc/udev/rules.d/99-platformio-udev.rules >/dev/null
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Or, for ST-Link alone:

```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="0483", ATTR{idProduct}=="374b", MODE="0666"' \
  | sudo tee /etc/udev/rules.d/99-stlink.rules >/dev/null
sudo udevadm control --reload-rules && sudo udevadm trigger
```

**Then unplug and replug the board.** udev applies rules on device *add*, so an
already-enumerated ST-Link keeps its old permissions. Skipping the replug is
the most common reason the fix "does not work".

Verify:

```bash
ls -la /dev/bus/usb/001/0NN     # should now be crw-rw-rw-
```

## 4. Upload

```bash
pio run -e nucleo -t upload
```

Expect `Programming Finished` / `Verified OK` in about 2.5 s.

## 5. Serial console

The ST-Link provides a USB CDC virtual COM port. **Address it by its by-id
path**, not `/dev/ttyACMn` — the numbering shifts when other boards are
plugged in:

```bash
ls /dev/serial/by-id/ | grep STLink
# usb-STMicroelectronics_STM32_STLink_<serial>-if02
```

Add to `platformio.ini`:

```ini
monitor_port = /dev/serial/by-id/usb-STMicroelectronics_STM32_STLink_<serial>-if02
```

The `-if02` suffix matters: the ST-Link is a composite device and `if02` is the
VCP interface.

---

## Two quirks worth knowing before they confuse you

### The VCP and SWD share one USB device

Resetting the target over SWD — `openocd ... reset`, or a debugger connect —
**disconnects the serial port**. So a boot banner is genuinely hard to catch:
by the time the port re-enumerates, the message has been printed.

Do not fight it. **Give the firmware a command that reprints on demand:**

```cpp
while (Serial.available()) {
    if (Serial.read() == 'i') reportIdentity();
}
```

Then the host opens the port at leisure and asks. Useful on a bench anyway.

### The VCP drops bytes on long bursts

At 115200, a multi-line burst loses the occasional character. Steady output is
clean — 4/4 heartbeat lines intact over 22 s in testing — but a 15-line banner
arrives with gaps.

Cosmetic for a console. **Do not build datalogging on it.** Options: drop to
57600, insert a short delay between lines, or use a separate UART or Ethernet
for anything that matters.

*Also worth knowing: a host-side reconnect loop makes this look far worse than
it is. Each reopen discards the kernel buffer. Hold the port open.*

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `LIBUSB_ERROR_ACCESS` on upload | no udev rule for ST-Link | step 3, **and replug** |
| Fix applied but still fails | board not replugged | unplug/replug |
| Serial works, upload does not | VCP is unprivileged, SWD is not | step 3 |
| Garbled serial | host reconnecting on every error | hold the port open |
| Console silent after debugging | SWD reset dropped the VCP | reopen the port; use the `i` command |
| `pio device monitor` crashes | needs a TTY, not a pipe | read the port directly, or run interactively |
| Wrong `/dev/ttyACMn` | numbering shifts between boards | use the `by-id` path |

## Verifying it actually works

Have the firmware read its own identity registers rather than trusting the
build configuration:

| What | Where | Expected on an F767ZI |
|---|---|---|
| Device ID / revision | `DBGMCU->IDCODE` | **0x451**, rev 0x1001 |
| Flash size | `*(uint16_t*)0x1FF0F442` | **2048** (KB) |
| Unique ID | `0x1FF0F420`, 96-bit | non-zero |
| Core clock | `SystemCoreClock` | **216 MHz** |
| Reset cause | `RCC->CSR` | power-on, pin, watchdog… |

`0x451` is the STM32F76x/F77x family. Anything else means the board file and
the silicon disagree — worth catching before trusting a pin assignment.

`SystemCoreClock` reading 216 MHz confirms the PLL is configured; **16 MHz
would mean it fell back to HSI**, which is a silent and very confusing failure
mode because everything still runs, just slowly and with wrong baud rates.
