# NEXUS ONE — Security Review v2.0

**Workstream:** NEW cross-cutting security review (REVIEW ONLY — no files edited)
**Date:** 2026-10-19 · **Reviewer role:** Security Review lead (combined playbooks:
security-architect, security-appsec-engineer, security-penetration-tester,
security-ai-generated-code-auditor)
**Scope roots inspected:**
`ARCHIVE_v1_7/03_freeze_v1_0/V1_0_FREEZE/protocol/BLE_PROTOCOL.md` ·
`CODE_v1_6/firmware/nexus_controller/nexus_controller.ino` ·
`CODE_v1_7/android-build/NexusLauncher/.../NexusBleClient.kt` (+ `MainActivity.kt`,
`AndroidManifest.xml`) ·
`DESIGN_v2_0/modules/{cooling,keyboard,neural,satellite}_module/*.ino` +
`bay_module_common.h` ·
`ARCHIVE_v1_7/05_code/CODE_v1_6/modules/*.ino` (baseline) ·
`DESIGN_v2_0/laptop/nexus_os_desktop.html` ·
`ARCHIVE_v1_7/02_design_versions/ELECTRONICS_v0_8/os/nexus_os.html`

**Verdict:** 4 findings rated **High** that are **fix-before-merge**, 1 **High**
architecture gap blocking the v2.0 modules, 5 **Medium**, 4 **Low**,
4 **Informational**. No Criticals (nothing found that gives an *unauthenticated*
attacker safety-critical actuation — the command path itself is encrypted-only,
but the pairing ceremony that creates the bonded trust is unenforced, which is
why the top findings cluster there). No hardcoded secrets anywhere in scope.

---

## 1. System overview & trust boundaries

```
                    ┌──────────── BLE (LESC, bonded) ────────────┐
  HOST PHONE        │                                            │  ESP32-S3 SPINE
  NexusLauncher     │   GATT: 0001 angle · 0002 detents ·         │  nexus_controller.ino
  NexusBleClient.kt │   0003 batt · 0004 bay · 0005 therm ·       │  "the safety owner"
                    │   0010 cmd (WRITE_ENC) · 0020 info          │
                    └────────────────────────────────────────────┘
                                         │ pogo: 5V·GND·USB2·I2C(0x2A)·ID-R
                                         ▼
                                   BAY MODULE (one at a time)
                        keyboard(HID) · storage(MSC) · camera · sensor
                        battery · cooling · neural(USB NPU) · satellite(UART modem)
```

**Trust boundaries:**
1. **Air gap (BLE)** — untrusted: anyone in ~10 m radio range. Must cross
   pairing-window + bonding + encryption before any state read or command.
2. **Pogo bus (I2C 0x2A / ID-resistor / USB2)** — semi-trusted: whatever module
   is physically docked. The spine must identify it *before* applying power.
3. **Host app** — semi-trusted: the controller "may refuse"; the phone
   *requests*, the spine *decides*.
4. **Module supply chain** — untrusted until identified: a malicious module is
   a BadUSB/HID or bus-level attacker.

**What the protocol promises (BLE_PROTOCOL.md):** LESC + bonding before *any*
characteristic is readable; command char additionally encrypted; device
advertises **only** during a 60 s pairing window opened by a 2 s button hold,
otherwise connectable **only by bonded hosts**; controller is safety owner;
bay powers down 30 s after heartbeat loss; calibrate only at closed detent.

---

## 2. STRIDE-lite threat model

