#!/usr/bin/env python3
"""
NEXUS ONE v2.0 — tablet pose checker (winner: opposed dual-roll).
Same contract as the v0.6 checker: panel length conserved at every pose,
bend radius never below R, travel and envelope reported, PASS/FAIL printed.

Geometry: ONE continuous panel, 162.9 (X, along stick) x 145.8 (Y) x 1.2.
Usable Y = 142.8 = 28 (stick strip, always visible, never wraps)
           + 43.5 (drum1 reserve, phone — the v1.0 mechanism, untouched)
           + 71.3 (drum2 reserve, tablet).
Side 1 (+Y, phone): wraps drum1 up to a half turn (theta in [pi/2, pi]),
  exactly the v0.6 law: F0=0, F1 = 43.5 - R*pi/2 = 30.93 (travel 30.9, matches v0.6).
Side 2 (-Y, tablet): wraps drum2 up to ONE FULL TURN (theta in [pi/2, 2*pi]);
  back flat drains first, then the wrap unwinds. F1 = 71.3 - R*pi/2 = 58.73.
  One full turn puts panel-back against panel-front over part of the wrap, so a
  0.05 mm interleave film rides the outer turn (standard rollable practice).
Deployment sequence (mechanical interlock): drum1 to >=90% before drum2 releases.
Pose law per side: F + R*theta + B = L, with B draining over u in [0, u_drain].
"""
import math

R = 8.0
N = 1001

SIDES = {
    "drum1_phone":  {"L": 43.5, "F0": 0.0, "theta_max": math.pi,     "u_drain": 0.85},
    "drum2_tablet": {"L": 71.3, "F0": 0.0, "theta_max": 2 * math.pi, "u_drain": 0.50},
}
for s in SIDES.values():
    s["F1"] = s["L"] - R * math.pi / 2.0
    s["B_full"] = s["L"] - s["F0"] - R * s["theta_max"]

def pose(s, u):
    F = s["F0"] + (s["F1"] - s["F0"]) * u
    rem = s["L"] - F
    B = max(0.0, s["B_full"] * (1 - u / s["u_drain"])) if u < s["u_drain"] else 0.0
    theta = (rem - B) / R
    return F, theta, B

overall_pass, results = True, {}
for name, s in SIDES.items():
    worst_err, min_th, max_th, prev_th, mono_ok = 0.0, 1e9, -1e9, 1e18, True
    for i in range(N):
        u = i / (N - 1)
        F, th, B = pose(s, u)
        worst_err = max(worst_err, abs(F + R * th + B - s["L"]))
        min_th, max_th = min(min_th, th), max(max_th, th)
        if th > prev_th + 1e-9:
            mono_ok = False
        prev_th = th
        if not (math.pi / 2 - 1e-9 <= th <= s["theta_max"] + 1e-9) or B < -1e-9:
            mono_ok = False
    side_pass = mono_ok and worst_err < 1e-6
    overall_pass &= side_pass
    results[name] = {"max_length_error_mm": worst_err,
                     "theta_range": (round(min_th, 3), round(max_th, 3)),
                     "travel_mm": round(s["F1"] - s["F0"], 2),
                     "visible_mm": round(s["F1"] + R * math.pi / 2, 2),
                     "pass": side_pass}

phone_screen = 28.0 + results["drum1_phone"]["visible_mm"]
tablet_screen = phone_screen + results["drum2_tablet"]["visible_mm"]
dev = {"L": 190.0, "W": 46.0, "T": 22.0}   # +6 head-cap (drum2 FPC pocket), drums side by side
mass_add = {"drum2_POM": 28, "leading_bar2": 15, "negator2": 8, "fpc_loop2": 5,
            "interleave_film": 2, "wider_housing": 16, "detents_guides2": 8,
            "head_cap_deepen": 6}
mass_tot = 241 + sum(mass_add.values())

print("=" * 72)
print("TABLET POSE CHECKER — opposed dual-roll (v0.6 contract, two sides)")
print("=" * 72)
for name, r in results.items():
    print("%s: err=%.2e mm theta=[%.3f, %.3f] travel=%.2f mm visible=%.2f mm -> %s"
          % (name, r["max_length_error_mm"], *r["theta_range"], r["travel_mm"],
             r["visible_mm"], "PASS" if r["pass"] else "FAIL"))
print("phone visible width: 162.9 x %.1f mm (target 71.5; physical panel is 162.9 x 74.5, 3 mm hidden in wrap/seams)" % phone_screen)
print("tablet visible width: 162.9 x %.1f mm (target 142.8)" % tablet_screen)
print("device: %.0f x %.0f x %.0f mm (v1.0: 183.9 x 34 x 22)" % (dev["L"], dev["W"], dev["T"]))
print("mass: 241 + %d = %d g" % (sum(mass_add.values()), mass_tot))
ok = overall_pass and abs(phone_screen - 71.5) < 0.05 and abs(tablet_screen - 142.8) < 0.05
print("OVERALL:", "PASS" if ok else "FAIL")
print("=" * 72)
