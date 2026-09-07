// Ignition scheduling tests. Native, no hardware.

#include <unity.h>
#include <math.h>
#include <initializer_list>
#include "SparkScheduler.h"

namespace {
const uint8_t kFiringOrder[8] = {1, 3, 7, 2, 6, 5, 4, 8};   // 5.4L Triton 2V

spark::Scheduler make(float advance = 10.0f, float dwellMs = 3.0f) {
    spark::Scheduler s;
    s.begin(8, kFiringOrder);
    s.setAdvanceDeg(advance);
    s.setDwellMs(dwellMs);
    return s;
}
}  // namespace

void test_eight_cylinders_90_degrees_apart() {
    auto s = make();
    for (uint8_t i = 0; i < 8; i++) {
        TEST_ASSERT_FLOAT_WITHIN(0.01f, i * 90.0f, s.tdcAngle(i));
    }
}

void test_firing_order_is_respected() {
    auto s = make();
    for (uint8_t i = 0; i < 8; i++) {
        TEST_ASSERT_EQUAL_UINT8(kFiringOrder[i], s.fireEvent(i).cylinder);
    }
}

void test_zero_advance_fires_at_tdc() {
    auto s = make(0.0f);
    for (uint8_t i = 0; i < 8; i++) {
        TEST_ASSERT_FLOAT_WITHIN(0.01f, s.tdcAngle(i), s.fireEvent(i).angle720);
    }
}

void test_advance_moves_spark_before_tdc() {
    auto s = make(25.0f);
    // Cylinder at TDC 180 should fire at 155.
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 155.0f, s.fireEvent(2).angle720);
    // The first cylinder wraps: 0 - 25 becomes 695.
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 695.0f, s.fireEvent(0).angle720);
}

void test_dwell_is_a_time_so_its_angle_scales_with_rpm() {
    auto s = make(10.0f, 3.0f);
    // 3 ms at 1000 rpm = 18 crank degrees; at 6000 rpm = 108.
    TEST_ASSERT_FLOAT_WITHIN(0.1f, 18.0f,  s.dwellDegrees(1000.0f));
    TEST_ASSERT_FLOAT_WITHIN(0.1f, 108.0f, s.dwellDegrees(6000.0f));
}

void test_dwell_duration_in_time_is_constant() {
    auto s = make(10.0f, 3.0f);
    for (float rpm : {600.0f, 2000.0f, 5000.0f}) {
        const float degs = s.dwellDegrees(rpm);
        const float ms   = degs / (rpm * 0.006f);
        TEST_ASSERT_FLOAT_WITHIN(0.01f, 3.0f, ms);
    }
}

void test_dwell_starts_before_spark() {
    auto s = make(10.0f, 3.0f);
    const float rpm = 2000.0f;
    for (uint8_t i = 0; i < 8; i++) {
        const float fire  = s.fireEvent(i).angle720;
        const float dwell = s.dwellEvent(i, rpm).angle720;
        float gap = fire - dwell;
        if (gap < 0.0f) gap += 720.0f;
        TEST_ASSERT_FLOAT_WITHIN(0.1f, s.dwellDegrees(rpm), gap);
    }
}

void test_next_event_is_always_ahead() {
    auto s = make();
    spark::Event e;
    float until;
    for (float a = 0.0f; a < 720.0f; a += 7.3f) {
        TEST_ASSERT_TRUE(s.nextEvent(a, 2500.0f, e, until));
        TEST_ASSERT_TRUE_MESSAGE(until > 0.0f && until <= 720.0f,
                                 "next event must be strictly ahead and within one cycle");
    }
}

void test_sixteen_events_per_cycle() {
    // Eight cylinders, each with a dwell-start and a fire. Stepping event to
    // event, the 16th hop must land back on the one we started from — that is
    // what "16 events per cycle" actually means, and unlike counting by
    // distance travelled it does not depend on where the walk begins.
    auto s = make();
    spark::Event e;
    float until;
    float a = s.fireEvent(0).angle720;      // start exactly on a known event
    const float start = a;

    for (int i = 0; i < 16; i++) {
        TEST_ASSERT_TRUE(s.nextEvent(a, 2500.0f, e, until));
        a = e.angle720;
    }
    TEST_ASSERT_FLOAT_WITHIN_MESSAGE(0.01f, start, a,
                                     "16 hops should return to the starting event");
}

void test_events_are_evenly_spaced() {
    // Fixed advance and dwell put every event an equal distance apart: eight
    // cylinders x two events = 16, so 45 degrees at 720/16. Uneven spacing
    // would mean a cylinder is being served late.
    auto s = make(10.0f, 3.0f);
    spark::Event e;
    float until;
    float a = s.fireEvent(0).angle720;
    for (int i = 0; i < 16; i++) {
        TEST_ASSERT_TRUE(s.nextEvent(a, 2500.0f, e, until));
        TEST_ASSERT_FLOAT_WITHIN_MESSAGE(0.01f, 45.0f, until,
                                         "events should be 45 degrees apart");
        a = e.angle720;
    }
}

void test_dwell_overlap_limit_is_found() {
    auto s = make(10.0f, 3.0f);
    // Events are 90 degrees apart. 3 ms fills 90 degrees at 5000 rpm:
    //   90 / (3 * 0.006) = 5000
    TEST_ASSERT_FLOAT_WITHIN(1.0f, 5000.0f, s.maxRpmForDwell());
    TEST_ASSERT_FALSE_MESSAGE(s.dwellOverlaps(4000.0f), "3 ms fits at 4000 rpm");
    TEST_ASSERT_TRUE_MESSAGE(s.dwellOverlaps(5500.0f),
                             "3 ms cannot fit between events at 5500 rpm");
}

void test_shorter_dwell_raises_the_limit() {
    auto s = make(10.0f, 2.0f);
    TEST_ASSERT_FLOAT_WITHIN(1.0f, 7500.0f, s.maxRpmForDwell());
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_eight_cylinders_90_degrees_apart);
    RUN_TEST(test_firing_order_is_respected);
    RUN_TEST(test_zero_advance_fires_at_tdc);
    RUN_TEST(test_advance_moves_spark_before_tdc);
    RUN_TEST(test_dwell_is_a_time_so_its_angle_scales_with_rpm);
    RUN_TEST(test_dwell_duration_in_time_is_constant);
    RUN_TEST(test_dwell_starts_before_spark);
    RUN_TEST(test_next_event_is_always_ahead);
    RUN_TEST(test_sixteen_events_per_cycle);
    RUN_TEST(test_events_are_evenly_spaced);
    RUN_TEST(test_dwell_overlap_limit_is_found);
    RUN_TEST(test_shorter_dwell_raises_the_limit);
    return UNITY_END();
}