| Threat | Where | Design control | Implemented? |
|---|---|---|---|
| **Spoofing** — rogue phone bonds as "the host" | BLE pairing | 2 s button-hold pairing window + bonded-only otherwise | **NO** — always advertises, no button logic (§F1) |
| **Spoofing** — rogue peripheral impersonates NEXUS-ONE to the phone | Android `connect()` | (none specified) | **NO** — name-match only, version never verified (§F6) |
| **Tampering** — unauthenticated GATT writes | Command char 0010 | WRITE_ENC + `isBonded()&&isEncrypted()` check | YES — defense in depth, correct |
| **Tampering** — command replay | BLE link | LESC session encryption | YES (no custom crypto — good) |
| **Tampering** — malicious module on pogo bus | Bay I2C/USB | Identify-before-power, reg2 cross-check, fault→cut | **NO** — spine has zero module-ID code (§F4) |
| **Repudiation** | — | n/a (no billing/audit surface) | — |
| **Info disclosure** — telemetry to unbonded observer | Notify chars | "bonding required before any characteristic is readable" | **PARTIAL** — CCCD subscribe path not hardened (§F5, verify on target) |
| **DoS** — connection-slot exhaustion | BLE | (none) | **NO** — always-on advertising (§F7) |
| **DoS** — watchdog bypass keeps bay powered | Heartbeat | 30 s link-loss cut | **BYPASSABLE** — any connect resets it (§F3) |
| **EoP** — moduleId OOB corrupts thermal law | Cmd 0x02 | (none — missing validation) | **NO** (§F2) |
| **EoP** — keyboard module as keystroke injector | USB HID | (none — procedural only) | **NO technical control** (§F8) |

---

## 3. Findings (worst-first)

### F1 — HIGH — fix before merge — Pairing window not implemented; anyone in range can bond
**File:line:** `CODE_v1_6/firmware/nexus_controller/nexus_controller.ino:34,175`
(`loop()` has no button handling at all)
**Exploit path:** `PIN_PAIR_BTN` is declared (line 34) but never referenced again.
`setup()` calls `NimBLEDevice::getAdvertising()->start()` unconditionally (line 175);
`loop()` contains no 2 s-hold detection, no 60 s window, no bonded-whitelist.
The spec's physical-presence gate ("advertises only while the tail button is held
2 s… otherwise connectable only by bonded hosts") exists only in prose.
**Attack chain (simplest first):** attacker in BLE range → connects (device is
always discoverable) → initiates pairing → `setSecurityAuth(true,true,true)` with
default NoInputNoOutput IO caps = **Just Works** (the `mitm=true` flag is
aspirational; without a display/keyboard there is no active-MITM protection) →
bonded → full command authority: `0x01` panel off (display DoS), `0x02` bay power
with arbitrary moduleId (→F2), `0x04` calibrate (needs closed detent), `0x00`
heartbeats to hold the bay on. LESC still defeats *passive* eavesdropping, but
the pairing ceremony has no effective authentication.
**Fix patch (coordinator applies):**
```cpp
// setup(): DELETE the unconditional start; replace with bonded-only mode.
static uint32_t pairWindowUntil = 0;
void advertiseBondedOnly() {
  auto* adv = NimBLEDevice::getAdvertising();
  // re-add bonded peers from the bond DB, then whitelist-filter:
  // for (auto& p : bondedPeers()) NimBLEDevice::whiteListAdd(p.addr);
  adv->setScanFilter(true, true);
  adv->start();
}
// loop(): 2 s debounced hold of PIN_PAIR_BTN -> open 60 s window, then back.
if (pairButtonHeldMs(2000) && millis() > pairWindowUntil) {
  pairWindowUntil = millis() + 60000;
  auto* adv = NimBLEDevice::getAdvertising();
  adv->setScanFilter(false, false); adv->start();
}
if (pairWindowUntil && millis() > pairWindowUntil) { pairWindowUntil = 0; advertiseBondedOnly(); }
```
Note: `PIN_PAIR_BTN = 0` is also the ESP32-S3 BOOT strapping pin — a 2 s hold at
reset enters download mode. Either move to a dedicated GPIO in rev 2 or document
the interaction. This one fix also closes F7.

### F2 — HIGH — fix before merge — Unchecked `moduleId` in SetModulePower: OOB read corrupts the thermal law
**File:line:** `nexus_controller.ino:128` (`case 0x02`), read at `:101` and `:113`
**Exploit path:** `case 0x02: if (v.size() > 2) { moduleId = v[1]; setModulePower(v[2] != 0); }`
— `v[1]` (0–255) is stored with **no range check**. `MODULE_DRAW_W` (line 28) has
6 entries (indices 0–5). `estimateDrawW()` (line 101) and `notifyBay()` (line 113)
then read `MODULE_DRAW_W[moduleId]` out of bounds. Consequences: (a) the safety
owner's budget math runs on garbage/NaN — with NaN, `draw <= budget` is false and
`draw > budget+0.5` is false, so the module is **never cut** while `budgetState`
sticks at 1; (b) the bay load switch is driven for module IDs the firmware cannot
account for — including v2.0 IDs 6/7/8 (keyboard/neural/satellite) on this v1.6
firmware, a live **v2.0 interop landmine**; (c) a bonded rogue host (via F1) or a
compromised legitimate app can deliberately defeat thermal enforcement.
**Fix patch:**
```cpp
case 0x02: if (v.size() > 2) {
  uint8_t id = v[1];
  if (id > 5) break;                 // v1.x spine knows IDs 0..5 only; refuse unknown
  moduleId = id; setModulePower(v[2] != 0);
} break;
```
(v2.0 spine must extend the table to 0..8 *and* cross-check against the module's
self-reported reg2 — see F4.)

