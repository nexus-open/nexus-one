# NEXUS ONE v2.1 — B8 v2 THERMAL MODEL (Workstream A)

2026-10-19 · DIGITAL-ONLY · real physics · script: `thermal_calc_v2.py`
(python3, stdlib only) · raw evidence: `thermal_calc_v2_stdout.txt`
Read-only reference: `DESIGN_v2_0/materials/materials_v2.md` §4,
`DESIGN_v2_0/modules/thermal_calc.py` + `modules_report.md` §2.

## 0. Method (the v2.0 cooling workstream's discipline, copied)

1. Re-derive the frozen v1 baseline FIRST and show the model reproduces it.
2. Only then extend it — changing ONLY the shell-material terms.
3. Every non-datasheet input is ASSUMPTION-labelled. The one unmeasurable
   interior bundle (R_gap) is calibrated ONCE against the frozen 8.8 K/W
   and then FIXED for all v2 configurations.

## 1. Resistance network

Heat injected at the die junction; series 1-D path to ambient:

```
Tj --R_jc--> case --R_TIM--> tray --R_gap--> [spreader] --R_c1--> shell inner
   --R_spread (lateral spreading in shell/spreader plate)-->
   --R_thr (through-thickness conduction)--> skin --R_skin_air--> Tamb
```

- R_spread = ln(R_shell/R_src) / (2π·Σk·t): radial spreading in a thin
  plate stack from a point source (standard thin-plate approximation,
  t ≪ r). Parallel conductive layers sum as Σk·t.
- R_thr = Σ t/(k·A_spine_back): 1-D through-wall conduction.
- R_skin_air = 1/((h_conv + h_rad)·A_eff): natural convection in parallel
  with radiation. h_rad = ε·σ·(T1+T2)·(T1²+T2²), linearised at skin 43 °C.
- Cap convention (frozen v0.4/v1.2): P_cap = (43 − Tamb)/R_total_die_to_air.
  This is CONSERVATIVE — it applies the 43 °C skin limit against the full
  stack including junction/TIM/interior terms. Skin-hotspot-only caps would
  be ~15–25% higher and are NOT claimed.

## 2. Parameters table

| # | Parameter | Value | Source |
|---|---|---|---|
| 1 | Skin limit 43 °C; ambients 25 / 35 °C | frozen | v1.0 law / v1.2 pocket study |
| 2 | Folded Rth v1 = 8.8 K/W; laws 2 / 1.5 / 3 W | frozen | v0.4 model, v1.2 report |
| 3 | Device 183.9×34×22 mm; A_outer = 221 cm² | measured dims | v1.0 freeze BOM |
| 4 | 6061 Al k=167; Ti-6Al-4V k=6.7 | datasheet class | materials_v2.md §1 |
| 5 | CFRP k_in=7 (band 5–10), k_thr=1 | ASSUMPTION | materials_v2.md §4 |
| 6 | Graphite ply k_in=400, t=0.1 mm | datasheet class (PGS) | — |
| 7 | Wall t=1.5 mm; spreader Al t=0.8 mm | ASSUMPTION | mass-study ASSUMPTIONs |
| 8 | R_jc=0.8 K/W (SoC BGA class) | ASSUMPTION | — |
| 9 | R_TIM=0.30 K/W (0.2 mm, k=3, 15×15 mm pad) | computed | datasheet-class TIM |
| 10 | Source radius 10 mm; shell equiv. radius 92 mm | ASSUMPTION | geometry estimate |
| 11 | h_conv: 6 folded (stagnant pocket) / 10 open (free air) | ASSUMPTION | textbook 5–10 band (Incropera) |
| 12 | Pocket area factor 0.7 (30% blanketed) | ASSUMPTION | — |
| 13 | Emissivity: Al anodized 0.8 / CFRP 0.9 | ASSUMPTION | class values |
| 14 | R_gap = 0.55 K/W interior bundle | CALIBRATED | closes v1 to frozen 8.8 |
| 15 | R_c1 = 0.5 K/W spreader→shell TIM+clamp (config b) | ASSUMPTION | dominant-term sensitivity §6 |
| 16 | Batt module: 1.0 W self-heat, κ=0.5 coupled | ASSUMPTION | calibrated to v1 1.5 W law |
| 17 | Cooling path R_mod = 2.5 + 1.16 = 3.66 K/W | v2.0 frozen | modules/thermal_calc.py |
| 18 | v2 device mass 261 g (before spreader) | computed | materials mass study |

Checked and excluded: Ti rail axial conduction (2 rails, 12 mm² each,
1144 K/W — negligible vs shell spreading); POM drum (k≈0.3 — negligible);
ceramic accents (cosmetic, negligible area).

## 3. v1 baseline reproduction (the gate)

