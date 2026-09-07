#pragma once
// Full 720-degree engine position — crank angle plus cam phase.
//
// A four-stroke completes one cycle in two crank revolutions, so the crank
// decoder's 0-360 is ambiguous: every angle occurs twice per cycle, once on
// compression and once on exhaust. The cam sensor resolves it. On the 5.4L the
// CMP (C100) gives one pulse per cam revolution, which is one pulse per 720
// degrees of crank.
//
// Sequential injection and coil-on-plug both need this. Without cam sync the
// engine can still run wasted-spark and batch-fire — worth remembering as a
// limp mode, since a failed CMP should not strand the truck.
//
// Arduino-free on purpose, like CrankDecoder: it takes only the crank
// decoder's state and cam edge timing, so it can be tested natively.

#include <stdint.h>

namespace engine {

enum class PhaseState : uint8_t {
    kNoCrank,     // crank not synced — nothing is knowable
    kWaitingCam,  // crank synced, cam pulse not yet seen; running on 360
    kSynced,      // full 720 position known
};

struct Phase {
    PhaseState state       = PhaseState::kNoCrank;
    uint8_t    revolution  = 0;      // 0 or 1 within the 720 cycle
    float      angle720    = 0.0f;   // 0-719.99, TDC of cylinder 1 at 0
    uint32_t   camSyncs    = 0;
    uint32_t   camRejects  = 0;      // pulses at an implausible crank angle
};

class Position {
  public:
    // camSyncAngleDeg: crank angle at which the cam pulse is expected, within
    // revolution 0. toleranceDeg: how far off that a pulse may be before it is
    // rejected as noise rather than trusted as sync.
    void begin(float camSyncAngleDeg = 0.0f, float toleranceDeg = 30.0f);

    // Called on every crank tooth with the decoder's current state. Tracks
    // which of the two revolutions the cycle is in by counting gaps.
    void onCrankTooth(bool crankSynced, uint16_t toothIndex, float crankAngleDeg);

    // Called on each cam edge, with the crank angle at that instant.
    void onCamEdge(float crankAngleDeg);

    Phase phase() const { return _phase; }
    bool  synced() const { return _phase.state == PhaseState::kSynced; }

  private:
    float _camSyncAngle = 0.0f;
    float _tolerance    = 30.0f;
    bool  _sawGap       = false;
    uint16_t _lastTooth = 0;
    Phase _phase;
};

}  // namespace engine
