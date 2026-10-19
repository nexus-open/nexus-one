# B6 — RF WINDOW STUDY (cap-window transparency, graphite keep-outs, satellite link)

**Status:** SIMULATION FROM PUBLISHED MATERIAL CONSTANTS — not a bench measurement.
**Evidence:** `rf_calc_b6.py` (runnable), `rf_calc_b6_stdout.txt` (verbatim run).
**Depends on:** v2.0 satellite design point (`DESIGN_v2_0/modules/modules_report.md` §3:
MT6825-class, n255/n256, 23 dBm TX + 3 dBi patch → EIRP 26 dBm; GEO FSPL 187.8 dB;
R17 IoT-NTN −13 dB SNR operating point @180 kHz, 128x reps);
v2.1 thermal config (c) graphite-ply flag (`DESIGN_v2_1/thermal/thermal_model_v2.md`).

## 1. Verdicts

| Band | Wall IL (2.0 mm PC/ABS) | Verdict |
|---|---|---|
| NTN n255 L-band UL 1640 MHz | 0.014–0.032 dB | **Link: MARGINAL-YES** (see §4) |
| NTN n256 S-band UL ~2000 MHz | 0.020–0.044 dB | **Link: MARGINAL** (see §4) |
| BLE 2.4 GHz (on-board control) | 0.05 dB (nom) | **No impact** — +32.8 dB margin at 10 m |
| Wi-Fi-class 5 GHz (forward) | 0.11–0.21 dB | **No on-board radio in v1.0/v2.0**; negligible if added |

Bottom line on the windows: **a 2.0 mm PC/ABS cap is essentially transparent
(≤0.05 dB) at every band of interest.** The frozen v1.0 choice of polymer RF
windows is confirmed on paper — and the reason is physics: the wall is ~0.02
wavelengths thick, so the two interface reflections nearly cancel (coherent
Airy-slab calculation; the incoherent worst case is still <0.3 dB).

## 2. Graphite ply (v2.1 thermal config c) — RF coupling

Published Panasonic PGS: σ = 1.0e6 S/m (standard), 2.0e6 S/m (thin grades),
thickness 10–100 µm. At these conductivities a 25–50 µm ply is 60–150 skin
depths at L-band and presents 0.01–0.04 Ω/sq:

| Grade | t | Skin depth @1.6 GHz | SE (normal incidence) |
|---|---|---|---|
| std (1e6 S/m) | 25 µm | 12.5 µm | **73.5 dB** |
| std (1e6 S/m) | 50 µm | 12.5 µm | **79.5 dB** |
| thin (2e6 S/m) | 25 µm | 8.8 µm | **79.5 dB** |
| thin (2e6 S/m) | 50 µm | 8.8 µm | **85.5 dB** |

**Any graphite ply in an antenna near-field path is an opaque reflector
(73–86 dB block).** If Hari picks thermal config (c), the keep-outs below are
mandatory — this closes the RF-coupling flag raised in `thermal_model_v2.md`.

## 3. Detuning risk — cap-window antenna

Antenna per v2.0 design: 25×25×4 mm ceramic RHCP patch behind the 2.0 mm cap.
A high-ε ceramic substrate dominates the stored field, so the thin PC
superstrate pulls f_res down only an estimated −1…−5% (vs −10…−20% for a
low-ε patch). **Rule: the antenna is tuned with the 2.0 mm cap present
(in-situ tune).** Budgeted until measured: 0.5 dB untuned / 0.2 dB tuned
penalty. RHCP axial-ratio impact: second order (<0.3 dB) with a symmetric
window. Exact pull needs a full-wave solver (HFSS/CST class) → NOT-VERIFIED.

## 4. Satellite link budgets (design point + window debits)

EIRP 26 dBm − 0.05 dB (wall) − 0.2 dB (tuned detune) = 25.75 dBm.
Misc: 0.5 dB atmosphere + 0.5 dB polarization + 1.5 dB hand/body.
Required C/N0 = −13 dB + 10log10(180 kHz) − 10log10(128 reps) = 18.5 dBHz.

| Path | C/N0 rx | Margin (nominal) | Margin (bounded) |
|---|---|---|---|
| GEO L-band n255 (design point) | 24.1 dBHz | **+5.6 dB** | +2.6…+10.6 dB |
| GEO S-band n256 | 22.4 dBHz | **+3.9 dB** | +0.9…+8.9 dB |
| LEO 550 km L-band (16 reps) | 65.3 dBHz | **+37.8 dB** | +33.8…+41.8 dB |

