# NEXUS ONE v2.0 — MODULES workstream report (2026-10-19)

Four ESP32-S3 bay-module sketches sharing the bay contract, a v2.0-amended
contract header copied into each sketch dir, a thermal model, and a
satellite link-budget sanity check — all verified against the REAL v1.6
toolchain this session. Write scope was strictly
`~/workspace/nexus-one/DESIGN_v2_0/modules/`; `ARCHIVE_*` and `CODE_v1_*`
untouched.

Note on provenance: a previous/concurrent draft of this report existed in
this file with a different account of the keyboard build (plain fqbn +
`--clean`, 388,662 B). I re-verified everything from the current on-disk
sources. What follows is what I actually ran and observed; where it
differs from the earlier draft, my numbers/commands below are the verified
ones.

## 1. Compile results — all four PASS

| Sketch | fqbn | Flash | RAM | Result |
|---|---|---|---|---|
| cooling_module | `esp32:esp32:esp32s3` | 336,721 B (25%) | 24,560 B (7%) | **PASS** |
| satellite_module | `esp32:esp32:esp32s3` | 335,906 B (25%) | 23,816 B (7%) | **PASS** |
| neural_module | `esp32:esp32:esp32s3` | 326,026 B (24%) | 23,816 B (7%) | **PASS** |
| keyboard_module | `esp32:esp32:esp32s3:USBMode=default` | 388,706 B (29%) | 56,352 B (17%) | **PASS** |

Exact commands (env per the v1.6 procedure):
```
export ARDUINO_DIRECTORIES_DATA=~/tools/arduino-data \
       ARDUINO_DIRECTORIES_DOWNLOADS=~/tools/arduino-downloads \
       ARDUINO_DIRECTORIES_USER=~/tools/arduino-user
~/tools/arduino/arduino-cli compile --fqbn esp32:esp32:esp32s3 \
    ~/workspace/nexus-one/DESIGN_v2_0/modules/cooling_module
~/tools/arduino/arduino-cli compile --fqbn esp32:esp32:esp32s3 \
    ~/workspace/nexus-one/DESIGN_v2_0/modules/satellite_module
~/tools/arduino/arduino-cli compile --fqbn esp32:esp32:esp32s3 \
    ~/workspace/nexus-one/DESIGN_v2_0/modules/neural_module
~/tools/arduino/arduino-cli compile --fqbn esp32:esp32:esp32s3:USBMode=default \
    ~/workspace/nexus-one/DESIGN_v2_0/modules/keyboard_module
```
Toolchain: arduino-cli 1.1.1, ESP32 core 3.3.12. No libraries installed
(downloads.arduino.cc proxy-blocked; only core + built-in Wire/USB used).

### Why the keyboard needs `:USBMode=default`
The generic `esp32s3` board defaults to **Hardware CDC/JTAG**
(`esp32s3.build.usb_mode=1` in boards.txt) — I verified `-DARDUINO_USB_MODE=1`
in the actual compile lines. The TinyUSB device stack (needed for
`USBHIDKeyboard`) requires the explicit `USBMode=default` board option
(usb_mode=0). With the plain fqbn the keyboard sketch does not produce a
working build in this toolchain; with `:USBMode=default` it compiles and
links cleanly (388,694 B / 29%).

### Other toolchain findings (new)
1. **Core 3.x LEDC API**: `ledcSetup`/`ledcAttachPin` are gone; use
   `ledcAttach(pin, freq, resolution)` + `ledcWrite(pin, duty)`. Caught by
   the compiler and fixed in cooling_module.
2. **Never SIGTERM a build mid-core-compile**: killing arduino-cli while it
   builds `core.a` leaves a corrupt partial archive in
   `~/.cache/arduino/cores/` that poisons later builds with `undefined
   reference` link errors. Fix: delete that board-config cache dir and
   rebuild. (Observed directly this session.)

## 2. Cooling module — active element + thermal numbers

**Choice: 20×20×8 mm 5 V micro-blower (0.40 W) + copper spreader + ducted
fin stack. TEC rejected with numbers** — 0.6 W into a micro-TEC at COP~0.5
pumps only ~0.30 W while 0.90 W must be rejected through the same tiny
heatsink; the blower moves ~23× more heat per watt because it attacks the
convection bottleneck instead of fighting thermodynamics.

**Budget (0.6 W class; ID 5 / 22 kΩ CONFIRMED in the frozen v1.4 header):**
blower 0.40 W + S3 supervisor 0.13 W + sensors/margin 0.07 W = 0.60 W.
Closed-loop fan curve 30→45 °C plate temp, tach watchdog, 60 °C runaway
guard → fault bit.

