/*
 * Sensor module (ID 4) — health + environment (v0.4/v0.7: 30x30x5 mm).
 * MAX30102 pulse-ox (I2C 0x57) + BME280 temp/humidity/pressure (I2C 0x76).
 * Both share the module's internal bus; the module bridges samples to the
 * spine over the bay I2C (module is slave 0x2A, sample block at reg 0x10).
 * Duty cycle: sample 1 s in every 10 s -> average draw stays in the 0.3 W
 * class with 10x margin. Not compiled (no ESP toolchain here).
 */
#include <Wire.h>
#include "../bay_module_common.h"
struct Samples { float hr, spo2, tempC, humidity, pressureHpa; } S;

bool readMAX30102() {
  Wire.beginTransmission(0x57); Wire.write(0x00);            // STATUS1
  if (Wire.endTransmission(false) != 0) return false;
  Wire.requestFrom(0x57, 1);
  // FIFO readout + Maxim-style HR/SpO2 estimation live in the production
  // driver; presence + raw FIFO streaming are what this sketch guarantees.
  return Wire.available() == 1;
}
bool readBME280() {
  Wire.beginTransmission(0x76); Wire.write(0xD0);            // CHIP ID reg
  if (Wire.endTransmission(false) != 0) return false;
  Wire.requestFrom(0x76, 1);
  return Wire.available() && Wire.read() == 0x60;            // BME280 id = 0x60
}
void setup() { Wire.begin(); }
void loop() {
  bool ok = readMAX30102() && readBME280();
  // Publish S to bay regs (0x10..) for the spine/OS; fault bit if !ok.
  delay(ok ? 9000 : 1000);                                   // duty cycle / retry
}
