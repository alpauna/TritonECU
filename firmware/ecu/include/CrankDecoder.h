#pragma once
// 36-1 crank wheel decoder.
//
// The 1999 F-150 5.4L uses a 36-tooth wheel with one tooth removed, read by a
// variable-reluctance sensor (EEC-V pinout pins 21/22, CKP+/CKP-). Each tooth
// is 10 degrees of crank rotation; the gap is where 360 degrees is anchored.
//
// This class deals only in tooth timestamps. It knows nothing about GPIOs,
// interrupts or the VR conditioner ahead of it, which is what lets the whole
// decode be unit-tested against synthetic tooth streams before any hardware
// exists. See docs/roadmap.md — M3 is the highest-risk milestone in the
// project, and the electrical half is risky enough on its own.
//
// Sync strategy: a missing tooth shows up as an interval roughly twice the
// previous one. Comparing against the *previous interval* rather than a fixed
// threshold is what makes this work while cranking, where speed is low,
// irregular, and changing between every tooth.

#include <stdint.h>

namespace crank {

constexpr uint16_t kDefaultTeeth   = 36;   // physical positions, including the gap
constexpr uint8_t  kDefaultMissing = 1;

enum class State : uint8_t {
    kNoSignal,   // nothing seen yet, or teeth stopped arriving
    kSearching,  // receiving teeth, gap not yet identified
    kSynced,     // gap found, crank angle is known
};

struct Status {
    State    state          = State::kNoSignal;
    uint32_t rpm            = 0;
    // Degrees since the gap, 0-359.99. Only meaningful when kSynced.
    float    crankAngleDeg  = 0.0f;
    uint16_t toothIndex     = 0;      // 0 = first tooth after the gap
    uint32_t syncCount      = 0;      // times sync was achieved
    uint32_t syncLossCount  = 0;      // times sync was lost
};

class Decoder {
  public:
    void begin(uint16_t teeth = kDefaultTeeth, uint8_t missing = kDefaultMissing);

    // Feed one rising edge from the VR conditioner. Timestamps are
    // microseconds and must be monotonic. Safe to call from an ISR: no
    // allocation, no division by a runtime zero, no blocking.
    void onTooth(uint64_t timestampUs);

    // Call periodically. Declares loss of signal if no tooth has arrived for
    // longer than the timeout, which is what stops a stalled engine from
    // reporting its last known rpm forever.
    void poll(uint64_t nowUs);

    Status status() const { return _status; }
    bool   synced() const { return _status.state == State::kSynced; }

    // Degrees per tooth, from the configured wheel.
    float degreesPerTooth() const { return _degPerTooth; }

  private:
    void loseSync(uint64_t nowUs);

    uint16_t _teeth       = kDefaultTeeth;
    uint8_t  _missing     = kDefaultMissing;
    uint16_t _realTeeth   = kDefaultTeeth - kDefaultMissing;  // edges per revolution
    float    _degPerTooth = 10.0f;

    uint64_t _lastToothUs = 0;
    uint32_t _lastGapUs   = 0;   // interval before the previous one
    uint32_t _prevGapUs   = 0;   // most recent interval
    bool     _haveLast    = false;

    Status _status;
};

}  // namespace crank
