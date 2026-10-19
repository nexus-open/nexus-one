# NEXUS ONE v2.1 — Security Fixes (firmware branch)

**Branch:** `DESIGN_v2_1/firmware/nexus_controller/nexus_controller.ino`
**Base:** `CODE_v1_6/firmware/nexus_controller/nexus_controller.ino` (copied, never modified;
the v1.6 NimBLE-encrypted-characteristic patch is preserved — see the "v1.6 compile fix"
comment in `setup()`).
**Review:** `DESIGN_v2_0/security/SECURITY_REVIEW_v2_0.md` — findings F1–F5, F13.
**Out of scope for this branch (unchanged):** F6/F9 (Android client), F8 (HID attestation),
F10/F11/F12 (module-side), I3 (RPA privacy).

Verification status legend: **COMPILED** = real toolchain build clean ·
**UNIT-TESTED** = executed in the Python logic model (`verification/logic_tests/`) ·
**NOT-VERIFIED** = never run on ESP32-S3 target hardware.

---

## F1 — HIGH — Pairing window (also closes F7)

**Fix:** 2 s debounced hold of `PIN_PAIR_BTN` opens a 60 s open-advertising window;
otherwise the device advertises bonded-only (whitelist scan filter over the bond DB).
The old unconditional `NimBLEDevice::getAdvertising()->start()` in `setup()` is deleted.
**F7** (single connection) is enforced in `ServerCb::onConnect`: a second concurrent
connection is immediately disconnected (this NimBLE-Arduino version exposes no
`setMaxConnections` API).

**BOOT-pin interaction (documented in code):** `PIN_PAIR_BTN = 0` is the ESP32-S3
strapping pin — holding it *through a reset* enters ROM download mode (firmware never
runs, so no window opens). The window is evaluated only in `loop()`, i.e. while the
firmware is already running; a hold during normal operation cannot reset the chip.
Rev-2 hardware should move the pair button to a dedicated GPIO.

**File:line evidence** (`firmware/nexus_controller/nexus_controller.ino`):
- `pairButtonDown()` :283 — debounced active-low read (~60 ms, 3 agreeing reads)
- `pairWindowTick()` :304 — 2 s hold → 60 s window → back to bonded-only
- `advertiseBondedOnly()` :290 — whitelist + `setScanFilter(true, true)`; boot calls this, not open advertising
- `ServerCb::onConnect` :360 — second-connection disconnect; `onDisconnect` → `advertiseBondedOnly()`
- `recordBondedPeer()` :300 / `onAuthenticationComplete` :360 — bond DB for the whitelist

**Verification:** COMPILED · UNIT-TESTED (f1–f5: boot is bonded-only, 1999 ms no-open,
2000 ms opens, closes at 60 s). **NOT-VERIFIED on target:** whitelist/scan-filter
semantics of this NimBLE-Arduino version; whitelist is append-only here (no
`clearWhiteList` API — accumulation is harmless since every entry is a window-bonded peer).

## F2 — HIGH — moduleId range validation

**Fix:** `case 0x02` refuses IDs `> MODULE_ID_MAX (8)`; `MODULE_DRAW_W` extended to
9 entries (0..8) with the v2.0 draws: keyboard 0.5, neural 2.0, satellite 3.0 W.
A changed ID requested while the bay is ON drops the rail to OFF first so
`bayTick()` re-runs the F4 identify before the thermal law prices the new ID.

**File:line evidence:** `MODULE_DRAW_W[9]` + `MODULE_ID_MAX` (constants block, :44);
`case 0x02` in `CmdCallbacks::onWrite` :328.

**Verification:** COMPILED · UNIT-TESTED (d1–d3: 9 and 255 refused, state untouched;
8 accepted; b8/b9: same-ID re-request keeps the rail up, changed-ID re-identifies).

## F3 — HIGH — Heartbeat watchdog refresh gating

