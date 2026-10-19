/*
 * NEXUS ONE — Controller Firmware v2.1 SECURITY BRANCH (ESP32-S3, Arduino + NimBLE)
 * Base: CODE_v1_6/firmware/nexus_controller/nexus_controller.ino (v1.3 logic +
 * the v1.6 NimBLE-encrypted-characteristic compile patch — PRESERVED, see the
 * "v1.6 compile fix" note in setup()).
 *
 * This branch implements the fix-before-merge findings of
 * DESIGN_v2_0/security/SECURITY_REVIEW_v2_0.md:
 *   F1 pairing window (2 s hold -> 60 s open advertising; bonded-only otherwise)
 *   F7 single connection (folded into F1)
 *   F2 moduleId range validation 0..8 (v2.0 module table)
 *   F3 heartbeat watchdog refresh only from authenticated sources
 *   F4 bay identify-before-power contract (spine side)
 *   F5 CCCD/notify hardening (app-layer; see long note — HW validation required)
 *   F13 absolute calibrate + detent debounce
 *
 * NOT carried over from the review (out of this branch's scope):
 *   F6/F9 Android client fixes, F8 HID attestation, F10/F11/F12 module-side
 *   fixes, I3 RPA privacy.
 *
 * HARDWARE/NOT-VERIFIED: compiled with the real toolchain (see
 * verification/compile_v2_1.txt) but NEVER run on an ESP32-S3 target here.
 * F5's CCCD behavior, the F1 whitelist/scan-filter semantics, and the whole
 * F4 bay sequence are code-reasoned only — all marked NOT-VERIFIED below.
 */
#include <Wire.h>
#include <NimBLEDevice.h>
#include <vector>

// ---------- Frozen design constants ----------
static const float DRUM_MAX_DEG   = 220.0f;   // v0.7: 0.61 rev over travel
static const float BUDGET_FOLDED_W = 2.0f;    // v0.4 thermal law
static const float BUDGET_FOLDED_BATTMOD_W = 1.5f;  // v0.7 derate
static const float BUDGET_OPEN_W   = 3.0f;    // v0.6 thermal law
static const float OPEN_THRESHOLD_DEG = 198.0f; // >=90% deployment = "open"
static const uint32_t HEARTBEAT_TIMEOUT_MS = 30000;  // protocol: bay off after 30 s
// [v2.1/F2] extended to 0..8 (v2.0 module IDs); index = moduleId.
// 0 none, 1 battery (adds capacity), 2 camera, 3 storage, 4 sensor,
// 5 cooling, 6 keyboard, 7 neural, 8 satellite.
static const float MODULE_DRAW_W[9] = {
  0.0f, 0.0f, 2.5f, 1.2f, 0.3f, 0.6f, 0.5f, 2.0f, 3.0f
};
static const uint8_t MODULE_ID_MAX = 8;

// ---------- Pairing window (F1) ----------
static const uint32_t PAIR_HOLD_MS   = 2000;   // debounced hold to open the window
static const uint32_t PAIR_WINDOW_MS = 60000;  // open-advertising window

// ---------- Bay trust contract (F4) ----------
static const int PIN_BAY_ID_ADC = 9;  // ADC1_CH8 — REV-2 BOARD ADDITION.
  // The v0.8 tray board does NOT route pogo pin 7 (ID) to an ADC. Rev-2 must
  // wire the ID divider (10k pull-up to 3V3 on the spine, module coding
  // resistor to GND) to GPIO9. Until the board exists, identify() cannot run
  // on hardware — keep every v2.0 bay module labeled "spine support pending".
static const uint8_t BAY_I2C_ADDR = 0x2A;   // bay module slave address.
  // Shares Wire1 with the MAX17048 gauge (0x36) — the addresses cannot
  // collide. Rev-2 routes pogo pins 5/6 (I2C SDA/SCL) to the Wire1 pair.
static const uint8_t BAY_REG_TX_PERMIT = 0x20;  // satellite TX gate register

