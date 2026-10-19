/*
 * NEXUS ONE — Satellite module (ID 8, 68 kOhm, 3.0 W peak class) — v2.0
 * Envelope (v0.7 rail 120x24): 60x24x10 mm. Antenna lives in the POLYMER
 * END-CAP window (see below), fed by micro-coax from this module.
 *
 * NTN CHIPSET CLASS: MT6825-class standalone IoT-NTN modem —
 *   3GPP Release-17 IoT-NTN, L-band (n255: 1626.5-1660.5 MHz UL) and
 *   S-band (n256), integrated Cortex-M4F + transceiver + PMU.
 *   Existence proof: MediaTek MT6825 ships in Motorola Defy 2, CAT S75,
 *   Motorola Defy Satellite Link (Bullitt Satellite Connect) — two-way
 *   satellite messaging on GEO constellations. Sources in
 *   ../modules_report.md. The S3 here is the SUPERVISOR (bay contract,
 *   power sequencing, TX gating); the modem is a separate SiP on UART.
 *
 * ANTENNA: L-band ceramic patch ~25x25x4 mm (or stamped helix), RHCP,
 *   mounted in the end-cap RF window, ground-plane keep-out per the
 *   modem vendor layout guide. THE CAP MUST STAY POLYMER: at 1.6 GHz a
 *   metal cap is a Faraday shield (skin depth ~2 um — total block) and
 *   near-field metal detunes the patch. This is the physical reason the
 *   frozen v1.0 design already specifies PC/ABS cap windows.
 *
 * POWER BUDGET (5 V rail, 10 W bay max, open-mode thermal law <=3 W):
 *   TX burst, 23 dBm (200 mW RF): PA @38% PAE ......... 0.53 W
 *   Modem transceiver + baseband (RX/TX active) ........ 0.90 W
 *   ESP32-S3 supervisor (80 MHz, radio off) ........... 0.25 W
 *   PMIC/LDO losses + antenna mismatch margin ........ 0.32 W
 *   PEAK TX .......................................... ~2.00 W
 *   Reported class 3.0 W = worst-case ceiling (cold temp, VSWR 2:1).
 *   Firmware duty-cycles TX to <=10% -> average <= ~0.5 W.
 *   TX is GATED: only when the spine reports OPEN mode (reg 0x20 = 1).
 *   Folded: modem held in PSM sleep (uA class), RX-only paging.
 *   Boot: modem rail OFF -> <50 mA per contract.
 *
 * BAY CONTRACT: I2C slave 0x2A. reg0=ID(8), reg1=fw, reg2=draw(30 = 3.0 W
 * peak class), reg3 bit0=fault. Spine WRITES reg 0x20: bit0 = open-mode
 * TX permit. 0x10: modem state u8, 0x11: RSSI s8 (dBm), 0x12: TX duty %.
 * Modem control: UART2 115200, Hayes-style AT set (ASSUMPTION — exact
 * command set follows the chosen modem vendor's integration manual).
 */
#include <Wire.h>
#include "bay_module_common.h"

#define FW_VER          0x20
#define MODEM_PWR_PIN   4    // load-switch enable for modem 5 V rail
#define MODEM_READY_PIN 5    // modem READY GPIO
#define MODEM_TXD_PIN   16   // S3 RX2 <- modem TX
#define MODEM_RXD_PIN   17   // S3 TX2 -> modem RX
#define VSWR_ADC_PIN    7    // reflected-power detector, ADC

static const ModuleId MY_ID = MOD_SATELLITE;
static volatile uint8_t i2c_reg = 0;
static volatile uint8_t reg3_fault = 0;
static volatile uint8_t spine_mode = 0;   // written by spine @0x20
static uint8_t  modem_state = 0;          // 0 off,1 booting,2 idle,3 rx,4 tx
static int8_t   rssi_dbm = -127;
static uint8_t  tx_duty_pct = 0;
static uint32_t tx_ms_window = 0, tx_ms_total = 0;
static ModState state = M_BOOT_LOW;

