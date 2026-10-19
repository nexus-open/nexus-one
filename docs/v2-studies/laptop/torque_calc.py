#!/usr/bin/env python3
"""NEXUS ONE v2.0 - laptop mode kickstand statics.
Side-view 2D rigid-body model. Units: mm, g, N, mN.m.
Prints CoM, support polygon, tip-over verdict, leg geometry, hinge torque spec.
Run: python3 torque_calc.py
"""
import math

g = 9.81
print("=== NEXUS ONE v2.0 kickstand statics (laptop / easel pose) ===")

# ---- masses (g) ----
m_stick = 229.0   # ASSUMPTION: 241 g device = 229 g stick+batteries+drum + 12 g panel+bezel
m_panel = 12.0    # ASSUMPTION: flexible AMOLED 162.9x71.5 + bezel
m_kb    = 31.0    # keyboard module design mass (see keyboard_kickstand_design.md)
m_leg   = 6.0     # ASSUMPTION: 2-stage telescopic leg
m_tot   = m_stick + m_panel + m_kb
print(f"propped mass = {m_tot:.0f} g  (241 device + 31 keyboard)")

# ---- pose: device plane 75 deg above desk, leaning back 15 deg from vertical ----
# side view: x horizontal (user at +x), y vertical; stick bottom-front edge at origin.
# device-plane coords: s along plane from bottom edge, w out-of-plane (+ toward user)
th = math.radians(15.0)
def world(s, w):
    return (-s*math.sin(th) + w*math.cos(th), s*math.cos(th) + w*math.sin(th))

parts = {  # name: (mass_g, s_mm, w_mm)
    "stick":    (m_stick, 17.0,   0.0),   # bar: s in [0,34], w in [-11,11]
    "panel":    (m_panel, 69.75,  0.0),   # plate: s in [34,105.5]
    "keyboard": (m_kb,    17.0, -14.75),  # docked on back face, 7.5 mm thick
}
xc = sum(m*world(s, w)[0] for m, s, w in parts.values()) / m_tot
yc = sum(m*world(s, w)[1] for m, s, w in parts.values()) / m_tot
print(f"CoM: x = {xc:.2f} mm, y = {yc:.2f} mm  (x from stick bottom-front edge)")
for name, (m, s, w) in parts.items():
    x, y = world(s, w)
    print(f"  {name:8s} {m:5.0f} g  @ ({x:7.2f}, {y:6.2f}) mm")

# ---- kickstand: hinge at tail-cap back-top corner, leg deploys 0 -> 75 deg ----
# stowed dir (s,w) = (-1,0) (down along back face); deployed = rotate 75 deg off the face
delta = math.radians(75.0)
# solve leg length L so the foot lands exactly on the desk (y=0) at 75 deg
# foot(s,w) = (30 - L*cos75, -11 - L*sin75); y(s,w) = s*cos15 + w*sin15 = 0
L = (30*math.cos(th) - 11*math.sin(th)) / (math.cos(delta)*math.cos(th) + math.sin(delta)*math.sin(th))
hx, hy = world(30.0, -11.0)                       # hinge point
fs, fw = 30 - L*math.cos(delta), -11 - L*math.sin(delta)
fx, fy = world(fs, fw)                            # foot point
print(f"hinge H = ({hx:.2f}, {hy:.2f}) mm")
print(f"leg L = {L:.1f} mm (2-stage telescopic; stowed 34 mm) -> foot F = ({fx:.2f}, {fy:.2f}) mm")
assert abs(fy) < 0.05, "foot must land on desk"

# ---- tip-over: support polygon = [foot_x, stick bottom patch front] ----
front = 10.6   # stick bottom face w in [-11,11] -> x in [-10.6,+10.6]
print(f"support polygon x in [{fx:.1f}, {front:.1f}] mm")
rear_margin, front_margin = xc - fx, front - xc
tip = "NO TIP-OVER" if fx < xc < front else "!!! TIPS OVER !!!"
print(f"tip margins: rear {rear_margin:.1f} mm / front {front_margin:.1f} mm -> {tip}")

# forward push at screen top that would tip it forward (pivot about front corner)
h_top = world(105.5, 0.0)[1]
W = m_tot/1000*g
Pmax = W*front_margin/h_top
print(f"max forward push at screen top before tip-over: {Pmax:.2f} N")
print("note: typing force is downward on the keyboard deck -> stabilising, not tipping")

# ---- leg load in static equilibrium ----
# device CoM sits 3.97 mm ahead of the stick's rear-bottom corner: the slab is
# self-stable on its 21.2 mm deep base; the leg is ~unloaded statically and acts
# as the rear prop / positive 75-deg stop against backward bumps.
print("static leg load ~ 0 N (device self-stable on base; leg = rear prop / angle stop)")

# ---- hinge friction torque ----
# must hold the deployed leg's pose against its own weight + handling disturbance
tau_leg_mNm = m_leg/1000*g*(L/2)*math.cos(math.atan2(hy, hx-fx))  # N.mm = mN.m
# disturbance allowance (ASSUMPTION): 25% of device-weight moment about H, SF 2.0
tau_dev_H = sum(m/1000*g*abs(world(s, w)[0]-hx) for m, s, w in parts.values())  # mN.m
tau_req = (tau_leg_mNm + 0.25*tau_dev_H)*2.0
print(f"hinge torque: leg self-weight moment = {tau_leg_mNm:.2f} mN.m")
print(f"hinge torque: device-weight moment about H = {tau_dev_H:.1f} mN.m")
print(f"REQUIRED = (leg + 25% disturbance allowance) x SF2.0 = {tau_req:.1f} mN.m")
print("SPECIFY: 20 mN.m nominal micro friction hinge, 0-75 deg, detent-free")
print(f"         holding margin on static leg load: {20.0/max(tau_leg_mNm,1e-9):.1f}x")

# ---- ID resistor sanity (keyboard = 33 kOhm, spine divider 10k pull-up to 3V3) ----
for r, name in [(22000, "cooling"), (33000, "keyboard"), (10**9, "open")]:
    v = 3.3*r/(10000+r)
    print(f"ID {name:8s} R={r/1000:6.1f} k -> {v:.3f} V ({v/3.3*4095:.0f} ADC counts @12b)")