The cap wall is **not** the link-killer (0.03–0.05 dB). The margin hinges on
satellite G/T (−10 dB/K nominal, bounded −12…−6 — the dominant uncertainty)
and in-situ antenna efficiency with hand/body loading. S-band's pessimistic
floor (+0.9 dB) sits below a 3 dB implementation reserve — **not claimed
without a better-G/T operator or measured efficiency.**

**DECISIVE LINE:** the satellite module's cap-window antenna closes its link
budget on paper at **LEO-class with +37.8 dB (YES)**; at the **GEO design
point it is MARGINAL-YES on L-band (+5.6 dB nominal, +2.6 dB pessimistic
floor)** and **MARGINAL on S-band (+3.9 dB nominal, +0.9 dB floor — not
claimed)**. The window itself is transparent; graphite anywhere near the
window is a total block.

## 5. Antenna placement rules — satellite module

1. **Window:** RHCP patch boresight normal to the cap outer surface; polymer
   window must clear the antenna footprint by ≥1.5× in all directions
   (no Ti rail, shield, or copper crossing the aperture).
2. **Keep-outs (conductor ≥1 Ω/sq, incl. graphite ply):** radius **≥25 mm**
   around the NTN patch center (≈λ/8 @1.6 GHz, λ=184 mm); **≥15 mm** around
   the BLE antenna (≈λ/8 @2.44 GHz). If config (c) is chosen, the graphite
   ply terminates outside these radii or carries a ≥50×50 mm cut-out.
3. **Ground:** patch sits on a contiguous ≥40×40 mm ground area on the module
   PCB for stable axial ratio; module ground ties to spine ground at one
   point only (no loops through the window).
4. **Tune loaded:** final antenna match is done with the production 2.0 mm
   cap fitted; free-space tune is invalid by rule.
5. **Orientation:** cap window faces sky in open mode (top/tail cap per v2.0
   module layout); the satellite module is TX-gated to open mode only
   (frozen v2.0 rule — folded = PSM sleep, RX-only).

## 6. ASSUMPTION / NOT-VERIFIED register

- **A1.** Exact PC/ABS blend constants unpublished → bounded by PC (S1) and
  ABS (S2) endpoints: εr 2.5–3.0, tanδ 0.005–0.02. Nominal (2.9, 0.01).
- **A2.** Plane-wave normal-incidence slab model for wall IL; oblique/near-
  field deviations are second order at these thicknesses.
- **A3.** Satellite G/T: −10 dB/K GEO (bounded −12…−6), −5 dB/K LEO (bounded
  −8…−2). Dominant margin uncertainty — operator data needed.
- **A4.** Hand/body/polarization/atmosphere = 2.5 dB total; in-situ antenna
  efficiency folded in at 0.2 dB tuned penalty.
- **A5.** S-band uses the same 3 dBi radiator assumption as L-band (dual-band
  patch or second element — module design detail).
- **N1.** No bench measurement exists: no VNA coupon test of the actual cap
  plastic, no in-situ antenna tune, no anechoic efficiency.
- **N2.** No full-wave (HFSS/CST) model of patch + cap + hand — detuning and
  axial ratio are estimated, not simulated.
- **N3.** Per-operator G/T, EIRP-density regulatory masks, and 3GPP R17
  module certification remain unverified (carried from v2.0).
- **N4.** BLE antenna placement "adjacent to cap window" per v1.0 RF-window
  intent; exact board antenna not re-extracted here.

## 7. Sources

- [S1] Curbell Plastics, *Plastics for High-Performance Radomes* (GHz table):
  PC εr 2.90@2.5 GHz / 2.74@2.44 GHz / 2.96@5 GHz; tanδ 0.005@2.5 / 0.0051@2.44 / 0.006@5 GHz.
  <https://www.curbellplastics.com/wp-content/uploads/2022/11/Plastics-for-High-Performance-Radomes-White-Paper.pdf>
- [S2] PMC11314315 (peer-reviewed): pure ABS εr′ 2.48, εr″ 0.085–0.115 @8–12 GHz
  → tanδ 0.034–0.046 (X-band upper bound). <https://pmc.ncbi.nlm.nih.gov/articles/PMC11314315/>
- [S3] Panasonic PGS datasheet: ab-plane σ = 10,000 S/cm = 1.0e6 S/m (std),
  20,000 S/cm = 2.0e6 S/m (thin); 10–100 µm.
  <https://industrial.panasonic.com/cdbs/www-data/pdf/AYA0000/AYA0000C59.pdf>
- [S4] v2.0 satellite link design point: `DESIGN_v2_0/modules/modules_report.md` §3.
- [S5] v2.1 thermal config (c) + RF flag: `DESIGN_v2_1/thermal/thermal_model_v2.md`.
- [S6] Cap wall 2.0 mm class: v0.3, per `ARCHIVE_v1_7/00_START_HERE/MASTER_INDEX.md`.
