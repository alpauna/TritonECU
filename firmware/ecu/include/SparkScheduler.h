#pragma once
// Ignition scheduling for coil-on-plug.
//
// The 1999 5.4L has eight individual coils (C1011-C1018), so every cylinder is
// timed on its own — there is no companion-cylinder pairing to exploit. Firing
// order 1-3-7-2-6-5-4-8, one event every 90 degrees of the 720-degree cycle.
//
// Two angles matter per cylinder:
//   * fire  — the spark, at (TDC - advance)
//   * dwell — coil charge start, a fixed *time* before the spark
//
// Dwell is a time, not an angle: a coil needs roughly the same milliseconds to
// saturate regardless of engine speed. Converting it to crank degrees is
// therefore rpm-dependent, and at high rpm the dwell angle grows until it
// starts to overlap the previous cylinder's event. That limit is real and is
// checked here rather than discovered on a dyno.
//
// Arduino-free so it can be tested natively.

#include <stdint.h>

namespace spark {

constexpr uint8_t kMaxCylinders = 12;

enum class EventType : uint8_t { kDwellStart, kFire };

struct Event {
    uint8_t   cylinder = 0;         // 1-based, as the firing order is written
    EventType type     = EventType::kFire;
    float     angle720 = 0.0f;      // where in the cycle it happens
};

class Scheduler {
  public:
    void begin(uint8_t cylinders, const uint8_t* firingOrder);

    void setAdvanceDeg(float degBtdc)  { _advanceDeg = degBtdc; }
    void setDwellMs(float ms)          { _dwellMs = ms; }
    float advanceDeg() const           { return _advanceDeg; }
    float dwellMs() const              { return _dwellMs; }

    // TDC of a cylinder, by its position in the firing order.
    float tdcAngle(uint8_t firingIndex) const;

    // Dwell expressed in crank degrees at this speed.
    float dwellDegrees(float rpm) const;

    // Where this cylinder's spark and dwell-start fall in the cycle.
    Event fireEvent(uint8_t firingIndex) const;
    Event dwellEvent(uint8_t firingIndex, float rpm) const;

    // The next event strictly after `angle720`, and how far away it is.
    bool nextEvent(float angle720, float rpm, Event& out, float& degreesUntil) const;

    // True when dwell has grown long enough to reach back into the previous
    // cylinder's spark. Above this the coil cannot be given its full charge
    // time without overlapping, and dwell must be clamped.
    bool dwellOverlaps(float rpm) const;

    // Highest rpm at which the requested dwell still fits between events.
    float maxRpmForDwell() const;

  private:
    uint8_t _cylinders = 8;
    uint8_t _order[kMaxCylinders] = {1, 3, 7, 2, 6, 5, 4, 8};
    float   _advanceDeg = 10.0f;
    float   _dwellMs    = 3.0f;
};

}  // namespace spark
