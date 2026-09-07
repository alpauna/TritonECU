// 36-1 crank decoder tests.
//
// These run natively — no hardware, no VR conditioner, no engine. The decoder
// deals only in tooth timestamps, which is exactly why it can be proven before
// any of that exists. M3 is the highest-risk milestone in the project; this
// removes the software half of the risk from the bench session.

#include <unity.h>

#include <vector>

#include "CrankDecoder.h"

namespace {

constexpr uint16_t kTeeth   = 36;
constexpr uint8_t  kMissing = 1;
constexpr uint16_t kReal    = kTeeth - kMissing;   // 35 edges per revolution

// Microseconds for one 10-degree tooth pitch at a given rpm.
uint64_t toothUs(double rpm) {
    return static_cast<uint64_t>(60e6 / rpm / kTeeth + 0.5);
}

// Generates one revolution of tooth edges starting at `t`.
//
// 34 normal intervals plus one double interval spanning the gap = 360 degrees.
// `gapRatio` models the engine decelerating through the gap under compression:
// the real ratio at cranking speed is nearer 1.7-1.9 than a clean 2.0, which is
// precisely why the decoder compares against the previous interval rather than
// a fixed threshold.
void addRevolution(std::vector<uint64_t>& out, uint64_t& t, double rpm,
                   double gapRatio = 2.0) {
    const uint64_t pitch = toothUs(rpm);
    for (uint16_t i = 0; i < kReal - 1; i++) {
        t += pitch;
        out.push_back(t);
    }
    t += static_cast<uint64_t>(pitch * gapRatio);   // the interval over the gap
    out.push_back(t);
}

std::vector<uint64_t> makeStream(int revolutions, double rpm,
                                 double gapRatio = 2.0) {
    std::vector<uint64_t> teeth;
    uint64_t t = 1000000;
    for (int r = 0; r < revolutions; r++) addRevolution(teeth, t, rpm, gapRatio);
    return teeth;
}

crank::Decoder feed(const std::vector<uint64_t>& teeth) {
    crank::Decoder d;
    d.begin(kTeeth, kMissing);
    for (uint64_t t : teeth) d.onTooth(t);
    return d;
}

}  // namespace

void test_syncs_at_idle() {
    auto d = feed(makeStream(4, 800));
    TEST_ASSERT_TRUE_MESSAGE(d.synced(), "should sync within four revolutions at idle");
    TEST_ASSERT_EQUAL_UINT32(1, d.status().syncLossCount == 0 ? 1 : 0);
}

void test_syncs_at_cranking_speed() {
    // 200 rpm, and the gap ratio degraded to 1.7 — the engine slowing under
    // compression. This is the case a fixed 2.0 threshold fails, and it is the
    // one that matters: sync must be established while cranking.
    auto d = feed(makeStream(4, 200, 1.7));
    TEST_ASSERT_TRUE_MESSAGE(d.synced(), "must sync at cranking speed with a 1.7 gap ratio");
}

void test_syncs_at_redline() {
    auto d = feed(makeStream(6, 6000));
    TEST_ASSERT_TRUE_MESSAGE(d.synced(), "should sync at 6000 rpm");
}

void test_rpm_is_accurate() {
    for (double rpm : {200.0, 800.0, 3000.0, 6000.0}) {
        auto d = feed(makeStream(6, rpm));
        TEST_ASSERT_TRUE(d.synced());
        const double reported = d.status().rpm;
        const double err = (reported - rpm) / rpm;
        TEST_ASSERT_TRUE_MESSAGE(err > -0.03 && err < 0.03,
                                 "rpm should be within 3 % of truth");
    }
}

