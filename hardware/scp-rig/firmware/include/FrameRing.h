#pragma once
#include <stdint.h>
#include <string.h>
#include <atomic>

// Single-producer / single-consumer ring for decoded SCP frames.
//
// The producer is the capture side (PIO/ISR). The consumer is the SD writer.
// They never block each other: indices are free-running counters, masked only on
// access, so "full" and "empty" are never ambiguous — the failure mode a ring
// with wrapping indices has, where head == tail means both.
//
// WHY THIS EXISTS: an SD card stalls 100-250 ms for wear levelling, and the
// writer blocks for the whole pause. Without a buffer, every frame arriving
// during that stall is simply gone — and the one you drove out to capture is a
// MIL transition that lasts milliseconds.
//
// OVERFLOW POLICY: drop the NEWEST and count it. The alternative, overwriting
// the oldest, leaves a gap too but moves it somewhere harder to reason about.
// Either way the rule is the same and it matters more than the choice:
// **a silently dropped frame is worse than no capture**, because nothing in the
// file says the gap is there. Callers must log dropped() into the capture.
struct ScpFrame {
    uint64_t tUs;        // capture timestamp, free-running microseconds
    uint8_t  len;        // payload bytes used, 0-12
    uint8_t  flags;      // bit0 = CRC bad, bit1 = framing error, bit2 = gap marker
    uint8_t  data[12];
};
static_assert(sizeof(ScpFrame) == 24, "ScpFrame should stay small and aligned");

template <uint32_t SLOTS>
class FrameRing {
    static_assert(SLOTS && ((SLOTS & (SLOTS - 1)) == 0), "SLOTS must be a power of two");
public:
    // Producer side. Returns false if the ring is full; the frame is dropped and
    // counted rather than overwriting unread data.
    bool push(const ScpFrame& f) {
        const uint32_t head = _head.load(std::memory_order_relaxed);
        const uint32_t tail = _tail.load(std::memory_order_acquire);
        if ((uint32_t)(head - tail) >= SLOTS) {      // wrap-safe fullness test
            _dropped.fetch_add(1, std::memory_order_relaxed);
            return false;
        }
        _buf[head & (SLOTS - 1)] = f;
        _head.store(head + 1, std::memory_order_release);

        const uint32_t used = (uint32_t)(head + 1 - tail);
        if (used > _high.load(std::memory_order_relaxed))
            _high.store(used, std::memory_order_relaxed);
        return true;
    }

    // Consumer side.
    bool pop(ScpFrame& out) {
        const uint32_t tail = _tail.load(std::memory_order_relaxed);
        if (tail == _head.load(std::memory_order_acquire)) return false;   // empty
        out = _buf[tail & (SLOTS - 1)];
        _tail.store(tail + 1, std::memory_order_release);
        return true;
    }

    uint32_t size() const {
        return _head.load(std::memory_order_acquire) - _tail.load(std::memory_order_acquire);
    }
    static constexpr uint32_t capacity() { return SLOTS; }
    uint32_t dropped()   const { return _dropped.load(std::memory_order_relaxed); }
    uint32_t highWater() const { return _high.load(std::memory_order_relaxed); }
    void clearStats() { _dropped.store(0); _high.store(0); }

private:
    ScpFrame _buf[SLOTS];
    std::atomic<uint32_t> _head{0};
    std::atomic<uint32_t> _tail{0};
    std::atomic<uint32_t> _dropped{0};
    std::atomic<uint32_t> _high{0};
};
