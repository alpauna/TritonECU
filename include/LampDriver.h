#pragma once
#include <Arduino.h>

// Off / steady / blink, with an asymmetric duty so an advisory pulse can be a
// short flash rather than a 50% square wave. Threshold logic decides the mode;
// this only owns the cadence.
//
// Shared: the CEL uses it for the pre-fault / fault / critical tiers, and the
// O/D OFF lamp needs the same thing (docs/dash-indicators.md) — steady for
// "overdrive cancelled", flashing for a transmission fault. An OutputRule
// cannot express a cadence, which is why this exists.
class LampDriver {
public:
    enum Mode : uint8_t { OFF = 0, STEADY, BLINK };

    // Re-arming with identical parameters is a no-op, so this can be called
    // every loop without ever restarting the phase.
    void set(Mode m, uint16_t periodMs = 1000, uint16_t onMs = 500) {
        if (periodMs == 0) periodMs = 1000;
        if (m == _mode && periodMs == _period && onMs == _onMs) return;
        _mode = m;
        _period = periodMs;
        _onMs = onMs;
        _phase = millis();   // a mode change starts lit, so the first flash of
                             // a new condition is immediate and legible
    }

    bool state(uint32_t now) const {
        switch (_mode) {
            case STEADY: return true;
            case BLINK:  return ((uint32_t)(now - _phase) % _period) < _onMs;
            case OFF:
            default:     return false;
        }
    }

    Mode mode() const { return _mode; }

private:
    Mode     _mode   = OFF;
    uint16_t _period = 1000;
    uint16_t _onMs   = 500;
    uint32_t _phase  = 0;
};
