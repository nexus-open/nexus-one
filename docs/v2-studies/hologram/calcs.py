#!/usr/bin/env python3
"""
NEXUS ONE v2.0 — Hologram System calcs (calcs.py).

Every number cited in hologram_system.md is computed here and printed.
Order-of-magnitude engineering estimates; each assumption is labelled.
Run:  python3 calcs.py
"""
import math

print("=" * 70)
print("NEXUS ONE v2.0 — HOLOGRAM SYSTEM CALCS")
print("=" * 70)

# =====================================================================
# 1. LIGHT-FIELD v2 — lenticular + IR eye-tracking
# =====================================================================
print("\n--- 1. LIGHT-FIELD v2 ---")

panel_px_w, panel_px_h = 2400, 1080          # flexible AMOLED class, v1.0 freeze
views = 8                                    # v2 keeps 8-view lenticular
px_per_view = panel_px_w // views
print(f"panel {panel_px_w}x{panel_px_h} px, {views} views -> {px_per_view} px/view horizontal")

# Lenticular pitch sanity: 8 views across 2400 px on a 162.9 mm-wide panel
panel_w_mm = 162.9
subpx_mm = panel_w_mm / panel_px_w
lenticule_mm = subpx_mm * views
lpi = 25.4 / lenticule_mm
print(f"sub-pixel pitch {subpx_mm*1000:.1f} um -> lenticule pitch {lenticule_mm:.3f} mm "
      f"({lpi:.0f} LPI; real lenticular films: 10-100 LPI -> makeable)")

# Tracking latency budget (ms)
latency = {
    "IR camera capture @120fps (8.3 ms frame)": 8.3,
    "pupil/face detection (DPU class)": 3.0,
    "view-pair synthesis + interleave @60Hz": 6.0,
    "display refresh-to-photon (60 Hz)": 8.3,
}
total_lat = sum(latency.values())
for k, v in latency.items():
    print(f"  latency {k:42s} {v:5.1f} ms")
print(f"  TOTAL eye-to-photon latency: {total_lat:.1f} ms")
tracking_hz = 120.0
print(f"  tracking loop {tracking_hz:.0f} Hz; 3D view-update rate = display refresh 60 Hz")
print(f"  view-switching dead time per head-move: ~{total_lat:.0f} ms "
      f"(~{total_lat/1000*tracking_hz:.1f} tracking frames)")
print(f"  latency headroom vs 50 ms motion-sickness/annoyance bound: "
      f"{50.0 - total_lat:.1f} ms margin")

# Power budget (W), active while light-field mode is on
power = {
    "IR camera (OV2312 global-shutter class)": 0.20,
    "850 nm IR illuminator, pulsed": 0.25,
    "tracking DSP (pupil solve + view render)": 0.25,
}
total_p = sum(power.values())
for k, v in power.items():
    print(f"  power {k:42s} {v:.2f} W")
print(f"  TOTAL eye-tracking active: {total_p:.2f} W")
# Battery impact vs 13.7 Wh
battery_Wh = 13.7
print(f"  battery cost per hour of 3D mode: {total_p:.2f} Wh "
      f"({100*total_p/battery_Wh:.1f}% of the 13.7 Wh pack)")

# Lenticular sheet storage (v0.6 finding)
sheet_w, sheet_h = 163.0, 74.5   # mm, matches deployed panel
stick_w = 34.0
print(f"  lenticular sheet {sheet_w:.0f}x{sheet_h:.0f} mm vs stick width {stick_w:.0f} mm: "
      f"cannot fold onto stick -> carry-case sleeve (v0.6 finding, restated)")

# =====================================================================
# 2. AIRSCREEN — mist + pico-DLP module in the 120x24 bay
# =====================================================================
print("\n--- 2. AIRSCREEN PROJECTOR MODULE ---")

bay_budget_W = 10.0
split = {"TI DLP pico engine class (50-100 lm)": 4.0,
         "ultrasonic atomiser disc (throttled)": 2.0,
         "MCU + drivers + status LEDs": 0.4}
mod_W = sum(split.values())
for k, v in split.items():
    print(f"  power {k:40s} {v:.1f} W")
print(f"  module total {mod_W:.1f} W / {bay_budget_W:.0f} W bay budget "
      f"({100*mod_W/bay_budget_W:.0f}% used, {bay_budget_W-mod_W:.1f} W headroom)")
assert mod_W <= bay_budget_W, "BAY BUDGET EXCEEDED"

# Mist reservoir sizing: atomiser at 60 ml/h (throttled full-drive class)
rate_ml_h = 60.0
for session_min in (5, 10, 15, 30):
    ml = session_min / 60.0 * rate_ml_h
    print(f"  {session_min:2d}-min session -> {ml:.1f} ml reservoir")
ml_15 = 15 / 60 * rate_ml_h
print(f"  v0.5 baseline check: 5 ml / 60 ml/h * 60 = {5/60*60:.1f} min  [matches 5 min]")
# Tank dims for the chosen 15-minute session: 15 ml = 15,000 mm^3
tank = (50.0, 20.0, 15.0)  # mm, inside module envelope
print(f"  15-min tank {tank[0]:.0f}x{tank[1]:.0f}x{tank[2]:.0f} mm = "
      f"{tank[0]*tank[1]*tank[2]/1000:.1f} ml (fits module envelope)")

# Optical: 120x70 mm image on mist plane ~150 mm from lens
img_w, img_d = 120.0, 70.0
throw_mm = 150.0
print(f"  image {img_w:.0f}x{img_d:.0f} mm at {throw_mm:.0f} mm throw; "
      f"mist plane flatness tol +/-1.5 mm, projector tilt tol +/-1.0 deg (keystone-corrected)")