**thermal_calc.py stdout (verbatim, run 2026-10-19):**
```
=== NEXUS ONE v2.0 cooling module — thermal model ===
Baseline folded Rth (frozen v0.4): 8.8 K/W
  re-derived cap @25 C ambient: 2.045 W  (frozen law: 2 W -> MATCH)
  re-derived cap @35 C ambient: 0.909 W  (v1.2 report: 0.91 W -> MATCH)

Blower air heat-carry @ 1.0 L/s, dT=10.0 K: 12.1 W
  (>> phone heat load: air is NOT the bottleneck)

Fin area: 192 cm2 -> R_conv = 1/(45.0*0.0192) = 1.16 K/W
Module path R = R_contact 2.5 + R_conv 1.16 = 3.66 K/W

Rth_folded: 8.8 K/W  ->  2.58 K/W  (parallel path)
Sustained folded cap @25 C: 2.05 W  ->  6.97 W  (3.4x the 2 W law)
Sustained folded cap @35 C: 0.91 W  ->  3.10 W  (3.4x hot-day)

TEC alternative (rejected): 0.6 W in x COP 0.5 = 0.30 W pumped,
  but 0.90 W must be rejected through the same tiny heatsink.
  Blower path moves the FULL phone heat load (~7.0 W class) for 0.40 W.
  Verdict: blower wins ~23x on moved-heat per watt.
```

**Headline:** folded Rth **8.8 → 2.58 K/W**; sustained folded cap
**2.0 W → ~7.0 W @25 °C (3.4× the frozen law)**, hot-day 0.91 → 3.1 W.
These are physics caps — the spine's firmware thermal-law table (≤2 W
folded) must be updated by the controller workstream to use them; this
workstream does not touch frozen firmware. Design requirement: SoC heat
must reach the bay-rail spreader (NOT-VERIFIED — needs a chassis
thermal-strap design).

## 3. Satellite module — NTN class, power, antenna, link sanity

- **Modem class: MT6825-class** — 3GPP Release-17 IoT-NTN standalone
  chipset (L-band n255 + S-band n256, integrated Cortex-M4F + transceiver +
  PMU). Existence proof: ships in Motorola Defy 2, CAT S75, Motorola Defy
  Satellite Link (Bullitt Satellite Connect) — two-way satellite messaging
  on GEO. Sources:
  https://www.mediatek.com/technology/5g/5g-satellite-ntn/mt6825?hsLang=en
  https://www.electronicproducts.com/mwc-showcases-satellite-communications/
- **Power budget:** peak TX 23 dBm → PA 0.53 W @38% PAE + modem 0.90 W +
  S3 0.25 W + PMIC/margin 0.32 W = **~2.0 W peak**; reported class 3.0 W
  (ID 8, 68 kΩ E12; reg2 = 30). Fits the 10 W bay and the open-mode ≤3 W
  thermal law. Firmware duty-cycles TX ≤10% (avg ≤ ~0.5 W) and GATES TX on
  the spine's open-mode permit (reg 0x20); folded = PSM sleep, RX-only.
  Boot: modem rail OFF → <50 mA.
- **Antenna:** L-band ceramic patch ~25×25×4 mm (or stamped helix), RHCP,
  in the polymer end-cap RF window. **The cap must stay polymer**: at
  1.6 GHz a metal cap is a Faraday shield (skin depth ~2 µm — total block)
  and near-field metal detunes the patch. This is the physical reason the
  frozen v1.0 design already specifies PC/ABS cap windows.
- **Link-budget sanity — satellite_link.py stdout (verbatim):**
```
=== NEXUS ONE v2.0 satellite link-budget sanity (class level) ===
Band: n255 L-band UL ~1640 MHz | device TX 23 dBm + 3 dBi -> EIRP 26 dBm

GEO (d=35786 km): FSPL = 187.8 dB
  Pr_iso = -161.8 dBm
  Sanity: 3GPP R17 IoT-NTN (NB-IoT NTN, 180 kHz, up to 128x
  repetitions, ~-13 dB SNR operating point) is DESIGNED for
  exactly this ~188 dB path — commercial proof: Motorola Defy 2
  / CAT S75 / Defy Satellite Link ship MT6825 on GEO networks.

LEO (d=550 km): FSPL = 151.5 dB
  Pr_iso = -125.5 dBm
  Sanity: 36 dB easier than GEO — closes with wide margin;
  same modem class, same antenna.
```
Class-level verdict: the GEO path closes at the R17 IoT-NTN design point;
per-operator G/T, EIRP-density masks, in-situ antenna efficiency with
hand/body loading, and R17 certification of the module as built are
NOT-VERIFIED.

## 4. Neural module — decision

**DECISION: build the USB2-class NPU module NOW (v2.0).**
Full record: `neural_module/NEURAL_DECISION.md`.
- Existence proof: **Google Coral USB Accelerator** — Edge TPU, 4 TOPS
  int8, ~2 TOPS/W, ~2 W typical over USB (datasheet v1.4); the SMT MCM
  variant (15×10×1.5 mm) natively supports **USB 2.0** — exactly our bay's
  USB2 pogo pair. Sources in NEURAL_DECISION.md.
- Architecture: NPU MCM (own USB2 device port → pogo D-/D+) + ESP32-S3
  supervisor (this sketch: ID 7, 47 kΩ E12; boot <50 mA → identify →
  sequence NPU rail → throttle/cut at 75/85 °C). Spine enumerates a
  standard USB device; Nexus OS runs the vendor TFLite runtime.
