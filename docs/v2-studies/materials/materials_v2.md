# NEXUS ONE v2.0 — MATERIALS STUDY (premium materials, honest RF constraints)

Workstream: MATERIALS v2 · 2026-10-19 · DIGITAL-ONLY · no physical work performed.

Frozen v1.0 reference: stick 183.9×34×22 mm, 241 g total (v1.0 mass budget), drum POM,
end caps PC/ABS (RF WINDOWS — antennas behind them), thermal law ≤2 W folded.
Part dimensions from `ARCHIVE_v1_7/03_freeze_v1_0/V1_0_FREEZE/bom/BOM.csv` (52 items).

Poster demands mapped: titanium alloy rails/frame (Grade 5), carbon-fibre back panel,
ceramic-glass accents, end caps STAY polymer (RF, non-negotiable — §3).

---

## 1. Mass delta study

Script: `mass_calc.py` (runs with `python3 mass_calc.py`). Geometry is modelled from
BOM specs with explicit ASSUMPTION tags (wall thickness 1.5 mm, cap fill fraction 35%,
drum bore R5, dovetail +15% profile). Densities are standard published material data:
Ti-6Al-4V 4.43 g/cm³ (MatWeb/AMS 4911) · CFRP quasi-isotropic 1.6 g/cm³ (Hexcel 8552 class) ·
6061-T6 Al 2.70 · PC/ABS 1.15 (Bayblend T65 class) · POM 1.41 (Delrin 100) ·
alumina 3.90 g/cm³ (sintered Al₂O₃).

The delta applies ONLY to structural parts; the rest of the 241 g (battery, panel,
PCBs, magnets, wiring, modules) is carried over unchanged.

### 1.1 Calculator output (verbatim stdout)

```
==============================================================================
NEXUS ONE v2.0 MATERIALS STUDY — mass delta (structural parts only)
==============================================================================
Part                                           v1 [g]   v2 [g]  delta [g]
------------------------------------------------------------------------------
S01 Spine back shell (v1: 6061 Al / v2: CFRP)    23.38    13.85      -9.52
S01 PC antenna inserts x2 (both versions)        0.83     0.83      +0.00
M08 Guide rails x2 (v1: 6061 Al / v2: Ti64)     11.92    19.55      +7.64
B01 Module rail dovetail (v1: 6061 Al / v2: Ti64)    26.83    44.02     +17.19
S04 Spine tray (PC/ABS, both versions)          11.42    11.42      +0.00
M01 Drum (POM, both versions)                   28.14    28.14      +0.00
M04 Leading bar (6061 Al, both versions)         7.24     7.24      +0.00
S02 Tail end cap 16x34x22 (PC/ABS, both)         4.82     4.82      +0.00
S03 Head end cap 8x34x22 (PC/ABS, both)          2.41     2.41      +0.00
ACC Ceramic accents 2x 60x10x1 (v2 only, NEW)     0.00     4.68      +4.68
------------------------------------------------------------------------------
STRUCTURAL SUBTOTAL                            116.98   136.96     +19.98

Frozen v1.0 device total (baseline) :    241.0 g
Structural-part mass delta (v2-v1)   :   +19.98 g
Projected v2.0 device total         :    261.0 g
Delta vs 241 g baseline             : +19.98 g  (+8.3 %)

Largest contributors:
  B01 Module rail dovetail (v1: 6061 Al / v2: Ti64)  +17.19 g
  S01 Spine back shell (v1: 6061 Al / v2: CFRP)   -9.52 g
  M08 Guide rails x2 (v1: 6061 Al / v2: Ti64)    +7.64 g
  ACC Ceramic accents 2x 60x10x1 (v2 only, NEW)   +4.68 g

Note: end caps (S02/S03) and drum (M01) are UNCHANGED by design
(RF windows + low-friction roll surface). Ceramic accents are v2-only adds.
==============================================================================
```

### 1.2 Result

- **Mass delta: +20.0 g → projected v2.0 total 261.0 g, +8.3 % over the 241 g v1.0 budget.**
- The headline: titanium is ~64% denser than aluminium, so at *identical section
  geometry* the Ti rails/frame cost +24.8 g while the CFRP shell only gives back −9.5 g.
  The posters' "titanium rails" demand is therefore a **net mass increase** unless
  sections are thinned.
- Honest recovery path (NOT a design change, noted for WS-lead review): Ti-6Al-4V
  yield (~880 MPa) is ~3.2× 6061-T6 (~276 MPa). Thinning the Ti rails/dovetail to
  ~60% section volume recovers near-parity (0.6 × 63.57 g ≈ 38.1 g vs Al 38.75 g)
  *at equal static strength* — but fatigue/dovetail contact-stress must be checked
  before claiming it, so it is NOT baked into the v2 number. Status: GAP + route.

---

## 2. Stiffness sanity — specific stiffness of the unroll-load path

No FEA; material indices only. The parts that carry the unroll loads are the
M08 guide rails and the B01/S01 spine frame. Specific stiffness = E/ρ (×10⁶ m²/s²).