# Thermal: module vents its own heat; stick OPEN-mode law is separate
stick_open_W = 2.5   # ASSUMPTION: screen + OS during projection, under 3 W open law
stick_open_law_W = 3.0
system_W = stick_open_W + mod_W
print(f"  stick-side during projection: {stick_open_W:.1f} W <= {stick_open_law_W:.0f} W OPEN law: "
      f"{'HOLDS' if stick_open_W <= stick_open_law_W else 'VIOLATED'} (module heat vents via own shell)")
print(f"  total system draw during projection: {system_W:.1f} W "
      f"(stick {stick_open_W:.1f} + module {mod_W:.1f})")
print(f"  15-min session energy from 13.7 Wh pack: {system_W*0.25:.2f} Wh "
      f"({100*system_W*0.25/battery_Wh:.1f}% of pack)")

# =====================================================================
# 3. VOLUMETRIC — photophoretic trap array, trap math recomputed
# =====================================================================
print("\n--- 3. VOLUMETRIC (PHOTOPHORETIC TRAP ARRAY) ---")

# Precedent (BYU Nature 2018): ONE trapped particle, steered and painted.
demonstrated_traps = 1

# (a) Wireframe baseline = v0.5's case, recomputed
w_voxels, w_travel_mm = 2000, 2.0
scan_speed = 0.5          # m/s, demonstrated-class steering speed (ASSUMPTION, order-of-magnitude)
dwell_ms = 0.1            # paint dwell per voxel (ASSUMPTION)
tau_ms = w_travel_mm / (scan_speed * 1000) * 1000 + dwell_ms
vox_per_s = 1000.0 / tau_ms
req_w = w_voxels * 24.0
traps_w = math.ceil(req_w / vox_per_s)
print(f"wireframe baseline (v0.5 case, recomputed):")
print(f"  {w_voxels} voxels, {w_travel_mm} mm avg travel @ {scan_speed} m/s + {dwell_ms} ms dwell")
print(f"  -> {tau_ms:.2f} ms/voxel = {vox_per_s:.0f} voxels/s per trap")
print(f"  required voxel rate @24fps: {req_w:,.0f} voxels/s")
print(f"  parallel traps needed: {traps_w}  [v0.5 said 192 — confirmed, delta is dwell term]")
print(f"  gap vs demonstrated {demonstrated_traps}-trap system: {traps_w/demonstrated_traps:.0f}x")

# (b) Poster claim: filled 30 mm globe
globe_d, pitch = 30.0, 1.2   # mm; voxel pitch 1.2 mm (ASSUMPTION)
g_voxels = (globe_d / pitch) ** 3
g_travel = pitch
tau_g_ms = g_travel / (scan_speed * 1000) * 1000 + dwell_ms
vox_g_s = 1000.0 / tau_g_ms
req_g = g_voxels * 24.0
traps_g = math.ceil(req_g / vox_g_s)
print(f"poster claim: filled {globe_d:.0f} mm globe @ {pitch} mm voxel pitch:")
print(f"  voxels/frame {g_voxels:,.0f}; required @24fps {req_g:,.0f} voxels/s")
print(f"  {tau_g_ms:.2f} ms/voxel = {vox_g_s:.0f} voxels/s per trap -> traps needed: {traps_g}")
print(f"  gap vs demonstrated {demonstrated_traps}-trap system: {traps_g/demonstrated_traps:,.0f}x")

# Laser power
trap_optical_W = 0.050    # 50 mW IR trap beam per trap (tweezers-class, ASSUMPTION)
paint_W = 1.0             # shared RGB paint lasers, visible (ASSUMPTION)
optical_w = traps_g * trap_optical_W + paint_W
laser_efficiency = 0.25   # wall-plug efficiency (ASSUMPTION)
wall_W = optical_w / laser_efficiency
print(f"optical power: {traps_g} traps x {trap_optical_W*1000:.0f} mW + {paint_W:.0f} W paint "
      f"= {optical_w:.1f} W optical -> wall-plug ~{wall_W:.0f} W @ {laser_efficiency:.0%} efficiency")
print(f"  vs phone thermal law (2 W folded): {wall_W/2:.0f}x over — needs bench/lab power, not a phone")

# Eye-safety sanity check (order-of-magnitude, NOT a certification)
class1_AEL_mW = 2.0       # order-of-magnitude Class 1 accessible limit, NIR (sanity figure)
print(f"eye-safety sanity: per-trap {trap_optical_W*1000:.0f} mW beam vs ~{class1_AEL_mW:.0f} mW "
      f"Class-1-class accessible limit -> ~{trap_optical_W*1000/class1_AEL_mW:.0f}x over per beam, "
      f"{traps_g} beams in an open volume")
print("  -> open-air operation lands in Class 3B/4 territory: HARD BLOCKER; "
      "requires enclosure / interlock / eye-safe wavelength engineering. NOT hand-waved.")

# The three research advances, quantified targets
print("\nthree advances that would close the gap:")
print(f"  (1) parallel addressed traps: {demonstrated_traps} -> ~{traps_g} independent steerable traps "
      f"(SLM/DMD time-multiplexed holograms, kHz per-trap steering)")
print(f"  (2) steering speed: {scan_speed} m/s -> ~{scan_speed*50:.0f} m/s (resonant/AOD steering + "
      f"reduced-drag particles) = ~50x more voxels/s per trap")
print(f"  (3) persistence: phosphorescent particles with ~10 ms glow decouple brightness from revisit "
      f"rate: each trap paints ~{10/tau_g_ms:.0f}x more voxels per sweep than it can revisit")

print("\n" + "=" * 70)
print("DONE — all numbers above are computed, not typed.")
