/*
 * NEXUS ONE — Cooling module (ID 5, 22 kOhm, 0.6 W class) — v2.0
 * Envelope (v0.7 rail 120x24): 60x24x12 mm.
 *
 * ACTIVE ELEMENT CHOICE — 20x20x8 mm 5 V micro-blower + copper spreader +
 * ducted fin stack, NOT a TEC. Numbers (see ../thermal_calc.py):
 *   Blower: 0.40 W (80 mA @ 5 V). ASSUMED 1.0 L/s @ ~200 Pa
 *           (2004-class micro-blower, Sunon/Delta class).
 *   Air heat-carry at 1.0 L/s: Q = rho*Vdot*cp*dT
 *     = 1.2e-3 kg/s * 1005 J/kgK * 10 K = 12.1 W  -> air is NOT the limit.
 *   Fin stack: 12 Cu fins 40x20 mm, both sides = 192 cm^2,
 *     h_forced ~= 45 W/m^2K (ASSUMED, ~1 m/s duct velocity)
 *     R_conv = 1/(45 * 0.0192) = 1.16 K/W.
 *   Cold-plate contact to bay rail (30x20 mm TIM pad): R_contact = 2.5 K/W
 *     (ASSUMED — the dominant term; demands a real TIM + clamp force).
 *   Module path R = 3.66 K/W in parallel with chassis 8.8 K/W
 *     -> Rth_folded 8.8 -> ~2.6 K/W; sustained folded cap 2.0 W -> ~7.0 W
 *     at 25 C ambient (thermal_calc.py prints the exact numbers).
 * TEC alternative REJECTED with numbers: 0.6 W into a micro-TEC gives
 *   COP ~= 0.5 at dT=10 K -> only ~0.3 W pumped, while 0.9 W must be
 *   rejected through the same tiny heatsink. The blower moves ~23x
 *   (thermal_calc.py exact figure) more heat per watt because it attacks
 *   the convection bottleneck instead of fighting thermodynamics.
 *
 * POWER BUDGET (5 V rail, 0.6 W = 120 mA max):
 *   micro-blower @ full PWM :  80 mA  (0.40 W)
 *   ESP32-S3 supervisor     :  25 mA  (0.13 W, 80 MHz, radio off)
 *   NTC + tach + margin     :  15 mA  (0.07 W)
 *   TOTAL worst case        : 120 mA  (0.60 W) — at the class limit.
 * Boot: blower OFF, S3 light peripherals only -> <50 mA per contract.
 *
 * BAY CONTRACT: I2C slave 0x2A. reg0=ID(5), reg1=fw, reg2=draw(6 = 0.6 W),
 * reg3 bit0=fault. 0x10: RPM u16, 0x12: plate temp s16 0.1 C, 0x14: PWM %.
 */
#include <Wire.h>
#include "bay_module_common.h"

#define FW_VER          0x20
#define BLOWER_PWM_PIN  5    // LEDC PWM to blower driver FET
#define BLOWER_TACH_PIN 6    // tach pulses, interrupt
#define NTC_PIN         7    // cold-plate NTC divider, ADC
#define PWM_CH          0
#define PWM_FREQ        25000
#define PWM_RES         8

static const ModuleId MY_ID = MOD_COOLING;
static volatile uint8_t i2c_reg = 0;
static volatile uint8_t reg3_fault = 0;
static volatile uint32_t tach_pulses = 0;
static uint8_t  pwm_duty = 0;
static uint16_t rpm = 0;
static int16_t  plate_tenthC = 250;
static uint32_t last_tach_check = 0, last_tach_count = 0;
static ModState state = M_BOOT_LOW;

void IRAM_ATTR onTach() { tach_pulses++; }

void onI2cReceive(int n) {
  if (n < 1) return;
  i2c_reg = (uint8_t)Wire.read();
  while (Wire.available()) (void)Wire.read();  // no writable regs in v2.0
}
void onI2cRequest() {
  switch (i2c_reg) {
    case 0x00: Wire.write((uint8_t)MY_ID); break;
    case 0x01: Wire.write(FW_VER); break;
    case 0x02: Wire.write((uint8_t)(module_draw_w(MY_ID) * 10.0f + 0.5f)); break;  // 6
    case 0x03: Wire.write(reg3_fault); break;
    case 0x10: Wire.write((uint8_t)(rpm >> 8)); Wire.write((uint8_t)rpm); break;
    case 0x12: Wire.write((uint8_t)(plate_tenthC >> 8)); Wire.write((uint8_t)plate_tenthC); break;
    case 0x14: Wire.write(pwm_duty); break;
    default:   Wire.write((uint8_t)0xFF); break;
  }
}

// NTC 10k B=3950, divider 10k to 3V3. Returns 0.1 C.
int16_t readPlateTemp() {
  int raw = analogRead(NTC_PIN);
  if (raw <= 0) raw = 1; if (raw >= 4095) raw = 4094;
  float r = 10000.0f * (4095.0f / raw - 1.0f);
  float tK = 1.0f / (1.0f/298.15f + logf(r/10000.0f)/3950.0f);
  return (int16_t)((tK - 273.15f) * 10.0f);
}

void setBlower(uint8_t pct) {
  if (pct > 100) pct = 100;
  pwm_duty = pct;
  ledcWrite(BLOWER_PWM_PIN, (uint32_t)pct * 255 / 100);
}

void setup() {
  // BOOT: blower hard OFF first -> module draws <50 mA for identify.
  pinMode(BLOWER_PWM_PIN, OUTPUT); digitalWrite(BLOWER_PWM_PIN, LOW);
  setCpuFrequencyMhz(80);
  // btStop()/WiFi off: default build has radio off until started; nothing to do.
  analogReadResolution(12);
  pinMode(BLOWER_TACH_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(BLOWER_TACH_PIN), onTach, FALLING);
  ledcAttach(BLOWER_PWM_PIN, PWM_FREQ, PWM_RES);  // core 3.x API
  setBlower(0);
  Wire.begin(0x2A);
  Wire.onReceive(onI2cReceive);
  Wire.onRequest(onI2cRequest);
  state = M_IDENTIFIED;  // spine has read regs 0..2 by now (its poll cycle)
  state = M_ON;
}

void loop() {
  plate_tenthC = readPlateTemp();

  // Closed-loop fan curve: 0% below 30 C plate, linear to 100% at 45 C.
  uint8_t target;
  if (plate_tenthC < 300)      target = 0;
  else if (plate_tenthC > 450) target = 100;
  else target = (uint8_t)((plate_tenthC - 300) * 100 / 150);
  setBlower(target);

  // Tach watchdog: 2 pulses/rev typical; expect >1000 RPM when driven.
  uint32_t now = millis();
  if (now - last_tach_check >= 3000) {
    uint32_t dp = tach_pulses - last_tach_count;
    last_tach_count = tach_pulses; last_tach_check = now;
    rpm = (uint16_t)(dp * 20 / 2);  // pulses per 3 s, 2 pulses/rev -> RPM
    if (pwm_duty > 20 && rpm < 1000) {
      reg3_fault |= 0x01;          // blower stall -> spine cuts bay power
      state = M_FAULT;
      setBlower(100);              // last-ditch: full drive before spine acts
    }
    if (plate_tenthC > 600) {      // 60 C plate: thermal runaway guard
      reg3_fault |= 0x02;
      state = M_FAULT;
      setBlower(100);
    }
  }
  delay(250);
}
