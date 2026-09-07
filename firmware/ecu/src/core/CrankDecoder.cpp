#include "CrankDecoder.h"

namespace crank {
namespace {

// A missing tooth doubles the interval. Accept anything above this multiple of
// the previous interval as the gap.
//
// 1.5 rather than 2.0 because the engine decelerates through the gap under
// compression: the real ratio at cranking is often 1.7-1.9, not a clean 2.0.
// Set it at 2.0 and the gap is missed while cranking, which is exactly when
// sync must be established.
constexpr float kGapRatioMin = 1.5f;

// And an upper bound, so one absurdly long interval — a dropped tooth, or the
// engine simply stopping — is not mistaken for the gap.
constexpr float kGapRatioMax = 3.0f;

// After the gap, the next interval returns to normal. Require that to confirm,
// so a single noise-induced long interval cannot fake sync on its own.
constexpr float kNormalRatioMax = 1.4f;

// No teeth for this long means the engine has stopped.
constexpr uint32_t kSignalTimeoutUs = 500000;   // 0.5 s — below 20 rpm on a 36-1

}  // namespace

void Decoder::begin(uint16_t teeth, uint8_t missing) {
    _teeth       = teeth;
    _missing     = missing;
    _realTeeth   = static_cast<uint16_t>(teeth - missing);
    _degPerTooth = 360.0f / static_cast<float>(teeth);

    _lastToothUs = 0;
    _lastGapUs   = 0;
    _prevGapUs   = 0;
    _haveLast    = false;
    _status      = Status{};
}

void Decoder::loseSync(uint64_t) {
    if (_status.state == State::kSynced) _status.syncLossCount++;
    _status.state         = State::kSearching;
    _status.crankAngleDeg = 0.0f;
    _status.toothIndex    = 0;
}

void Decoder::onTooth(uint64_t timestampUs) {
    if (!_haveLast) {
        _lastToothUs = timestampUs;
        _haveLast    = true;
        _status.state = State::kSearching;
        return;
    }

    const uint64_t interval64 = timestampUs - _lastToothUs;
    _lastToothUs = timestampUs;

    // Reject nonsense outright rather than letting it into the ratio maths.
    if (interval64 == 0 || interval64 > kSignalTimeoutUs) {
        _prevGapUs = 0;
        loseSync(timestampUs);
        return;
    }
    const uint32_t interval = static_cast<uint32_t>(interval64);

    if (_prevGapUs == 0) {          // first usable interval, nothing to compare
        _prevGapUs = interval;
        return;
    }

    const float ratio = static_cast<float>(interval) / static_cast<float>(_prevGapUs);

    if (ratio >= kGapRatioMin && ratio <= kGapRatioMax) {
        // This interval spans the gap, so this edge is the first tooth after it.
        _status.toothIndex    = 0;
        _status.crankAngleDeg = 0.0f;
        if (_status.state != State::kSynced) {
            _status.state = State::kSynced;
            _status.syncCount++;
        }
    } else if (ratio > kGapRatioMax) {
        // Far too long to be the gap — a dropped tooth or a stopping engine.
        loseSync(timestampUs);
    } else if (_status.state == State::kSynced) {
        _status.toothIndex++;
        if (_status.toothIndex >= _realTeeth) {
            // A full revolution should have ended at the gap. Arriving here
            // means the gap was missed, so the angle can no longer be trusted.
            loseSync(timestampUs);
        } else {
            // Tooth index counts real teeth, but the gap occupies a physical
            // position too — after the gap, index 1 is 2 tooth-widths on.
            _status.crankAngleDeg =
                (_status.toothIndex + _missing) * _degPerTooth;
        }
    }

    // RPM from the most recent interval. One tooth is 360/teeth degrees, so a
    // revolution is `teeth` intervals of this length.
    if (ratio < kNormalRatioMax || _status.state != State::kSynced) {
        const uint32_t usPerRev = interval * _teeth;
        if (usPerRev > 0) _status.rpm = 60000000UL / usPerRev;
    }

    _lastGapUs = _prevGapUs;
    _prevGapUs = interval;
}

void Decoder::poll(uint64_t nowUs) {
    if (!_haveLast) return;
    if (nowUs - _lastToothUs > kSignalTimeoutUs) {
        if (_status.state == State::kSynced) _status.syncLossCount++;
        _status.state         = State::kNoSignal;
        _status.rpm           = 0;
        _status.crankAngleDeg = 0.0f;
        _status.toothIndex    = 0;
        _haveLast             = false;
        _prevGapUs            = 0;
    }
}

}  // namespace crank
