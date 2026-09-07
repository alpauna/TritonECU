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

struct Data {
    Engine   engine;
    uint32_t bootCount = 0;   // proves persistence across power cycles
    String   vehicle   = "1999 Ford F-150 4WD 5.4L 2V / 4R70W";
};

extern Data data;

// Loads /config.json. Writes defaults and returns true if the file is missing
// or unparseable — a corrupt config should not stop the ECU booting.
bool load();
bool save();

void report();

}  // namespace config
