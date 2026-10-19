/*
 * NEXUS ONE — Neural module (ID 7, 47 kOhm, 2.0 W class) — v2.0
 * Envelope (v0.7 rail 120x24): 45x24x8 mm.
 *
 * ARCHITECTURE (decision record: NEURAL_DECISION.md):
 *   The NPU is an Edge-TPU-class MCM (15x10x1.5 mm LGA) with its OWN
 *   USB2 device port wired straight to pogo pins 3/4 (D-/D+). The spine
 *   enumerates it like a Coral-class USB accelerator — no custom driver,
 *   just the vendor TFLite runtime on Nexus OS. The ESP32-S3 in THIS
 *   sketch is the SUPERVISOR only: bay contract, power sequencing,
 *   thermal throttle. Its USB peripheral is NOT used.
 *   Class numbers (ASSUMPTION-labelled, from the Coral existence proof):
 *   4 TOPS int8, ~2 TOPS/W, 2.0 W draw class. USB2 HS (480 Mbps) bounds
 *   model-load bandwidth, not steady-state inference streaming.
 *
 * POWER BUDGET (5 V rail, 10 W bay max, open-mode law <=3 W):
 *   NPU MCM @ full inference .... 1.60 W  (ASSUMPTION, Coral-class)
 *   S3 supervisor (80 MHz) ...... 0.25 W
 *   PMIC losses + margin ........ 0.15 W
 *   TOTAL ...................... 2.00 W  -> reg2 = 20 (0.1 W units)
 *   Folded: allowed only with spine thermal permit; supervisor throttles
 *   the NPU rail at 75 C die (temp sensor on MCM lid) and faults at 85 C.
 *   Boot: NPU rail OFF -> <50 mA per contract.
 *
 * BAY CONTRACT: I2C slave 0x2A. reg0=ID(7), reg1=fw, reg2=draw(20),
 * reg3 bit0=fault. 0x10: NPU temp s8 (C), 0x11: ready flag, 0x12: throttle
 * state (0 full, 1 throttled, 2 rail cut).
 */
#include <Wire.h>
#include "bay_module_common.h"

#define FW_VER          0x20
#define NPU_PWR_PIN     4    // load-switch enable for NPU 5 V rail
#define NPU_READY_PIN   5    // NPU MCM READY GPIO
#define NPU_TEMP_PIN    7    // analog temp sensor on MCM lid
#define TEMP_THROTTLE_C 75
#define TEMP_CUT_C      85

static const ModuleId MY_ID = MOD_NEURAL;
static volatile uint8_t i2c_reg = 0;
static volatile uint8_t reg3_fault = 0;
static int8_t  npu_tempC = 25;
static uint8_t npu_ready = 0;
static uint8_t throttle = 0;   // 0 full, 1 throttled, 2 rail cut
static ModState state = M_BOOT_LOW;

void onI2cReceive(int n) {
  if (n < 1) return;
  i2c_reg = (uint8_t)Wire.read();
  while (Wire.available()) (void)Wire.read();  // no writable regs in v2.0
}
void onI2cRequest() {
  switch (i2c_reg) {
    case 0x00: Wire.write((uint8_t)MY_ID); break;
    case 0x01: Wire.write(FW_VER); break;
    case 0x02: Wire.write((uint8_t)(module_draw_w(MY_ID) * 10.0f + 0.5f)); break;  // 20
    case 0x03: Wire.write(reg3_fault); break;
    case 0x10: Wire.write((uint8_t)npu_tempC); break;
    case 0x11: Wire.write(npu_ready); break;
    case 0x12: Wire.write(throttle); break;
    default:   Wire.write((uint8_t)0xFF); break;
  }
}

// ASSUMED sensor: 10 mV/C analog, 500 mV @ 0 C (TMP36 class). Replace with
// the MCM vendor's recommended sensor in production.
int8_t readNpuTemp() {
  int raw = analogRead(NPU_TEMP_PIN);
  float mv = raw * 3300.0f / 4095.0f;
  return (int8_t)((mv - 500.0f) / 10.0f);
}

void setup() {
  // BOOT: NPU rail hard OFF -> <50 mA.
  pinMode(NPU_PWR_PIN, OUTPUT); digitalWrite(NPU_PWR_PIN, LOW);
  pinMode(NPU_READY_PIN, INPUT);
  setCpuFrequencyMhz(80);
  analogReadResolution(12);
  Wire.begin(0x2A);
  Wire.onReceive(onI2cReceive);
  Wire.onRequest(onI2cRequest);
  state = M_IDENTIFIED;

  // Power sequence: rail on, wait READY (USB enum is the spine's job).
  digitalWrite(NPU_PWR_PIN, HIGH);
  uint32_t t0 = millis();
  while (!digitalRead(NPU_READY_PIN) && millis() - t0 < 10000) delay(100);
  if (!digitalRead(NPU_READY_PIN)) { reg3_fault |= 0x01; state = M_FAULT; return; }
  npu_ready = 1;
  state = M_ON;
}

void loop() {
  npu_tempC = readNpuTemp();
  if (npu_tempC >= TEMP_CUT_C) {
    // 85 C: cut the rail; spine sees fault + USB device drop, re-enumerates
    // on recovery. This is the thermal-law enforcement point for this module.
    digitalWrite(NPU_PWR_PIN, LOW);
    npu_ready = 0; throttle = 2;
    reg3_fault |= 0x02; state = M_FAULT;
  } else if (npu_tempC >= TEMP_THROTTLE_C) {
    // 75 C: throttle — in production this asserts the MCM's THROTTLE pin /
    // clock-gates via the vendor driver hint; here we record + flag so the
    // spine can shed load. Rail stays on.
    throttle = 1;
    reg3_fault |= 0x04;
  } else if (npu_tempC < TEMP_THROTTLE_C - 10) {
    if (throttle == 1) { throttle = 0; reg3_fault &= ~0x04; }
    if (state == M_FAULT && throttle == 0 && (reg3_fault & 0x02)) {
      // Recovered below cut threshold with hysteresis: re-sequence the rail.
      reg3_fault &= ~0x02;
      digitalWrite(NPU_PWR_PIN, HIGH);
      delay(500);
      npu_ready = digitalRead(NPU_READY_PIN) ? 1 : 0;
      if (npu_ready) state = M_ON;
    }
  }
  delay(1000);
}