**Fix:** `onConnect` sets `lastHeartbeatMs` **only** when `info.isBonded() &&
info.isEncrypted()`; the same gate in `onAuthenticationComplete` covers a pairing
that completes inside the window. An unauthenticated connect/disconnect no longer
touches the watchdog — only an authenticated `0x00` heartbeat or a
bonded+encrypted (re)connect refreshes it.

**File:line evidence:** `ServerCb::onConnect` :360, `ServerCb::onAuthenticationComplete` :360.

**Verification:** COMPILED · UNIT-TESTED (c1–c5: unauth connect does not refresh and
the watchdog still fires; bonded+encrypted connect and auth-complete refresh;
disconnect alone does not; `0x00` heartbeat refreshes).

## F4 — HIGH — Bay identify-before-power contract (spine side)

**Fix (in order):**
1. `bayDividerId(analogRead(PIN_BAY_ID_ADC))` **before** `PIN_BAY_EN` is enabled —
   `setup()` holds the rail LOW at boot.
2. `bayIdentify()` enables the boot-low rail, then I2C-master polls 0x2A regs 0–3
   (3 tries). The module self-limits to <50 mA at boot per the module-side contract.
3. Cross-check: reg0 == divider ID, reg0 == BLE-requested ID (if nonzero),
   reg2 (0.1 W units) == `MODULE_DRAW_W[reg0]` ±0.15 W, reg3 fault bit clear.
   Any mismatch/fault → `bayCut()` within one 100 ms poll cycle; `bayTick()`
   re-polls while ON so a mid-session fault or ID change also cuts.
4. Reg `0x20` TX-permit written **only** when `drumDeg >= OPEN_THRESHOLD_DEG`
   (≥90% open), revoked on close.
5. `usbHostMayEnumerate()` gates USB-host enumeration on `BAY_ON` — hook only;
   no USB-host stack is compiled in this build (rev-2 work).

**Hardware notes (in code):** `PIN_BAY_ID_ADC = 9` (ADC1_CH8) is a **rev-2 board
addition** — the v0.8 tray does not route pogo pin 7 to an ADC. Bay I2C shares
Wire1 with the MAX17048 (0x36 vs 0x2A, no collision); rev-2 routes pogo 5/6 there.
ADC thresholds sit at midpoints between nominals (1k:372 … 68k:3570, open:4095).

**File:line evidence:** `bayDividerId()` :160, `bayReadRegs()` :172, `bayWriteReg()` :179,
`bayIdentify()` :186, `bayCut()` :206, `bayTick()` :216, `usbHostMayEnumerate()` :248, `setModulePower()` :251.

**Verification:** COMPILED · UNIT-TESTED (a1–a4 ADC mapping incl. 33k/47k/68k;
b1–b9 mismatch/fault/I2C-fail cuts, honest-module pass, mid-session cut, no-module
stays off, requested-vs-docked mismatch, re-identify on ID change; e1–e4 TX-permit
gate). **NOT-VERIFIED on target:** the entire bay sequence (no rev-2 board, no ADC
characterization). **Known marginality (measured):** the 47k/68k nominals sit only
~2.7% from their thresholds — the tightest window of the table. A ±2% combined
error budget (1% resistors + calibrated ADC) holds (tested); ±5% ADC error would
misidentify 6↔7↔8. Requires hardware ADC characterization before the F4 claim ships.

## F5 — MEDIUM — CCCD / notify hardening