### F3 — HIGH — fix before merge — Heartbeat watchdog reset by any unauthenticated connect
**File:line:** `nexus_controller.ino:137` (`ServerCb::onConnect`)
**Exploit path:** `onConnect` sets `lastHeartbeatMs = millis()` for **every**
connection, bonded or not. The link-loss rule (line ~204: bay off after 30 s
without heartbeat) is therefore defeated by an in-range attacker who simply
connects/disconnects every <30 s — no bonding, no heartbeat writes needed.
The "bay powers down 30 s after link loss" guarantee is void while the
legitimate host is gone; a power-hungry module (e.g. camera 2.5 W burst class)
stays energized. Thermal law still runs, but the fail-safe the protocol promises
does not.
**Fix patch:**
```cpp
void onConnect(NimBLEServer*, NimBLEConnInfo& info) override {
  hostConnected = true; hostBonded = info.isBonded();
  if (info.isBonded() && info.isEncrypted()) lastHeartbeatMs = millis();
  // else: leave the watchdog alone — only an authenticated heartbeat (0x00)
  // or a bonded+encrypted (re)connect may refresh it.
}
```

### F4 — HIGH — architecture, fix before v2.0 modules merge — Bay trust contract is specified but not implemented in the spine
**Files:** `DESIGN_v2_0/modules/*/bay_module_common.h` (header comment claims
*"Spine firmware v1.3/v1.6 reads the same divider/regs"*) vs
`CODE_v1_6/firmware/nexus_controller/nexus_controller.ino` (contains **zero**
lines of module identification: no ADC read of the ID resistor, no I2C master
poll of 0x2A, no reg2 draw-class cross-check, no reg3 fault-bit handling, no
reg 0x20 TX-permit write).
**Impact:** (a) the spine powers the bay purely on BLE command — any docked
module, including one that lies about (or never reports) its draw class, gets
full rail power; the thermal law prices whatever `moduleId` the *phone* claimed
(→F2), not what is physically present; (b) the satellite module's open-mode TX
gate (`spine_mode` bit, `satellite_module.ino:61-63`) is **dead code in practice**
— nothing ever writes reg 0x20, so `txBurst()` always returns false (fail-safe
today, but the design's safety story is fiction); (c) the keyboard/storage
"spine is the USB host / gates enumeration" comments have no spine counterpart —
no USB-host code exists; (d) the header comment is a **false claim** (honest-labels
violation): it asserts behavior the frozen firmware does not have. Every v2.0
module sketch was written against a spine that does not exist.
**Fix (spine work item, coordinator-owned):** implement in spine firmware, in
this order, before any v2.0 module is treated as supported: (1) ADC read of the
ID divider **before** enabling `PIN_BAY_EN`; (2) I2C-master poll of 0x2A regs
0–3; (3) cross-check reg0 ID vs divider ID vs BLE-requested moduleId and reg2
draw class vs `module_draw_w()` — mismatch or reg3 fault bit → cut bay power
within one poll cycle; (4) write reg 0x20 TX-permit only when drum ≥90% open;
(5) gate USB-host enumeration of keyboard/storage/neural on successful
identification. Until then, label all v2.0 bay modules "spine support pending".

### F5 — MEDIUM — Unauthenticated clients can likely subscribe to notifications (telemetry leak)
**File:line:** `nexus_controller.ino:161-167` (characteristic creation)
**Analysis:** every characteristic gets `READ_ENC` (good for ATT *reads*), and
the command char gets `WRITE_ENC` plus an explicit `isBonded()&&isEncrypted()`
check in `onWrite` (good). But the auto-created CCCD (0x2902) descriptor that
*enables notifications* is never given encrypted-only permissions. In the NimBLE
stack the CCCD is a separate attribute whose write permission defaults to open,
so an unbonded, unencrypted client that connects (trivial while F1 stands) can
plausibly write the CCCD and receive drum-angle/battery/thermal/bay telemetry in
plaintext — violating "bonding required before *any* characteristic is readable".
**Confidence: heuristic** — the code intent is clear, the property flags are
visible, but the exact ATT-layer behavior of the CCCD under `READ_ENC` was **not
verified on target** (no ESP32 toolchain in this environment; see §5).
**Fix:** explicitly create the 0x2902 descriptor with encrypted-only access for
each notify characteristic (or verify the stack already gates it), then
**validate on hardware**: an unbonded test client attempting to subscribe must
be rejected before bonding. Do not ship on the assumption in the line-153 comment.

### F6 — MEDIUM — fix before merge — Android client trusts any device named "NEXUS-ONE"; protocol version never verified
**File:line:** `NexusBleClient.kt:76-84` (`connect()`), `:106` (DeviceInfo read),
missing `onCharacteristicRead`
**Exploit path:** `connect()` scans with no filter and connects to the first
device whose advertised name is `"NEXUS-ONE"` — a name anyone can spoof.
`onServicesDiscovered` reads DeviceInfo ("protocol version must be 1" per the
comment) but **`onCharacteristicRead` is never overridden** — the read result is
silently dropped, so a version mismatch (or a rogue device serving garbage) is
accepted without action. The client also never checks bond state before
`writeCmd`. **Attack chain:** attacker advertises "NEXUS-ONE" → phone connects to
the impostor instead of the real device → heartbeats/commands go nowhere (DoS of
the real link; bay powers down after 30 s — fail-safe, but the user sees a dead
device) → impostor feeds spoofed telemetry (fake battery/thermal) into the OS UI
→ impostor can initiate Just Works pairing *with the phone*.
**Fix patch:** (1) scan with a `ScanFilter` on the service UUID
`4e455855-0000-…`, plus a scan timeout; (2) implement `onCharacteristicRead`,
parse DeviceInfo, `if (protoVer != 1) { g.disconnect(); return; }`; (3) gate
`writeCmd` on `device.bondState == BluetoothDevice.BOND_BONDED`.

### F7 — MEDIUM — Connection-slot exhaustion DoS while advertising is always-on
**File:line:** `nexus_controller.ino:175` (+ NimBLE default multi-connection)
**Exploit path:** with unrestricted advertising (F1), an in-range attacker opens
up to the stack's max concurrent connections and holds them — the legitimate
host cannot connect. No authentication is needed to occupy a slot.
**Fix:** closed by the F1 patch (pairing window + bonded whitelist + single-
connection configuration: `NimBLEDevice::setMTU`/`setMaxConnections(1)`-class
tuning per the Arduino core in use).

### F8 — MEDIUM — Keyboard module is an unauthenticated HID keystroke injector (BadUSB class)
**File:line:** `DESIGN_v2_0/modules/keyboard_module/keyboard_module.ino`
**Analysis:** by design the module enumerates as a USB HID keyboard to the host
(`Keyboard.begin()`, matrix scan → `Keyboard.press/release`). There is **no
technical control** binding "this HID device is the genuine keyboard module":
no identification gating on the spine (F4), no attestation, no user confirmation
on the phone for new HID devices. A compromised or counterfeit bay module =
arbitrary keystrokes into the host OS (credential theft, command injection).
The sketch itself is clean (bounded matrix, FN key never sent, radio off), so
this is an architecture/control gap, not a code bug.
**Fix:** procedural — first-party modules only, physical bay access = trust
(dock briefly); technical — F4's USB-enumeration gating (spine enumerates the
HID device only after I2C identification succeeds) plus a phone-side "new input
device" confirmation. Document the residual risk; it cannot be coded away
entirely for HID.