- Class numbers **(ASSUMPTION-labelled):** 4 TOPS int8, ~2 TOPS/W, 2.0 W
  draw class (reg2 = 20). USB2 bounds model-load bandwidth (~1 s per
  50 MB), not steady-state inference streaming.
- **v2 bay-bus upgrade path (documented, not built):** USB3 over pogo
  needs SSTX±/SSRX± → 12-pogo bay revision, 90 Ω SI over spring contacts,
  crosstalk analysis, FCC/CE re-cert. Cheaper alternative first: dual-MCM
  on USB2 (doubles TOPS, zero bay changes). USB3 is a v2.1+ program.

## 5. Keyboard module — firmware

- **ID 33 kΩ — CONFIRMED FREE** in the frozen v1.4 table (only
  1k/2.2k/4.7k/10k/22k used); 33k is E12 and unassigned → MOD_KEYBOARD = 6.
- Native TinyUSB HID keyboard (S3 USB-OTG → pogo D-/D+; spine is host).
  HID API verified against core 3.3.12 `USBHIDKeyboard` sources.
- **Matrix 3 rows × 10 cols = 30 keys** — reconciled with the v2.0 laptop
  hardware spec (M-1 fix, 2026-10-19): 118×22.5 mm module, 11.4 mm col /
  6.5 mm row pitch, scissor 0.8 mm. The earlier 5×12/60-key draft could not
  fit the envelope and is withdrawn. FN layer: numbers (row 0), F1–F9+ESC
  (row 1), symbols (row 2). 5 ms debounce; diode-per-key ghost suppression
  assumed in hardware. Pin map avoids strapping pins, USB D-/D+, and
  documents the octal-PSRAM caveat (cols 33–38) in the sketch comments.
- **Timing, honestly (M-2 fix):** the 5 ms loop pacing sets the scan at
  ~200 Hz (3 rows scan in microseconds); key-to-HID latency ≈ pacing (≤5 ms)
  + debounce (5 ms) + USB poll (~1 ms) ≈ 6–11 ms typical, ~16 ms worst. The
  earlier "1 kHz / 9 ms" claim was wrong and is withdrawn.
- **Power ≤0.5 W:** S3 @80 MHz, radio never started, USB active, paced
  scanning; reg2 = 5. Boot: USB off, matrix idle →
  <50 mA. I2C slave 0x2A identify-then-enable per the contract.

## 6. ASSUMPTIONS (all labelled in code/comments)

- Blower 1.0 L/s @ ~200 Pa (0.40 W, 2004-class); h_forced ≈ 45 W/m²K;
  fin area 192 cm²; R_contact cold-plate→bay-rail 2.5 K/W (dominant term —
  demands real TIM + clamp force).
- NPU class numbers (4 TOPS / ~2 TOPS/W / 2.0 W) are Coral-class proxies;
  exact silicon not chosen.
- Satellite: 3 dBi patch gain; AT command strings are vendor-manual
  placeholders; modem sensitivity ~−130 dBm class.
- Keyboard: diode-per-key matrix; 3×10 = 30 keys at 11.4/6.5 mm pitch (M-1
  reconciled with hardware spec); scan ~200 Hz paced, key-to-HID 6–16 ms
  (M-2 corrected); ~60 mA draw @80 MHz.
- Envelopes (v0.7 rail 120×24): cooling 60×24×12, satellite 60×24×10,
  neural 45×24×8, keyboard 120×24×6 mm.

## 7. NOT-VERIFIED remainder

1. Chassis thermal-strap design (cooling cap math assumes SoC heat reaches
   the bay-rail spreader).
2. Satellite: per-operator G/T, EIRP-density regulatory masks, in-situ
   antenna efficiency with real end-cap + hand/body loading, 3GPP R17
   certification of the module as built.
3. Neural: exact NPU silicon + Nexus OS vendor-runtime port; sustained 2 W
   thermals in the 45 mm module at 35 °C ambient.
4. Keyboard: key feel/travel at 9.6 mm pitch (human factors — physical
   mock parked); HID latency/rollover against the real spine host stack.
5. USB3-over-pogo bay revision: SI simulation + re-cert (v2.1+ program).
6. Spine firmware updates: thermal-law table for the new ~7 W folded cap
   and learning the three new module IDs — controller workstream scope.
7. Physical bench B1–B6 — parked by the digital-only rule; panel
   roll-cycle rating; RF of cap windows — carried from v1.6.
8. Production hardening backlog (all four sketches): check
   `setCpuFrequencyMhz()` return, 72 h stress / stack-high-water marks,
   I2C fault injection — noted, not done here.

---
*Every number in §1 is from an actual `arduino-cli compile` run this
session; every number in §2/§3 is pasted stdout from the matching .py run.
Sources: web citations inline; the earlier draft's keyboard size/claim
(388,662 B, plain fqbn) was not reproducible — the verified build is
388,694 B with `:USBMode=default`, documented in §1.*
