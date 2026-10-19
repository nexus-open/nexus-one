# NEXUS ONE — BOM delta v2.0 (vs the 52-item v1.0 master BOM)

Conventions carried from v1.0: **qty-0** = designed/researched/branched but deliberately NOT in the v2.0 device baseline (variant, dock, branch, or research). No prices: ₹0 project, engineering record only.

## CHANGED items

| ID | Item | v1.0 | v2.0 | Status |
|---|---|---|---|---|
| S01 | Spine shell | 6061 aluminium or GF-nylon, 183.9×34, 2 PC antenna inserts | **Ti-6Al-4V rails + CFRP back shell + graphite spreader ply in layup + PC/ABS end caps (RF windows)** — mass 241→261.3 g | DESIGN (frozen, v2.1 config c) |
| X05 | Cooling module | Graphite + vapour-chamber back plate (concept class) | **Final design:** micro-blower 0.40 W + Cu spreader + fin stack; folded cap 2.0→6.97 W; fw 336,721 B | DESIGN (frozen) |
| X06 | Projector | qty-0 research DOCK (pico DLP + atomiser, ~6 W, own battery) | **Promoted to bay module:** mist + pico-DLP in the 120×24 bay, 6.4 W of the 10 W bay (DLP 4.0 + atomiser 2.0 + control 0.4), 15 ml = 15-min session, 120×70 mm @150 mm; firmware sketch pending; bay ID reserved (MOD_PROJECTOR not yet in enum) | DESIGN (frozen, fw pending) |

## ADDED items (qty>0)

| ID | Item | Spec | Status |
|---|---|---|---|
| S05 | Kickstand | Deployable 0–75°, 20 mN·m hinge, no-tip-over proven (statics, 33/33 ids) | DESIGN (frozen) |
| X08 | Keyboard module | 118×22.5 mm, 30 keys (3×10, M-1 reconciled), 0.5 W, ~31 g, 33 kΩ ID, TinyUSB HID | DESIGN (frozen) |
| X09 | Neural module | Edge-TPU-class MCM ~4 TOPS int8 @2 W (Coral-class existence proof; exact silicon ASSUMPTION), 47 kΩ | DESIGN (frozen) |
| X10 | Satellite module | MT6825-class 3GPP R17 IoT-NTN, 68 kΩ, 3.0 W peak duty-cycled ≤10%, TX open-mode-gated | DESIGN (frozen) |

## Tablet variant (qty-0 on phone baseline; qty-1 in the tablet variant config)

| ID | Item | Spec | Status |
|---|---|---|---|
| S06 | Tablet drum-2 | R8, 71.3 mm tablet panel reserve, ≤1 full turn, interleave film | DESIGN (frozen variant) |
| S07 | Cam-interlock | Tablet sequencing interlock — tolerances NOT-VERIFIED | DESIGN |

## Branch / research (qty-0, NOT in the frozen device)

| ID | Item | Spec | Status |
|---|---|---|---|
| X11 | Nexus Spine SoM branch | i.MX 95-class 60×24 mm, 16 GB (8 on-SoM + micro-CAMM 8 GB); open-only burst 3.7 min to Tj 105 °C | DESIGNED branch — merge gated |
| X07 | Micro-CAMM RAM module | Future area-array LPDDR (unchanged from v1.0) | RESEARCH |
| R01 | Photophoretic volumetric display | Gap re-measured ~1000× (938 traps, ~192 W), eye-safety hard blocker | RESEARCH |
| R02 | 6G front-end | Antenna keep-outs only; no radio (unchanged) | RESEARCH |

## Unchanged (re-affirmed)

All other v1.0 BOM items carry over byte-for-byte: S02–S04 (caps, tray), M01–M09 (drum, bearings, negator, leading bar, pinion, detents, magnets, rails, screws), M10 MECH-B legacy (qty-0), D01–D05 (panel class, driver, FPC loop, light-field cover, strip fab research), E01–E12 (spine board, ESP32-S3, encoder, detent sensors, charger, gauge, boost, buck, bay switches, USB-C, battery, protection), W01–W06 (wiring), B01–B03 (rail, pogo array, magnets), X01–X04 (battery/camera/storage/sensor modules), H01–H03 (host phone, launcher, carry case).

E01 note: the spine tray board spec is unchanged for the host-brain baseline; the SoM branch is a separate qty-0 hardware branch, not a BOM change.

## Flagged during assembly

- Keyboard firmware size is recorded as 388,694 B in the v2.0 vision map but 388,706 B in the v2.0 coordinator's final report (12 B rebuild delta). Kept as 388,694 B (map value) pending a byte-check; flagged, not silently fixed.
- v1.0's X06 dock spec is SUPERSEDED by the bay-module spec — the dock version is retained in the v1.0 archive only.
- In v2.0's `bay_module_common.h`, MOD_PROJECTOR has no assigned ID resistor yet (IDs 1–8 taken); a bay ID for the projector module must be assigned when its firmware is written (gated open item).