### F9 — MEDIUM — Android: no scan filter/timeout; permission flow unimplemented (crash)
**File:line:** `NexusBleClient.kt:71-84`, `MainActivity.kt:42-45`, class-level
`@SuppressLint("MissingPermission")`
**Analysis:** `startScan` with no `ScanFilter` and no timeout runs until a name
match — battery drain and first-match-wins (feeds F6). `MainActivity` calls
`ble.connect()` with the permission flow explicitly deferred to "the production
build" — on Android 12+, without `BLUETOOTH_SCAN`/`BLUETOOTH_CONNECT` granted,
the suppressed-lint calls throw `SecurityException` → crash on connect.
**Fix:** implement the runtime permission request before `connect()` (remove the
suppression once real); add service-UUID scan filter + 10 s scan timeout.
Classify as fix-before-merge for the app (availability), hardening for security.

### F10 — LOW — Neural module thermal-cut auto-recovery can oscillate forever
**File:line:** `DESIGN_v2_0/modules/neural_module/neural_module.ino:100-112`
**Exploit/robustness path:** on overtemp the rail is cut; once temp falls below
`TEMP_THROTTLE_C - 10` with no spine involvement, the sketch **re-enables the
rail by itself**. If the thermal condition persists (hot pocket, blocked vent),
this becomes cut → cool → re-enable → overheat → cut indefinitely, power-cycling
the NPU rail and chattering the fault bit.
**Fix patch:** add a latch — after 3 thermal cuts, stay cut and keep
`reg3_fault` set until the spine power-cycles the bay:
```cpp
static uint8_t thermal_cuts = 0;
// in the cut branch: if (++thermal_cuts >= 3) { /* latched: do not re-enable */ }
// reset thermal_cuts only in setup() (i.e. on spine power-cycle).
```

