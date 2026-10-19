# NEXUS ONE — FROZEN PARAMETERS v2.0

**Date:** 2026-10-19 · **Status:** DESIGN FREEZE · **Folder:** `~/workspace/nexus-one/FREEZE_v2_0/`
**Supersedes/extends:** v1.0 freeze (`ARCHIVE_v1_7/03_freeze_v1_0/V1_0_FREEZE/`). Nothing in v1.0 is modified; this sheet states what carries over unchanged and what v2 adds/changes, each with its evidence.

---

## 0. Carried over UNCHANGED from v1.0 (frozen, re-affirmed)

These parameters were frozen in v1.0 and survive v2.0 byte-for-byte:

- **Form:** ROLL architecture (MECH-B superseded in v0.6 and stays superseded). One flexible AMOLED wraps an internal drum; panel unrolls sideways out of a slot. No segments, no telescoping.
- **Phone-mode stick:** 183.9 × 34 × 22 mm.
- **Screen:** 162.9 × 71.5 mm, single continuous panel; bend radius R8 held at every deployment pose (checker: 1,001 poses, panel length conserved 0.000 mm).
- **Panel class:** 6.67″ flexible AMOLED 2400×1080 class, ≈162.9×74.5 mm (dynamic roll-cycle rating still NOT-VERIFIED — see OPEN_ITEMS).
- **Internal battery:** 13.7 Wh (2 × 6.85 Wh).
- **Module bay:** 120×24 rail, 8 pogo pins (2 power / USB2 / I2C / GND), 10 W max; identify-before-power boot contract (module boots low → identifies → full power).
- **Mechanism constants:** drum R8; negator spring 12 N·mm / 1.5 N at drum surface; opening force ≈2.0 N; magnetic detents ≥3 N; rack+pinion drum sync m0.5/32T; FPC rolling U-loop R6 (tip travel 13.1 mm, take-up 15.7 mm, target 54,750 cycles); sequencing rule: LEFT deploys first, RIGHT folds first.
- **Electronics:** spine tray board 140×26 mm in 4.5 mm tray; ESP32-S3 controller; AS5600 drum encoder + MAX17048 gauge on SEPARATE I2C buses (shared fixed address 0x36 — v1.3 design catch); DRV5032 detent switches; BQ25890-class charger; USB-C.
- **Default compute architecture:** host-brain — the phone supplies compute/cellular/AI; the ESP32-S3 is the mechanism/safety controller only.
- **BLE protocol v1.0:** UUID base `4e455855-…-00805f9b34fb`, bonded LE Secure Connections, controller is safety owner, 30 s heartbeat watchdog, bay power cut 30 s after link loss. The v2.1 security branch changes (pairing-window 60 s etc.) live in a COPY only — the frozen protocol is unchanged; merge is a gated step (see OPEN_ITEMS).
- **Nexus OS / launcher:** prototype HTML (drum-encoder-driven deployment slider, sim-number readouts) + signed Android launcher APK (681 KB, v1.7). Pocket Mode 0.9 W hot-day cap; thumb-reach OS fix v0.8.1.
- **Pocket fit:** RISK ACCEPTED by the user ("yeah i would carry") — known limitation, not a blocker.
- **Light-field cover:** stores in the carry-case sleeve (cannot fold onto the stick — v0.6 finding).
- **v1 thermal law (for the v1 PC/ABS/POM stack, kept as reference):** folded ≤2 W, folded + battery module ≤1.5 W, open ≤3 W.
- **v1 stack mass:** 241 g (PC/ABS caps, POM drum, aluminium/GF-nylon spine).
- **Poster claims that stay RESIZED, not frozen:** 120 mm stick dims, free-space interactive hologram, 6G service, 4TB-per-card, 200MP-in-spine, 150 g stick — see the vision maps for their honest statuses.

---

## 1. Device baseline v2.0 (phone-mode stick — FROZEN)

| Parameter | Frozen value | Evidence |
|---|---|---|
| Dimensions | 183.9 × 34 × 22 mm (unchanged v1.0) | v1.0 freeze |
| Shell | Ti-6Al-4V rails + CFRP back shell + **graphite spreader ply in the layup** + PC/ABS end caps (RF windows — non-negotiable) | v2.0 materials study; v2.1 B8 config (c) chosen 2026-10-19 |
| Mass (stick, no modules) | **261.3 g** (+20 g vs v1, +8.3%) | v2.0 mass calc (re-run evidence in DESIGN_v2_0/verification) |
| Thermal law v2 | folded ≤**0.9 W** @25 °C (graphite-stack cap 1.25 W); hot-day derate ~**0.5 W class**; **2 W folded only with cooling module docked** (5.36–6.68 W capability); open ≤3 W | v2.1 B8 model — reproduces the v1 law exactly first (2.045/0.909/1.55/2.99 W vs frozen 2.0/0.91/1.5/3.0), then quantifies config (c) |
| v1 law status | Kept as reference for the v1 stack only; the v2 law governs the frozen v2 device | B8 report |
| Graphite RF rule | See §6 — mandatory keep-outs or the ply becomes a 73–86 dB RF block | B6 |