enum BayState : uint8_t { BAY_OFF = 0, BAY_BOOT = 1, BAY_ON = 2, BAY_FAULT = 3 };
BayState bayState = BAY_OFF;
uint8_t bayIdentifiedId = 0;     // ID proven by divider+I2C cross-check
uint8_t bayRequestedId = 0;      // BLE-requested moduleId (validated 0..8)
bool bayPowerRequested = false;  // BLE SetModulePower(true), pending identify
bool bayTxPermitted = false;     // reg 0x20 state (satellite TX gate)
bool bayUsbEnumAllowed = false;  // F4: USB-host enumeration gate
uint8_t bayFaultCode = 0;        // bit0 id-mismatch, bit1 reg3-fault,
                                 // bit2 I2C-fail, bit3 requested-id mismatch

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
NimBLEServer* bleServer = nullptr;
bool hostConnected = false, hostBonded = false, hostEncrypted = false;
uint32_t lastHeartbeatMs = 0;
std::vector<NimBLEAddress> bondedPeers;  // peers bonded via the pairing window

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
// [v2.1/F13] debounced detent read: 3 consecutive agreeing raw reads
// (~60 ms at the 20 ms loop cadence) before the stable value updates.
uint8_t detentBitsDebounced() {
  static uint8_t lastRaw = 0xFF, stable = 0xFF, agree = 0;
  uint8_t raw = detentBits();
  if (raw == lastRaw) { if (agree < 255) agree++; }
  else { lastRaw = raw; agree = 1; }
  if (agree >= 3) stable = raw;
  return stable;
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

// ---------- Bay trust contract (F4, spine side) ----------
// Expected 12-bit ADC codes (3V3 ref, 10k pull-up): code = 4095 * R/(10k+R)
//   1k:372  2k2:738  4k7:1310  10k:2047  22k:2814  33k:3143  47k:3376  68k:3570  open:4095
// Thresholds sit at the midpoints between adjacent nominals, so 1% coding
// resistors plus ADC error stay well inside their windows.
uint8_t bayDividerId(int raw) {
  if (raw > 3832) return 0;    // open — no module docked
  if (raw > 3473) return 8;    // 68k  satellite
  if (raw > 3259) return 7;    // 47k  neural
  if (raw > 2978) return 6;    // 33k  keyboard
  if (raw > 2430) return 5;    // 22k  cooling
  if (raw > 1678) return 4;    // 10k  sensor
  if (raw > 1024) return 3;    // 4k7  storage
  if (raw > 555)  return 2;    // 2k2  camera
  if (raw > 120)  return 1;    // 1k   battery
  return 255;                  // shorted/invalid divider
}
bool bayReadRegs(uint8_t reg[4]) {   // I2C-master poll of 0x2A regs 0-3
  Wire1.beginTransmission(BAY_I2C_ADDR); Wire1.write(0x00);
  if (Wire1.endTransmission(false) != 0) return false;
  if (Wire1.requestFrom(BAY_I2C_ADDR, (uint8_t)4) != 4) return false;
  for (int i = 0; i < 4; i++) reg[i] = Wire1.read();
  return true;
}
bool bayWriteReg(uint8_t r, uint8_t v) {
  Wire1.beginTransmission(BAY_I2C_ADDR); Wire1.write(r); Wire1.write(v);
  return Wire1.endTransmission() == 0;
}
// (1) ADC read of the ID divider BEFORE enabling PIN_BAY_EN; (2) I2C poll of
// 0x2A regs 0-3 on the boot-low rail (the module self-limits to <50 mA at boot
// per the module-side contract); (3) cross-check; mismatch/fault -> fail.
bool bayIdentify() {
  uint8_t divId = bayDividerId(analogRead(PIN_BAY_ID_ADC));  // BEFORE rail enable
  if (divId == 0 || divId == 255) { bayFaultCode |= 0x01; return false; }
  digitalWrite(PIN_BAY_EN, HIGH);                            // boot-low rail
  bayState = BAY_BOOT;
  uint8_t reg[4] = {0, 0, 0, 0};
  bool ok = false;
  for (int t = 0; t < 3 && !ok; t++) { ok = bayReadRegs(reg); delay(25); }
  if (!ok) { bayFaultCode |= 0x04; return false; }            // (2) I2C failed
  float regDrawW = reg[2] * 0.1f;                            // reg2: 0.1 W units
  if (reg[0] != divId)                        { bayFaultCode |= 0x01; return false; }
  if (bayRequestedId != 0 && reg[0] != bayRequestedId)
                                              { bayFaultCode |= 0x08; return false; }
  if (fabsf(regDrawW - MODULE_DRAW_W[reg[0]]) > 0.15f)
                                              { bayFaultCode |= 0x01; return false; }
  if (reg[3] & 0x01)                          { bayFaultCode |= 0x02; return false; }
  bayIdentifiedId = reg[0];
  if (bayRequestedId == 0) moduleId = bayIdentifiedId;  // adopt proven ID for the thermal law
  return true;
}
void bayCut() {   // mismatch or reg3 fault -> cut bay power within one poll cycle
  digitalWrite(PIN_BAY_EN, LOW);
  bayState = BAY_FAULT;
  modulePower = false;
  bayUsbEnumAllowed = false;
  bayTxPermitted = false;
  notifyBay();
}
// Continuous re-poll while ON: a mid-session reg3 fault bit or an ID change
// cuts the rail within one poll cycle. Also maintains the TX-permit gate.
void bayTick() {
  if (bayState == BAY_OFF) {
    if (bayPowerRequested) {
      uint8_t divId = bayDividerId(analogRead(PIN_BAY_ID_ADC));
      if (divId != 0 && divId != 255) {
        bayFaultCode = 0;
        if (bayIdentify()) bayState = BAY_ON;  // full power only after proven identify
        else bayCut();
        // no module docked -> request stays pending, rail stays off
      }
    }
    return;
  }
  if (bayState == BAY_ON) {
    uint8_t reg[4];
    if (!bayReadRegs(reg)) { bayFaultCode |= 0x04; bayCut(); return; }
    if (reg[0] != bayIdentifiedId)          { bayFaultCode |= 0x01; bayCut(); return; }
    if (reg[3] & 0x01)                      { bayFaultCode |= 0x02; bayCut(); return; }
    // (4) reg 0x20 TX-permit only when the drum encoder reads >=90% open.
    bool permit = drumDeg >= OPEN_THRESHOLD_DEG;
    if (permit != bayTxPermitted) {
      bayTxPermitted = permit;
      bayWriteReg(BAY_REG_TX_PERMIT, permit ? 1 : 0);
    }
    modulePower = true;
    bayUsbEnumAllowed = true;
  }
}
// [v2.1/F4-5] USB-host enumeration gate: the spine enumerates a bay USB device
// (keyboard HID / storage MSC / neural) ONLY after successful identification.
// NOTE: no USB-host stack is compiled in this build (ESP32-S3 USB-OTG host
// bring-up is rev-2 work); this is the gate hook that host enable must call.
bool usbHostMayEnumerate() { return bayState == BAY_ON && bayUsbEnumAllowed; }

// ---------- Actuators ----------
void setModulePower(bool on) {
  bayPowerRequested = on;
  if (!on) {   // cut is immediate; a later power-on re-runs identify
    digitalWrite(PIN_BAY_EN, LOW);
    bayState = BAY_OFF;
    modulePower = false;
    bayUsbEnumAllowed = false;
    bayTxPermitted = false;
    bayFaultCode = 0;
  }
  // power-ON goes through bayTick() identify; modulePower asserts only on BAY_ON
  notifyBay();
}
void notifyBay() {
  if (!chBay) return;
  uint8_t buf[4] = {moduleId, (uint8_t)(modulePower ? 1 : 0), 0, 0};
  uint16_t ma = modulePower ? (uint16_t)(MODULE_DRAW_W[moduleId] / 5.0f * 1000) : 0;
  buf[2] = ma & 0xFF; buf[3] = ma >> 8;
  chBay->setValue(buf, 4); notifySafe(chBay);
}
// [v2.1/F5] notifications are only ever sent on a bonded+encrypted link, so an
// unbonded client that manages to subscribe to a CCCD receives nothing.
bool notifyLinkSecure() { return hostConnected && hostBonded && hostEncrypted; }
void notifySafe(NimBLECharacteristic* ch) { if (ch && notifyLinkSecure()) ch->notify(); }

// ---------- Pairing window (F1) ----------
// NOTE on PIN_PAIR_BTN = GPIO0 (ESP32-S3 BOOT strapping pin): holding it
// *through a reset* enters ROM download mode — firmware never runs, so no
// window can open. The window is only evaluated here in loop(), i.e. while the
// firmware is already running; a hold during normal operation never resets the
// chip. Rev-2 hardware should move the pair button to a dedicated GPIO.
// Debounced (active-low): 3 consecutive agreeing reads at the 20 ms cadence.
bool pairButtonDown() {
  static uint8_t agree = 0; static bool last = false, stable = false;
  bool raw = (digitalRead(PIN_PAIR_BTN) == LOW);
  if (raw == last) { if (agree < 255) agree++; } else { last = raw; agree = 0; }
  if (agree >= 3) stable = raw;
  return stable;
}
void advertiseBondedOnly() {
  auto* adv = NimBLEDevice::getAdvertising();
  adv->stop();
  // This NimBLE-Arduino version exposes only whiteListAdd (append-only, no
  // clear): every entry ever added is a peer bonded through a pairing window,
  // so accumulation is harmless — the filter still excludes everyone else.
  for (auto &a : bondedPeers) NimBLEDevice::whiteListAdd(a);
  adv->setScanFilter(true, true);   // scan requests + connects: whitelist only
  adv->start();
}
void recordBondedPeer(const NimBLEAddress& a) {
  for (auto &p : bondedPeers) if (p == a) return;
  bondedPeers.push_back(a);
}
void pairWindowTick(uint32_t now) {
  static uint32_t btnHoldStart = 0, pairWindowUntil = 0;
  static bool windowOpen = false;
  if (pairButtonDown()) {
    if (btnHoldStart == 0) btnHoldStart = now;
    else if (!windowOpen && now - btnHoldStart >= PAIR_HOLD_MS) {
      windowOpen = true;
      pairWindowUntil = now + PAIR_WINDOW_MS;
      auto* adv = NimBLEDevice::getAdvertising();
      adv->stop();
      adv->setScanFilter(false, false);   // open advertising for 60 s
      adv->start();
    }
  } else {
    btnHoldStart = 0;
  }
  if (windowOpen && (int32_t)(now - pairWindowUntil) >= 0) {
    windowOpen = false;
    pairWindowUntil = 0;
    advertiseBondedOnly();                // back to bonded-only
  }
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
      // [v2.1/F2] refuse module IDs outside the known table (0..8).
      case 0x02: if (v.size() > 2) {
                   uint8_t id = v[1];
                   if (id > MODULE_ID_MAX) break;
                   bool powerOn = v[2] != 0;
                   if (powerOn && (bayState != BAY_ON || bayIdentifiedId != id)) {
                     // (re-)identify: rail off until the divider+I2C
                     // cross-check proves the newly requested ID. Without
                     // this, the thermal law would price a requested ID the
                     // docked module never proved.
                     digitalWrite(PIN_BAY_EN, LOW);
                     bayState = BAY_OFF; modulePower = false;
                     bayUsbEnumAllowed = false; bayTxPermitted = false;
                   }
                   bayRequestedId = id; moduleId = id;
                   setModulePower(powerOn);
                 } break;
      case 0x03: if (v.size() > 1) brightnessCapPct = min<uint8_t>(v[1], 100); break;
      // [v2.1/F13] absolute calibrate at the closed detent only.
      case 0x04: if (detentBitsDebounced() & 2) angleZeroOffset = drumDeg; break;
      case 0x05: break; // LED patterns: rev 2
    }
  }
};
struct ServerCb : NimBLEServerCallbacks {
  void onConnect(NimBLEServer* s, NimBLEConnInfo& info) override {
    if (hostConnected) { s->disconnect(info); return; }  // F7: single connection
    hostConnected = true;
    hostBonded = info.isBonded();
    hostEncrypted = info.isEncrypted();
    // [v2.1/F3] the watchdog refreshes ONLY from a bonded+encrypted
    // (re)connect or an authenticated 0x00 heartbeat — never from an
    // arbitrary connect.
    if (hostBonded && hostEncrypted) lastHeartbeatMs = millis();
    if (hostBonded) recordBondedPeer(info.getAddress());
  }
  void onAuthenticationComplete(NimBLEConnInfo& info) override {
    hostBonded = info.isBonded();
    hostEncrypted = info.isEncrypted();
    if (hostBonded && hostEncrypted) lastHeartbeatMs = millis();  // F3
    if (hostBonded) recordBondedPeer(info.getAddress());
  }
  void onDisconnect(NimBLEServer*, NimBLEConnInfo&, int) override {
    hostConnected = false; hostBonded = false; hostEncrypted = false;
    advertiseBondedOnly();   // any disconnect -> back to bonded-only
  }
};

