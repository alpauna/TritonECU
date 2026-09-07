#include "EnginePosition.h"

namespace engine {
namespace {

float wrap720(float a) {
    while (a < 0.0f)      a += 720.0f;
    while (a >= 720.0f)   a -= 720.0f;
    return a;
}

// Smallest absolute difference between two crank angles, accounting for wrap.
float angleDelta360(float a, float b) {
    float d = a - b;
    while (d < -180.0f) d += 360.0f;
    while (d >  180.0f) d -= 360.0f;
    return d < 0.0f ? -d : d;
}

}  // namespace

void Position::begin(float camSyncAngleDeg, float toleranceDeg) {
    _camSyncAngle = camSyncAngleDeg;
    _tolerance    = toleranceDeg;
    _sawGap       = false;
    _lastTooth    = 0;
    _phase        = Phase{};
}

void Position::onCrankTooth(bool crankSynced, uint16_t toothIndex,
                            float crankAngleDeg) {
    if (!crankSynced) {
        // Losing crank sync invalidates everything above it. Cam sync is not
        // recoverable on its own, because the revolution count is derived from
        // counting crank gaps.
        _phase.state      = PhaseState::kNoCrank;
        _phase.revolution = 0;
        _phase.angle720   = 0.0f;
        _sawGap           = false;
        return;
    }

    // toothIndex returning to 0 means the gap just passed: a new revolution.
    if (toothIndex == 0 && _lastTooth != 0) {
        if (_phase.state == PhaseState::kSynced) {
            _phase.revolution ^= 1;
        }
        _sawGap = true;
    }
    _lastTooth = toothIndex;

    if (_phase.state == PhaseState::kNoCrank) {
        _phase.state = PhaseState::kWaitingCam;
    }

    _phase.angle720 = (_phase.state == PhaseState::kSynced)
                          ? wrap720(crankAngleDeg + 360.0f * _phase.revolution)
                          : crankAngleDeg;
}

void Position::onCamEdge(float crankAngleDeg) {
    if (_phase.state == PhaseState::kNoCrank) return;   // nothing to anchor to

    if (_phase.state == PhaseState::kSynced) {
        // Already synced: this pulse is a check, not a source of truth. A pulse
        // at the wrong crank angle is noise or a failing sensor, and trusting
        // it would move the whole cycle 360 degrees — every cylinder firing on
        // the exhaust stroke.
        if (angleDelta360(crankAngleDeg, _camSyncAngle) > _tolerance) {
            _phase.camRejects++;
            return;
        }
        // A valid pulse must land in revolution 0. If it does not, the
        // revolution count has slipped; correct it rather than drift.
        if (_phase.revolution != 0) {
            _phase.revolution = 0;
            _phase.camRejects++;
        }
        return;
    }

    // First good pulse establishes the phase. By definition the cam pulse
    // occurs in revolution 0.
    if (angleDelta360(crankAngleDeg, _camSyncAngle) > _tolerance) {
        _phase.camRejects++;
        return;
    }
    _phase.revolution = 0;
    _phase.state      = PhaseState::kSynced;
    _phase.camSyncs++;
    _phase.angle720   = wrap720(crankAngleDeg);
}

}  // namespace engine
