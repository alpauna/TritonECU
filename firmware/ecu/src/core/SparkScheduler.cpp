#include "SparkScheduler.h"

namespace spark {
namespace {

float wrap720(float a) {
    while (a < 0.0f)    a += 720.0f;
    while (a >= 720.0f) a -= 720.0f;
    return a;
}

}  // namespace

void Scheduler::begin(uint8_t cylinders, const uint8_t* firingOrder) {
    if (cylinders == 0 || cylinders > kMaxCylinders) return;
    _cylinders = cylinders;
    for (uint8_t i = 0; i < cylinders; i++) _order[i] = firingOrder[i];
}

float Scheduler::tdcAngle(uint8_t firingIndex) const {
    return (720.0f / _cylinders) * (firingIndex % _cylinders);
}

float Scheduler::dwellDegrees(float rpm) const {
    if (rpm <= 0.0f) return 0.0f;
    // Crank degrees per millisecond = rpm * 360 / 60 / 1000 = rpm * 0.006.
    return _dwellMs * rpm * 0.006f;
}

Event Scheduler::fireEvent(uint8_t firingIndex) const {
    Event e;
    e.cylinder = _order[firingIndex % _cylinders];
    e.type     = EventType::kFire;
    e.angle720 = wrap720(tdcAngle(firingIndex) - _advanceDeg);
    return e;
}

Event Scheduler::dwellEvent(uint8_t firingIndex, float rpm) const {
    Event e;
    e.cylinder = _order[firingIndex % _cylinders];
    e.type     = EventType::kDwellStart;
    e.angle720 = wrap720(tdcAngle(firingIndex) - _advanceDeg - dwellDegrees(rpm));
    return e;
}

bool Scheduler::nextEvent(float angle720, float rpm, Event& out,
                          float& degreesUntil) const {
    const float now = wrap720(angle720);
    float best = 721.0f;
    bool found = false;

    for (uint8_t i = 0; i < _cylinders; i++) {
        const Event candidates[2] = {dwellEvent(i, rpm), fireEvent(i)};
        for (const Event& c : candidates) {
            float d = c.angle720 - now;
            if (d <= 0.0f) d += 720.0f;      // strictly ahead, wrapping
            if (d < best) { best = d; out = c; found = true; }
        }
    }
    degreesUntil = best;
    return found;
}

bool Scheduler::dwellOverlaps(float rpm) const {
    // Events are one cylinder-spacing apart. Dwell has to fit inside that gap,
    // or the coil is still being told to charge when the previous one fires.
    return dwellDegrees(rpm) >= (720.0f / _cylinders);
}

float Scheduler::maxRpmForDwell() const {
    if (_dwellMs <= 0.0f) return 1e9f;
    const float spacing = 720.0f / _cylinders;
    return spacing / (_dwellMs * 0.006f);
}

}  // namespace spark