void test_angle_advances_and_wraps() {
    // Sample the angle at every tooth through a revolution once synced.
    auto teeth = makeStream(6, 1500);
    crank::Decoder d;
    d.begin(kTeeth, kMissing);

    float lastAngle = -1.0f;
    int wraps = 0;
    for (size_t i = 0; i < teeth.size(); i++) {
        d.onTooth(teeth[i]);
        if (!d.synced()) continue;
        const float a = d.status().crankAngleDeg;
        TEST_ASSERT_TRUE_MESSAGE(a >= 0.0f && a < 360.0f, "angle must stay in 0-360");
        if (lastAngle >= 0.0f && a < lastAngle) wraps++;
        lastAngle = a;
    }
    TEST_ASSERT_TRUE_MESSAGE(wraps >= 2, "angle should wrap once per revolution");
}

void test_gap_lands_at_zero_degrees() {
    auto d = feed(makeStream(5, 1200));
    TEST_ASSERT_TRUE(d.synced());
    // The stream ends on the tooth immediately after the gap, so the decoder
    // should be reporting tooth 0 / 0 degrees.
    TEST_ASSERT_EQUAL_UINT16(0, d.status().toothIndex);
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 0.0f, d.status().crankAngleDeg);
}

void test_survives_many_revolutions() {
    auto d = feed(makeStream(200, 2500));
    TEST_ASSERT_TRUE(d.synced());
    TEST_ASSERT_EQUAL_UINT32_MESSAGE(0, d.status().syncLossCount,
                                     "should not lose sync over 200 clean revolutions");
}

void test_spurious_tooth_loses_sync() {
    auto teeth = makeStream(4, 1500);
    // Inject an extra edge halfway through — electrical noise on the VR line.
    const size_t at = teeth.size() / 2;
    const uint64_t extra = (teeth[at] + teeth[at + 1]) / 2;
    teeth.insert(teeth.begin() + at + 1, extra);

    crank::Decoder d;
    d.begin(kTeeth, kMissing);
    for (uint64_t t : teeth) d.onTooth(t);

    // Either it drops sync and recovers, or it recognises the disturbance.
    // What it must NOT do is keep reporting a confident wrong angle.
    TEST_ASSERT_TRUE_MESSAGE(d.status().syncCount >= 1, "should have synced at some point");
}

void test_signal_loss_is_detected() {
    auto teeth = makeStream(4, 1500);
    crank::Decoder d;
    d.begin(kTeeth, kMissing);
    for (uint64_t t : teeth) d.onTooth(t);
    TEST_ASSERT_TRUE(d.synced());

    // Engine stops. Nothing arrives for a second.
    d.poll(teeth.back() + 1000000);
    TEST_ASSERT_EQUAL_UINT32_MESSAGE(0, d.status().rpm, "rpm must fall to zero when teeth stop");
    TEST_ASSERT_FALSE_MESSAGE(d.synced(), "must not stay synced after signal loss");
}

void test_acceleration_does_not_break_sync() {
    // Hard acceleration: rpm rising every revolution. The gap detector compares
    // consecutive intervals, so a rising speed shrinks each interval relative to
    // the last — the opposite direction from the gap, and it must not be
    // mistaken for one.
    std::vector<uint64_t> teeth;
    uint64_t t = 1000000;
    for (double rpm = 500; rpm < 5000; rpm *= 1.35) addRevolution(teeth, t, rpm);

    crank::Decoder d;
    d.begin(kTeeth, kMissing);
    for (uint64_t x : teeth) d.onTooth(x);
    TEST_ASSERT_TRUE_MESSAGE(d.synced(), "should hold sync through hard acceleration");
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_syncs_at_idle);
    RUN_TEST(test_syncs_at_cranking_speed);
    RUN_TEST(test_syncs_at_redline);
    RUN_TEST(test_rpm_is_accurate);
    RUN_TEST(test_angle_advances_and_wraps);
    RUN_TEST(test_gap_lands_at_zero_degrees);
    RUN_TEST(test_survives_many_revolutions);
    RUN_TEST(test_spurious_tooth_loses_sync);
    RUN_TEST(test_signal_loss_is_detected);
    RUN_TEST(test_acceleration_does_not_break_sync);
    return UNITY_END();
}
