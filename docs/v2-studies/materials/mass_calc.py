#!/usr/bin/env python3
"""
NEXUS ONE v2.0 — MATERIALS MASS DELTA STUDY (mass_calc.py)

Compares v1.0 structural-part masses (current materials: PC/ABS, POM, 6061 Al)
against the v2 premium-materials stack (Ti-6Al-4V rails/frame, CFRP back panel,
alumina-ceramic accents), using real densities and BOM v1.0 part dimensions.

Baseline: v1.0 device total = 241 g (DESIGN_FREEZE_v1_0.md, v0.6/v0.7 estimates).
The delta applies ONLY to the structural parts modelled here; the rest of the
241 g (battery, panel, PCBs, magnets, wiring, modules) is carried over unchanged.

Geometry is modelled from BOM specs in
  ARCHIVE_v1_7/03_freeze_v1_0/V1_0_FREEZE/bom/BOM.csv
with explicit ASSUMPTION tags where a dimension had to be estimated
(wall thickness, hollow fill fraction, bore diameter).

DENSITIES (standard material data, quoted as published reference values):
  - Ti-6Al-4V (Grade 5):        4.43 g/cm^3  (MatWeb / AMS 4911)
  - CFRP quasi-isotropic lam.:  1.60 g/cm^3  (Hexcel 8552 datasheet class)
  - 6061-T6 aluminium:          2.70 g/cm^3  (standard)
  - PC/ABS blend:               1.15 g/cm^3  (Bayblend T65 datasheet class)
  - POM (Delrin/acetal):        1.41 g/cm^3  (DuPont Delrin 100 datasheet)
  - Alumina ceramic (Al2O3):    3.90 g/cm^3  (standard sintered alumina)
"""

# ---------------------------------------------------------------- densities
RHO = {
    "Ti64":   4.43,   # Ti-6Al-4V Grade 5
    "CFRP":   1.60,   # carbon-fibre reinforced polymer, quasi-isotropic
    "Al6061": 2.70,   # 6061-T6 aluminium
    "PCABS":  1.15,   # polycarbonate / ABS blend
    "POM":    1.41,   # polyoxymethylene (Delrin)
    "AL2O3":  3.90,   # alumina ceramic (accents)
}

V10_TOTAL_G = 241.0  # frozen v1.0 device total, DESIGN_FREEZE_v1_0.md

# ------------------------------------------------------- part geometry (mm)
# Each entry: (v1 material, v2 material, volume_cm3, note)
# volume_cm3 is the net solid volume of the part in that material's share.
# PC antenna inserts inside S01 are modelled as a separate line item.

def mm3_to_cm3(v):
    return v / 1000.0

parts = {}

# S01 — Spine back shell: formed shell 183.9 x 34 x 1.5 mm (ASSUMPTION: wall t=1.5 mm),
#         minus 2x PC antenna insert cutouts 30 x 8 x 1.5 mm (from BOM spec).
_shell_gross = mm3_to_cm3(183.9 * 34.0 * 1.5)
_insert_vol  = mm3_to_cm3(2 * 30.0 * 8.0 * 1.5)
parts["S01 Spine back shell (v1: 6061 Al / v2: CFRP)"] = {
    "vol": _shell_gross - _insert_vol, "v1_mat": "Al6061", "v2_mat": "CFRP"}
parts["S01 PC antenna inserts x2 (both versions)"] = {
    "vol": _insert_vol, "v1_mat": "PCABS", "v2_mat": "PCABS"}  # unchanged: RF

# M08 — Guide rails (bar track) x2: 183.9 x 3 x 4 mm bars, in end caps (ASSUMPTION: section).
parts["M08 Guide rails x2 (v1: 6061 Al / v2: Ti64)"] = {
    "vol": mm3_to_cm3(2 * 183.9 * 3.0 * 4.0), "v1_mat": "Al6061", "v2_mat": "Ti64"}

# B01 — Module rail (dovetail) 120 x 24 back recess: plate 120 x 24 x 3 mm
#         + 15% extra for the dovetail profile (ASSUMPTION).
parts["B01 Module rail dovetail (v1: 6061 Al / v2: Ti64)"] = {
    "vol": mm3_to_cm3(120.0 * 24.0 * 3.0) * 1.15, "v1_mat": "Al6061", "v2_mat": "Ti64"}

