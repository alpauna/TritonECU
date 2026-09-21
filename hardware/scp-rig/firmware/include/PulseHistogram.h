#pragma once
#include <stdint.h>
#include <string.h>

// Bins edge-to-edge intervals and finds the clusters in them.
//
// The point: J1850 PWM carries meaning in *where the falling edge lands inside a
// bit*, so the decoder needs tp values in nanoseconds. Rather than hard-coding
// numbers from a half-remembered datasheet — which produces a decoder that fails
// like broken hardware — measure the bus and let the clusters name themselves.
//
// Thirty seconds on a running truck is enough. The output is a short list like
// "8.0 us x 41k, 16.1 us x 39k, 24.2 us x 2k", and those are the constants.
template <uint32_t BINS, uint32_t NS_PER_BIN>
class PulseHistogram {
public:
    struct Cluster {
        uint32_t centroidNs;   // intensity-weighted centre — not the peak bin
        uint32_t count;        // samples in the cluster
        uint32_t loNs, hiNs;   // extent, so spread is visible
    };

    void clear() { memset(_bin, 0, sizeof(_bin)); _total = _over = 0; }

    void add(uint32_t ns) {
        const uint32_t b = ns / NS_PER_BIN;
        if (b >= BINS) { _over++; return; }   // counted, never silently dropped
        _bin[b]++;
        _total++;
    }

    // Walk the bins, gather runs that stay above a floor, and report each run's
    // centroid.
    //
    // The floor is a fraction of the TOTAL sample count, not of the tallest bin.
    // That distinction is the whole point: a peak-relative floor buries the rare
    // intervals, and on this bus the rare intervals are the ones that matter —
    // SOF, EOF and IFS happen once per frame while ordinary bits happen dozens
    // of times per frame, so they can sit two orders of magnitude below the
    // common peaks and still be structural rather than noise.
    //
    // Default 1 per mille: a bin counts if it holds at least 0.1 % of all
    // samples. Genuine scatter lands far below that; a real but rare interval
    // does not.
    uint32_t clusters(Cluster* out, uint32_t maxOut, uint32_t floorPerMille = 1) const {
        if (!_total) return 0;
        const uint32_t floor = (_total * floorPerMille) / 1000;

        uint32_t n = 0;
        uint32_t i = 0;
        while (i < BINS && n < maxOut) {
            if (_bin[i] <= floor) { i++; continue; }
            uint32_t j = i, sum = 0;
            uint64_t weighted = 0;
            while (j < BINS && _bin[j] > floor) {
                const uint32_t mid = j * NS_PER_BIN + NS_PER_BIN / 2;
                weighted += (uint64_t)_bin[j] * mid;
                sum += _bin[j];
                j++;
            }
            out[n].centroidNs = (uint32_t)(weighted / sum);
            out[n].count = sum;
            out[n].loNs = i * NS_PER_BIN;
            out[n].hiNs = j * NS_PER_BIN;
            n++;
            i = j;
        }
        return n;
    }

    uint32_t total() const { return _total; }
    uint32_t overRange() const { return _over; }
    uint32_t bin(uint32_t i) const { return i < BINS ? _bin[i] : 0; }
    static constexpr uint32_t binNs() { return NS_PER_BIN; }
    static constexpr uint32_t spanNs() { return BINS * NS_PER_BIN; }

private:
    uint32_t _bin[BINS];
    uint32_t _total = 0;
    uint32_t _over  = 0;
};
