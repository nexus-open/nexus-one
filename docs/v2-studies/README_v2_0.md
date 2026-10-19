# NEXUS ONE v2.0 — Build README

**Built 2026-10-19** under Fabulous's mandates: DIGITAL-ONLY, REAL PHYSICS, HONEST LABELS, AUTONOMY, no scope cuts. The v1.0 freeze (ARCHIVE_v1_7, CODE_v1_6/v1_7) is untouched; v2.0 is a new branch under `DESIGN_v2_0/`.

**What v2.0 is:** ten of v1.8's eleven GAP+ROUTE vision elements now have real, simulated, parametric designs. The eleventh (volumetric holography) was re-measured — the gap is ~1000×, reported, not hidden.

## What was built (evidence numbers)

| Workstream | Headline | Evidence |
|---|---|---|
| Tablet mode | Opposed dual-roll: one panel, drum 1 (v1.0 phone mech untouched) + drum 2 (−Y, 71.3 mm reserve, ≤1 turn @ R8). Screen 162.9×142.8 exact. Stick 190×46×22 mm, 329 g (+88), pull ~2.9 N | checker.py PASS: 1,001 poses/side, length conserved ~1e-14 mm |
| Laptop mode | Keyboard module hw (118×22.5 mm, 30 keys, 0.5 W, ~31 g, 33 kΩ); kickstand 0–75°, 20 mN·m hinge, no tip-over proven; Nexus OS desktop mode (3 windows, real sim numbers) | check.py PASS (33/33 ids); statics calc |
| Modules | 4 firmware sketches compile | 336,721 / 335,906 / 326,026 / 388,706 B flash |
| Cooling module | Rth 8.8→2.58 K/W; folded cap 2.0→6.97 W (3.4×) | thermal calc re-derives frozen law exactly first |
| Own-brain spine | 60×24 mm SoM, fits tray 80.9% fill / 3.6 mm; full AI = open-only burst (3.7 min to Tj 105°C); folded derate = 2×A55@800 MHz, NPU OFF; 16 GB RAM | power sim |
| Hologram | Light-field v2 (0.70 W, 25.6 ms eye-to-photon) + AirScreen module (6.4 W, 15 ml/15 min) | spec + eye-tracking math |
| Materials | Ti rails + CFRP shell, polymer caps stay (RF windows): 241→261 g (+20 g, +8.3%) | mass_calc + material math |
| Roadmap | RICE-ranked backlog; top item B8 v2 thermal model (1.25); B1 refreshed with delivered tablet numbers | 9 scores recomputed exactly |
| Security review | 0 Critical, 5 High, 4 Medium, 4 Low, 4 Informational | reviewed vs frozen CODE_v1_6, read-only |
| Verification | Independent 2×-deterministic re-runs: **9/9 PASS** byte-identical; GO (with conditions) | VERIFICATION_REPORT_v2_0.md + 20 evidence captures |

**Keyboard cross-workstream defect (M-1) — fixed in this build:** the module firmware drafted a 5×12/60-key layout that could not fit the 118×22.5 mm hardware envelope. The firmware now implements the hardware spec exactly (3×10 = 30 keys, FN layers, ~200 Hz paced scan, key-to-HID 6–16 ms — the earlier "1 kHz" timing claim is withdrawn). Recompiled clean: 388,706 B.

**Volumetric hologram — honest gap:** the poster's filled 30 mm globe needs 938 traps ≈ **1000×** beyond demonstrated 1-trap systems (~192 W wall-plug; Class 3B/4 — eye safety is a HARD BLOCKER). The product layer never promises the globe.

**2 W folded thermal law — conflict found:** the Ti/CFRP premium stack conducts ~25× worse than aluminium; the folded law does not survive it as drawn. A graphite spreader + 1-D model (roadmap B8) is the critical-path item before any v2 freeze.

## v2.0 pack contents

```
DESIGN_v2_0/
├── tablet/            dual-roll design + checker + renders spec
├── laptop/            keyboard/kickstand design + desktop OS HTML
├── modules/           4 compiled firmware sketches + report
├── own_brain/        SoM spine design + power sim
├── hologram/         light-field v2 + AirScreen + volumetric research
├── materials/        premium materials study + renders spec
├── roadmap/          ROADMAP_v2_x.md (RICE-ranked)
├── security/         SECURITY_REVIEW_v2_0.md
├── verification/     VERIFICATION_REPORT_v2_0.md + evidence/
├── vision_map/       nexus-one-vision-map-v2-0.html (31 elements: 14 proven / 11 designed / 3 gap+route / 3 vision-only)
├── renders/          tablet_mode_v2.webp (verified against design)
├── COORDINATION.md   build log
└── README_v2_0.md    this file
```

## NOT-VERIFIED remainder (open list)

1. Maker panel dynamic roll-cycle rating (datasheets don't publish it)
2. RF behaviour of the polymer cap windows (BLE/Wi-Fi/satellite antennas)
3. Any physical bench result — parked by the digital-only rule
4. True volumetric holography + 6G service — research tracks
5. v2 thermal model for Ti/CFRP vs the 2 W folded law (roadmap B8)
6. Tablet interleave-film wear + drum-2 FPC fatigue
7. Bay identify-before-power contract: specified in v2.0 copies, unimplemented in frozen spine firmware (security F4) — gates any module merge
8. Security Highs F1–F3, F5: pairing window, moduleId OOB read, heartbeat reset, CCCD telemetry — fix before any BLE/app merge
9. Satellite in-situ antenna efficiency + certification
10. NPU exact silicon (Coral-class proxies used, ASSUMPTION-labelled)

Renders in this pack are renders (laptop-mode render attempt failed — media service 503; spec retained in materials/renders_spec.md).
