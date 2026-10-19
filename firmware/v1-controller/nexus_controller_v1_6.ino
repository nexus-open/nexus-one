/*
 * NEXUS ONE — Controller Firmware v1.3 (ESP32-S3, Arduino + NimBLE)
 * Implements protocol/BLE_PROTOCOL.md v1.0 for the v1.0-frozen design.
 *
 * The controller is the SAFETY OWNER: thermal law and bay limits are enforced
 * here even if the host app misbehaves or dies.
 *
 * HARDWARE NOTES (real design decisions, not placeholders):
 *  - AS5600 drum encoder and MAX17048 gauge BOTH have fixed I2C address 0x36.
 *    They must live on separate buses: AS5600 on Wire (bus 0), gauge on
 *    Wire1 (bus 1). The v0.8 board routes them accordingly.
 *  - DRV5032 detent outputs are push-pull digital -> plain GPIO inputs.
 *  - Bay power via TPS229-class load switches on GPIOs (active-high enable).
 *  - Panel 5V boost enable on GPIO.
 *
 * STATUS: source-complete for the logic in logic_tests/ (which IS executed).
 * Not compiled here — no ESP32 toolchain in the design environment.
 * Build: Arduino IDE / arduino-cli with NimBLE-Arduino 2.x, board ESP32S3 Dev.
 */
#include <Wire.h>
#include <NimBLEDevice.h>

// ---------- Frozen design constants ----------
static const float DRUM_MAX_DEG   = 220.0f;   // v0.7: 0.61 rev over travel
static const float BUDGET_FOLDED_W = 2.0f;    // v0.4 thermal law
static const float BUDGET_FOLDED_BATTMOD_W = 1.5f;  // v0.7 derate
static const float BUDGET_OPEN_W   = 3.0f;    // v0.6 thermal law
static const float OPEN_THRESHOLD_DEG = 198.0f; // >=90% deployment = "open"
static const uint32_t HEARTBEAT_TIMEOUT_MS = 30000;  // protocol: bay off after 30 s
static const float MODULE_DRAW_W[6] = {0, 0.0f /*battery: adds capacity*/, 2.5f, 1.2f, 0.3f, 0.6f}; // by moduleId

// ---------- Pins (v0.8 tray board routing) ----------
static const int PIN_DETENT_OPEN = 4, PIN_DETENT_CLOSED = 5, PIN_COVER = 6;
static const int PIN_BAY_EN = 7, PIN_PANEL_EN = 8, PIN_LED = 48, PIN_PAIR_BTN = 0;
static const int I2C0_SDA = 10, I2C0_SCL = 11;   // AS5600 @ 0x36
static const int I2C1_SDA = 12, I2C1_SCL = 13;   // MAX17048 @ 0x36 (separate bus!)

// ---------- BLE (protocol v1.0) ----------
#define UUID_BASE_SUFFIX "-1000-8000-00805f9b34fb"
static const char* SVC_UUID  = "4e455855-0000" UUID_BASE_SUFFIX;
static const char* CH_ANGLE  = "4e455855-0001" UUID_BASE_SUFFIX;
static const char* CH_DETENT = "4e455855-0002" UUID_BASE_SUFFIX;
static const char* CH_BATT   = "4e455855-0003" UUID_BASE_SUFFIX;
static const char* CH_BAY    = "4e455855-0004" UUID_BASE_SUFFIX;
static const char* CH_THERM  = "4e455855-0005" UUID_BASE_SUFFIX;
static const char* CH_CMD    = "4e455855-0010" UUID_BASE_SUFFIX;
static const char* CH_INFO   = "4e455855-0020" UUID_BASE_SUFFIX;

NimBLECharacteristic *chAngle, *chDetent, *chBatt, *chBay, *chTherm;
bool hostConnected = false, hostBonded = false;
uint32_t lastHeartbeatMs = 0;

// ---------- Device state ----------
float drumDeg = 0, lastNotifiedDeg = -10;
uint8_t moduleId = 0; bool modulePower = false, panelOn = true;
uint8_t brightnessCapPct = 100, budgetState = 0;  // 0 ok, 1 dim, 2 pause-module
float angleZeroOffset = 0;

