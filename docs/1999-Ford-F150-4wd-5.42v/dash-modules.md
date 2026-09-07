# Instrument panel modules — what the replacement ECU must coexist with

Sources: `Dash-Component-1.png`, `Dash-Component-2.png`, `Dash-Componet-3.png`

The PCM is one node among many. These sheets show the rest, and they settle
three questions the design had open.

## Modules behind the dash

| Ref | Module |
|---|---|
| C239, C240, C241 | **Generic Electronic Module (GEM)** — also listed as **Central Timer Module (CTM)** at C239 |
| C236, C237 | **Instrument cluster** — also hosts PATS logic on this truck |
| C297 | **PATS transceiver module** — the antenna ring at the ignition lock |
| C228 | Data link connector (DLC) — the same C228 as the DLC sheet |
| C222 | RABS module |
| C208 | Restraints control module |
| C216 | Autolamp module |
| C221 | **Transfer case shift relay module** |
| C276, C277 | Rear air suspension (RAS) module |
| C242, C243 | Central junction box (relays) |

### GEM or CTM, not both

C239 is listed for **both** the Central Timer Module and the Generic Electronic
Module. These are alternative fitments — the truck has one or the other
depending on options, with the GEM being the higher-content version (it adds
4WD and other functions to the CTM's lighting, wipers and chimes).

**[CONFIRM ON TRUCK]** which is fitted. It changes what goes quiet when the PCM
is removed, and therefore what the SCP capture in Phase 0 needs to reproduce.

## Switches and inputs relevant to the ECU

| Ref | Input | ECU pin | Note |
|---|---|---|---|
| C252 | Brake pedal position (BPP) | 92 | TCC unlock, and safety-relevant |
| C251 | **Transmission control switch (TCS)** | 29 in, 12 out | OD on/off switch and its indicator lamp |
| C250 | Ignition switch | — | run/start sense |
| C230 | 4WD mode switch | — | feeds the transfer case shift module, not the PCM |
| C204 | **Inertia fuel shutoff switch** | — | see below |

## Three questions these sheets answer

### 1. The transfer case is not the ECU's problem

An earlier note asked whether the replacement ECU would have to drive an
electronic-shift transfer case. **C221 is a dedicated transfer case shift relay
module**, fed by the 4WD mode switch (C230) and the 4x4 low/high indicator
switch (C189 on the transmission). That is a self-contained subsystem.

The ECU may want to *know* the range — low range should change shift points and
line pressure — but it does not have to actuate it. **[CONFIRM]** whether the
GEM sits between the mode switch and the relay module, because if it does, and
if it needs PCM data to decide, that becomes a Phase 0 capture item.

### 2. PATS confirmed: transceiver separate, logic in the cluster

C297 is the **PATS transceiver module** — the coil around the ignition lock that
reads the key transponder. It is only the reader. The anti-theft *logic* lives
in the instrument cluster (C236/C237), which is what "PATS Type C" means and
what the earlier analysis assumed.

This confirms the position already taken: the cluster authorises **the PCM** over
SCP. A replacement ECU never asks, so PATS has nothing to withhold. No
decryption, no emulation, no work. Expect the theft lamp to misbehave and
nothing else.

### 3. The inertia fuel shutoff switch is in the fuel pump path — leave it there

**C204, the inertia fuel shutoff switch.** In a collision it opens and kills the
fuel pump, mechanically, with no software involved. It sits in series with the
pump circuit downstream of the relay the PCM controls.

The replacement ECU drives the fuel pump relay exactly as the OEM PCM did, and
the inertia switch stays where it is. It is easy to "simplify" this away while
rewiring, and it must not be — it is the one thing that stops the pump feeding a
ruptured fuel line after a crash. It also explains a classic no-start: a tripped
inertia switch looks exactly like a dead fuel pump relay.

Note as well that ECU pin 40 is a **fuel pump monitor** input. The OEM PCM
watches the pump circuit and can tell a commanded-on pump from a running one —
worth reproducing, because it is what distinguishes "I asked for fuel pressure"
from "I have fuel pressure".

## Other data link connectors

The truck has **four** diagnostic connectors, not one. Only C228 is the OBD-II
DLC; do not confuse them when probing:

| Ref | For |
|---|---|
| C228 | OBD-II / SCP — the one that matters |
| C207 | RABS |
| C268 | Differential speed sensor (DSS) |
| C285 | Rear air suspension |