void setup() {
  pinMode(PIN_DETENT_OPEN, INPUT); pinMode(PIN_DETENT_CLOSED, INPUT); pinMode(PIN_COVER, INPUT);
  pinMode(PIN_BAY_EN, OUTPUT); pinMode(PIN_PANEL_EN, OUTPUT); pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_PAIR_BTN, INPUT_PULLUP);   // BOOT button, active-low (see F1 note)
  digitalWrite(PIN_BAY_EN, LOW);         // [F4] bay rail off at boot until identify
  digitalWrite(PIN_PANEL_EN, HIGH);
  analogReadResolution(12);
  Wire.begin(I2C0_SDA, I2C0_SCL); Wire1.begin(I2C1_SDA, I2C1_SCL);

  NimBLEDevice::init("NEXUS-ONE");
  NimBLEDevice::setSecurityAuth(true, true, true);          // bonding + LE Secure Connections
  bleServer = NimBLEDevice::createServer();
  bleServer->setCallbacks(new ServerCb());
  bleServer->advertiseOnDisconnect(false);   // we restart advertising manually
  auto* svc = bleServer->createService(SVC_UUID);
  // v1.6 compile fix (2026-10-19, real toolchain): v1.3 used the Bluedroid
  // setAccessPermissions()/ESP_GATT_PERM_* API, which does not exist in
  // NimBLE-Arduino. NimBLE enforces encrypted access with the READ_ENC /
  // WRITE_ENC property flags at creation time — same protocol rule
  // (every characteristic requires an encrypted, bonded link).
  // [v2.1/F5] CCCD note: NimBLE-Arduino 2.x auto-creates the 0x2902 CCCD
  // inside the stack and explicitly disables manual 0x2902 creation
  // (NimBLEDescriptor.cpp: "Manually created 2902 descriptor has no
  // functionality; please remove" — it is hidden). This library version
  // exposes NO API to set encrypted-only ATT permissions on the CCCD, so the
  // descriptor itself cannot be hardened here. Compensating control enforced
  // below: notifySafe() only ever notifies on a bonded+encrypted link, so an
  // unbonded subscriber receives no telemetry. HARDWARE VALIDATION REQUIRED
  // before the "bonding required before any characteristic is readable" claim
  // ships: an unbonded test client must be observed to be rejected (or
  // starved) on subscribe. Status: NOT-VERIFIED on target.
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
  uint8_t info[4] = {0x01, 0x03, 0x02, 0x01};               // fw 2.1, hw rev 1, protocol 1
  chInfo->setValue(info, 4);
  svc->start();
  // [v2.1/F1] DELETE the old unconditional advertising start. Boot enters
  // bonded-only mode; the 60 s pairing window opens only on the 2 s hold.
  advertiseBondedOnly();
}

