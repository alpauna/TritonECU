#pragma once
#include <Arduino.h>

// Auto-silence with re-arm, for an audible annunciator.
//
// An alarm that cannot be silenced gets disconnected, and then nothing
// annunciates ever again. One that silences permanently is no better than none.
// So: sound for a while, go quiet, and speak up again the moment something NEW
// is wrong.
//
// "New" means a fault bit that has not been part of this episode, or an
// escalation in severity. A fault that flaps in and out does NOT re-arm — that
// is the failure mode which makes an alarm unsilenceable in practice. The
// episode ends, and the slate is wiped, only when every fault has cleared.
class AlarmPolicy {
public:
    void configure(uint32_t silenceAfterMs) { _silenceAfterMs = silenceAfterMs; }

    // mask: the faults currently annunciating. tier: severity, so an escalation
    // from "fault" to "critical" re-arms even when the bits are unchanged.
    // Returns true while the annunciator should be sounding.
    bool update(uint32_t now, uint8_t mask, uint8_t tier) {
        if (mask == 0) {                 // episode over
            _seen = 0;
            _tier = 0;
            _armed = false;
            _sounding = false;
            return false;
        }
        const bool isNew = !_armed || ((mask & ~_seen) != 0) || (tier != _tier);
        if (isNew) {
            _start = now;
            _armed = true;
        }
        _seen |= mask;                   // accumulate, so flapping cannot re-arm
        _tier = tier;
        _sounding = (uint32_t)(now - _start) < _silenceAfterMs;
        return _sounding;
    }

    // A fault is present but the annunciator has gone quiet on its own.
    bool silenced() const { return _armed && !_sounding; }

private:
    uint32_t _silenceAfterMs = 300000;   // 5 minutes
    uint32_t _start    = 0;
    uint8_t  _seen     = 0;
    uint8_t  _tier     = 0;
    bool     _armed    = false;
    bool     _sounding = false;
};