| Check | Model | Frozen | Verdict |
|---|---|---|---|
| Folded cap @25 °C | 2.045 W | 2.0 W law | MATCH |
| Folded cap @35 °C | 0.909 W | 0.91 W (v1.2) | MATCH |
| Folded+batt @25 °C | 1.55 W | 1.5 W law | MATCH |
| Open cap @25 °C | 2.99 W | 3.0 W law | MATCH |
| v1 folded layer sum | 8.800 K/W | 8.8 K/W | MATCH |

v1 folded decomposition (K/W): R_jc 0.80 + R_TIM 0.30 + R_spread(Al) 1.41 +
R_thr(Al) 0.001 + R_skin_air 5.74 + R_gap 0.55 (calibrated) = 8.80.
Note the v1.0 shell path (spreading + skin_air ≈ 7.2 K/W) is the same order
as the "≈5 K/W" order-of-magnitude in materials_v2.md §4 — consistent.

## 4. Configuration results

### (a) v2 Ti/CFRP as drawn — 261.0 g
Folded Rth = 40.95 K/W, dominated by R_spread = 33.64 K/W (CFRP k_in=7 vs
Al 167 — the 25× conductivity collapse materials §4 warned about,
quantified). Caps: **0.44 W @25 °C / 0.20 W @35 °C** folded;
0.47 / 0.21 W open. k-band sweep: even optimistic k_in=10 gives 0.58 W.
**The 2 W folded law is dead on this stack by ~4.5×.**

### (b) Hybrid: 0.8 mm 6061 Al spreader under CFRP — 274.5 g (+13.5 g)
Spreader→shell contact R_c1 = 0.5 K/W (TIM + clamp). Folded Rth = 10.26 K/W
(R_spread 2.45, R_skin_air 5.42 — note: the pocket skin_air term is now the
dominant residual; internal improvements have diminishing returns past this
point). Caps: **1.75 W @25 °C / 0.79 W @35 °C** folded; 2.34 / 1.05 W open;
1.25 / 0.29 W folded+batt. Cu-spreader alternative rejected with numbers:
+44.8 g for only −1.3 K/W → 305.8 g total, bad trade.

### (c) Graphite spreader ply in CFRP layup — 261.3 g (+0.3 g net)
0.1 mm PGS-class ply (k_in=400) replacing one CFRP ply. Folded Rth = 14.39
K/W (R_spread 7.09). Caps: **1.25 W @25 °C / 0.56 W @35 °C** folded;
1.52 / 0.68 W open; 0.75 / 0.06 W folded+batt. Mass cost is ~zero, but the
ply is conductive — RF keep-out coupling near the antenna windows is
NOT-VERIFIED.

### (d) Pocket-Mode 0.9 W envelope (v1.0 OS spec)
| Stack | Folded @25 °C | Folded @35 °C | 0.9 W verdict |
|---|---|---|---|
| (a) | 0.44 W | 0.20 W | DEAD everywhere |
| (b) | 1.75 W | 0.79 W | LEGAL @25 (1.9× margin); dead hot-day |
| (c) | 1.25 W | 0.56 W | LEGAL @25 (1.4× margin); dead hot-day |

Pocket-Mode 0.9 W is legal folded at 25 °C on (b) and (c) only, and dead on
ALL stacks folded at 35 °C hot-day — a hot-day pocket derate (~0.5 W) or the
cooling path is required.

### (e) Cooling-module-standard: bay path (3.66 K/W) as v2 folded baseline
Parallel with each chassis folded path:

| Stack | Rth folded | Cap @25 °C | Cap @35 °C | 2 W law |
|---|---|---|---|---|
| (a) | 3.36 K/W | 5.36 W | 2.38 W | LEGAL |
| (b) | 2.70 K/W | 6.68 W | 2.98 W | LEGAL |
| (c) | 2.92 K/W | 6.17 W | 2.75 W | LEGAL |
| (v1 ref) | 2.58 K/W | 6.97 W | 3.11 W | LEGAL (reproduces v2.0) |

The 2 W folded law survives ONLY as cooling-module-gated. Caveat: the
R_contact 2.5 K/W ASSUMPTION was made against an Al bay rail; the v2 rail
is Ti-6Al-4V and rail-side spreading at the module clamp is NOT in this
number. The chassis thermal strap (SoC heat → bay rail) remains
NOT-VERIFIED, carried from the v2.0 modules report.

### (f) Mode-dependent legal caps (W)

| Stack | fold@25 | fold@35 | open@25 | open@35 | batt@25 | batt@35 |
|---|---|---|---|---|---|---|
| v1 (ref) | 2.05 | 0.92 | 2.99 | 1.34 | 1.55 | 0.42 |
| (a) Ti/CFRP | 0.44 | 0.20 | 0.47 | 0.21 | 0.00 | 0.00 |
| (b) Al spreader | 1.75 | 0.79 | 2.34 | 1.05 | 1.25 | 0.29 |
| (c) graphite | 1.25 | 0.56 | 1.52 | 0.68 | 0.75 | 0.06 |

