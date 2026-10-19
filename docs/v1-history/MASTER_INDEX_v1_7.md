# NEXUS ONE — Master Archive (2026-10-19; refreshed same day through v1.7)

**Idea & builder: Fabulous.** Concept poster 10:17 IST → design freeze the
same day. All work is DIGITAL (Fabulous's mandate): no hardware exists, and
nothing physical was asked of him. Every claim below carries its evidence
type; anything not evidenced is listed under NOT VERIFIED, in the open.

## The device (v1.0 frozen)
Roll-expanding stick phone: 183.9 × 34 × 22 mm, ~241 g. One real flexible
AMOLED (162.9 × 74.5 mm class) wraps an R8 drum; sliding bar unrolls it to a
162.9 × 71.5 mm screen. ESP32-S3 controller, host phone as brain (USB-C video
+ BLE state link), magnetic module bay (battery/camera/storage/sensor).

## Timeline — every version, with how it was checked
| Ver | What | Evidence |
|---|---|---|
| Plan | Build-plan PDF, phases 0–5, ₹0 | `01_origin/` (plan since superseded by digital-only rule) |
| v0.2 | MECH-B mechanism (ChatGPT handoff) | Bundle in `01_origin/`; its validator was missing — rebuilt in v0.3 |
| v0.3 | MECH-B validated; NEW collision rule (left deploys first) | Python checker reproduced all v0.2 numbers exactly + independent-motion test |
| v0.4 | Physics sim + audit of EVERY poster component (6 fail/resize) | Monte Carlo 20k builds; drop/friction/thermal sims |
| v0.5 | Invention pack for the 6 failures | Physics-legal designs + sims; volumetric hologram = research (~100× gap), 6G service = not inventable |
| v0.6 | ROLL architecture replaces the 3-frame stack | Checker: panel length conserved 0.000 mm / 1,001 poses, R8 always |
| v0.7 | FPC loop, negator spring, antenna caps, module bay | Checker PASS |
| v0.8 | Host-link board + Nexus OS prototype | Board checker PASS (fit, power modes, wire drops) |
| v1.0 | DESIGN FREEZE: BOM (52 items), BLE protocol, Android skeleton | `03_freeze_v1_0/` |
| v1.1 | ALL SCAD COMPILED (OpenSCAD 2021.01) → STL + renders | Bounding boxes match frozen dims exactly (183.90 etc.) |
| v1.2 | Digital pocket test (ergonomics sim) | Pocket-length RISK found, accepted by Fabulous; 2 OS fixes applied (v0.8.1) |
| v1.3 | Controller firmware + Android BLE client | Firmware logic model executed: 12/12 tests PASS |
| v1.4 | Module firmware sketches + posed CAD renders | Source; renders visually verified (stick/half/full/cover) |
| v1.6 | TOOLCHAIN: ESP32 core 3.3.12 + NimBLE 2.5.1, JDK 17, kotlinc 1.9.24 | Controller + all 4 module sketches COMPILE (one real fix: Bluedroid-only API → NimBLE READ_ENC/WRITE_ENC); logic tests 12/12; Kotlin compiles; signed debug APK assembled manually (Gradle fetch blocked by sandbox egress policy — see CODE_v1_6/README) |
| v1.7 | Android BLE API modernization (API 33+ typed calls, legacy path kept for minSdk 26) | Recompiled: ZERO warnings; APK rebuilt + signature verified; protocol bytes unchanged |

## NOT VERIFIED — the complete open list
1. Maker panel dynamic roll-cycle rating (needs a dynamic-rated panel class).
2. RF behaviour of the antenna cap windows (design intent only).
3. ~~Firmware and Android UNCOMPILED~~ — CLOSED by v1.6/v1.7: all firmware
   and the Android launcher compile on real toolchains; a signed debug APK
   exists. (The APK was assembled manually because this sandbox blocks
   Gradle's dependency downloads; the patched Gradle build files are in
   `05_code/CODE_v1_7/android-build/` for a normal dev machine.)
4. Bench tests B1–B6 and any physical build — parked by Fabulous's digital-only
   rule; they exist as plans (`04_validation/…POST_FREEZE_v1_1/bench/`).
5. True volumetric holography (~100× gap) and 6G service — research tracks.

## How to explore
Freeze doc: `03_freeze_v1_0/V1_0_FREEZE/docs/DESIGN_FREEZE_v1_0.md` ·
Run Nexus OS: `02_design_versions/ELECTRONICS_v0_8/os/nexus_os.html`
(v0.8.1 update in `04_validation/DIGITAL_VALIDATION_v1_2/os/`) ·
CAD renders: `05_code/CODE_v1_4/renders/` · STLs: `04_validation/POST_FREEZE_v1_1/scad_compile/`
