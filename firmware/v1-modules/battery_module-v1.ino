/*
 * Battery module (ID 1) — +10 Wh (v0.7: 70x30x8 mm, 55 g).
 * The only module that SUPPLIES power. Its controller (small MCU + its own
 * MAX17048-class gauge at 0x36 on the module's private bus) offers the spine
 * three states over bay I2C: IDLE / SUPPLEMENT (feed the 5 V rail through
 * the pogo within the 10 W bay limit) / CHARGE (accept charge from spine).
 * Hard rules enforced module-side, spine cannot override:
 *   - cell 3.0–4.2 V window, NTC 0–45 C charge window (standard LiPo limits)
 *   - supplement current capped so pogo pins stay in their 2 A class
 *   - any fault -> open its own series FET first, report second
 * Not compiled (no ESP toolchain here).
 */
#include "../bay_module_common.h"
enum Offer : uint8_t { IDLE = 0, SUPPLEMENT = 1, CHARGE = 2 };
Offer offer = IDLE;
float cellV = 0, cellTempC = 25; uint8_t cellPct = 0;

bool cellSafe(bool charging) {
  if (cellV < 3.0f || cellV > 4.25f) return false;
  if (charging && (cellTempC < 0.0f || cellTempC > 45.0f)) return false;
  return true;
}
void loop() {
  // read gauge + NTC (production driver), then:
  if (!cellSafe(offer == CHARGE)) {
    // open series FET (GPIO in production spin), set FAULT reg, offer=IDLE
    offer = IDLE;
  }
  // Spine polls reg 0x20 for {offer, pct, mV} and folds it into Nexus OS
  // battery state; the 1.5 W folded derate (v0.7) applies while attached.
  delay(500);
}
void setup() {}
