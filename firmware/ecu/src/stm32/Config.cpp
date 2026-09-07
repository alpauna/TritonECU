#include "Config.h"

#include <ArduinoJson.h>

#include "StorageStm32.h"

namespace config {

Data data;

namespace {
constexpr const char* kPath = "/config.json";
constexpr const char* kTmp  = "/config.tmp";
}  // namespace

bool load() {
    if (!storage::mounted()) {
        Serial.println("[cfg] no card — running on built-in defaults");
        return false;
    }

    SdFat& sd = storage::fs();
    if (!sd.exists(kPath)) {
        Serial.printf("[cfg] %s missing — writing defaults\n", kPath);
        return save();
    }

    FsFile f = sd.open(kPath, O_RDONLY);
    if (!f) {
        Serial.printf("[cfg] cannot open %s — using defaults\n", kPath);
        return save();
    }

    JsonDocument doc;
    const DeserializationError err = deserializeJson(doc, f);
    f.close();

    if (err) {
        // Keep booting. A config that will not parse is a reason to fall back,
        // not a reason to leave the engine without a controller.
        Serial.printf("[cfg] %s is not valid JSON (%s) — rewriting defaults\n",
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
    return true;
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

    // Temp file then rename, so losing power mid-write cannot leave a
    // truncated config behind. An engine bay is not a friendly place for
    // filesystem assumptions.
    sd.remove(kTmp);
    FsFile f = sd.open(kTmp, O_WRONLY | O_CREAT | O_TRUNC);
    if (!f) {
        Serial.println("[cfg] cannot open temp file for write");
        return false;
    }
    const size_t written = serializeJsonPretty(doc, f);
    f.sync();
    f.close();
    if (written == 0) {
        Serial.println("[cfg] wrote 0 bytes");
        sd.remove(kTmp);
        return false;
    }
    sd.remove(kPath);
    if (!sd.rename(kTmp, kPath)) {
        Serial.println("[cfg] rename failed");
        return false;
    }
    return true;
}

void report() {
    Serial.printf("  vehicle      : %s\n", data.vehicle.c_str());
    Serial.printf("  engine       : %u cyl, %u cc, %u-%u crank wheel\n",
                  data.engine.cylinders, data.engine.displacementCc,
                  data.engine.crankTeeth, data.engine.crankMissing);
    Serial.print("  firing order : ");
    for (uint8_t i = 0; i < 8; i++) {
        Serial.printf("%u%s", data.engine.firingOrder[i], i < 7 ? "-" : "\n");
    }
    Serial.printf("  boot count   : %lu\n", (unsigned long)data.bootCount);
}

}  // namespace config
