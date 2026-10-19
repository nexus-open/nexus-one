# NEXUS ONE — Roadmap

Built from the v2.0 open-items register (16 carried NOT-VERIFIED items) plus the natural milestones. Status at release: v2.0 DESIGN FREEZE is complete; the v2.1 security branch and the B6/B8 studies are designed and simulated.

## Milestones

### M1 — Community prototype program
Run the bench plan B1–B6 ([`docs/BENCH_PLAN.md`](docs/BENCH_PLAN.md)) with the sim-tied pass criteria. This is the single highest-value milestone: it turns the blueprint into a device and closes the largest group of open items at once.

### M2 — Panel durability rig (the #1 unknown)
No maker publishes a dynamic roll-cycle rating for flexible AMOLEDs. M2 needs a maker datasheet or a community-built roll-cycle rig to validate the design target of ~54,750 cycles at bend radius R8.

### M3 — Firmware merge (gated)
Merge the v2.1 security branch (pairing window, identify-before-power, watchdog gating, detent debounce) into the ship firmware. **Gate:** F5 hardware validation — NimBLE 2.x auto-creates the CCCD with no API for encrypted-only permissions; the subscribe behaviour with an unbonded client must be observed on hardware before the bonded-command claim ships. (The frozen v1.6/v1.7 spine stays untouched until then.)

### M4 — Satellite operator data
Close the link-budget uncertainties: per-operator G/T, in-situ antenna efficiency, 3GPP R17 module certification. Current paper verdicts: LEO +37.8 dB (yes), GEO L-band n255 +5.6/+2.6 dB (marginal-yes), GEO S-band not claimed.

### Research tracks (standing — never product promises)
- **Volumetric holography:** gap recomputed upward to ~1000× (938 traps, ~192 W) with an **eye-safety hard blocker** (Class 3B/4). Research only — never the product layer.
- **6G service:** antennas are designable; the service does not exist to invent.

## Open items register (the honest list)

The full register lives at [`docs/freeze-v2/OPEN_ITEMS_v2_0.md`](docs/freeze-v2/OPEN_ITEMS_v2_0.md) — 16 items, each naming what would close it:

1. F5 hardware validation (gates the firmware merge) · 2. v2.1 → ship merge (gated step) · 3. Panel roll-cycle rating · 4. Cap-window RF: full-wave sim + VNA coupon · 5. Physical bench results (parked — see M1) · 6. Volumetric holography + eye safety · 7. 6G service · 8. Tablet film wear + drum-2 FPC fatigue · 9. Satellite G/T + in-situ efficiency + R17 cert · 10. Graphite-ply coupling near keep-outs (in-situ) · 11. TIM + clamp design for R_c1 · 12. CFRP layup detail · 13. Projector module firmware + bay ID assignment (MOD_PROJECTOR ID reserved) · 14. OS desktop UX findings U-1, U-3–U-6 · 15. Neural module exact silicon (Coral-class proxies; exact part assumption-labelled) · 16. Light-field eye-tracking bench test.

## How progress lands

Milestones close when their evidence lands in `docs/` with the house-rule receipts (checker outputs, compile logs, calculations). See [CONTRIBUTING.md](CONTRIBUTING.md).