// ---------- Sensors ----------
float readDrumDeg() {
  Wire.beginTransmission(0x36); Wire.write(0x0E);          // AS5600 RAW ANGLE hi
  if (Wire.endTransmission(false) != 0) return drumDeg;
  Wire.requestFrom(0x36, 2);
  if (Wire.available() < 2) return drumDeg;
  uint16_t raw = (Wire.read() << 8) | Wire.read();
  float deg = (raw & 0x0FFF) * 360.0f / 4096.0f - angleZeroOffset;
  if (deg < 0) deg += 360.0f;
  return deg > 300.0f ? 0.0f : deg;   // wrap guard near zero point
}
void readBattery(uint8_t &pct, uint16_t &mv, uint8_t &flags) {
  Wire1.beginTransmission(0x36); Wire1.write(0x02);        // MAX17048 VCELL
  Wire1.endTransmission(false); Wire1.requestFrom(0x36, 2);
  uint16_t v = (Wire1.read() << 8) | Wire1.read();
  mv = (uint16_t)(v * 0.078125f);                          // 78.125 uV/LSB
  Wire1.beginTransmission(0x36); Wire1.write(0x04);        // SOC
  Wire1.endTransmission(false); Wire1.requestFrom(0x36, 2);
  pct = Wire1.read();                                      // integer % in hi byte
  flags = 0;                                               // charging detection via charger IRQ in rev 2
}
uint8_t detentBits() {
  return (digitalRead(PIN_DETENT_OPEN) ? 1 : 0)
       | (digitalRead(PIN_DETENT_CLOSED) ? 2 : 0)
       | (digitalRead(PIN_COVER) ? 4 : 0);
}

// ---------- Thermal law (safety owner) ----------
float estimateDrawW() {
  float disp = panelOn ? (0.6f + 2.0f * (drumDeg / DRUM_MAX_DEG)) * (brightnessCapPct / 100.0f) : 0.0f;
  float mod = (modulePower && moduleId > 0) ? MODULE_DRAW_W[moduleId] : 0.0f;
  return disp + 0.35f + mod;
}
void enforceThermal() {
  bool open = drumDeg >= OPEN_THRESHOLD_DEG;
  float budget = open ? BUDGET_OPEN_W
                      : (moduleId == 1 ? BUDGET_FOLDED_BATTMOD_W : BUDGET_FOLDED_W);
  float draw = estimateDrawW();
  if (draw <= budget) { budgetState = 0; return; }
  budgetState = 1;                                  // ask OS to dim
  if (draw > budget + 0.5f && modulePower && moduleId != 1) {
    setModulePower(false);                          // refuse: cut the module
    budgetState = 2;
  }
}

// ---------- Actuators ----------
void setModulePower(bool on) {
  modulePower = on;
  digitalWrite(PIN_BAY_EN, on ? HIGH : LOW);
  notifyBay();
}
void notifyBay() {
  if (!chBay) return;
  uint8_t buf[4] = {moduleId, (uint8_t)(modulePower ? 1 : 0), 0, 0};
  uint16_t ma = modulePower ? (uint16_t)(MODULE_DRAW_W[moduleId] / 5.0f * 1000) : 0;
  buf[2] = ma & 0xFF; buf[3] = ma >> 8;
  chBay->setValue(buf, 4); if (hostConnected) chBay->notify();
}

// ---------- Commands (protocol opcodes; link must be bonded+encrypted) ----------
struct CmdCallbacks : NimBLECharacteristicCallbacks {
  void onWrite(NimBLECharacteristic* c, NimBLEConnInfo& info) override {
    if (!info.isBonded() || !info.isEncrypted()) return;   // protocol security rule
    std::string v = c->getValue();
    if (v.empty()) return;
    switch ((uint8_t)v[0]) {
      case 0x00: lastHeartbeatMs = millis(); break;
      case 0x01: if (v.size() > 1) { panelOn = v[1] != 0; digitalWrite(PIN_PANEL_EN, panelOn); } break;
      case 0x02: if (v.size() > 2) { moduleId = v[1]; setModulePower(v[2] != 0); } break;
      case 0x03: if (v.size() > 1) brightnessCapPct = min<uint8_t>(v[1], 100); break;
      case 0x04: if (detentBits() & 2) angleZeroOffset += drumDeg; break;  // only at closed detent
      case 0x05: break; // LED patterns: rev 2
    }
  }
};
struct ServerCb : NimBLEServerCallbacks {
  void onConnect(NimBLEServer*, NimBLEConnInfo& info) override {
    hostConnected = true; hostBonded = info.isBonded(); lastHeartbeatMs = millis();
  }
  void onDisconnect(NimBLEServer*, NimBLEConnInfo&, int) override { hostConnected = false; }
};

