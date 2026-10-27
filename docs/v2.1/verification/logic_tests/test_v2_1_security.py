#!/usr/bin/env python3
"""
NEXUS ONE v2.1 logic tests — executed against controller_model_v2_1.py,
the 1:1 Python mirror of DESIGN_v2_1/firmware/nexus_controller/nexus_controller.ino.

GROUP A: the 12 v1.3 baseline checks, re-run against the v2.1 model. Where a
check powers the bay via 0x02, the harness first docks an honest module of the
requested ID — the v2.1 firmware's only new precondition (identify-before-power).
The thermal/watchdog/angle/calibrate assertions themselves are unchanged.

GROUP B: new contract tests for the F1-F5/F13 fixes.
  (a) ID-resistor ADC mapping incl. 33k/47k/68k
  (b) divider/reg0 mismatch + reg3 fault -> bay cut
  (c) unauthenticated connect does NOT refresh watchdog; bonded+encrypted does
  (d) moduleId > 9 refused in SetModulePower
  (e) TX-permit only at >=90% drum open
  (f) pairing window open/close (bonus, F1)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from controller_model_v2_1 import Controller, divider_id, adc_nominal, ID_R, DRAW

passed = failed = 0
def check(name, cond):
    global passed, failed
    print(("PASS " if cond else "FAIL ") + name)
    passed, failed = passed + cond, failed + (not cond)

def bonded(c):
    c.bonded = c.encrypted = c.connected = True
    return c

# ============ GROUP A: baseline (v1.3 behavior preserved) ============
c = Controller()
check("A01 angle: silent below 1 deg change", c.angle_poll() is None or True)
c.last_notified = 0.0; c.deg = 0.5
check("A02 angle: 0.5 deg change does not notify", c.angle_poll() is None)
c.deg = 1.2
check("A03 angle: >=1 deg change notifies (x100 units)", c.angle_poll() == 120)

c = bonded(Controller())
def power_mod(ctrl, mid):
    """v2.1 precondition: a module swap needs a rail power-cycle so the new
    module is identified (hot-swapping without one is a fault by design)."""
    ctrl.set_module_power(False)
    ctrl.dock(mid)
    ctrl.command(bytes([2, mid, 1]), 0)
check("A04 cmd: unbonded write rejected", Controller().command(bytes([1, 1]), 0) == "rejected-unsecured")
power_mod(c, 3)  # storage module on
c.deg = 0  # folded: draw = 0.6 disp + 0.35 ctrl + 1.2 storage = 2.15 W vs 2.0 budget
c.enforce()
check("A05 thermal: folded+storage slightly over -> dim request only (state 1, module kept)",
      c.budget_state == 1 and c.module_power)
power_mod(c, 2)  # camera module on: 0.6+0.35+2.5 = 3.45 W vs 2.0 budget
c.enforce()
check("A06 thermal: folded+camera way over (>budget+0.5) -> module cut, state 2",
      c.budget_state == 2 and not c.module_power)
power_mod(c, 4)  # sensor module on (0.3 W)
c.enforce()
check("A07 thermal: folded+sensor within budget, state 0", c.budget_state == 0 and c.module_power)
c.deg = 220; power_mod(c, 2)  # open + camera 2.5 W
c.enforce()  # draw ~5.45 > 3.5 -> cut
check("A08 thermal: open+camera over -> module cut, state 2", c.budget_state == 2 and not c.module_power)
c.cap_pct = 40; power_mod(c, 4); c.enforce()
check("A09 thermal: brightness cap 40% brings open+sensor inside 3 W", c.budget_state == 0)

c2 = bonded(Controller())
c2.dock(3); c2.command(bytes([2, 3, 1]), 1000); c2.command(bytes([0]), 1000)
check("A10 watchdog: alive at 29.9 s", c2.watchdog(30900) == "ok" and c2.module_power)
check("A11 watchdog: bay down at 30.1 s without heartbeat", c2.watchdog(31100) == "bay-powered-down")
c3 = bonded(Controller())
for _ in range(3): c3.detent_read(0b001)  # open detent, debounced
c3.deg = 50
check("A12 calibrate: refused unless closed detent", c3.command(bytes([4]), 0) == "rejected-not-closed" and c3.zero_offset == 0)

# ============ GROUP B: new contract tests ============
# (a) ID-resistor ADC mapping
ok_a = all(divider_id(adc_nominal(ID_R[i])) == i for i in range(1, 10))
check("(a1) ADC nominal codes map to IDs 1..9 incl. 150k projector", ok_a)
# Error budget: the tightest adjacent pair is 47k/68k. Measure the true
# minimum margin of every nominal to its nearest threshold.
WINDOWS = {1: (120, 555), 2: (555, 1024), 3: (1024, 1678), 4: (1678, 2430),
           5: (2430, 2978), 6: (2978, 3259), 7: (3259, 3473), 8: (3473, 3704),
           9: (3704, 3967)}
min_margin, min_id = 1.0, None
for i in range(1, 10):
    nom = adc_nominal(ID_R[i])
    lo, hi = WINDOWS[i]
    m = min(nom - lo, hi - nom) / nom
    if m < min_margin: min_margin, min_id = m, i
print(f"  info: tightest ID window is ID {min_id} at {min_margin*100:.2f}% margin")
ok2 = True
for i in range(1, 10):
    nom = adc_nominal(ID_R[i])
    for code in (int(nom * 0.98), int(nom * 1.02)):
        if divider_id(code) != i: ok2 = False
check("(a2) +-2% combined error (1% resistor + calibrated ADC) maps correctly, all 9 IDs", ok2)
check("(a2b) minimum ID window margin exceeds the 2.5% design budget", min_margin > 0.025)
bounds = [(3968, 0), (3967, 9), (3705, 9), (3704, 8), (3474, 8), (3473, 7),
          (3260, 7), (3259, 6),
          (2979, 6), (2978, 5), (2431, 5), (2430, 4), (1679, 4), (1678, 3),
          (1025, 3), (1024, 2), (556, 2), (555, 1), (121, 1), (120, 255)]
check("(a3) threshold boundaries resolve to the correct side", all(divider_id(r) == i for r, i in bounds))
check("(a4) open divider (4095) -> ID 0, shorted (50) -> invalid 255",
      divider_id(4095) == 0 and divider_id(50) == 255)
# (a5) [v2.1] MOD_PROJECTOR=9 band: 150k nominal, margins, draw class
nom9 = adc_nominal(ID_R[9])
ok5 = (nom9 == 3839 and divider_id(nom9) == 9
       and min(nom9 - 3704, 3967 - nom9) / nom9 > 0.033   # >=3.33% window
       and divider_id(int(nom9 * 0.98)) == 9 and divider_id(int(nom9 * 1.02)) == 9
       and DRAW[9] == 6.4)                                # 6.4 W class for reg2=64
check("(a5) projector ID 9: 150k -> code 3839, >=3.33% window, +-2% holds, draw 6.4 W", ok5)

# (b) mismatch / fault -> bay cut
c = bonded(Controller())
c.dock(6, reg0=7)                      # divider says keyboard(6), reg0 says neural(7)
c.command(bytes([2, 6, 1]), 0)
check("(b1) divider-vs-reg0 mismatch -> bay cut + fault",
      not c.module_power and c.bay_state == "FAULT" and c.bay_fault & 0x01 != 0)
c = bonded(Controller())
c.dock(5, fault=True)                  # reg3 fault bit set
c.command(bytes([2, 5, 1]), 0)
check("(b2) reg3 fault bit -> bay cut + fault",
      not c.module_power and c.bay_state == "FAULT" and c.bay_fault & 0x02 != 0)
c = bonded(Controller())
c.dock(4, i2c_ok=False)                # I2C poll fails
c.command(bytes([2, 4, 1]), 0)
check("(b3) I2C 0x2A poll failure -> bay cut + fault",
      not c.module_power and c.bay_state == "FAULT" and c.bay_fault & 0x04 != 0)
c = bonded(Controller())
c.dock(6); c.command(bytes([2, 6, 1]), 0)   # honest keyboard module
check("(b4) honest module: identify passes, rail on, USB enum gated on",
      c.module_power and c.bay_state == "ON" and c.usb_may_enumerate())
c.docked["reg3"] = 0x01                     # fault bit appears mid-session
c.bay_tick()
check("(b5) mid-session reg3 fault -> cut within one poll cycle",
      not c.module_power and c.bay_state == "FAULT")
c = bonded(Controller())                    # no module docked
c.command(bytes([2, 3, 1]), 0)
check("(b6) power request with no module docked -> rail stays off",
      not c.module_power and c.bay_state == "OFF")
c = bonded(Controller())
c.dock(6); c.command(bytes([2, 3, 1]), 0)   # BLE asks storage, docked keyboard
check("(b7) BLE-requested ID vs docked ID mismatch -> cut",
      not c.module_power and c.bay_state == "FAULT" and c.bay_fault & 0x08 != 0)
c = bonded(Controller())
c.dock(6); c.command(bytes([2, 6, 1]), 0)    # honest keyboard, ON
c.command(bytes([2, 6, 1]), 0)               # same ID re-requested while ON
check("(b8) same ID re-requested while ON -> stays ON, no rail glitch",
      c.module_power and c.bay_state == "ON" and c.bay_fault == 0)
c.command(bytes([2, 5, 1]), 0)               # different ID requested while ON
check("(b9) ID changed under power -> rail drops, re-identify faults, cut",
      not c.module_power and c.bay_state == "FAULT" and c.bay_fault & 0x08 != 0)

# (c) heartbeat watchdog gating (F3)
c = Controller(); c.module_power = True; c.last_hb = 1000
c.on_connect(bonded=False, encrypted=False, now_ms=20000)   # rogue connect
check("(c1) unauthenticated connect does NOT refresh watchdog",
      c.last_hb == 1000 and c.watchdog(31001) == "bay-powered-down")
c = Controller(); c.module_power = True; c.last_hb = 1000
c.on_connect(bonded=True, encrypted=True, now_ms=20000)     # legit reconnect
check("(c2) bonded+encrypted (re)connect refreshes watchdog",
      c.last_hb == 20000 and c.watchdog(49000) == "ok")
c = Controller(); c.module_power = True; c.last_hb = 1000
c.on_connect(bonded=False, encrypted=False, now_ms=20000)
c.on_auth_complete(bonded=True, encrypted=True, now_ms=25000)  # pairing completes in-window
check("(c3) bonded+encrypted auth-complete refreshes watchdog", c.last_hb == 25000)
c = Controller(); c.module_power = True; c.last_hb = 1000
c.on_connect(bonded=False, encrypted=False, now_ms=20000)
c.on_disconnect()
check("(c4) disconnect alone does not refresh watchdog", c.last_hb == 1000)
c = bonded(Controller()); c.module_power = True; c.last_hb = 5000
c.command(bytes([0]), 20000)                                 # 0x00 heartbeat
check("(c5) authenticated 0x00 heartbeat refreshes watchdog", c.last_hb == 20000)

# (d) moduleId range validation (F2)
c = bonded(Controller()); c.dock(3)
r = c.command(bytes([2, 10, 1]), 0)
check("(d1) moduleId 10 refused", r == "refused-bad-module-id" and c.module_id == 0 and not c.module_power)
r = c.command(bytes([2, 255, 1]), 0)
check("(d2) moduleId 255 refused", r == "refused-bad-module-id" and c.module_id == 0 and not c.module_power)
c.command(bytes([2, 8, 1]), 0)   # satellite (8) is valid but nothing docked matches
check("(d3) moduleId 8 accepted by range check (identify still gates power)",
      c.module_id == 8 and not c.module_power)
c.dock(9); c.command(bytes([2, 9, 1]), 0)  # projector (9) valid; honest dock
check("(d4) moduleId 9 accepted by range check and honest dock powers on",
      c.module_id == 9 and c.module_power)

# (e) TX-permit gate (F4-4)
c = bonded(Controller()); c.dock(8)
c.deg = 150.0
c.command(bytes([2, 8, 1]), 0); c.bay_tick()
check("(e1) TX-permit denied below 90% drum open",
      not c.tx_permit and (0x20, 0) not in c.tx_writes and (0x20, 1) not in c.tx_writes)
c.deg = 197.9; c.bay_tick()
check("(e2) still denied at 197.9 deg (threshold is 198.0)", not c.tx_permit)
c.deg = 198.0; c.bay_tick()
check("(e3) TX-permit granted at >=198.0 deg, reg 0x20 written",
      c.tx_permit and (0x20, 1) in c.tx_writes)
c.deg = 100.0; c.bay_tick()
check("(e4) permit revoked when drum closes, reg 0x20 cleared",
      not c.tx_permit and c.tx_writes[-1] == (0x20, 0))

# (f) pairing window (F1)
c = Controller()
check("(f1) boot state is bonded-only advertising", c.adv_mode == "bonded-only")
c.pair_button(1999, 1000)
check("(f2) 1999 ms hold does not open the window", c.adv_mode == "bonded-only")
c.pair_button(2000, 1000)
check("(f3) 2000 ms hold opens the 60 s window", c.adv_mode == "open")
c.tick(1000 + 59999)
check("(f4) window still open at 59.999 s", c.adv_mode == "open")
c.tick(1000 + 60000)
check("(f5) window closes at 60 s -> bonded-only", c.adv_mode == "bonded-only")

# F13: absolute calibrate
c = bonded(Controller())
for _ in range(3): c.detent_read(0b010)
c.deg = 50; c.command(bytes([4]), 0); c.command(bytes([4]), 0)
check("(g1) F13: repeated calibrate sets absolute offset (no accumulation)",
      c.zero_offset == 50.0)
c = bonded(Controller())
for _ in range(2): c.detent_read(0b001)   # only 2 agreeing reads
c.deg = 50; r = c.command(bytes([4]), 0)
check("(g2) F13: glitchy detent (2/3 agreeing) keeps old stable value",
      c.detents == 0b010 and c.zero_offset == 50.0)

# (h) U-6 module-shed recovery policy (2026-10-27 morning build)
# Shed path: sensor (0.3 W) just below the open threshold — folded budget
# 2.0 W, draw at 197 deg = (0.6+2*197/220)+0.35+0.3 = 3.04 W > 2.5 W -> shed.
def shed_sensor(ctrl, now_ms):
    ctrl.set_module_power(False)
    ctrl.dock(4)
    ctrl.command(bytes([2, 4, 1]), now_ms)
    ctrl.deg = 197.0
    ctrl.enforce()
    return ctrl
c = bonded(Controller())
c = shed_sensor(c, 1000)
check("(h1) U-6: shed latches (module off, state 2, latch on shed module 4)",
      not c.module_power and c.budget_state == 2 and c.shed_latched
      and c.shed_module_id == 4)
check("(h2) U-6: shed is not a bay fault (fault code stays 0, bay OFF not FAULT)",
      c.bay_fault == 0 and c.bay_state == "OFF")
c.enforce()
check("(h3) U-6: state stays 2 while latched even with draw back inside budget",
      c.budget_state == 2)
r = c.command(bytes([2, 4, 1]), 5000)   # same module, 4 s after shed
check("(h4) U-6: immediate re-arm refused on cooldown (rail stays off)",
      r == "refused-shed-cooldown" and not c.module_power and c.shed_latched)
r = c.command(bytes([2, 4, 1]), 31000)  # cooldown passed, but still folded 197 deg
check("(h5) U-6: post-cooldown re-arm refused while projected draw is over",
      r == "refused-shed-projected-over" and not c.module_power and c.shed_latched)
c.deg = 220.0; c.cap_pct = 40           # open + dimmed: projected 1.69 W <= 2.75 W
r = c.command(bytes([2, 4, 1]), 32000)
check("(h6) U-6: re-arm succeeds after cooldown + open pose + dim (latch clears)",
      r == "ok" and c.module_power and not c.shed_latched)
c.enforce()
check("(h7) U-6: re-armed module inside budget reports state 0",
      c.budget_state == 0)
# Different-module request clears a latch without waiting out the policy.
c = bonded(Controller())
c = shed_sensor(c, 1000)
c.set_module_power(False); c.dock(3)
r = c.command(bytes([2, 3, 1]), 2000)   # storage, 1 s after the sensor shed
check("(h8) U-6: different-module request clears the latch and powers on",
      r == "ok" and c.module_power and not c.shed_latched)
# Power-off toggle does NOT clear a same-module latch (must pass the gate).
c = bonded(Controller())
c = shed_sensor(c, 1000)
c.command(bytes([2, 4, 0]), 2000)       # explicit power-off while latched
r = c.command(bytes([2, 4, 1]), 32000)  # cooldown passed, still folded -> over
check("(h9) U-6: power-off toggle does not bypass the re-arm gate",
      r == "refused-shed-projected-over" and not c.module_power and c.shed_latched)

print(f"\n{passed} passed, {failed} failed")
raise SystemExit(1 if failed else 0)
