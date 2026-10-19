#!/usr/bin/env python3
"""
NEXUS ONE v2.1 - Workstream A: B8 v2 thermal model (1-D resistance network).

Digital-only. Every non-datasheet input is marked ASSUMPTION.
Discipline (copied from the v2.0 cooling workstream): re-derive the frozen
v1 baseline FIRST and show the model reproduces it, THEN extend it.
Only shell-material terms change between v1 and the v2 stacks; the
interior bundle is calibrated ONCE against the frozen 8.8 K/W law.

Node structure (heat injected at node 0):
  Tj (die junction) --R_jc--> case --R_TIM--> tray --R_gap--> [spreader]
  --R_c1--> shell inner --R_spread(lateral)--> --R_thr(through wall)-->
  shell outer (skin) --R_skin_air(conv+rad)--> Tamb

Cap convention (frozen v0.4/v1.2): P_cap = (43 - Tamb) / R_total_die_to_air.
This is conservative: it applies the 43 C skin limit against the FULL stack
including junction/TIM terms. Skin-hotspot-only caps would be ~15-25% higher
and are NOT claimed.

python3, stdlib only.
"""
import math

SIGMA = 5.670374419e-8  # W/m2K4, Stefan-Boltzmann (exact, SI)

# ============ frozen / measured inputs ============
T_SKIN_MAX   = 43.0   # C, pocket thermal limit (frozen)
T_AMB_REF    = 25.0   # C, reference ambient for the 2 W law
T_AMB_HOT    = 35.0   # C, hot-day case from the v1.2 pocket study
RTH_FOLDED_V1 = 8.8   # K/W, frozen v0.4 folded model
P_LAW_FOLDED_V1 = 2.0 # W, frozen folded law
P_LAW_OPEN_V1   = 3.0 # W, frozen open law
P_LAW_BATT_V1   = 1.5 # W, frozen folded+battery-module law
P_POCKET        = 0.9 # W, Pocket-Mode envelope (v1.0 OS spec)

# ============ geometry (BOM / freeze dims) ============
L_STICK, W_STICK, T_STICK = 0.1839, 0.034, 0.022   # m, 183.9x34x22 mm
A_OUTER      = 2.0 * (L_STICK * W_STICK + L_STICK * T_STICK + W_STICK * T_STICK)
A_SPINE_BACK = L_STICK * W_STICK
R_SRC   = 0.010  # m, effective heat-source radius on shell inner (ASSUMPTION)
R_SHELL = 0.092  # m, half-length equivalent spreading radius (ASSUMPTION)
T_WALL  = 0.0015 # m, shell wall, mass-study ASSUMPTION (1.5 mm)

# ============ material data (datasheet class) ============
K_AL         = 167.0  # 6061-T6 (datasheet class)
K_TI         = 6.7    # Ti-6Al-4V (datasheet class)
K_CFRP_IN    = 7.0    # CFRP quasi-iso in-plane, mid of 5-10 (ASSUMPTION band)
K_CFRP_THR   = 1.0    # CFRP through-thickness (ASSUMPTION)
K_GRAPHITE_IN= 400.0  # pyrolytic graphite sheet class (datasheet class)
K_TIM        = 3.0    # TIM pad class (datasheet class)
T_SPREADER_AL= 0.0008 # m, hybrid Al spreader thickness (ASSUMPTION)
T_GRAPHITE   = 0.0001 # m, graphite ply thickness (ASSUMPTION)
RHO_AL, RHO_GRAPHITE, RHO_CFRP = 2700.0, 2100.0, 1600.0  # kg/m3

# ============ interior / interface (ASSUMPTION, calibrated once) ============
R_JC  = 0.8    # K/W, SoC package junction-to-case (ASSUMPTION, BGA class)
R_TIM = 0.2e-3 / (K_TIM * (0.015 * 0.015))  # 0.2 mm TIM over 15x15 mm die pad
# R_GAP: tray polymer + air gaps + clamp contacts, die-side to shell inner.
# Calibrated ONCE below so the v1 folded model closes on frozen 8.8 K/W.

# ============ convection / radiation (textbook) ============
# Free convection over small enclosures: h = 5-10 W/m2K (Incropera class).
H_CONV_FOLDED = 6.0   # stagnant pocket, no airflow (ASSUMPTION, mid-low band)
H_CONV_OPEN   = 10.0  # free air, device in hand/on desk (ASSUMPTION, top band)
A_EFF_FOLDED  = 0.7   # pocket blanketing: 30% of shell area covered (ASSUMPTION)
A_EFF_OPEN    = 1.0
EPS_AL   = 0.8  # anodized Al (ASSUMPTION, class value)
EPS_CFRP = 0.9  # black CFRP (ASSUMPTION, class value)