The open-mode 3 W law is dead on all passive v2 stacks (best: (b) 2.34 W).
The folded+batt 1.5 W law is dead on all passive v2 stacks (best: (b)
1.25 W). Open-mode caps do NOT credit the unrolled panel-back heat path —
NOT-VERIFIED, potentially favourable.

## 5. Dominant-term sensitivity (config b, folded cap @25 °C, baseline 1.75 W)

- R_c1 (spreader→shell contact): 0.2 → 1.81 W; 0.5 → 1.75 W; 1.0 → 1.67 W.
  The contact is a first-order term — it demands a real TIM + clamp-force
  design, exactly as the v2.0 cooling model flagged for its own contact.
- R_gap (interior bundle): 0.2 → 1.82 W; 0.55 → 1.75 W; 1.0 → 1.68 W.
- h_conv folded: 5 → 1.67 W; 6 → 1.75 W; 8 → 1.90 W (non-dominant for (b)).
- k_cfrp_in band on (a): 5 → 0.33 W; 7 → 0.44 W; 10 → 0.58 W —
  (a) is dead across the whole plausible band.

## 6. VERDICT — which shell configurations are legal at which power caps

**NO configuration keeps the 2 W folded law passively.** Highest legal
passive folded caps: (b) **1.75 W** @25 °C / 0.79 W @35 °C · (c) **1.25 W**
@25 / 0.56 W @35 · (a) **0.44 W** @25 / 0.20 W @35.

Decisive outcomes:
1. **(a) as drawn is thermally non-viable** — 0.44 W folded @25 °C,
   0.47 W open. It fails every frozen law (2 W folded, 3 W open,
   1.5 W batt, 0.9 W pocket). Do not freeze v2 on this stack.
2. **(b) hybrid Al spreader** is the highest passive cap (1.75 W folded
   @25 °C) and the only stack legal at the 0.9 W Pocket-Mode envelope with
   ~1.9× margin — at +13.5 g (274.5 g total) and a packaging-fit check
   still owed (0.8 mm plate inside the 22 mm stack).
3. **(c) graphite ply** clears 0.9 W folded @25 °C (1.4× margin) at ~zero
   mass cost (261.3 g) — the mass-efficient route — but needs RF
   keep-out verification for the conductive ply near antenna windows.
4. **The 2 W folded law survives only as cooling-module-gated (e)**:
   5.4–6.7 W folded @25 °C on every stack. This is the route back to 2 W,
   but it requires the module present (bay-ID-gated cap raise in the spine
   firmware) plus the NOT-VERIFIED chassis thermal strap.
5. **Hot-day (35 °C) folded kills 0.9 W on every passive stack**
   (best 0.79 W on (b)) — the v2 folded law needs a hot-day derate
   (~0.5 W on (c), ~0.75 W on (b)) or cooling-module gating.
6. **Recommended v2 thermal law**: folded ≤ 0.9 W (Pocket-Mode envelope)
   on stack (b) or (c) at 25 °C ambient; 2 W folded ONLY with cooling
   module docked; open-mode cap per-stack (2.3 / 1.5 W) until the
   panel-back path is quantified.

## 7. NOT-VERIFIED remainder (this workstream)

1. R_gap = 0.55 K/W interior bundle — calibrated, not measured; bundles
   tray polymer, air gaps, clamp contacts.
2. Spreading geometry (10 mm source radius, 92 mm shell radius) —
   ASSUMPTION, not from a layout.
3. h_conv 6/10, pocket area factor 0.7, emissivities 0.8/0.9 — textbook/
   class values, not measured on this device.
4. R_c1 = 0.5 K/W spreader→shell contact — needs a TIM + clamp-force
   design (dominant term per §5).
5. Al spreader packaging fit (0.8 mm plate in the 22 mm stack) — not checked.
6. Graphite ply RF coupling near the PC antenna keep-outs — unverified.
7. CFRP layup / through-thickness k — ASSUMED (carried from materials §5.1).
8. Cooling path: Ti-rail-side spreading at the module clamp not modelled;
   chassis thermal strap SoC→bay-rail NOT-VERIFIED (carried from v2.0).
9. Open-mode panel-back heat path — not credited; could raise open caps.
10. Battery-module self-heat 1.0 W / κ = 0.5 — ASSUMPTION calibrated to
    the v1 law, not measured.
11. Galvanic isolation Al-spreader↔Ti/CFRP (config b) — noted in
    materials §5.5, not designed.
12. Skin-limit convention: caps use full die-to-air Rth (frozen
    convention, conservative); a skin-hotspot-only convention would raise
    caps ~15–25% — not claimed without a hotspot measurement.