Decision record: config (c) graphite was chosen over (b) Al-spreader (1.75/0.79 W, 274.5 g) because folded mode is low-power by law (idle 0.30 W) so the Al margin buys nothing usable, and the graphite is a ply inside the existing CFRP layup — no new part, no unverified packaging fit. Both stacks fail 0.9 W @35 °C anyway, so the hot-day derate applies either way.

---

## 2. Tablet variant (FROZEN DESIGN VARIANT — not the default device)

| Parameter | Frozen value | Evidence |
|---|---|---|
| Mechanism | Opposed dual-roll: drum 1 (+Y, the untouched v1.0 phone mechanism) + drum 2 (−Y, 71.3 mm tablet panel reserve, ≤1 full turn at R8, interleave film); one continuous panel | v2.0 tablet study — single/dual-panel alternatives evaluated and rejected on numbers |
| Screen | **162.9 × 142.8 mm** exact | checker PASS: 1,001 poses/side, panel length conserved ~1e-14 mm, bend ≥ R8 everywhere |
| Stick envelope (tablet config) | 190 × 46 × 22 mm | tablet design report |
| Mass | 329 g (+88 g vs phone baseline) | mass calc |
| Pull force | ≈2.9 N (manual) | force sim |
| NOT-VERIFIED | Interleave-film wear; drum-2 FPC fatigue; cam-interlock tolerances | carried in OPEN_ITEMS |

---

## 3. Laptop mode (FROZEN — bay module + accessory + OS mode)

| Parameter | Frozen value | Evidence |
|---|---|---|
| Keyboard module (bay ID 6, 33 kΩ) | 118 × 22.5 mm; 3×10 = 30-key matrix (M-1 reconciled to hardware envelope); 0.5 W class; ~31 g; TinyUSB HID (`:USBMode=default` fqbn); scan ~200 Hz paced; key-to-HID 6–16 ms (M-2 corrected); FN layers | v2.0 laptop study; firmware compiles (388,694 B) |
| Kickstand | Deployable, 0–75°; 20 mN·m hinge; no-tip-over proven in statics | torque_calc.py + statics check (33/33 ids PASS) |
| Nexus OS desktop mode | 3 windows + taskbar; triggers on bay id=6 + drum encoder ≥90%; brightness auto-caps 78% to hold the 3 W open law | nexus_os_desktop.html; desktop UX findings U-1, U-3–U-6 still open (U-2 fixed) |
| Render | `DESIGN_v2_0/renders/laptop_mode_v2.webp` | verified against renders_spec.md |

---

## 4. Module roster v2 (9 modules — FROZEN interface + designs)

Bay: 120×24 rail, 8 pogo pins, 10 W max, ID-resistor identify (1% metal film, spine 10 kΩ pull-up), spine-side identify-before-power (v2.1 branch fix F4 — frozen spine fw unchanged until the gated merge).

| Bay ID | Module | ID resistor | Draw | Notes |
|---|---|---|---|---|
| 1 | Battery | 1 kΩ | +10 Wh supply | LiPo safety windows module-side, spine cannot override (v1.0) |
| 2 | Camera Pro | 2.2 kΩ | 2.5 W peak | Periscope, 200MP-class (v0.5 design); 10 s burst + cool-down enforced module-side |
| 3 | Storage | 4.7 kΩ | 1.2 W | Dual 2TB microSD = 4 TB; own USB-C MSC; fw 427,910 B |
| 4 | Sensor | 10 kΩ | 0.3 W | Health/env; fw 290,877 B |
| 5 | Cooling | 22 kΩ | 0.6 W | Micro-blower + Cu spreader + fins; folded Rth 8.8 → 2.58 K/W; folded cap 2.0 → 6.97 W (3.4×); fw 336,721 B |
| 6 | Keyboard | 33 kΩ | 0.5 W | §3 spec; fw 388,694 B |
| 7 | Neural | 47 kΩ | 2.0 W | Edge-TPU-class MCM ~4 TOPS int8 (Coral-class existence proof; exact silicon ASSUMPTION-labelled); USB2 bounds model-load (~1 s/50 MB), not inference; S3 supervisor 75 °C throttle / 85 °C cut; fw 326,026 B |
| 8 | Satellite | 68 kΩ | 3.0 W peak, duty-cycled ≤10% | MT6825-class 3GPP R17 IoT-NTN; TX gated on spine open-mode permit only; folded = PSM sleep, RX-only; fw 335,906 B |
| — | **Projector (AirScreen)** | reserved (MOD_PROJECTOR not in v2.0 enum — ID assignment pending) | 6.4 W (DLP 4.0 + atomiser 2.0 + control 0.4) | Bay module (promoted from v1.0 research dock): mist + pico-DLP, 15 ml = 15-min session, 120×70 mm image @150 mm throw; firmware sketch pending |

All firmware sketches compile first-pass with ESP32 core 3.3.12 (v2.0 independent verification: all checkers 2× byte-identical, sketches recompiled `--clean` byte-exact, verdict GO-with-conditions, conditions fixed).

---