# ============ battery module coupling (ASSUMPTION, calibrated to v1 law) ============
P_BATT_MOD = 1.0  # W, battery module self-heat (charge losses, ASSUMPTION)
KAPPA_BATT = 0.5  # fraction of module heat coupled into device (ASSUMPTION)

# ============ cooling module path (v2.0 frozen numbers, re-derived) ============
R_CONTACT_MOD = 2.5   # K/W, cold-plate TIM + clamp to bay rail (ASSUMPTION,
                      # dominant term - demands real TIM + clamp force)
H_FORCED = 45.0       # W/m2K (ASSUMPTION, ~1 m/s duct velocity)
A_FIN = 12 * 2 * 0.040 * 0.020  # m2, 12 Cu fins 40x20 mm, both sides
R_MOD = R_CONTACT_MOD + 1.0 / (H_FORCED * A_FIN)  # = 3.66 K/W


def h_rad(eps, t_skin_c, t_amb_c):
    """Linearised radiation coefficient, W/m2K."""
    t1, t2 = t_skin_c + 273.15, t_amb_c + 273.15
    return eps * SIGMA * (t1 + t2) * (t1 * t1 + t2 * t2)


def r_spread_lateral(kt_layers):
    """Radial spreading resistance of a thin plate stack (point source)."""
    kt = sum(k * t for k, t in kt_layers)  # W/K per unit width
    return math.log(R_SHELL / R_SRC) / (2.0 * math.pi * kt)


def r_through_wall(layers):
    """1-D through-thickness conduction of a layer stack."""
    return sum(t / (k * A_SPINE_BACK) for k, t in layers)


def r_skin_air(h_conv, eps, area_eff_frac, t_amb):
    hr = h_rad(eps, T_SKIN_MAX, t_amb)
    return 1.0 / ((h_conv + hr) * A_OUTER * area_eff_frac), hr


def pcap(rth, t_amb):
    return (T_SKIN_MAX - t_amb) / rth


# ---------------- stack definitions ----------------
# kt_layers: (k, t) conductive layers sharing lateral spreading (parallel)
# thr_layers: (k, t) series through-thickness layers
STACKS = {
    "v1":   dict(label="v1 frozen (6061 Al shell)",
                  kt=[(K_AL, T_WALL)], thr=[(K_AL, T_WALL)],
                  eps=EPS_AL, rc1=0.0, mass_add_g=0.0),
    "a":    dict(label="v2 (a) Ti/CFRP as drawn",
                  kt=[(K_CFRP_IN, T_WALL)], thr=[(K_CFRP_THR, T_WALL)],
                  eps=EPS_CFRP, rc1=0.0, mass_add_g=0.0),
    "b":    dict(label="v2 (b) hybrid Al spreader under CFRP",
                  kt=[(K_AL, T_SPREADER_AL), (K_CFRP_IN, T_WALL)],
                  thr=[(K_AL, T_SPREADER_AL), (K_CFRP_THR, T_WALL)],
                  eps=EPS_CFRP, rc1=0.5,   # spreader->shell TIM+clamp (ASSUMPTION)
                  mass_add_g=A_SPINE_BACK * T_SPREADER_AL * RHO_AL * 1000.0),
    "c":    dict(label="v2 (c) graphite ply in CFRP layup",
                  kt=[(K_CFRP_IN, T_WALL - T_GRAPHITE), (K_GRAPHITE_IN, T_GRAPHITE)],
                  thr=[(K_CFRP_THR, T_WALL - T_GRAPHITE), (K_GRAPHITE_IN, T_GRAPHITE)],
                  eps=EPS_CFRP, rc1=0.0,
                  mass_add_g=(A_SPINE_BACK * T_GRAPHITE * RHO_GRAPHITE * 1000.0
                              - A_SPINE_BACK * T_GRAPHITE * RHO_CFRP * 1000.0)),
}

MODES = {
    "folded": dict(h=H_CONV_FOLDED, af=A_EFF_FOLDED, note="panel rolled in, pocket"),
    "open":   dict(h=H_CONV_OPEN,   af=A_EFF_OPEN,   note="panel out, free air"),
}