void onI2cReceive(int n) {
  if (n < 1) return;
  uint8_t r = Wire.read(); i2c_reg = r;
  if (r == 0x20 && Wire.available()) spine_mode = Wire.read();  // TX permit
  while (Wire.available()) (void)Wire.read();
}
void onI2cRequest() {
  switch (i2c_reg) {
    case 0x00: Wire.write((uint8_t)MY_ID); break;
    case 0x01: Wire.write(FW_VER); break;
    case 0x02: Wire.write((uint8_t)(module_draw_w(MY_ID) * 10.0f + 0.5f)); break;  // 30
    case 0x03: Wire.write(reg3_fault); break;
    case 0x10: Wire.write(modem_state); break;
    case 0x11: Wire.write((uint8_t)rssi_dbm); break;
    case 0x12: Wire.write(tx_duty_pct); break;
    default:   Wire.write((uint8_t)0xFF); break;
  }
}

// Minimal AT exchange; production driver implements the full 3GPP R17
// attach/paging/message flow per the modem vendor manual.
bool modemCmd(const char *cmd, const char *expect, uint32_t timeout_ms) {
  Serial2.printf("%s\r\n", cmd);
  uint32_t t0 = millis();
  String line;
  while (millis() - t0 < timeout_ms) {
    while (Serial2.available()) {
      char c = (char)Serial2.read();
      if (c == '\n') {
        if (line.indexOf(expect) >= 0) return true;
        line = "";
      } else if (c != '\r') line += c;
    }
    yield();
  }
  return false;
}

void setup() {
  // BOOT: modem rail hard OFF -> <50 mA.
  pinMode(MODEM_PWR_PIN, OUTPUT); digitalWrite(MODEM_PWR_PIN, LOW);
  pinMode(MODEM_READY_PIN, INPUT);
  setCpuFrequencyMhz(80);
  analogReadResolution(12);
  Wire.begin(0x2A);
  Wire.onReceive(onI2cReceive);
  Wire.onRequest(onI2cRequest);
  state = M_IDENTIFIED;

  // Power sequence: rail on, wait READY, init UART, attach.
  digitalWrite(MODEM_PWR_PIN, HIGH);
  modem_state = 1;
  uint32_t t0 = millis();
  while (!digitalRead(MODEM_READY_PIN) && millis() - t0 < 15000) delay(100);
  if (!digitalRead(MODEM_READY_PIN)) { reg3_fault |= 0x01; state = M_FAULT; return; }
  Serial2.begin(115200, SERIAL_8N1, MODEM_TXD_PIN, MODEM_RXD_PIN);
  // ASSUMED command set; replace with vendor manual strings in production.
  if (!modemCmd("AT", "OK", 2000))                    { reg3_fault |= 0x02; state = M_FAULT; return; }
  modemCmd("AT+CFUN=1", "OK", 5000);                       // full functionality
  modemCmd("AT+CEREG=1", "OK", 2000);                      // NTN reg unsolicited
  modem_state = 2;
  state = M_ON;
}

// One supervised TX burst. Returns false if not permitted right now.
bool txBurst(const char *msg) {
  if (!(spine_mode & 0x01)) return false;   // folded: TX forbidden by law
  if (state != M_ON) return false;
  uint32_t now = millis();
  if (now - tx_ms_window >= 60000) { tx_ms_window = now; tx_ms_total = 0; }
  tx_duty_pct = (uint8_t)(tx_ms_total * 100 / 60000);
  if (tx_duty_pct >= 10) return false;      // <=10% TX duty -> avg <= ~0.5 W
  modem_state = 4;
  uint32_t t0 = millis();
  Serial2.printf("AT+NTNSEND=\"%s\"\r\n", msg);   // ASSUMED; vendor-specific
  bool ok = modemCmd("", "+NTNSENT", 30000);       // wait for send confirm
  tx_ms_total += millis() - t0;
  modem_state = 2;
  if (!ok) { reg3_fault |= 0x04; }
  return ok;
}

void loop() {
  // VSWR sanity: reflected detector high -> antenna fault (cap damaged?).
  int vswr = analogRead(VSWR_ADC_PIN);
  if (modem_state >= 2 && vswr > 3600) reg3_fault |= 0x08;
  else reg3_fault &= ~0x08;
  // Poll registration/RSSI in background (vendor-specific strings).
  Serial2.printf("AT+CSQ\r\n");
  delay(5000);
}
