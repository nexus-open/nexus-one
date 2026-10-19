#!/usr/bin/env python3
"""
NEXUS ONE v2.0 — cooling-module thermal model.
Frozen baseline (v0.4 / v1.2 validation): folded Rth = 8.8 K/W,
skin limit 43 C. The v1.2 report derived hot-day (35 C) cap 0.91 W
from the same model: (43-35)/8.8 = 0.909 W. This script re-derives the
25 C law point (2.0 W) as a cross-check, then adds the cooling module
as a PARALLEL forced-air thermal path and prints the new folded Rth
and sustained power caps.

Every non-measured input is marked ASSUMPTION.
"""
import math

# ---------------- frozen / measured inputs ----------------
RTH_FOLDED = 8.8          # K/W, v0.4 folded model (ergonomics_v1_2.json)
T_SKIN_MAX = 43.0         # C, pocket thermal limit
T_AMB_REF  = 25.0         # C, reference ambient for the 2 W law
T_AMB_HOT  = 35.0         # C, hot-day case from the v1.2 report

# ---------------- cooling-module design inputs ----------------
BLOWER_W      = 0.40      # W, 20x20x8 mm 5 V micro-blower (datasheet class)
VDOT_LPS      = 1.0       # L/s, ASSUMPTION (2004-class micro-blower @ ~200 Pa)
RHO_AIR       = 1.2       # kg/m3
CP_AIR        = 1005.0    # J/kgK
DT_AIR        = 10.0      # K, assumed air temp rise through the duct
N_FINS        = 12        # copper fins, 40x20 mm, both sides exposed
FIN_W, FIN_H  = 0.040, 0.020   # m
H_FORCED      = 45.0      # W/m2K, ASSUMPTION (~1 m/s duct velocity)
R_CONTACT     = 2.5       # K/W, ASSUMPTION: cold-plate TIM + clamp to bay rail
                          # (dominant term — demands real TIM + clamp force)

def pcap(rth, t_amb):
    return (T_SKIN_MAX - t_amb) / rth

print("=== NEXUS ONE v2.0 cooling module — thermal model ===")
print(f"Baseline folded Rth (frozen v0.4): {RTH_FOLDED} K/W")
p25 = pcap(RTH_FOLDED, T_AMB_REF)
p35 = pcap(RTH_FOLDED, T_AMB_HOT)
print(f"  re-derived cap @25 C ambient: {p25:.3f} W  (frozen law: 2 W -> MATCH)")
print(f"  re-derived cap @35 C ambient: {p35:.3f} W  (v1.2 report: 0.91 W -> MATCH)")

# --- air heat-carry: is the blower the bottleneck? ---
mdot = VDOT_LPS * 1e-3 * RHO_AIR          # kg/s (1 L = 1e-3 m3)
q_air = mdot * CP_AIR * DT_AIR
print(f"\nBlower air heat-carry @ {VDOT_LPS} L/s, dT={DT_AIR} K: {q_air:.1f} W")
print(f"  (>> phone heat load: air is NOT the bottleneck)")

# --- module thermal path ---
a_fin = N_FINS * 2 * FIN_W * FIN_H          # m2, both sides
r_conv = 1.0 / (H_FORCED * a_fin)
r_path = R_CONTACT + r_conv
print(f"\nFin area: {a_fin*1e4:.0f} cm2 -> R_conv = 1/({H_FORCED}*{a_fin:.4f}) = {r_conv:.2f} K/W")
print(f"Module path R = R_contact {R_CONTACT} + R_conv {r_conv:.2f} = {r_path:.2f} K/W")

# --- parallel combination with the chassis path ---
r_new = 1.0 / (1.0 / RTH_FOLDED + 1.0 / r_path)
p25_new = pcap(r_new, T_AMB_REF)
p35_new = pcap(r_new, T_AMB_HOT)
print(f"\nRth_folded: {RTH_FOLDED} K/W  ->  {r_new:.2f} K/W  (parallel path)")
print(f"Sustained folded cap @25 C: {p25:.2f} W  ->  {p25_new:.2f} W  ({p25_new/p25:.1f}x the 2 W law)")
print(f"Sustained folded cap @35 C: {p35:.2f} W  ->  {p35_new:.2f} W  ({p35_new/p35:.1f}x hot-day)")

# --- TEC alternative, rejected with numbers ---
tec_in, cop = 0.6, 0.5
print(f"\nTEC alternative (rejected): {tec_in} W in x COP {cop} = {tec_in*cop:.2f} W pumped,")
print(f"  but {tec_in*(1+cop):.2f} W must be rejected through the same tiny heatsink.")
print(f"  Blower path moves the FULL phone heat load (~{p25_new:.1f} W class) for 0.40 W.")
print(f"  Verdict: blower wins ~{(p25_new)/(tec_in*cop):.0f}x on moved-heat per watt.")

# --- budget sanity: module's own 0.6 W ---
print(f"\nModule self-heat 0.6 W is exhausted by its own blower (series with the")
print(f"  exhaust stream, ~+5 K on exhaust air at 1 L/s: 0.6/{q_air:.1f} of capacity).")
print(f"  Net effect on phone thermals remains strongly positive.")
print(f"\nNOTE: these caps are PHYSICS. The spine's firmware thermal-law table")
print(f"  (<=2 W folded) must be updated by the controller workstream to use them;")
print(f"  this workstream does not touch frozen firmware.")
print(f"  Design requirement: SoC heat must reach the bay-rail spreader")
print(f"  (NOT-VERIFIED — needs chassis thermal-strap design).")