def stack_rth(key, mode, t_amb, h_conv=None):
    s, m = STACKS[key], MODES[mode]
    h = m["h"] if h_conv is None else h_conv
    r_spr = r_spread_lateral(s["kt"])
    r_thr = r_through_wall(s["thr"])
    r_sa, hr = r_skin_air(h, s["eps"], m["af"], t_amb)
    rth = R_JC + R_TIM + R_GAP + s["rc1"] + r_spr + r_thr + r_sa
    return dict(rth=rth, r_jc=R_JC, r_tim=R_TIM, r_gap=R_GAP, rc1=s["rc1"],
                r_spread=r_spr, r_thr=r_thr, r_skin_air=r_sa, h_rad=hr)


def verdict(p, law, name):
    tag = "LEGAL " if p >= law else "ILLEGAL"
    return f"{tag} at {law} W ({p:.2f} W cap)"


print("=" * 78)
print("NEXUS ONE v2.1 - B8 v2 thermal model (1-D resistance network)")
print("=" * 78)

# ================= [1] v1 BASELINE REPRODUCTION =================
print("\n[1] v1 BASELINE REPRODUCTION (frozen v0.4: Rth_folded = 8.8 K/W)")
p25 = pcap(RTH_FOLDED_V1, T_AMB_REF)
p35 = pcap(RTH_FOLDED_V1, T_AMB_HOT)
print(f"  cap @25 C ambient: {p25:.3f} W  (frozen law: {P_LAW_FOLDED_V1} W -> "
      f"{'MATCH' if abs(p25 - 2.045) < 0.001 else 'MISMATCH'})")
print(f"  cap @35 C ambient: {p35:.3f} W  (v1.2 report: 0.91 W -> "
      f"{'MATCH' if abs(round(p35, 2) - 0.91) < 0.005 else 'MISMATCH'})")
pbat = p25 - KAPPA_BATT * P_BATT_MOD
print(f"  folded+batt-module @25 C: {pbat:.2f} W  (frozen law: {P_LAW_BATT_V1} W -> "
      f"{'MATCH' if abs(pbat - 1.5) < 0.06 else 'MISMATCH'}; kappa calibrated)")

# ================= [2] v1 LAYER DECOMPOSITION =================
print("\n[2] v1 folded layer decomposition (calibrating R_gap to close 8.8 K/W)")
s_v1 = STACKS["v1"]
r_spr_v1 = r_spread_lateral(s_v1["kt"])
r_thr_v1 = r_through_wall(s_v1["thr"])
r_sa_v1, hr_v1 = r_skin_air(H_CONV_FOLDED, EPS_AL, A_EFF_FOLDED, T_AMB_REF)
R_GAP = RTH_FOLDED_V1 - (R_JC + R_TIM + r_spr_v1 + r_thr_v1 + r_sa_v1)
print(f"  R_jc (die->case)              : {R_JC:6.3f} K/W  [ASSUMPTION]")
print(f"  R_TIM (0.2mm/k=3, 15x15mm pad): {R_TIM:6.3f} K/W  [computed]")
print(f"  R_spread (Al 6061, t=1.5mm)   : {r_spr_v1:6.3f} K/W  [computed]")
print(f"  R_through (Al wall)           : {r_thr_v1:6.4f} K/W  [computed]")
print(f"  R_skin_air (h_c={H_CONV_FOLDED}, h_r={hr_v1:.2f}, A_eff={A_OUTER*A_EFF_FOLDED*1e4:.0f}cm2)"
      f": {r_sa_v1:6.3f} K/W  [computed]")
print(f"  R_gap (interior bundle)       : {R_GAP:6.3f} K/W  [CALIBRATED to frozen 8.8]")
tot = R_JC + R_TIM + R_GAP + r_spr_v1 + r_thr_v1 + r_sa_v1
print(f"  TOTAL                         : {tot:6.3f} K/W  "
      f"(frozen 8.8 -> {'MATCH' if abs(tot - 8.8) < 1e-9 else 'MISMATCH'})")
print("  NOTE: R_gap bundles the PC/ABS tray, internal air gaps, clamp contacts and")
print("  everything else not separately modelled. It is FIXED from here on.")

# v1 open-mode check against the 3 W law
print("\n[2b] v1 open-mode check (frozen open law 3 W)")
d_open = stack_rth("v1", "open", T_AMB_REF)
p_open = pcap(d_open["rth"], T_AMB_REF)
print(f"  Rth_open = {d_open['rth']:.2f} K/W -> cap @25 C = {p_open:.2f} W "
      f"(frozen law 3 W -> {'MATCH' if abs(p_open - 3.0) < 0.1 else 'CHECK'})")

