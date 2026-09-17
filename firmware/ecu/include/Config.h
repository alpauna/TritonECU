#pragma once
// Persistent configuration, JSON on the SD card.
//
// Only holds what a milestone actually needs. Fields get added as they are
// earned — an empty config is better than one full of speculative knobs.
//
// Engine values default to the target vehicle: 1999 F-150 5.4L 2V. See
// docs/1999-Ford-F150-4wd-5.42v/.

#include <Arduino.h>
#include <stdint.h>

namespace config {

struct Engine {
    uint8_t  cylinders     = 8;
    // 5.4L Triton 2V. [CONFIRM ON TRUCK] — carried from the target document.
    uint8_t  firingOrder[8] = {1, 3, 7, 2, 6, 5, 4, 8};
    // 36-1 variable reluctance on the crank, 10 degrees per tooth. Verified:
    // the EEC-V pinout shows CKP+ / CKP- as a two-wire differential coil.
    uint16_t crankTeeth    = 36;
    uint8_t  crankMissing  = 1;
    // Displacement in cc, for the volumetric-efficiency maths later.
    uint16_t displacementCc = 5408;   // true 5.4L Triton displacement
};

// Electric cooling fans — two, staged, replacing the clutch fan.
// Full design and the reasoning behind every default: docs/cooling-fans.md.
//
// Thresholds are CYLINDER HEAD temperature. This truck has no coolant sensor:
// EEC-V pin 66 is Cyl Head Temp and the MegaSquirt build jumpered its ECT input
// across to it. Head metal runs hotter and responds faster than coolant would,
// so these numbers are not the coolant numbers you would use on another engine.
struct Cooling {
    bool  enabled  = true;

    // Stage 1 carries normal traffic; stage 2 is for grades, towing and heat.
    // Off thresholds sit 5 degrees below on, which at idle airflow is several
    // minutes of run time — enough that the relays are not cycling.
    float fan1OnC  =  96.0f;   // 205 F
    float fan1OffC =  91.0f;   // 196 F
    float fan2OnC  = 103.0f;   // 217 F
    float fan2OffC =  98.0f;   // 208 F

    // The condenser needs airflow at idle whatever the head is doing, so A/C
    // pulls a fan on by itself. Stage 1 is enough for a condenser.
    bool    acFanOn    = true;
    uint8_t acFanStage = 1;    // 1 or 2

    // Highway cutoff. A PERMISSIVE, never an override: above the speed
    // threshold ram air already exceeds what the fans move, but only while the
    // head is genuinely cool. Above highwayMaxC the cutoff does not apply.
    bool     highwayCutoff    = false;   // opt in — see the doc before enabling
    uint16_t highwayCutoffKph = 72;      // ~45 mph
    float    highwayMaxC      = 91.0f;   // 196 F — same as fan1 off
    uint16_t highwayHoldMs    = 5000;    // speed must be sustained, not a blip

    // Never start both fans into the same inrush, and never chatter a relay.
    uint16_t stageDelayMs = 3000;
    uint16_t minRunMs     = 10000;

    // Cranking is not the moment to add 20 A of fan to the starter's load.
    bool crankInhibit = true;

    // Run-on after key-off, which the always-on MCU domain makes possible.
    // Heat soak after a hard pull is when the head peaks. Guarded by a battery
    // floor so a cooling fan can never be the reason the truck will not start.
    bool     runOn         = true;
    uint16_t runOnMaxS     = 300;
    float    runOnUntilC   = 95.0f;    // 203 F
    float    runOnMinVolts = 12.2f;
};

struct Data {
    Engine   engine;
    Cooling  cooling;
    uint32_t bootCount = 0;   // proves persistence across power cycles
    String   vehicle   = "1999 Ford F-150 4WD 5.4L 2V / 4R70W";
};

extern Data data;

// Loads /config.json. Writes defaults and returns true if the file is missing
// or unparseable — a corrupt config should not stop the ECU booting.
bool load();
bool save();

void report();

// Forces the cooling thresholds back into a sane ordering after a load.
// A hand-edited config that says "fan off above fan on" would leave the engine
// with no cooling at all, so this is a correction, not a rejection.
void sanitiseCooling();

}  // namespace config
