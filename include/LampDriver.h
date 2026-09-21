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
    enum Mode : uint8_t { OFF = 0, STEADY, BLINK, BURST };

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

    // N pulses, then quiet until the repeat window comes round again. This is
    // what an audible annunciator wants and a lamp does not: three beeps every
    // ten seconds says "attend to me" where a continuous tone just gets
    // disconnected. Also drives a flash-count indicator if one is ever wanted.
    void setBurst(uint16_t onMs, uint16_t offMs, uint8_t count, uint32_t repeatMs) {
        if (_mode == BURST && onMs == _onMs && offMs == _offMs &&
            count == _count && repeatMs == _repeat) return;
        _mode = BURST;
        _onMs = onMs;
        _offMs = offMs;
        _count = count ? count : 1;
        _repeat = repeatMs ? repeatMs : 1000;
        _phase = millis();
    }

    bool state(uint32_t now) const {
        switch (_mode) {
            case STEADY: return true;
            case BLINK:  return ((uint32_t)(now - _phase) % _period) < _onMs;
            case BURST: {
                uint32_t t = (uint32_t)(now - _phase) % _repeat;
                uint32_t cycle = (uint32_t)_onMs + _offMs;
                if (cycle == 0 || t >= cycle * _count) return false;  // quiet tail
                return (t % cycle) < _onMs;
            }
            case OFF:
            default:     return false;
        }
    }

    Mode mode() const { return _mode; }

private:
    Mode     _mode   = OFF;
    uint16_t _period = 1000;
    uint16_t _onMs   = 500;
    uint16_t _offMs  = 500;   // BURST only
    uint8_t  _count  = 1;     // BURST only
    uint32_t _repeat = 1000;  // BURST only
    uint32_t _phase  = 0;
};