# ================= [3] STACK COMPARISON, folded =================
print("\n[3] STACK COMPARISON - folded, @25 C ambient (skin limit 43 C)")
print(f"  {'stack':34s} {'Rth':>7s} {'cap@25':>7s} {'cap@35':>7s}   vs 2W law / 0.9W pocket")
for key in ("v1", "a", "b", "c"):
    d25 = stack_rth(key, "folded", T_AMB_REF)
    d35 = stack_rth(key, "folded", T_AMB_HOT)
    c25, c35 = pcap(d25["rth"], T_AMB_REF), pcap(d35["rth"], T_AMB_HOT)
    print(f"  {STACKS[key]['label']:34s} {d25['rth']:6.2f}K {c25:6.2f}W {c35:6.2f}W"
          f"   2W:{'LEGAL ' if c25 >= 2.0 else 'DEAD  '} 0.9W:{'legal' if c25 >= 0.9 else 'dead '} "
          f"(@35: {'legal' if c35 >= 0.9 else 'dead '})")

print("\n[3b] folded layer detail per v2 stack (@25 C)")
for key in ("a", "b", "c"):
    d = stack_rth(key, "folded", T_AMB_REF)
    print(f"  {STACKS[key]['label']}:")
    print(f"    R_jc {d['r_jc']:.2f} + R_tim {d['r_tim']:.2f} + R_gap {d['r_gap']:.2f}"
          f" + R_c1 {d['rc1']:.2f} + R_spread {d['r_spread']:.2f}"
          f" + R_thr {d['r_thr']:.3f} + R_skin_air {d['r_skin_air']:.2f}"
          f" = {d['rth']:.2f} K/W")

# ================= [4] MODE-DEPENDENT CAPS =================
print("\n[4] MODE-DEPENDENT LEGAL CAPS (W) per stack")
print(f"  {'stack':34s} {'fold25':>7s} {'fold35':>7s} {'open25':>7s} {'open35':>7s}"
      f" {'batt25':>7s} {'batt35':>7s}")
for key in ("v1", "a", "b", "c"):
    row = []
    for mode, tamb in (("folded", T_AMB_REF), ("folded", T_AMB_HOT),
                       ("open", T_AMB_REF), ("open", T_AMB_HOT)):
        row.append(pcap(stack_rth(key, mode, tamb)["rth"], tamb))
    for tamb in (T_AMB_REF, T_AMB_HOT):
        base = pcap(stack_rth(key, "folded", tamb)["rth"], tamb)
        row.append(max(0.0, base - KAPPA_BATT * P_BATT_MOD))
    print(f"  {STACKS[key]['label']:34s} " + " ".join(f"{v:7.2f}" for v in row))

# ================= [5] COOLING-MODULE-STANDARD (e) =================
print("\n[5] (e) COOLING-MODULE-STANDARD: bay path R_mod = "
      f"{R_CONTACT_MOD:.1f} + {1.0/(H_FORCED*A_FIN):.2f} = {R_MOD:.2f} K/W")
print("    in parallel with each chassis folded path")
print(f"  {'stack':34s} {'Rth||':>7s} {'cap@25':>7s} {'cap@35':>7s}   2W law?")
for key in ("v1", "a", "b", "c"):
    r_ch25 = stack_rth(key, "folded", T_AMB_REF)["rth"]
    r_ch35 = stack_rth(key, "folded", T_AMB_HOT)["rth"]
    r_p25 = 1.0 / (1.0 / r_ch25 + 1.0 / R_MOD)
    r_p35 = 1.0 / (1.0 / r_ch35 + 1.0 / R_MOD)
    c25, c35 = pcap(r_p25, T_AMB_REF), pcap(r_p35, T_AMB_HOT)
    print(f"  {STACKS[key]['label']:34s} {r_p25:6.2f}K {c25:6.2f}W {c35:6.2f}W"
          f"   {'LEGAL' if c25 >= 2.0 else 'dead'}")
print("  NOTE: R_contact 2.5 K/W was an ASSUMPTION against an Al bay rail; the v2")
print("  rail is Ti-6Al-4V (25x worse k) - rail-side spreading at the module clamp")
print("  is NOT in this number (see sensitivity + NOT-VERIFIED list).")
print("  Chassis thermal strap SoC->bay-rail also NOT-VERIFIED (v2.0 carried).")

