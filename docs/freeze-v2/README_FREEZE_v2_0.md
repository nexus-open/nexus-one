# NEXUS ONE — v2.0 Design Freeze (README)

## What this is

The v2.0 design freeze extends the v1.0 freeze (`ARCHIVE_v1_7/03_freeze_v1_0/V1_0_FREEZE/`) from a phone-mode stick to the full four-mode flagship the vision boards describe — without deleting anything from the vision and without fabricating a single number. Every new element carries its checker, compile, or calc behind it; every gap keeps its measured size and its route.

## How it relates to v1.0

- v1.0 (phone-mode stick, host-brain, PC/ABS stack, 241 g) is untouched and re-affirmed — its parameters are restated in `FROZEN_PARAMETERS_v2_0.md` §0 with "carried over unchanged" on each line.
- v2.0 adds: the **tablet design variant**, **laptop mode**, **9-module ecosystem**, the **graphite-ply premium shell (261.3 g)**, the **v2 thermal law**, the **B6 RF layout rules**, the **v2.1 security branch**, and the **own-brain SoM as a designed branch**.
- The v1 thermal law stays valid for the v1 stack; the v2 law governs the frozen v2 device. The frozen device keeps the v1.0 host-brain architecture; the v2.1 security fixes merge only in a gated step.

## What's in this folder

| File | Contents |
|---|---|
| `FROZEN_PARAMETERS_v2_0.md` | The frozen sheet: carried-over v1.0 params + v2 additions with evidence |
| `VISION_MAP_v2_1.html` | All 31 vision elements re-mapped on v2.0/v2.1 evidence (14 PROVEN / 11 DESIGNED / 3 GAP+ROUTE / 3 VISION ONLY) |
| `BOM_DELTA_v2_0.md` | What the master BOM gains/changes vs the 52-item v1.0 BOM (qty-0 conventions kept, no prices) |
| `OPEN_ITEMS_v2_0.md` | The carried NOT-VERIFIED register (16 items) |
| `README_FREEZE_v2_0.md` | This file |

Full evidence trees: `DESIGN_v2_0/` (designs, checkers, compiles, renders), `DESIGN_v2_1/` (thermal model, security branch, RF study).

## Decision log

1. **Re-baseline (2026-10-19 17:48).** The vision boards are the target and stay whole; engineering attaches statuses and works toward them — never shrinks them. The v1.8 map, v2.0 build, and this freeze all execute that re-baseline.
2. **Graphite ply (2026-10-19 19:36).** Hari delegated the thermal-stack choice ("It's your choice"). Muse chose config (c): folded mode is low-power by law (idle 0.30 W), so the Al spreader's extra thermal margin buys nothing usable; the graphite ply is a layer inside the existing CFRP layup — no new part, no unverified packaging fit. Its RF-coupling risk became a quantified layout rule (B6 keep-outs), not a reason to reject it.
3. **Tablet mechanism: opposed dual-roll.** Single- and dual-panel alternatives were evaluated and rejected on numbers; the dual-roll keeps one continuous panel with drum 2 holding ≤1 turn at R8.
4. **Neural module: build now on USB2.** Edge-TPU-class MCM (4 TOPS int8, ~2 TOPS/W) is real as a class; USB2 bounds only model-load bandwidth (~1 s/50 MB), not inference. USB3-over-pogo documented as a v2.x program, not built.
5. **AirScreen promoted to bay module.** The v1.0 research dock became a 6.4 W bay module in v2.0 (mist + pico-DLP in the 120×24 rail).
6. **Security: fix in a branch, freeze untouched.** All 5 Highs fixed in the v2.1 copy; F5 partial is hardware-validation-gated; the frozen firmware is deliberately unmodified — merge is a separate gated step.
7. **Volumetric holography reported worse, not hidden.** The gap recomputed from ~100× to ~1000× (938 traps, ~192 W) with an eye-safety hard blocker. Product displays remain AMOLED + light-field v2 + AirScreen.
8. **B6 verdicts.** Polymer cap windows confirmed transparent (0.014–0.032 dB L-band); graphite ply is a 73–86 dB RF block near antennas → the keep-out rules; satellite link: LEO YES (+37.8 dB), GEO L-band marginal-yes, S-band not claimed.

## What gates further freezes

The v2.1→ship firmware merge (F5 hardware validation, rev-2 board), tablet film/FPC fatigue life, VNA coupon + full-wave sim, per-operator satellite G/T + R17 certification — see `OPEN_ITEMS_v2_0.md`. The hologram and 6G tracks remain research; bench stays parked under the digital-only mandate.
