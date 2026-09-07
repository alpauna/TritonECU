#pragma once
// SD card, on the P4's native SDMMC controller.
//
// The Waveshare carrier wires its TF slot to SDMMC slot 0, whose CLK/CMD/D0-D3
// are fixed in silicon (GPIO39-44) with card power switched by GPIO45. The
// Arduino variant header declares all of that, so mounting needs no pin setup.
//
// This is deliberately not the old firmware's SPI path: SDMMC is a 4-bit bus,
// and moving off SPI also frees the four pins the S3 build spent on the card.

#include <Arduino.h>

namespace storage {

// Mounts the card, retrying in 1-bit mode if the 4-bit bus will not train —
// the usual symptom of a marginal card or a long adapter cable.
bool begin();

bool mounted();

// "SDMMC 4-bit", "SDMMC 1-bit", or "not mounted".
const char* backend();

uint64_t cardSizeBytes();
uint64_t usedBytes();

void report();

}  // namespace storage
