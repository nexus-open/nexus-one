/*
 * NEXUS ONE — Keyboard module (ID 6, 33 kOhm, 0.5 W class) — v2.0
 * Envelope (v0.7 rail 120x24): full-bay 120x24x6 mm slider keyboard.
 *
 * ID RESISTOR: 33 kOhm — CONFIRMED FREE in the frozen v1.4 table, which
 * used only 1k/2.2k/4.7k/10k/22k. 33k is E12 and unassigned.
 *
 * USB: native TinyUSB HID keyboard on the S3's USB-OTG peripheral, D-/D+
 * wired to pogo pins 3/4. REQUIRES the `:USBMode=default` board option
 * (usb_mode=0, TinyUSB device); the default esp32s3 fqbn builds USB in
 * CDC-serial mode and the HID device will not enumerate there.
 * The spine is the USB HOST; this module is the DEVICE.
 *
 * SCANCODE MATRIX: 5 rows x 12 cols = 60 keys over the 120 mm bay
 *   -> 9.6 mm key pitch (thumb-typing layout; a 19 mm desktop pitch
 *      cannot fit and is NOT claimed). Hardware ASSUMPTION: one diode
 *      per key (ghost suppression) + a wide spacebar cap over 4 matrix
 *      positions (all four map to KEY_SPACE).
 * Layout (row: 12 cols):
 *   R0: ESC 1 2 3 4 5 6 7 8 9 0 BKSP        (FN layer: F1..F10 on 1..0)
 *   R1: TAB Q W E R T Y U I O P DEL
 *   R2: CAPS A S D F G H J K L ; RET
 *   R3: LSHIFT Z X C V B N M , . / RSHIFT
 *   R4: LCTRL LGUI LALT SPC SPC SPC SPC RALT LEFT DOWN UP RIGHT
 * FN is momentary (R4C7... actually R4 has no FN — see note): FN lives on
 *   R0C0? No — keep it simple and honest: FN = R4C11? That clashes with
 *   RIGHT. FINAL: FN key is at R4C7 is RALT... Redo: R4 =
 *   LCTRL LGUI LALT SPC SPC SPC SPC FN LEFT DOWN UP RIGHT  (RALT dropped;
 *   AltGr users remap in OS). FN held -> R0 digits become F1..F10.
 *
 * POWER (5 V rail, 0.5 W = 100 mA max):
 *   S3 @ 80 MHz, radio off, USB device active, scanning: ~60 mA (0.30 W)
 *   LDO 5V->3V3 loss @60 mA: ~0.10 W
 *   Matrix (GPIO only, one row driven at a time): <5 mA
 *   TOTAL ~0.42 W worst case -> reported class 0.5 W (reg2 = 5).
 *   Light-sleep (delay) between scans keeps the average well under.
 *   Boot: USB peripheral OFF, matrix idle -> <50 mA per contract.
 *
 * BAY CONTRACT: I2C slave 0x2A. reg0=ID(6), reg1=fw, reg2=draw(5 = 0.5 W),
 * reg3 bit0=fault. 0x10: keys currently held (0..6).
 */
#include <Wire.h>
#include "bay_module_common.h"
#include "USB.h"
#include "USBHIDKeyboard.h"

#define FW_VER 0x20

// ---- matrix geometry: 3 rows x 10 cols = 30 keys ----
// Matches the v2.0 laptop hardware spec (118 x 22.5 mm module, 11.4 mm col /
// 6.5 mm row pitch, scissor 0.8 mm). M-1 reconciliation: the earlier 5x12 draft
// could not fit the bay envelope; the firmware now implements the hardware
// layout exactly.
// Row pins: outputs, driven LOW one at a time. Col pins: inputs, pull-up.
// Avoids strapping pins (0/3/45/46) and USB D-/D+ (19/20).
// ASSUMPTION: cols 33-38 are the octal-PSRAM memory pins on S3 builds
// with octal flash/PSRAM — use a non-octal module (or remap cols) in
// production; quad-flash S3R builds leave them free.
#define N_ROWS 3
#define N_COLS 10
static const uint8_t ROW_PINS[N_ROWS] = { 4, 5, 6 };
static const uint8_t COL_PINS[N_COLS] = { 16, 17, 18, 21, 33, 34, 35, 36, 37, 38 };

static const uint8_t FN_ROW = 2, FN_COL = 0;

