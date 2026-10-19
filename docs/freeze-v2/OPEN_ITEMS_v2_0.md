# NEXUS ONE — Open items register v2.0 (carried NOT-VERIFIED)

Every item below is carried openly from the v1.0 record plus the v2.0/v2.1 findings. None blocks the freeze; each names what would close it.

1. **F5 hardware validation — GATES the firmware merge and the bonding claim.** NimBLE 2.x auto-creates the CCCD with no API for encrypted-only ATT permissions; the v2.1 compensating control (notify only on bonded+encrypted links) is software only. The CCCD subscribe behaviour with an unbonded client must be observed on hardware before the bonded-command claim ships. Also gates merging the v2.1 security branch into ship firmware. (DESIGN_v2_1/firmware/)
2. **v2.1 → ship firmware merge (gated step).** All 5 Highs fixed in a v2.1 copy (F1–F4, F13; F5 partial); frozen v1.6/v1.7 spine untouched by design. Merge = separate gated step after F5 validation + rev-2 board. ADC marginality note: 47 kΩ/68 kΩ ID nominals sit ~2.7% from thresholds — the error budget must stay under ±2%.
3. **Maker panel dynamic roll-cycle rating.** Real 6.67″ flexible AMOLED class exists; datasheets do not publish dynamic roll ratings. Closes only with a maker datasheet or a dynamic-rated panel.
4. **Cap-window RF confirmation.** B6 (simulation from bounded material constants) says the window is transparent (0.014–0.032 dB L-band) — still needed: full-wave sim (HFSS/CST class) and a VNA coupon test of the actual cap plastic; in-situ antenna tune with the cap fitted.
5. **Any physical bench result — parked.** Digital-only mandate; bench plan B1–B6 remains reference only.
6. **Volumetric holography (~1000×) + eye-safety.** Gap recomputed UP: 938 traps, ~192 W wall-plug, Class 3B/4 blocker. Research track only — never the product layer.
7. **6G service.** Antennas designable; the service does not exist to invent. Research line.
8. **Tablet film wear + drum-2 FPC fatigue.** The tablet checker passes geometry; wear/fatigue life is unmeasured.
9. **Satellite: per-operator G/T, in-situ antenna efficiency, R17 module certification.** Link verdicts (LEO +37.8 dB YES; GEO L-band n255 +5.6/+2.6 marginal-YES; S-band not claimed) hinge on G/T −10 dB/K nominal (bounded −12…−6) — operator data needed.
10. **Graphite-ply coupling near keep-outs (in-situ).** The ≥25 mm (NTN) / ≥15 mm (BLE) / ≥50×50 mm cut-out rules are layout law from B6; in-device coupling is not simulated beyond the slab model.
11. **TIM + clamp design for R_c1 (thermal).** R_gap is calibration-classified; the chassis thermal-strap SoC→bay-rail path is carried from v2.0.
12. **CFRP layup detail + Al-spreader packaging fit.** Moot for the frozen (c) config (graphite ply is inside the layup, no separate spreader), recorded so the dropped (b) config is not silently revived.
13. **Projector module firmware + bay ID.** AirScreen bay module designed (6.4 W); MOD_PROJECTOR ID resistor unassigned; firmware sketch pending.
14. **OS desktop UX findings U-1, U-3–U-6.** Open from the v2.0 desktop-mode check (U-2 fixed).
15. **Neural module exact silicon.** Coral-class proxies used; exact part ASSUMPTION-labelled.
16. **Light-field eye-tracking not physically tested.** v2 spec (25.6 ms eye-to-photon, 0.70 W) is a design; no bench.
