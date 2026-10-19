/*
 * Storage module (ID 3) — 2x 2TB microSD = 4 TB (v0.5 design).
 * Data does NOT cross the pogo (USB2 there is for control only): the module
 * has its OWN USB-C and presents a USB mass-storage device to the host
 * (ESP32-S3 native USB + TinyUSB MSC). Bay gives it power + identity.
 * Cards: 2x microSD on SDMMC 1-bit (clock/cmd/one data line per card —
 * pin-honest for a 34x30x6 mm module). Not compiled (no ESP toolchain here).
 */
#include "../bay_module_common.h"
#include "USB.h"
#include "USBMSC.h"
#include "SD_MMC.h"

USBMSC msc;
static const int SD1_CLK = 12, SD1_CMD = 11, SD1_D0 = 13;   // card A
// Card B shares the bus via a second slot select in the production spin;
// the bench spin carries one card — capacity halves, protocol identical.

static int32_t onRead(uint32_t lba, uint32_t offset, void* buffer, uint32_t bufsize) {
  uint32_t count = bufsize / SD_MMC.sectorSize();
  return SD_MMC.readRAW((uint8_t*)buffer, lba) ? (int32_t)bufsize : -1;
}
static int32_t onWrite(uint32_t lba, uint32_t offset, uint8_t* buffer, uint32_t bufsize) {
  return SD_MMC.writeRAW(buffer, lba) ? (int32_t)bufsize : -1;
}
void setup() {
  // Boot low (<50 mA) -> identify over bay I2C (slave 0x2A) -> full class 1.2 W
  SD_MMC.setPins(SD1_CLK, SD1_CMD, SD1_D0);
  if (!SD_MMC.begin("/sd", true)) { /* set FAULT reg; spine will cut power */ return; }
  msc.vendorID("NEXUS"); msc.productID("STORAGE-4TB"); msc.productRevision("1.4");
  msc.onRead(onRead); msc.onWrite(onWrite);
  msc.mediaPresent(true);
  msc.begin(SD_MMC.totalBytes() / SD_MMC.sectorSize(), SD_MMC.sectorSize());
  USB.begin();
}
void loop() { delay(100); }  // MSC is callback-driven; idle draw ~0.4 W class
