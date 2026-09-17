# Power chain review — after this session's additions

The power board is **already drawn and twice reviewed** —
[`schematic-review-power.md`](schematic-review-power.md) and
[`schematic-review-power-v2.md`](schematic-review-power-v2.md). So this is not a
pre-schematic review. It asks a different question:

> **Does the power chain still add up, after everything hung on it since?**

A VREF supply, an SCP transceiver, a second gate buffer, a requirement that the
expander chain runs at 5 V, and a dozen sense dividers were all added without
anyone returning to the budget.

---

## 1. IMPORTANT — the 5 V budget counts a radio that was dropped and an MCU that was replaced

[`power-supply.md`](power-supply.md)'s load table is from the ESP32-P4 era:

| Stale entry | Claimed | Reality |
|---|--:|---|
| ESP32-P4 @400 MHz + 32 MB PSRAM | ~425 mA | the platform is **STM32F767ZI** |
| **ESP32-C6 module, peak TX** | ~300 mA | **Wi-Fi was dropped, not deferred** |
| VREF | ~25 mA | now on **its own LDO from the protected rail**, not this one |

**750 mA of phantom load** inside a *"~1.5 A realistic peak"*.

Rebuilt against what is actually on the board:

| 3.3 V rail, via TLV62085 | mA |
|---|--:|
| STM32F767ZI @ 216 MHz | 250 |
| SD card, peak | 100 |
| Ethernet PHY | 80 |
| 3.3 V logic, TLV7031, misc | 20 |
| **Total** | **450** → **330 mA** reflected to 5 V at 90 % |

| Direct 5 V loads | mA |
|---|--:|
| MCP23S17 ×2 **at 5 V** — now a requirement, not a choice | 20 |
| **74HCT541 ×2** — ignition, plus the new PWM gate buffer | 10 |
| ADS8588H | 25 |
| MAX9926 ×2 | 20 |
| **DRV8837**, during SCP transmission | 20 |
| **Total** | **95** |

### **5 V rail: ~425 mA, against a table claiming ~1.5 A.**

**The conclusions built on that table survive — they get stronger.**
`power-supply.md` used *"not 3 A"* to kill the argument for interleaving; at
425 mA that argument is not merely weak, it is absent. But a budget that is
wrong by 3.5× is not a budget, and the next decision that leans on it may not be
so forgiving.

> **[DECIDE]** whether the MAX25239's rating is now oversized. Not a fault —
> headroom on a supply is cheap — but it should be a known choice rather than an
> artefact of counting a radio that was deleted.

---

## 2. IMPORTANT — the sleep budget omits the battery-sense divider

[`always-on-domain.md`](always-on-domain.md) totals the parked draw at
**≈780 µA**, and the whole always-on architecture rests on that number staying
under what a parked vehicle tolerates.

The table lists the LTC4364, the STM32 in standby, the always-on converter and
the INA238. **It does not list the ADC's battery-voltage divider**, which sits on
a **permanently powered** rail:

```
47k / 10k from 14 V  =  246 uA     -- 31 % of the entire sleep budget
```

Unlike almost everything else added recently, this one cannot be gated away by
the 5 V rail going down: it is a resistor to ground on a live rail.

**Two fixes, both cheap:**

- **Raise the impedance.** 470 k / 100 k is the same ratio at **24.6 µA** — a
  tenth. The ADC then sees ~85 kΩ of source impedance, which wants a longer
  acquisition window or a small capacitor at the node, exactly as the feed
  dividers do.
- **Or gate it**, with a FET to ground — but that costs a part and a pin to save
  what the resistors already save for free.

---

## 3. Checked and clear — and the session's additions cost almost nothing

| | |
|---|---|
| **VREF LDO on the protected rail** | A new load on the LTC4364's output: 25 mA normally, 275 mA during a feed fault. Against a **4.5–5.0 A** current limit, invisible |
| **Sleep current added this session** | **≈10 µA**, and that is by design — the VREF LDO is `EN`-gated (1 µA disabled), and the TPS2H160B and both LM74700s are powered *from* the gated VREF rail, so they are simply unpowered |
| **All the new sense dividers** | Drain sense, and the 1138/391 supply sense, hang off circuits that are **"HOT IN START OR RUN"** — 361, 391 and 1138 are all switched. At key-off they are dead and the dividers draw **nothing**. That is luck rather than design, but it is worth knowing it held |
| **The one deliberate always-on addition** | The **TLV7031** SCP receiver, kept alive on 3.3 V so a scan tool can wake the ECU. A nanopower comparator — single-digit µA. **[CONFIRM]** against its datasheet |
| **Recirculation into VPWR** | The IAC freewheel returns to the connector side of the shunt, so it never traverses the INA238's sense resistor — see [`output-drivers.md`](output-drivers.md) |
| **Recirculation into the 5 V rail** | An SCP TX short-to-battery pushes ~83 mA into the 5 V rail through the driver's body diode. Against a 425 mA load, absorbed without trace |

---

## Summary

| # | Finding | Action |
|---|---|---|
| 1 | 5 V budget counts 750 mA of deleted hardware; real figure is ~425 mA | rebuild the table; **[DECIDE]** whether the converter is now oversized |
| 2 | Sleep budget omits a 246 µA divider on a permanent rail — 31 % of it | raise it to 470 k / 100 k |

Both findings are the same shape, and it is the shape this session keeps
finding: **a number that was correct when written, consumed by decisions taken
elsewhere, and never revisited.** The ADC budget, the VR channel count and now
the current budget. The fix each time is the same — give the number an owner and
make everything that spends it go through that owner.