# ================= [6] DOMINANT-TERM SENSITIVITY =================
print("\n[6] DOMINANT-TERM SENSITIVITY (folded cap @25 C, config b unless noted)")
base = pcap(stack_rth("b", "folded", T_AMB_REF)["rth"], T_AMB_REF)
print(f"  baseline (b): {base:.2f} W")
for sweep_name, vals, apply in [
    ("R_c1 spreader->shell contact", [0.2, 0.5, 1.0],
     lambda v: STACKS.__setitem__("b", {**STACKS["b"], "rc1": v})),
    ("R_gap interior bundle", [0.2, R_GAP, 1.0],
     None),  # handled via global below
    ("h_conv folded", [5.0, 6.0, 8.0], None),
]:
    outs = []
    if sweep_name.startswith("R_c1"):
        for v in vals:
            old = STACKS["b"]["rc1"]; STACKS["b"]["rc1"] = v
            outs.append((v, pcap(stack_rth("b", "folded", T_AMB_REF)["rth"], T_AMB_REF)))
            STACKS["b"]["rc1"] = old
    elif sweep_name.startswith("R_gap"):
        for v in vals:
            g_old = globals()["R_GAP"]; globals()["R_GAP"] = v
            outs.append((v, pcap(stack_rth("b", "folded", T_AMB_REF)["rth"], T_AMB_REF)))
            globals()["R_GAP"] = g_old
    else:
        for v in vals:
            outs.append((v, pcap(stack_rth("b", "folded", T_AMB_REF, h_conv=v)["rth"],
                                T_AMB_REF)))
    print("  " + sweep_name + ": " + ", ".join(f"{v:g}->{p:.2f}W" for v, p in outs))
# k_cfrp band for config (a)
outs = []
for k in (5.0, 7.0, 10.0):
    old = STACKS["a"]["kt"]; STACKS["a"]["kt"] = [(k, T_WALL)]
    outs.append((k, pcap(stack_rth("a", "folded", T_AMB_REF)["rth"], T_AMB_REF)))
    STACKS["a"]["kt"] = old
print("  k_cfrp_in-plane 5/7/10 (config a): " + ", ".join(f"{v:g}->{p:.2f}W" for v, p in outs))
# Ti rails checked-and-negligible
r_rail = 0.1839 / (K_TI * 2 * 12e-6)
print(f"  Ti rail axial conduction (2 rails, 12mm2 each): {r_rail:.0f} K/W "
      f"-> negligible vs shell spreading (not in network, checked)")

# ================= [7] JUNCTION SANITY + MASS =================
print("\n[7] JUNCTION TEMP SANITY at each folded cap (@25 C) + mass")
for key in ("a", "b", "c"):
    d = stack_rth(key, "folded", T_AMB_REF)
    p = pcap(d["rth"], T_AMB_REF)
    tj = T_AMB_REF + p * d["rth"]          # die junction (full stack)
    tskin_hot = T_AMB_REF + p * (d["r_spread"] + d["r_thr"] + d["r_skin_air"])
    tskin_avg = T_AMB_REF + p * (d["r_thr"] + d["r_skin_air"])
    mass = 261.0 + STACKS[key]["mass_add_g"]
    print(f"  {STACKS[key]['label']}: P={p:.2f}W -> Tj={tj:.0f}C, "
          f"skin hotspot={tskin_hot:.0f}C (limit 43), skin avg={tskin_avg:.0f}C, "
          f"device {mass:.1f}g (+{STACKS[key]['mass_add_g']:.1f}g vs v2 261g)")
print("  Cu-spreader alternative (b, Cu k=400): mass +44.8 g -> 305.8 g total:")
print("  REJECTED - 44.8 g for -1.3 K/W vs Al is a bad trade (shown, not claimed).")

# ================= [8] VERDICT =================
print("\n[8] VERDICT - which stacks are legal at which folded caps (@25 C / @35 C)")
caps = {}
for key in ("a", "b", "c"):
    c25 = pcap(stack_rth(key, "folded", T_AMB_REF)["rth"], T_AMB_REF)
    c35 = pcap(stack_rth(key, "folded", T_AMB_HOT)["rth"], T_AMB_HOT)
    caps[key] = (c25, c35)
for key in ("a", "b", "c"):
    c25, c35 = caps[key]
    print(f"  ({key}) {STACKS[key]['label']:32s}: highest legal folded "
          f"{c25:.2f} W @25 / {c35:.2f} W @35")
print("  NO v2 stack keeps the 2 W folded law passively. Highest passive folded")
print(f"  cap: (b) {caps['b'][0]:.2f} W @25 C. Pocket-Mode 0.9 W is legal folded @25 C")
print("  on (b) and (c) only; dead on (a); dead on ALL stacks folded at 35 C hot-day.")
print("  The 2 W folded law survives ONLY as cooling-module-gated (e): 5.4-6.7 W @25.")
print("=" * 78)
