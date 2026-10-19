/*
 * Camera Pro module (ID 2) — periscope 200MP-class (v0.5/v0.7: 60x30x22 mm).
 * The sensor (ISOCELL HP-class) is driven by the HOST over the module's own
 * high-speed link in the production design; this module-side controller owns
 * POWER SEQUENCING and the THERMAL BURST LAW only:
 *   capture bursts <= 10 s at 2.5 W, then forced cool-down to <= 0.4 W until
 *   the module thermistor reports the sink within budget (v0.8 policy:
 *   camera mode is burst-duty, never sustained).
 * Sensor register tables are sensor-datasheet work and are deliberately NOT
 * invented here — power/thermal logic is the module firmware's real job.
 * Not compiled (no ESP toolchain here).
 */
#include "../bay_module_common.h"
static const int PIN_SENSOR_PWR = 5, PIN_LENS_PWR = 6, PIN_THERM = 4;  // ADC thermistor
static const uint32_t BURST_MAX_MS = 10000;
uint32_t burstStart = 0; bool burstActive = false, lockout = false;

float sinkTempC() {  // 10k NTC divider, beta 3950 — standard conversion
  int raw = analogRead(PIN_THERM);
  float r = 10000.0f * raw / (4095.0f - raw);
  return 1.0f / (1.0f / 298.15f + logf(r / 10000.0f) / 3950.0f) - 273.15f;
}
void setRails(bool on) {
  digitalWrite(PIN_SENSOR_PWR, on); digitalWrite(PIN_LENS_PWR, on);
}
void setup() {
  pinMode(PIN_SENSOR_PWR, OUTPUT); pinMode(PIN_LENS_PWR, OUTPUT);
  setRails(false);  // boot low; spine enables after bay identification
}
void loop() {
  // Host requests capture by I2C reg write (slave 0x2A) — handled in the
  // production ISR; the law enforced here regardless of host behaviour:
  if (burstActive && millis() - burstStart > BURST_MAX_MS) {
    setRails(false); burstActive = false; lockout = true;   // forced cool-down
  }
  if (lockout && sinkTempC() < 45.0f) lockout = false;       // sink recovered
  delay(10);
}