### F11 — LOW — Cooling module drives a *stalled* blower at 100% (wrong fault response)
**File:line:** `DESIGN_v2_0/modules/cooling_module/cooling_module.ino:124-130`
**Analysis:** on tach-stall (`pwm_duty > 20 && rpm < 1000`) the code sets the
fault bit (correct) but then `setBlower(100)` — full drive into a stalled
blower wastes the 0.6 W budget and stresses the driver FET; the "last-ditch"
comment only makes sense for the overtemp branch. The spine cuts bay power on
the fault bit anyway, so the 100% drive is both wrong and pointless for stall.
**Fix patch:** split the responses —
```cpp
if (pwm_duty > 20 && rpm < 1000) { reg3_fault |= 0x01; state = M_FAULT; setBlower(0); }
if (plate_tenthC > 600)          { reg3_fault |= 0x02; state = M_FAULT; setBlower(100); }
```

### F12 — LOW (latent) — Satellite `txBurst` AT-quote injection if a caller is ever added
**File:line:** `DESIGN_v2_0/modules/satellite_module/satellite_module.ino:93-107`
**Analysis:** `txBurst` is currently **dead code** (no caller; `loop()` only polls
`AT+CSQ`), so not exploitable today. But `Serial2.printf("AT+NTNSEND=\"%s\"\r\n", msg)`
places `msg` inside AT quotes with no sanitization — a `"` in a future message
source (received SMS, host-provided text) breaks out into arbitrary AT commands
to the modem (e.g. reconfiguration, unauthorized TX).
**Fix patch (apply when the caller lands):**
```cpp
// allowlist + length cap before formatting:
static bool sanitize(char *dst, size_t n, const char *src) {
  size_t i = 0;
  for (; src[i] && i + 1 < n; i++) {
    char c = src[i];
    if (!(isalnum((unsigned char)c) || strchr(" .,!?-'", c))) return false;
    dst[i] = c;
  }
  dst[i] = 0; return i > 0 && i <= 140;
}
```

### F13 — LOW — Calibrate offset accumulates unboundedly; detent inputs undebounced
**File:line:** `nexus_controller.ino:130` (`angleZeroOffset += drumDeg`), `:88-92`
**Analysis:** each accepted `0x04` adds the current reading to `angleZeroOffset`
with no clamp — repeated calibrates (or one accepted on a glitchy detent edge;
`detentBits()` reads raw GPIO with no debounce on a 200 ms poll) walk the zero
point. `readDrumDeg` wraps at 360°, so this is reversible UI/telemetry drift,
not a safety break. **Fix (hardening):** set `angleZeroOffset = drumDeg`
(absolute) instead of accumulating, and debounce the detent GPIOs (e.g. require
3 consecutive agreeing reads).

