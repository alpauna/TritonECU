# Rebuild roadmap

Starting again, deliberately small. The rule: **nothing enters the tree until it
has been proven on hardware**, and each milestone proves exactly one thing.

## Why restart rather than port

The existing firmware is ~14,500 lines carrying a web UI, FTP server, MQTT,
tar.gz log rotation, a six-chip SPI expander chain and a custom-pin subsystem —
all written against an ESP32-S3 that was never in a truck. It works, but it was
built before any of the vehicle facts in `1999-Ford-F150-4wd-5.42v/` were
known, and one of its core decisions is now known to be wrong:

> Coils and injectors are on MCP23S17 SPI expanders (`coilPins` 264–271,
> `injectorPins` 280–287).

At 6000 rpm one crank degree is **27.8 µs**. An SPI transaction to an expander
is several microseconds *at best*, is not deterministic, and cannot be driven
from a hardware timer. Spark timing cannot live behind a port expander. That is
not a bug to patch; it is a structural assumption that has to change, and it
touches ignition, injection and the pin map together.

The old tree stays in git history and on the `esp32-p4` branch. Proven pieces
get ported forward deliberately — `TuneTable`, `CJ125Controller` and the sensor
maths are worth keeping. Everything else earns its place again.

## Principles

1. **Hard real-time is physically separate.** Spark and injection timing run
   from hardware timers on a dedicated core, touching nothing that can block.
   No SPI, no heap, no logging in that path.
2. **One milestone, one proof.** Each step ends with a specific bench
   observation, not "it compiles".
3. **Wi-Fi and the web UI come late.** They are the least risky and the most
   distracting part. An ECU that runs without them is worth more than a pretty
   dashboard that cannot sync a crank.
4. **Every vehicle fact is cited.** The `1999-Ford-F150-4wd-5.42v/` documents
   are the source of truth; assumptions get tagged, not buried.

## Milestones

| # | Milestone | Proves | Done when |
|---|---|---|---|
| **M0** | Board bring-up | toolchain, upload path, board identity | Boots, reports chip rev / PSRAM / flash over serial, heartbeat runs |
| **M1** | Storage + config | SDMMC, JSON config, persistence | Mounts the TF card, reads and writes a config file, survives reboot |
| **M2** | Analog front end | AD7606C-16 | 8 channels read within 1 % of a known bench voltage |
| **M3** | **Crank sync** | VR conditioning + 36-1 decode | Correct RPM and crank angle from a signal generator, including the missing tooth, from 100 to 7000 rpm |
| **M4** | Cam sync | full engine position | Knows the stroke; 720° position stable across restarts |
| **M5** | Spark output | timed output | Scope shows dwell and advance matching commanded values across rpm |
| **M6** | Injection output | timed output | Scope shows pulse width and phasing; 8 channels sequential |
| **M7** | Sensors → fuel | the maths | MAF/TPS/CHT/IAT feed a fuel calculation; open-loop numbers sane |
| **M8** | Wi-Fi + status page | ESP32-C6 hosted link | Serves live engine state over Wi-Fi |
| **M9** | Knock | piezo channel + DSP | Detects a tap on the block, windowed per cylinder |
| **M10** | Closed loop | CJ125 / wideband | AFR correction converges |
| **M11** | SCP bus | J1850 PWM | Reads the OEM PCM's traffic on the bench first, then the truck |
| **M12** | Transmission node | second board, TWAI link | 4R70W shifts under command |

M3 is the one that matters. It is the highest-risk item in the whole project —
VR amplitude is weakest at cranking, which is exactly when sync must be
established — and nothing downstream is testable until it works.

## Layout

```
firmware/ecu/          self-contained PlatformIO project
  src/                 implementation
  include/             headers
  test/                native unit tests where the maths allows
```

The old tree at the repository root is untouched for now, so both can be built
and compared. It gets removed once the rebuild passes it.