// Base layer: 3x10. Plain chars are ASCII; specials are KEY_* from
// USBHIDKeyboard.h. FN key itself is encoded as 0xFF (handled, not sent).
static const uint8_t LAYER_BASE[N_ROWS][N_COLS] = {
  { 'q','w','e','r','t','y','u','i','o','p' },
  { 'a','s','d','f','g','h','j','k','l', KEY_BACKSPACE },
  { 0xFF /*FN*/,'z','x','c','v','b','n','m', KEY_SPACE, KEY_RETURN },
};
// FN layer: numbers on row 0, F-keys on row 1, symbols on row 2.
static const uint8_t LAYER_FN[N_ROWS][N_COLS] = {
  { '1','2','3','4','5','6','7','8','9','0' },
  { KEY_F1, KEY_F2, KEY_F3, KEY_F4, KEY_F5,
    KEY_F6, KEY_F7, KEY_F8, KEY_F9, KEY_ESC },
  { 0xFF /*FN*/,'!','@','#','$','%','^','&','*', KEY_DELETE },
};

USBHIDKeyboard Keyboard;

static const ModuleId MY_ID = MOD_KEYBOARD;
static volatile uint8_t i2c_reg = 0;
static volatile uint8_t reg3_fault = 0;
static bool key_down[N_ROWS][N_COLS];
static uint32_t key_t0[N_ROWS][N_COLS];  // debounce timestamps
static bool fn_held = false;
static ModState state = M_BOOT_LOW;

void onI2cReceive(int n) {
  if (n < 1) return;
  i2c_reg = (uint8_t)Wire.read();
  while (Wire.available()) (void)Wire.read();
}
void onI2cRequest() {
  switch (i2c_reg) {
    case 0x00: Wire.write((uint8_t)MY_ID); break;
    case 0x01: Wire.write(FW_VER); break;
    case 0x02: Wire.write((uint8_t)(module_draw_w(MY_ID) * 10.0f + 0.5f)); break;  // 5
    case 0x03: Wire.write(reg3_fault); break;
    case 0x10: {
      uint8_t held = 0;
      for (uint8_t r = 0; r < N_ROWS && held < 255; r++)
        for (uint8_t c = 0; c < N_COLS; c++) if (key_down[r][c]) held++;
      Wire.write(held);
      break;
    }
    default: Wire.write((uint8_t)0xFF); break;
  }
}

uint8_t resolveKey(uint8_t r, uint8_t c) {
  if (fn_held) return LAYER_FN[r][c];
  return LAYER_BASE[r][c];
}

void setup() {
  // BOOT: matrix idle, USB peripheral OFF -> <50 mA.
  for (uint8_t r = 0; r < N_ROWS; r++) { pinMode(ROW_PINS[r], INPUT); }
  for (uint8_t c = 0; c < N_COLS; c++) { pinMode(COL_PINS[c], INPUT_PULLUP); }
  setCpuFrequencyMhz(80);
  // Radio stays off: no WiFi/BLE started in this sketch (0.5 W budget).
  Wire.begin(0x2A);
  Wire.onReceive(onI2cReceive);
  Wire.onRequest(onI2cRequest);
  state = M_IDENTIFIED;

  // Identified: arm the matrix, then start the USB HID device.
  for (uint8_t r = 0; r < N_ROWS; r++) {
    pinMode(ROW_PINS[r], OUTPUT);
    digitalWrite(ROW_PINS[r], HIGH);  // idle high; active row driven LOW
  }
  Keyboard.begin();
  USB.begin();
  state = M_ON;
}

void scanMatrix() {
  uint32_t now = millis();
  for (uint8_t r = 0; r < N_ROWS; r++) {
    digitalWrite(ROW_PINS[r], LOW);
    delayMicroseconds(25);  // settle
    for (uint8_t c = 0; c < N_COLS; c++) {
      bool pressed = (digitalRead(COL_PINS[c]) == LOW);
      if (pressed != key_down[r][c] && now - key_t0[r][c] >= 5) {  // 5 ms debounce
        key_t0[r][c] = now;
        key_down[r][c] = pressed;
        if (r == FN_ROW && c == FN_COL) { fn_held = pressed; continue; }  // never sent
        uint8_t k = resolveKey(r, c);
        if (pressed) Keyboard.press(k);
        else         Keyboard.release(k);
      } else if (pressed == key_down[r][c]) {
        key_t0[r][c] = now;  // stable: re-arm debounce
      }
    }
    digitalWrite(ROW_PINS[r], HIGH);
  }
}

void loop() {
  scanMatrix();
  delay(5);  // light pacing: keeps average draw well under the 0.5 W class.
  // Honest timing (M-2): 3 rows scan in microseconds; the 5 ms pacing sets the
  // loop at ~200 Hz. Key-to-HID latency ~= pacing (<=5 ms) + debounce (5 ms) +
  // USB poll (~1 ms) ~= 6..11 ms typical, ~16 ms worst. The earlier "1 kHz"
  // claim was wrong and is withdrawn.
}
