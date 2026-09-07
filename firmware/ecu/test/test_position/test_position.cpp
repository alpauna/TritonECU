// Cam sync / 720-degree engine position tests. Native, no hardware.

#include <unity.h>
#include "EnginePosition.h"

namespace {

constexpr float kCamAngle = 90.0f;   // cam pulse expected at 90 deg, revolution 0

// Walks the crank through `revs` revolutions of a 36-1 wheel, firing the cam
// once per two revolutions at kCamAngle. Returns the position tracker.
engine::Position runCycles(int revs, bool withCam = true, float camAngle = kCamAngle) {
    engine::Position p;
    p.begin(kCamAngle, 30.0f);

    for (int r = 0; r < revs; r++) {
        for (uint16_t tooth = 0; tooth < 35; tooth++) {
            const float angle = (tooth == 0) ? 0.0f : (tooth + 1) * 10.0f;
            p.onCrankTooth(true, tooth, angle);
            // Cam fires once every two revolutions, at camAngle.
            if (withCam && (r % 2 == 0) && angle >= camAngle && angle < camAngle + 10.0f) {
                p.onCamEdge(angle);
            }
        }
    }
    return p;
}

}  // namespace

void test_no_sync_without_crank() {
    engine::Position p;
    p.begin(kCamAngle);
    p.onCamEdge(90.0f);            // cam with no crank anchors nothing
    TEST_ASSERT_FALSE(p.synced());
    TEST_ASSERT_EQUAL(engine::PhaseState::kNoCrank, p.phase().state);
}

void test_crank_alone_gives_360_not_720() {
    auto p = runCycles(4, /*withCam=*/false);
    TEST_ASSERT_FALSE_MESSAGE(p.synced(), "cannot know the 720 phase without a cam pulse");
    TEST_ASSERT_EQUAL_MESSAGE(engine::PhaseState::kWaitingCam, p.phase().state,
                              "should report waiting for cam, not failed");
}

void test_cam_establishes_720_sync() {
    auto p = runCycles(4);
    TEST_ASSERT_TRUE_MESSAGE(p.synced(), "a cam pulse at the expected angle should sync");
    TEST_ASSERT_TRUE(p.phase().camSyncs >= 1);
}

void test_angle_covers_full_720() {
    engine::Position p;
    p.begin(kCamAngle, 30.0f);
    float maxSeen = 0.0f;
    bool sawOver360 = false;
    for (int r = 0; r < 8; r++) {
        for (uint16_t tooth = 0; tooth < 35; tooth++) {
            const float angle = (tooth == 0) ? 0.0f : (tooth + 1) * 10.0f;
            p.onCrankTooth(true, tooth, angle);
            if ((r % 2 == 0) && angle >= kCamAngle && angle < kCamAngle + 10.0f) {
                p.onCamEdge(angle);
            }
            if (p.synced()) {
                const float a = p.phase().angle720;
                TEST_ASSERT_TRUE_MESSAGE(a >= 0.0f && a < 720.0f, "angle must stay in 0-720");
                if (a > maxSeen) maxSeen = a;
                if (a >= 360.0f) sawOver360 = true;
            }
        }
    }
    TEST_ASSERT_TRUE_MESSAGE(sawOver360, "must reach the second revolution");
}

void test_cam_pulse_at_wrong_angle_is_rejected() {
    engine::Position p;
    p.begin(kCamAngle, 30.0f);
    for (uint16_t tooth = 0; tooth < 35; tooth++) {
        p.onCrankTooth(true, tooth, tooth == 0 ? 0.0f : (tooth + 1) * 10.0f);
    }
    // A pulse 180 degrees from where it belongs: noise, or a failing sensor.
    // Trusting it would put every cylinder on the exhaust stroke.
    p.onCamEdge(270.0f);
    TEST_ASSERT_FALSE_MESSAGE(p.synced(), "an implausible cam pulse must not establish sync");
    TEST_ASSERT_TRUE_MESSAGE(p.phase().camRejects >= 1, "and should be counted as rejected");
}

void test_losing_crank_drops_720_sync() {
    auto p = runCycles(4);
    TEST_ASSERT_TRUE(p.synced());
    p.onCrankTooth(false, 0, 0.0f);      // crank sync lost
    TEST_ASSERT_FALSE_MESSAGE(p.synced(), "720 sync cannot outlive crank sync");
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_no_sync_without_crank);
    RUN_TEST(test_crank_alone_gives_360_not_720);
    RUN_TEST(test_cam_establishes_720_sync);
    RUN_TEST(test_angle_covers_full_720);
    RUN_TEST(test_cam_pulse_at_wrong_angle_is_rejected);
    RUN_TEST(test_losing_crank_drops_720_sync);
    return UNITY_END();
}
