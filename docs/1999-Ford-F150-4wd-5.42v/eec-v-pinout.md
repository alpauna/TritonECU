# EEC-V 104-pin connector pinout — 1999 F-150 5.4L

Transcribed from `MSPNPP-EECV-8CM.xls_0.ods` in
[alpauna/MegaSquirt99FordF150](https://github.com/alpauna/MegaSquirt99FordF150),
which mapped this truck for an MS3Pro PNP + MicroSquirt install.

Columns: the MegaSquirt PNP function, whether the '99 F-150 pin matches,
the OEM wire colour, and the original notes.

**Pin numbering caveat.** This sheet numbers 1–104 flat. The Ford power-pin
sheet uses connector-relative numbering (A-13, A-20, B-17, C-17…). The two
do not obviously line up and **[CONFIRM]** is needed before wiring a
connector from these numbers alone.

| Pin | MS function | I/O | '99 F150 pin | Wire | Notes |
|---|---|---|---|---|---|
| 1 | Ign Coil 6 | IGNE | Same | ORG/YEL |  |
| 2 | -- | -- | Same |  |  |
| 3 | GND | Power Ground | Same | BLK/WHT | MicroSquirt Pin 22 (Power Ground) |
| 4 | -- | -- | Same |  |  |
| 5 | -- | -- | Same |  |  |
| 6 | -- | -- | Shift SOL(SS1) | ORG/YEL | MicroSquirt Pin 8 (Solenoid B) |
| 7 | -- | -- | TC Speed Sense | PNK |  |
| 8 | -- | -- | Same |  |  |
| 9 | -- | -- | Same |  |  |
| 10 | -- | -- | Same |  |  |
| 11 | -- | -- | Shift SOL(SS2) | VIO/ORG | MicroSquirt Pin 7 (Solenoid A) |
| 12 | -- | -- | Trans Control Indicator | WHT/LT GRN | OD On/Off Light +12v when OD is off This is a ground switched LED with proper resistor by LEDMicroSquirt Pin 35 maybe used as LED driver here! |
| 13 | -- | -- | DLC | VIO |  |
| 14 | -- | -- | 4x4 Low Indicator Sw | LT BLU/BLK |  |
| 15 | SCP- | J1850 Bus | Same | PNK/LT BLU |  |
| 16 | SCP+ | J1850 Bus | Same | TAN/ORG |  |
| 17 | -- | -- | Same |  |  |
| 18 | -- | -- | Same |  |  |
| 19 | Low Cool Fan | HC3 Inverted | -- |  | Electric Fan 1 |
| 20 | -- | -- | CSS | BRN/ORG | MicroSquirt Pin 16 (Solenoid D) |
| 21 | CKP+ | CKP+ | Same | DK BLU |  |
| 22 | CKP- | CKP- | Same | GRY |  |
| 23 | -- | -- | Same |  |  |
| 24 | GND | Power Ground | -- |  |  |
| 25 | GND | Power Ground | Same | BLK | MicroSquirt Pin 23 (Power Ground) |
| 26 | Ign Coil 1 | IGNA | Same | LT GRN/WHT |  |
| 27 | Ign Coil 5 | IGNF | Same | LT GRN/YEL |  |
| 28 | -- | -- | Same |  |  |
| 29 | -- | -- | TCS | TAN/WHT | OD On/Off 12v when OD is to be onMicroSquirt Pin 34 (Selector pos D) |
| 30 | -- | -- | Same |  |  |
| 31 | -- | -- | Same |  |  |
| 32 | -- | -- | KS Sensor | DK GRN/VIO | Need to hook up? |
| 33 | -- | -- | Same |  |  |
| 34 | -- | -- | Trans Pos Sensor 1 | YEL/BLK | MicroSquirt Pin 12 (Selector pos A) |
| 35 | -- | -- | RR HO2S Signal | RED/LT GRN | Not used |
| 36 | MAF Return | Sensor Ground | Same | TAN/LT BLU |  |
| 37 | -- | -- | TFT | ORG/BLK | MicroSquirt Pin 26 (Trans Temp) |
| 38 | ECT | CLT | -- |  | Jump this to pin 66 |
| 39 | IAT | IAT | Same | GRY |  |
| 40 | -- | -- | Fuel Pump Monitor | DK GRN/YEL |  |
| 41 | A/C cycle Sw | DI3 Inverted | Same | BLK/YEL |  |
| 42 | -- | -- | Same |  |  |
| 43 | -- | -- | Same |  |  |
| 44 | -- | -- | Same |  |  |
| 45 | -- | -- | Same |  |  |
| 46 | High Cool Fan | PWM2 | Intake Manifold Communicator(IMCC) | BRN | Electric Fan 2 |
| 47 | -- | -- | EVR CTRL | BRN/PNK |  |
| 48 | -- | -- | Same |  |  |
| 49 | -- | -- | Trans Pos Sensor 2 | LT BLU/BLK | MicroSquirt Pin 11 (Selector pos B) |
| 50 | -- | -- | Trans Pos Sensor 4 | WHT/BLK | MicroSquirt Pin 29 (Selector pos C) |
| 51 | GND | Power Ground | Same | BLK/WHT |  |
| 52 | Ign Coil 3 | IGNB | Same | WHT/BLK |  |
| 53 | Ign Coil 4 | IGNG | Same | DK GRN/VIO |  |
| 54 | -- | -- | TCC SOL | VIO/YEL | MicroSquirt Pin 9 (TCC (LU) Solenoid) |
| 55 | B+ KAM | 12V KAM | Same | RED/WHT |  |
| 56 | -- | -- | VAPOR VALVE | LT GRN/BLK |  |
| 57 | -- | -- | KNOCK SENSOR | YEL/RED |  |
| 58 | -- | -- | Same |  |  |
| 59 | -- | -- | TSS Speed Sensor | DK GRN/WHT |  |
| 60 | RF O2 | O2 via Jumper JP1 | Same | GRY/LT BLUE |  |
| 61 | -- | -- | LR HO2S Signal | VIO/LT GRN | Not used |
| 62 | -- | -- | Fuel Tank Pressure | RED/PNK | May add this later… |
| 63 | Fuel Press | AIN2 | -- |  | Will add fuel pressure to truck |
| 64 | -- | -- | Trans Pos Sensor 3 | LT BLU/YEL |  |
| 65 | -- | -- | DPFE Sensor | BRN/LT GRN | EGR Valve Pressure Difference Sensor |
| 66 | -- | -- | CYL Head Temp | YEL/LT GRN |  |
| 67 | -- | -- | Canister Vent | VIO/WHT |  |
| 68 | VSS+ | Out to Cruise | Same | GRY/BLK |  |
| 69 | AC WOT Clutch | PWM3 | Same | PNK/YEL |  |
| 70 | -- | -- | Same |  |  |
| 71 | 12V Switched | 12V Switched | Same | RED | MicroSquirt Pin 1 (Power) |
| 72 | Injector 7 | Injector C | Same | TAN/RED |  |
| 73 | Injector 5 | Injector F | Same | TAN/BLK |  |
| 74 | Injector 3 | Injector B | Same | BRN/YEL |  |
| 75 | Injector 1 | Injector A | Same | TAN |  |
| 76 | -- | -- | Same |  |  |
| 77 | GND | Power Ground | Same | BLK/WHT |  |
| 78 | Ign Coil 7 | IGNC | Same | PNK/LT BLU |  |
| 79 | Ign Coil 8 | IGNH | Same | WHT/RED |  |
| 80 | FP | Fuel Pump | Same | LT BLU/ORG |  |
| 81 | -- | -- | EPC SOL | WHT/YEL | MicroSquirt Pin 10 (EPC solenoid ) Note: Diode to 12v! See MicroSquirt section 3.4.1 |
| 82 | -- | -- | Same |  |  |
| 83 | IAC | PWM1/Idle | Same | WHT/LT BLU |  |
| 84 | OSS | DFIN1 via LM1850 | Same | DK BLU/YEL |  |
| 85 | CMP | CMP+ | Same | DK GRN |  |
| 86 | -- | -- | Same |  |  |
| 87 | LF O2 | O2 Via Jumper JP1 | Same | RED/BLK |  |
| 88 | MAF | AIN1 | Same | LT BLU/RED |  |
| 89 | TPS | TPS | Same | GRY/WHT |  |
| 90 | VREF | Vref | Same | BRN/WHT |  |
| 91 | SGND | Sensor Ground | Same | GRY/RED | MicroSquirt Pin 20 (Sensor Ground) |
| 92 | -- | -- | BPP SW | RED/LT GRN |  |
| 93 | RF O2 Heat | Power Ground | Same | RED/WHT |  |
| 94 | LF O2 Heat | Power Ground | Same | YEL/LT BLU |  |
| 95 | -- | -- | RR HO2S Heat | WHT/BLK | Not used |
| 96 | -- | -- | LR HO2S Heat | TAN/YEL | Not used |
| 97 | 12V Switched | 12V Switched | Same | RED | Power Wideband off this wire. |
| 98 | Injector 8 | Injector H | Same | LT BLU |  |
| 99 | Injector 6 | Injector E | Same | LT GRN/ORG |  |
| 100 | Injector 4 | Injector G | Same | BRN/LT BLU |  |
| 101 | Injector 2 | Injector D | Same | WHT |  |
| 102 | -- | -- | Same |  |  |
| 103 | GND | Power Ground | Same | BLK/WHT |  |
| 104 | IGN Coil 2 | IgnD | Same | PNK/WHT |  |

---

## What this pinout settles

### Confirms

- **CKP is variable-reluctance.** Pins 21/22 are **CKP+ (DK BLU) and CKP−
  (GRY)** — a two-wire differential coil, which is what a VR sensor is. A Hall
  sensor would be a single signal wire with separate supply and ground. The VR
  conditioner requirement stands.
- **OSS is variable-reluctance too.** Pin 84 is annotated *"DFIN1 via LM1850"* —
  almost certainly the **LM1815**, National's adaptive VR sensor amplifier.
  That is the MegaSquirt build conditioning the output-shaft speed sensor
  exactly as this design must.
- **The MAF really does have its own return.** Pin 36 is **MAF Return**
  (TAN/LT BLU = circuit 968) and pin 91 is a *separate* **SGND / Sensor Ground**
  (GRY/RED). Two distinct grounds, confirming the differential-measurement
  argument for the AD7606C.
- **SCP wiring matches the DLC sheet.** Pin 15 SCP− (PNK/LT BLU) and pin 16
  SCP+ (TAN/ORG) are circuits 915 and 914 — the same wires as DLC pins 10 and 2.
- **CHT, not ECT.** Pin 66 is **CYL Head Temp**, and the MegaSquirt build
  jumpers its own ECT input (pin 38) across to it, precisely because the truck
  has no coolant sensor to connect.
- **Coil-on-plug, eight coils.** Ign Coil 1–8 on pins 26, 104, 52, 53, 27, 1,
  78, 79.
- **Eight injectors.** Pins 75, 101, 74, 100, 73, 99, 72, 98.
- **Knock is a two-wire differential piezo** — pins 57 (YEL/RED) and 32
  (DK GRN/VIO).

### New — things not in the design yet

- **CSS, Coast Clutch Solenoid (pin 20, BRN/ORG).** A *fourth* 4R70W solenoid.
  The inventory listed SSA, SSB, TCC and EPC. This is a fifth output.
- **TR sensor is a 4-bit digital code**, not an analog ladder — Trans Pos
  Sensor 1–4 on pins 34, 49, 50, 64. Four digital inputs, decoded as a gear
  pattern. Cheaper than expected: expander inputs, not an ADC channel.
- **EPC needs a flyback diode to 12 V** (pin 81 note). Worth carrying into the
  driver design.
- **VSS output feeds cruise control** (pin 68, "Out to Cruise").
- Extra signals present that were not in the inventory: **Fuel Tank Pressure**
  (62), **Fuel Pump Monitor** (40), **BPP brake switch** (92), **4x4 Low
  Indicator** (14), **TCS / OD-off switch** (29) and its **indicator lamp** (12).

### Two things to resolve

1. **CMP may be Hall, not VR.** Pin 85 is a *single* wire labelled "CMP+"
   (DK GRN) with no matching CMP−. Both earlier documents assert CMP is
   variable-reluctance. A single signal wire is equally consistent with a
   three-wire Hall sensor powered from elsewhere, or with a single-ended VR
   returning on sensor ground. **[CONFIRM]** — it decides whether CMP needs a
   conditioner channel or connects almost directly.

2. **Only one VREF pin appears here.** Pin 90 (BRN/WHT) is the only VREF, but
   the Ford power-pin sheet lists **two** (A-20 and C-20). Either the second is
   unused on this application, or this sheet only records what the MegaSquirt
   install connected. **[CONFIRM]** — it decides whether the VREF supply needs
   one output feed or two, which is the main open question in
   [`../vref-supply.md`](../vref-supply.md).

---

## Architecture: the MegaSquirt build split engine and transmission

Worth noting what this pinout implies about how the job was previously solved.
The notes reference **two** modules throughout:

- **MS3Pro PNP** — engine control.
- **MicroSquirt** — transmission control. Its pin numbers are called out
  against SS1 (pin 6), SS2 (11), CSS (20), TCC (54), EPC (81), TFT (37), TSS
  (59), OSS (84) and the four TR inputs.

The two are linked over **CAN**, and the closing note in the sheet spells out
the bus termination: MS3Pro and MicroSquirt form the two ends.

That is the same split this design was calling "option C", and it was already
built and made to work on this truck. It also solves the ESP-ECU I/O problem
without a custom carrier — see the target document.