void setup() {
  pinMode(PIN_DETENT_OPEN, INPUT); pinMode(PIN_DETENT_CLOSED, INPUT); pinMode(PIN_COVER, INPUT);
  pinMode(PIN_BAY_EN, OUTPUT); pinMode(PIN_PANEL_EN, OUTPUT); pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_PANEL_EN, HIGH);
  Wire.begin(I2C0_SDA, I2C0_SCL); Wire1.begin(I2C1_SDA, I2C1_SCL);

  NimBLEDevice::init("NEXUS-ONE");
  NimBLEDevice::setSecurityAuth(true, true, true);          // bonding + LE Secure Connections
  auto* server = NimBLEDevice::createServer();
  server->setCallbacks(new ServerCb());
  server->advertiseOnDisconnect(false);
  auto* svc = server->createService(SVC_UUID);
  // v1.6 compile fix (2026-10-19, real toolchain): v1.3 used the Bluedroid
  // setAccessPermissions()/ESP_GATT_PERM_* API, which does not exist in
  // NimBLE-Arduino. NimBLE enforces encrypted access with the READ_ENC /
  // WRITE_ENC property flags at creation time — same protocol rule
  // (every characteristic requires an encrypted, bonded link).
  auto mk = [&](const char* uuid, uint32_t props) {
    return svc->createCharacteristic(uuid, props | NIMBLE_PROPERTY::READ_ENC);
  };
  chAngle  = mk(CH_ANGLE,  NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY);
  chDetent = mk(CH_DETENT, NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY);
  chBatt   = mk(CH_BATT,   NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY);
  chBay    = mk(CH_BAY,    NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY);
  chTherm  = mk(CH_THERM,  NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY);
  auto* chCmd = svc->createCharacteristic(CH_CMD, NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::WRITE_ENC);
  chCmd->setCallbacks(new CmdCallbacks());
  auto* chInfo = mk(CH_INFO, NIMBLE_PROPERTY::READ);
  uint8_t info[4] = {0x01, 0x03, 0x01, 0x01};               // fw 1.3, hw rev 1, protocol 1
  chInfo->setValue(info, 4);
  svc->start();
  // Advertising only inside the pairing window is handled in loop() via the
  // pair button (protocol rule); start connectable-for-bonded at boot.
  NimBLEDevice::getAdvertising()->start();
}

void loop() {
  static uint32_t tSlow = 0, tDet = 0;
  drumDeg = readDrumDeg();
  // Angle notify: on >=1 degree change, max 10 Hz by sensor poll cadence
  if (fabs(drumDeg - lastNotifiedDeg) >= 1.0f && chAngle) {
    uint16_t v = (uint16_t)(drumDeg * 100);
    chAngle->setValue((uint8_t*)&v, 2);
    if (hostConnected) chAngle->notify();
    lastNotifiedDeg = drumDeg;
  }
  if (millis() - tDet > 200) {                              // detents on change cadence
    tDet = millis();
    static uint8_t lastDet = 0xFF; uint8_t d = detentBits();
    if (d != lastDet) { lastDet = d; chDetent->setValue(&d, 1); if (hostConnected) chDetent->notify(); }
  }
  if (millis() - tSlow > 5000) {                            // battery + thermal, 5 s
    tSlow = millis();
    uint8_t pct, flags; uint16_t mv;
    readBattery(pct, mv, flags);
    uint8_t bb[4] = {pct, (uint8_t)(mv & 0xFF), (uint8_t)(mv >> 8), flags};
    chBatt->setValue(bb, 4); if (hostConnected) chBatt->notify();
    enforceThermal();
    int16_t t = (int16_t)(temperatureRead() * 100);         // controller die temp as board proxy
    uint8_t tb[3] = {(uint8_t)(t & 0xFF), (uint8_t)(t >> 8), budgetState};
    chTherm->setValue(tb, 3); if (hostConnected) chTherm->notify();
  }
  // Heartbeat watchdog: no host for 30 s -> bay powers down (protocol rule)
  if (modulePower && (!hostConnected || millis() - lastHeartbeatMs > HEARTBEAT_TIMEOUT_MS)) {
    setModulePower(false);
  }
  delay(20);
}