# S04 — Spine tray: 4.5 mm deep tray behind drum. Modelled as base plate
#         162.9 x 30 x 1.5 mm + side walls (ASSUMPTION: wall t=1.5 mm).
#         v1 = PC/ABS per v1.0 polymer baseline; kept polymer in v2 (RF-neutral).
_tray = (mm3_to_cm3(162.9 * 30.0 * 1.5)
         + mm3_to_cm3(2 * 162.9 * 4.5 * 1.5)
         + mm3_to_cm3(2 * 30.0 * 4.5 * 1.5))
parts["S04 Spine tray (PC/ABS, both versions)"] = {
    "vol": _tray, "v1_mat": "PCABS", "v2_mat": "PCABS"}

# M01 — Drum: POM tube, R8 outer / R5 bore (ASSUMPTION: bore dia), length 162.9 mm span.
import math
_drum = math.pi * (8.0**2 - 5.0**2) * 162.9 / 1000.0
parts["M01 Drum (POM, both versions)"] = {
    "vol": _drum, "v1_mat": "POM", "v2_mat": "POM"}  # unchanged: low-friction roll surface

# M04 — Leading bar with rack: Al bar 74.5 x 6 x 6 mm (ASSUMPTION: section).
parts["M04 Leading bar (6061 Al, both versions)"] = {
    "vol": mm3_to_cm3(74.5 * 6.0 * 6.0), "v1_mat": "Al6061", "v2_mat": "Al6061"}

# S02 / S03 — End caps: PC/ABS mouldings, hollow, 35% fill (ASSUMPTION).
#   STAY POLYMER IN v2 — non-negotiable RF windows (see materials_v2.md section 3).
parts["S02 Tail end cap 16x34x22 (PC/ABS, both)"] = {
    "vol": mm3_to_cm3(16.0 * 34.0 * 22.0) * 0.35, "v1_mat": "PCABS", "v2_mat": "PCABS"}
parts["S03 Head end cap 8x34x22 (PC/ABS, both)"] = {
    "vol": mm3_to_cm3(8.0 * 34.0 * 22.0) * 0.35, "v1_mat": "PCABS", "v2_mat": "PCABS"}

# v2-only: alumina-ceramic accent trim strips on spine, 2x 60 x 10 x 1 mm.
parts["ACC Ceramic accents 2x 60x10x1 (v2 only, NEW)"] = {
    "vol": mm3_to_cm3(2 * 60.0 * 10.0 * 1.0), "v1_mat": None, "v2_mat": "AL2O3"}

# ------------------------------------------------------------------- report
def mass(vol_cm3, mat):
    return 0.0 if (vol_cm3 is None or mat is None) else vol_cm3 * RHO[mat]

def main():
    print("=" * 78)
    print("NEXUS ONE v2.0 MATERIALS STUDY — mass delta (structural parts only)")
    print("=" * 78)
    print(f"{'Part':44s} {'v1 [g]':>8s} {'v2 [g]':>8s} {'delta [g]':>10s}")
    print("-" * 78)
    tot_v1 = tot_v2 = 0.0
    rows = []
    for name, p in parts.items():
        m1 = mass(p["vol"], p["v1_mat"])
        m2 = mass(p["vol"], p["v2_mat"])
        d = m2 - m1
        tot_v1 += m1
        tot_v2 += m2
        rows.append((name, m1, m2, d))
        print(f"{name:44s} {m1:8.2f} {m2:8.2f} {d:+10.2f}")
    print("-" * 78)
    print(f"{'STRUCTURAL SUBTOTAL':44s} {tot_v1:8.2f} {tot_v2:8.2f} {tot_v2 - tot_v1:+10.2f}")
    print()
    delta = tot_v2 - tot_v1
    new_total = V10_TOTAL_G + delta
    print(f"Frozen v1.0 device total (baseline) : {V10_TOTAL_G:8.1f} g")
    print(f"Structural-part mass delta (v2-v1)   : {delta:+8.2f} g")
    print(f"Projected v2.0 device total         : {new_total:8.1f} g")
    print(f"Delta vs 241 g baseline             : {delta:+6.2f} g  ({100*delta/V10_TOTAL_G:+.1f} %)")
    print()
    print("Largest contributors:")
    for name, m1, m2, d in sorted(rows, key=lambda r: abs(r[3]), reverse=True)[:4]:
        print(f"  {name:44s} {d:+7.2f} g")
    print()
    print("Note: end caps (S02/S03) and drum (M01) are UNCHANGED by design")
    print("(RF windows + low-friction roll surface). Ceramic accents are v2-only adds.")
    print("=" * 78)

if __name__ == "__main__":
    main()
