#include "Config.h"

#include <ArduinoJson.h>

#include "Console.h"
#include "StorageStm32.h"

namespace config {

Data data;

namespace {
constexpr const char* kPath = "/config.json";
constexpr const char* kTmp  = "/config.tmp";
}  // namespace

bool load() {
    if (!storage::mounted()) {
        console::println("[cfg] no card — running on built-in defaults");
        return false;
    }

    SdFat& sd = storage::fs();
    if (!sd.exists(kPath)) {
        console::printf("[cfg] %s missing — writing defaults\n", kPath);
        return save();
    }

    FsFile f = sd.open(kPath, O_RDONLY);
    if (!f) {
        console::printf("[cfg] cannot open %s — using defaults\n", kPath);
        return save();
    }

    JsonDocument doc;
    const DeserializationError err = deserializeJson(doc, f);
    f.close();

    if (err) {
        // Keep booting. A config that will not parse is a reason to fall back,
        // not a reason to leave the engine without a controller.
        console::printf("[cfg] %s is not valid JSON (%s) — rewriting defaults\n",
                      kPath, err.c_str());
        return save();
    }

    data.vehicle             = doc["vehicle"] | data.vehicle;
    data.bootCount           = doc["bootCount"] | data.bootCount;
    data.engine.cylinders    = doc["engine"]["cylinders"] | data.engine.cylinders;
    data.engine.crankTeeth   = doc["engine"]["crankTeeth"] | data.engine.crankTeeth;
    data.engine.crankMissing = doc["engine"]["crankMissing"] | data.engine.crankMissing;
    data.engine.displacementCc =
        doc["engine"]["displacementCc"] | data.engine.displacementCc;

    JsonArray fo = doc["engine"]["firingOrder"];
    if (fo && fo.size() == 8) {
        for (uint8_t i = 0; i < 8; i++) data.engine.firingOrder[i] = fo[i];
    }

    JsonObjectConst cool = doc["cooling"];
    Cooling& c = data.cooling;
    c.enabled           = cool["enabled"]           | c.enabled;
    c.fan1OnC           = cool["fan1OnC"]           | c.fan1OnC;
    c.fan1OffC          = cool["fan1OffC"]          | c.fan1OffC;
    c.fan2OnC           = cool["fan2OnC"]           | c.fan2OnC;
    c.fan2OffC          = cool["fan2OffC"]          | c.fan2OffC;
    c.acFanOn           = cool["acFanOn"]           | c.acFanOn;
    c.acFanStage        = cool["acFanStage"]        | c.acFanStage;
    c.highwayCutoff     = cool["highwayCutoff"]     | c.highwayCutoff;
    c.highwayCutoffKph  = cool["highwayCutoffKph"]  | c.highwayCutoffKph;
    c.highwayMaxC       = cool["highwayMaxC"]       | c.highwayMaxC;
    c.highwayHoldMs     = cool["highwayHoldMs"]     | c.highwayHoldMs;
    c.stageDelayMs      = cool["stageDelayMs"]      | c.stageDelayMs;
    c.minRunMs          = cool["minRunMs"]          | c.minRunMs;
    c.crankInhibit      = cool["crankInhibit"]      | c.crankInhibit;
    c.runOn             = cool["runOn"]             | c.runOn;
    c.runOnMaxS         = cool["runOnMaxS"]         | c.runOnMaxS;
    c.runOnUntilC       = cool["runOnUntilC"]       | c.runOnUntilC;
    c.runOnMinVolts     = cool["runOnMinVolts"]     | c.runOnMinVolts;
    sanitiseCooling();

    return true;
}

void sanitiseCooling() {
    Cooling& c = data.cooling;

    // An off threshold at or above its on threshold is a latch, not a
    // hysteresis band: the fan would switch off the instant it switched on.
    // Pull it back to a 2 degree minimum band rather than refusing the config.
    constexpr float kMinBand = 2.0f;
    if (c.fan1OffC > c.fan1OnC - kMinBand) {
        console::printf("[cfg] fan1OffC %.1f too close to fan1OnC %.1f — using %.1f\n",
                        c.fan1OffC, c.fan1OnC, c.fan1OnC - kMinBand);
        c.fan1OffC = c.fan1OnC - kMinBand;
    }
    if (c.fan2OffC > c.fan2OnC - kMinBand) {
        console::printf("[cfg] fan2OffC %.1f too close to fan2OnC %.1f — using %.1f\n",
                        c.fan2OffC, c.fan2OnC, c.fan2OnC - kMinBand);
        c.fan2OffC = c.fan2OnC - kMinBand;
    }
    // Stage 2 exists to add cooling, so it must come on after stage 1. If they
    // are inverted the two stages fight and the second never means anything.
    if (c.fan2OnC <= c.fan1OnC) {
        console::printf("[cfg] fan2OnC %.1f not above fan1OnC %.1f — using %.1f\n",
                        c.fan2OnC, c.fan1OnC, c.fan1OnC + 5.0f);
        c.fan2OnC  = c.fan1OnC + 5.0f;
        c.fan2OffC = c.fan2OnC - 5.0f;
    }
    // The highway cutoff must never be allowed to hold above a temperature at
    // which stage 1 wants to run. That would be a speed override of a thermal
    // limit, which is the one thing this feature must not be.
    if (c.highwayMaxC > c.fan1OnC) {
        console::printf("[cfg] highwayMaxC %.1f above fan1OnC %.1f — clamped\n",
                        c.highwayMaxC, c.fan1OnC);
        c.highwayMaxC = c.fan1OnC;
    }
    if (c.acFanStage < 1 || c.acFanStage > 2) c.acFanStage = 1;
}

bool save() {
    if (!storage::mounted()) return false;
    SdFat& sd = storage::fs();

    JsonDocument doc;
    doc["vehicle"]   = data.vehicle;
    doc["bootCount"] = data.bootCount;

    JsonObject eng = doc["engine"].to<JsonObject>();
    eng["cylinders"]      = data.engine.cylinders;
    eng["crankTeeth"]     = data.engine.crankTeeth;
    eng["crankMissing"]   = data.engine.crankMissing;
    eng["displacementCc"] = data.engine.displacementCc;
    JsonArray fo = eng["firingOrder"].to<JsonArray>();
    for (uint8_t i = 0; i < 8; i++) fo.add(data.engine.firingOrder[i]);

    const Cooling& c = data.cooling;
    JsonObject cool = doc["cooling"].to<JsonObject>();
    cool["enabled"]          = c.enabled;
    cool["fan1OnC"]          = c.fan1OnC;
    cool["fan1OffC"]         = c.fan1OffC;
    cool["fan2OnC"]          = c.fan2OnC;
    cool["fan2OffC"]         = c.fan2OffC;
    cool["acFanOn"]          = c.acFanOn;
    cool["acFanStage"]       = c.acFanStage;
    cool["highwayCutoff"]    = c.highwayCutoff;
    cool["highwayCutoffKph"] = c.highwayCutoffKph;
    cool["highwayMaxC"]      = c.highwayMaxC;
    cool["highwayHoldMs"]    = c.highwayHoldMs;
    cool["stageDelayMs"]     = c.stageDelayMs;
    cool["minRunMs"]         = c.minRunMs;
    cool["crankInhibit"]     = c.crankInhibit;
    cool["runOn"]            = c.runOn;
    cool["runOnMaxS"]        = c.runOnMaxS;
    cool["runOnUntilC"]      = c.runOnUntilC;
    cool["runOnMinVolts"]    = c.runOnMinVolts;

    // Temp file then rename, so losing power mid-write cannot leave a
    // truncated config behind. An engine bay is not a friendly place for
    // filesystem assumptions.
    sd.remove(kTmp);
    FsFile f = sd.open(kTmp, O_WRONLY | O_CREAT | O_TRUNC);
    if (!f) {
        console::println("[cfg] cannot open temp file for write");
        return false;
    }
    const size_t written = serializeJsonPretty(doc, f);
    f.sync();
    f.close();
    if (written == 0) {
        console::println("[cfg] wrote 0 bytes");
        sd.remove(kTmp);
        return false;
    }
    sd.remove(kPath);
    if (!sd.rename(kTmp, kPath)) {
        console::println("[cfg] rename failed");
        return false;
    }
    return true;
}

void report() {
    console::printf("  vehicle      : %s\n", data.vehicle.c_str());
    console::printf("  engine       : %u cyl, %u cc, %u-%u crank wheel\n",
                  data.engine.cylinders, data.engine.displacementCc,
                  data.engine.crankTeeth, data.engine.crankMissing);
    console::printf("  firing order : ");
    for (uint8_t i = 0; i < 8; i++) {
        console::printf("%u%s", data.engine.firingOrder[i], i < 7 ? "-" : "\n");
    }
    console::printf("  boot count   : %lu\n", (unsigned long)data.bootCount);

    const Cooling& c = data.cooling;
    console::printf("  fans         : %s  stage1 %.0f/%.0f C  stage2 %.0f/%.0f C\n",
                    c.enabled ? "on" : "DISABLED",
                    c.fan1OnC, c.fan1OffC, c.fan2OnC, c.fan2OffC);
    console::printf("  fan options  : a/c %s (stage %u)  highway cutoff ",
                    c.acFanOn ? "on" : "off", c.acFanStage);
    if (c.highwayCutoff) {
        console::printf("above %u kph while under %.0f C",
                        c.highwayCutoffKph, c.highwayMaxC);
    } else {
        console::printf("off");
    }
    console::printf("  run-on %s\n", c.runOn ? "on" : "off");
}

}  // namespace config