### Informational
- **I1 — No custom crypto, no hardcoded secrets (good).** Grep over all
  `.ino`/`.h`/`.kt`/`.py` in scope for `password=`, `secret=`, `api_key`,
  `ssid=`, bearer/private-key patterns: **zero hits**. Nothing client-reachable
  carries credentials. Keep it that way — especially when the satellite modem's
  real AT command set and any operator keys land.
- **I2 — Spec/doc inconsistencies (honest labels).** Heartbeat opcode `0x00` is
  documented under "Behaviour rules" but missing from the Commands table;
  `bay_module_common.h` (v2.0) falsely claims the v1.3/v1.6 spine "reads the
  same divider/regs" (see F4); the line-153 comment claims `READ_ENC`/`WRITE_ENC`
  is "the same protocol rule" as the spec's bonding requirement — true for
  reads/writes, unverified for the notify-subscribe path (F5).
- **I3 — BLE privacy (heuristic).** The firmware never configures the
  advertising address type; with always-on advertising (F1) the device is
  long-term trackable by its static name/address. After F1, prefer
  non-connectable directed/bonded-only advertising and a resolvable private
  address. Low priority.
- **I4 — `setSecurityAuth(true, true, true)` nuance.** The `mitm=true` request
  cannot produce real MITM protection with NoInputNoOutput IO capabilities —
  pairing will be Just Works. This is acceptable *only* with the physical-presence
  pairing window (F1) as the compensating control; do not describe the link as
  "MITM-protected" anywhere user-facing.

---

## 4. What was checked / what was NOT checked

**Checked (static, line-level):** every file in the scope list above —
controller firmware (209 lines, full), all four v2.0 module sketches + shared
header (full), v1.6 baseline modules (sensor/storage/camera/battery + frozen
header), Android BLE client + MainActivity call site + manifest, both Nexus OS
HTML prototypes (no network/storage/crypto/BLE in their JS — pure simulation
UI), both Python helpers (physics only), and a secrets grep across the tree.
Findings cite file:line and include exploit paths; heuristic items are labeled.

**NOT checked (could not verify in this environment):**
- **Runtime behavior on the ESP32-S3 target** — no ESP32 toolchain here, so the
  NimBLE-stack specifics behind F5 (CCCD permission behavior), whitelist/
  scan-filter semantics for the F1 patch, and `setSecurityAuth` IO-capability
  effects are code-reasoned, not executed. **F5 must be validated on hardware
  with an unbonded test client before the "bonding required" claim ships.**
- **Over-the-air testing** — no RF capture, no active pairing/MITM or
  GATT-fuzzing runs were performed.
- **Android runtime** — static review only; no on-device test of bonding flows,
  permission flows, or the impostor-device scenario (F6/F9).
- **ESP32-S3 platform hardening** — secure boot / flash encryption / eFuse
  posture is not covered by any in-scope file and was not assessed.
- **Backend/cloud** — the Render-hosted services (e.g. own-ManyChat) are outside
  this workstream's scope.
- **The v1.7 android-build copy of the controller firmware** named in the task
  brief does not exist under `CODE_v1_7/` (searched) — reviewed the
  `CODE_v1_6` original instead; flag if a divergent copy is supposed to exist.

---

## 5. Fix-before-merge vs hardening

**Fix before merge (ship-blockers):** F1 (pairing window + bonded-only
advertising), F2 (moduleId validation), F3 (watchdog refresh gating),
F4-spine (bay identification before v2.0 modules are supported), F6 (Android:
scan filter + DeviceInfo version check + bond check), F9-app (permission flow;
crash otherwise). F5's *validation* is a ship-blocker for the bonding claim
even though the code change may be small.

**Hardening (do soon, not blockers):** F7 (single-connection; folded into F1),
F8 (USB-enumeration gating + procedural module trust), F10 (thermal-cut latch),
F11 (stall vs overtemp fan response), F12 (AT sanitization when the caller
lands), F13 (absolute calibrate + detent debounce), I3 (RPA privacy).

**Residual risks to document, not fix in code:** HID BadUSB class (F8) is
inherent to a keyboard module; Just Works pairing has no active-MITM protection
(I4) — the button-hold window is the control; physical bay access = full trust
in the docked module until F4's identification lands.