**What was possible in this toolchain:** NimBLE-Arduino 2.x auto-creates the 0x2902
CCCD inside the stack and *explicitly disables* manual 0x2902 creation
(`NimBLEDescriptor.cpp`: "Manually created 2902 descriptor has no functionality;
please remove" — it is hidden). There is **no public API** to set encrypted-only
ATT permissions on the CCCD, so the descriptor itself could not be hardened here.

**Compensating control implemented:** every notify site now goes through
`notifySafe()`, which only notifies when the link is connected **and bonded and
encrypted** (`notifyLinkSecure()`). An unbonded client that manages to subscribe
to a CCCD receives no telemetry. `hostEncrypted` is tracked in `onConnect` /
`onAuthenticationComplete` / `onDisconnect`.

**File:line evidence:** `notifyLinkSecure()` :273, `notifySafe()` :274, all `notifySafe(chX)`
call sites in `loop()` :434 and `notifyBay()` :264; the long F5 comment in `setup()` :384.

**Verification:** COMPILED. **NOT-VERIFIED on target — ship-blocker for the bonding
claim:** an unbonded test client MUST be observed to be rejected (or starved) on
CCCD subscribe before "bonding required before any characteristic is readable" ships.

## F13 — LOW — Absolute calibrate + detent debounce

**Fix:** `case 0x04` sets `angleZeroOffset = drumDeg` (absolute) instead of
accumulating; `detentBitsDebounced()` requires 3 consecutive agreeing raw reads
(~60 ms at the 20 ms loop cadence) and is used for both the calibrate gate and the
detent notify path.

**File:line evidence:** `detentBitsDebounced()` :127; `case 0x04` :328; detent-notify block in `loop()` :434.

**Verification:** COMPILED · UNIT-TESTED (g1: repeated calibrate does not accumulate;
g2: 2/3 agreeing glitch keeps the old stable value; A12 baseline: refused unless closed).

---

## Build & test record

- **Compile:** `arduino-cli compile --fqbn esp32:esp32:esp32s3`
  → `Sketch uses 582561 bytes (44%) of program storage space` ·
  `Global variables use 34396 bytes (10%) of dynamic memory` · **zero warnings/errors**
  (stdout: `verification/compile_v2_1.txt`; esp32 core 3.3.12, NimBLE-Arduino 2.5.1,
  core+built-in libraries only — nothing installed from downloads.arduino.cc).
- **Baseline:** `test_firmware_logic.py` (v1.3 file, copied unmodified): **12/12**.
- **v2.1 suite** (`test_v2_1_security.py` vs `controller_model_v2_1.py`, 1:1 mirror of the .ino):
  **45/45** — A01–A12 baseline-equivalent (12) · (a) ADC mapping (5) · (b) bay contract (9) ·
  (c) watchdog gating (5) · (d) moduleId validation (3) · (e) TX-permit (4) ·
  (f) pairing window (5) · (g) F13 (2). Full stdout: `verification/logic_tests_v2_1.txt`.
- **Test-caught bugs during this workstream (fixed, all green now):**
  1. `bayIdentify()` left `bayState = BAY_BOOT` on success with nothing advancing it
     to `BAY_ON` — the rail would never have reached full power. Fixed in `bayTick()`.
  2. A changed moduleId requested while ON never re-identified — the thermal law would
     have priced an unproven ID. Fixed: rail drops to OFF, `bayTick()` re-identifies.
  3. Test-harness counter inflated by `cond` being a non-bool truthy int
     (`... and c.bay_fault & 0x01`); fixed with `!= 0` comparisons. All assertions were
     genuinely passing; only the summary count was wrong.

## What remains NOT-VERIFIED (hardware)

1. **F5/CCCD:** unbonded-client subscribe behavior on the real NimBLE stack — the
   bonding claim must not ship until a hardware test rejects (or starves) it.
2. **F1:** whitelist/scan-filter semantics on target; 2 s-hold ergonomics on the real BOOT button.
3. **F4:** entire bay sequence — needs the rev-2 board (GPIO9 ID-ADC routing, pogo 5/6
   to Wire1); ADC characterization of the 47k/68k window (±2% budget); module-side
   <50 mA boot self-limit; reg 0x20 write observed on a real satellite module.
4. **Whole firmware:** never executed on an ESP32-S3 — boot, BLE, sensors, and thermal
   paths are compile-checked and logic-tested only.
5. **Out-of-branch findings** still open: F6/F9 (Android), F8 (HID attestation),
   F10/F11/F12 (module sketches), I3 (RPA privacy).