void loop() {
  static uint32_t tSlow = 0, tDet = 0, tBay = 0;
  uint32_t now = millis();
  drumDeg = readDrumDeg();
  pairWindowTick(now);                                     // F1 pairing window
  if (now - tBay > 100) { tBay = now; bayTick(); }          // F4 bay contract, 10 Hz
  // Angle notify: on >=1 degree change, max 10 Hz by sensor poll cadence
  if (fabs(drumDeg - lastNotifiedDeg) >= 1.0f && chAngle) {
    uint16_t v = (uint16_t)(drumDeg * 100);
    chAngle->setValue((uint8_t*)&v, 2);
    notifySafe(chAngle);
    lastNotifiedDeg = drumDeg;
  }
  if (now - tDet > 200) {                                  // detents on change cadence
    tDet = now;
    static uint8_t lastDet = 0xFF; uint8_t d = detentBitsDebounced();  // F13
    if (d != lastDet) { lastDet = d; chDetent->setValue(&d, 1); notifySafe(chDetent); }
  }
  if (now - tSlow > 5000) {                                // battery + thermal, 5 s
    tSlow = now;
    uint8_t pct, flags; uint16_t mv;
    readBattery(pct, mv, flags);
    uint8_t bb[4] = {pct, (uint8_t)(mv & 0xFF), (uint8_t)(mv >> 8), flags};
    chBatt->setValue(bb, 4); notifySafe(chBatt);
    enforceThermal();
    int16_t t = (int16_t)(temperatureRead() * 100);         // controller die temp as board proxy
    uint8_t tb[3] = {(uint8_t)(t & 0xFF), (uint8_t)(t >> 8), budgetState};
    chTherm->setValue(tb, 3); notifySafe(chTherm);
  }
  // Heartbeat watchdog: no host for 30 s -> bay powers down (protocol rule)
  if (modulePower && (!hostConnected || now - lastHeartbeatMs > HEARTBEAT_TIMEOUT_MS)) {
    setModulePower(false);
  }
  delay(20);
}