| Material | E (GPa) | ρ (g/cm³) | E/ρ (×10⁶ m²/s²) | Role in v2 |
|---|---|---|---|---|
| Ti-6Al-4V (Grade 5) | 114 | 4.43 | **25.7** | rails M08, module rail B01 (v2) |
| CFRP quasi-isotropic laminate | 70 | 1.60 | **43.8** | spine back shell S01 (v2) |
| 6061-T6 aluminium | 68.9 | 2.70 | **25.5** | rails M08, rail B01, shell S01 (v1) |
| PA66-GF30 (ref.) | 9 | 1.37 | 6.6 | — (not used) |
| PC/ABS | 2.3 | 1.15 | 2.0 | end caps (both) |
| POM | 3.1 | 1.41 | 2.2 | drum (both) |
| Alumina (ref.) | 370 | 3.90 | 94.9 | accents only — brittle, non-structural |

Headline: **Ti buys no specific stiffness over aluminium (25.7 vs 25.5 — a wash);
it buys strength, wear, and premium feel.** The real stiffness win is the
**CFRP shell: +71% specific stiffness over the Al shell**, which is the part that
backs the whole unroll spine. Conclusion: the v2 stack is stiffness-neutral on the
rails (no FEA needed to say this) and stiffer on the shell — the mass penalty in
§1 is paying for durability/finish, not stiffness.

---

## 3. RF constraint — end caps STAY polymer (non-negotiable)

The S02 tail cap and S03 head cap stay PC/ABS mouldings in v2 — no titanium, no
carbon, no ceramic shell over them. The physics is Faraday shielding: a conductive
enclosure (Ti, Al, or CFRP, whose in-plane conductivity is high enough to matter)
surrounding the BLE/Wi-Fi front-end and the satellite module's NTN antenna behaves
as a closed conductive box; at 2.4 GHz the skin depth in titanium/aluminium is on
the order of a few microns, so a 1.5 mm metal cap attenuates the radiated field by
many tens of dB — effectively a dead radio. The antenna elements (chip-antenna
class, 10×5 mm keep-outs per W06) live behind the end caps precisely because
polymer is RF-transparent at these bands: its loss tangent is low and it presents
no conductive boundary for the fields to terminate on. Putting metal or carbon
over the caps would require external antenna apertures or re-entrant cutouts that
break the poster design language anyway. The two 30×8 mm PC inserts in the S01
spine shell serve the same role for the spine-side keep-outs and are retained in
the CFRP v2 shell for the same reason. **Rule: any v2 part that sits over an
antenna keep-out is polymer, full stop.**

---

## 4. Thermal note — titanium's conductivity vs the folded heat path

Per v0.4 the folded stick's shell is the heat path: with the panel rolled in,
there is no airflow and the device sheds its folded dissipation through the
spine shell to the hand/air. 6061 aluminium conducts at ~167 W/m·K; Ti-6Al-4V
conducts at ~6.7 W/m·K — roughly **25× worse** — and the CFRP shell is little
better (in-plane ~5–10, through-thickness ~1 W/m·K). Order of magnitude: if the
v1.0 shell path presented ~5 K/W, the v2 Ti/CFRP shell path presents on the order
of 50–125 K/W; at the frozen 2 W folded law that would imply a 100–250 K
temperature rise — physically impossible in a hand-held device, meaning the
*effective* path would bottleneck at the shell and the internals would cook.
Conclusion: **the 2 W folded law does not survive the premium-materials stack as
drawn.** It needs revisiting via one (or more) of: (a) a retained internal
aluminium/copper heat spreader under the CFRP shell (adds mass back, honest
trade); (b) a graphite spreader layer in the shell layup (in-plane ~400 W/m·K
class, keeps the CFRP cosmetic); or (c) lowering the folded budget toward the
Pocket-Mode 0.9 W envelope already in the v1.0 OS spec. Recommended: (b) +
quantify with a 1-D thermal-resistance model before any v2 freeze. Status: GAP.

---

## 5. NOT-VERIFIED remainder (materials workstream)

1. CFRP shell layup, ply count, and through-thickness conductivity — ASSUMED quasi-isotropic 1.6 g/cm³ / 70 GPa.
2. Ti rail/dovetail section thinning to recover mass parity — strength-equivalent only; fatigue and dovetail contact stress unverified.
3. Ceramic accent attachment (adhesive vs co-mould) and drop survivability of 1 mm alumina trim — unverified.
4. Folded thermal model with v2 materials (1-D resistance network) — not built; 2 W law flagged for revision.
5. Galvanic isolation between Ti rails and Al/CFRP neighbours (Ti is noble; dissimilar-metal corrosion at the dovetail) — noted, not designed.
6. Antenna detuning by the CFRP shell near the 30×8 mm PC inserts — keep-outs retained by design; coupling unverified.
7. All wall-thickness / fill-fraction geometry ASSUMPTIONS in `mass_calc.py` — honest estimates from BOM text, not measured parts.