## 5. RF rules (B6 — FROZEN layout law)

- The 2.0 mm PC/ABS cap wall is essentially transparent at all bands of interest: L-band IL 0.014–0.032 dB, BLE ~0.05 dB, 5 GHz 0.11–0.21 dB (constants bounded from published PC/ABS data; exact blend unpublished — ASSUMPTION-labelled). **Polymer-window choice CONFIRMED; the window is not the link-killer.**
- The graphite spreader ply is an opaque RF block (73–86 dB shielding). **Mandatory keep-outs** when it is routed: **≥25 mm radius around the NTN patch centre** (≈λ/8 @1.6 GHz), **≥15 mm around the BLE antenna** (≈λ/8 @2.44 GHz), or a **≥50×50 mm ply cut-out**. The graphite choice survives ONLY with these layout rules.
- Antenna rule: tune the NTN patch with the 2.0 mm cap present (in-situ tune); patch boresight normal to cap surface; window clears antenna footprint ≥1.5×.
- **Satellite link verdicts (paper, MT6825-class, EIRP 26 dBm, R17 IoT-NTN @180 kHz/128x reps): LEO +37.8 dB = YES; GEO L-band n255 +5.6 dB nominal / +2.6 dB floor = MARGINAL-YES (design point); GEO S-band n256 +3.9/+0.9 dB = marginal, NOT claimed.** Dominant uncertainty: satellite G/T (−10 dB/K nominal, bounded −12…−6). BLE control link margin +32.8 dB @10 m — no impact.
- NOT-VERIFIED: full-wave sim, VNA coupon of the actual cap plastic, per-operator G/T, R17 module certification (carried in OPEN_ITEMS).

---

## 6. Own-brain SoM (DESIGNED BRANCH — NOT in the frozen device baseline)

- Custom 60×24 mm Nexus Spine SoM (i.MX 95-class; no standard SoM fits the 26 mm tray): 80.9% tray fill, 3.6 mm ≤ 4.5 mm tray depth.
- Power sim: full AI is **open-mode-only, burst-duty** (3.7 min to Tj 105 °C); folded derate = 2×A55 @800 MHz, NPU OFF. RAM 8 GB on-SoM + micro-CAMM 8 GB = 16 GB.
- The frozen v2.0 device keeps the v1.0 host-brain architecture (ESP32-S3 stays safety owner; BLE frames unchanged). The SoM branch merges only in a v2.x hardware revision; merge is gated (rev-2 board routing, F4 bay sequence in silicon).
- Evidence: `DESIGN_v2_0/own_brain/own_brain_spine.md` + `power_sim.py` (evidence stdout in `verification/evidence/`).

---

## 7. Security posture (frozen vs branch — FROZEN: v1.0, BRANCH: v2.1)

- Frozen (v1.0): LE Secure Connections + bonding; commands only from bonded+encrypted peers; 30 s heartbeat watchdog; bay cut 30 s after link loss; 2 s button-hold pairing.
- v2.1 branch (BRANCH-complete, merge GATED): F1 pairing window (2 s hold → 60 s, bonded-only advertising otherwise); F2 moduleId 0..8 + extended draw table; F3 watchdog bonded-only refresh; F4 spine-side identify-before-power cross-check (ADC divider read before PIN_BAY_EN, reg cross-check, bay cut within one 100 ms poll cycle); F13 detent debounce; F5 PARTIAL (NimBLE 2.x auto-CCCD, no API for encrypted-only ATT perms — compensating control: notify only on bonded+encrypted links). Compile clean: 582,561 B (44%) flash / 34,396 B RAM (10%); tests 12/12 baseline + 45/45 extended (caught 3 real bugs pre-delivery).
- **F5's CCCD subscribe behaviour with an unbonded client must be validated on hardware before the bonding claim ships — gates the merge.** Frozen firmware untouched by design.

---

## 8. What v2.0 does NOT freeze

- Any physical build (digital-only mandate; bench B1–B6 parked as reference).
- Free-space volumetric holography: gap re-measured UPWARD to ~1000× (938 traps, ~192 W) + eye-safety HARD BLOCKER — research track only, never the product layer. Product displays: AMOLED, light-field v2 (0.70 W, 25.6 ms eye-to-photon, designed), AirScreen module (6.4 W).
- 6G service, per-operator satellite G/T, R17 certification.
- Prices (₹0 project; poster's $999–$1,499 is commercial vision only).
- The 120 mm poster stick dims (geometrically impossible with the real panel — geometry, not opinion).

## 9. Evidence index

`DESIGN_v2_0/` (designs, checkers, compiles, verification/evidence/*), `DESIGN_v2_1/` (thermal/, firmware/, rf/RF_STUDY_B6.md + rf_calc_b6.py + stdout), `VISION_MAP_v1_8/` (v1.8), `ARCHIVE_v1_7/00_START_HERE/MASTER_INDEX.md` (v0.2–v1.7 record). This freeze folder: `VISION_MAP_v2_1.html`, `BOM_DELTA_v2_0.md`, `OPEN_ITEMS_v2_0.md`, `README_FREEZE_v2_0.md`.
