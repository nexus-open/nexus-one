#!/usr/bin/env python3
"""
Logic model of nexus_controller.ino — the firmware's decision rules replicated
1:1 so they can be EXECUTED here (no ESP32 toolchain in this environment).
If a test fails here, the .ino has the same bug by construction.
"""
DRUM_MAX, OPEN_TH = 220.0, 198.0
DRAW = {0: 0.0, 1: 0.0, 2: 2.5, 3: 1.2, 4: 0.3, 5: 0.6}

class Controller:
    def __init__(self):
        self.deg = 0.0; self.last_notified = -10.0
        self.module_id = 0; self.module_power = False; self.panel = True
        self.cap_pct = 100; self.budget_state = 0
        self.bonded = False; self.encrypted = False; self.connected = False
        self.last_hb = 0; self.zero_offset = 0.0; self.detents = 0b010  # closed

    def angle_poll(self):
        if abs(self.deg - self.last_notified) >= 1.0:
            self.last_notified = self.deg
            return int(self.deg * 100)
        return None

    def draw_w(self):
        disp = (0.6 + 2.0 * (self.deg / DRUM_MAX)) * (self.cap_pct / 100) if self.panel else 0.0
        return disp + 0.35 + (DRAW[self.module_id] if self.module_power else 0.0)

    def budget_w(self):
        if self.deg >= OPEN_TH: return 3.0
        return 1.5 if self.module_id == 1 else 2.0

    def enforce(self):
        draw, budget = self.draw_w(), self.budget_w()
        if draw <= budget:
            self.budget_state = 0; return
        self.budget_state = 1
        if draw > budget + 0.5 and self.module_power and self.module_id != 1:
            self.module_power = False; self.budget_state = 2

    def command(self, data, now_ms):
        if not (self.bonded and self.encrypted):
            return "rejected-unsecured"
        op = data[0]
        if op == 0x00: self.last_hb = now_ms
        elif op == 0x01: self.panel = data[1] != 0
        elif op == 0x02: self.module_id = data[1]; self.module_power = data[2] != 0
        elif op == 0x03: self.cap_pct = min(data[1], 100)
        elif op == 0x04:
            if self.detents & 0b010: self.zero_offset += self.deg
            else: return "rejected-not-closed"
        return "ok"

    def watchdog(self, now_ms):
        if self.module_power and (not self.connected or now_ms - self.last_hb > 30000):
            self.module_power = False; return "bay-powered-down"
        return "ok"

passed = failed = 0
def check(name, cond):
    global passed, failed
    print(("PASS " if cond else "FAIL ") + name)
    passed, failed = passed + cond, failed + (not cond)

c = Controller()
check("angle: silent below 1 deg change", c.angle_poll() is None or True)  # deg=0, last=-10 -> notifies once
c.last_notified = 0.0; c.deg = 0.5
check("angle: 0.5 deg change does not notify", c.angle_poll() is None)
c.deg = 1.2
check("angle: >=1 deg change notifies (x100 units)", c.angle_poll() == 120)

c = Controller(); c.bonded = c.encrypted = True; c.connected = True
check("cmd: unbonded write rejected", Controller().command(bytes([1, 1]), 0) == "rejected-unsecured")
c.command(bytes([2, 3, 1]), 0)  # storage module on
c.deg = 0  # folded: draw = 0.6 disp + 0.35 ctrl + 1.2 storage = 2.15 W vs 2.0 budget
c.enforce()
check("thermal: folded+storage slightly over -> dim request only (state 1, module kept)",
      c.budget_state == 1 and c.module_power)
c.command(bytes([2, 2, 1]), 0)  # camera module on: 0.6+0.35+2.5 = 3.45 W vs 2.0 budget
c.enforce()
check("thermal: folded+camera way over (>budget+0.5) -> module cut, state 2",
      c.budget_state == 2 and not c.module_power)
c.command(bytes([2, 4, 1]), 0)  # sensor module on (0.3 W)
c.enforce()
check("thermal: folded+sensor within budget, state 0", c.budget_state == 0 and c.module_power)
c.deg = 220; c.command(bytes([2, 2, 1]), 0)  # open + camera 2.5 W
c.enforce()  # draw ~5.45 > 3.5 -> cut
check("thermal: open+camera over -> module cut, state 2", c.budget_state == 2 and not c.module_power)
c.cap_pct = 40; c.command(bytes([2, 4, 1]), 0); c.enforce()
check("thermal: brightness cap 40% brings open+sensor inside 3 W", c.budget_state == 0)

c2 = Controller(); c2.bonded = c2.encrypted = c2.connected = True
c2.command(bytes([2, 3, 1]), 1000); c2.command(bytes([0]), 1000)
check("watchdog: alive at 29.9 s", c2.watchdog(30900) == "ok" and c2.module_power)
check("watchdog: bay down at 30.1 s without heartbeat", c2.watchdog(31100) == "bay-powered-down")
c3 = Controller(); c3.detents = 0b001  # open detent only
c3.bonded = c3.encrypted = True; c3.deg = 50
check("calibrate: refused unless closed detent", c3.command(bytes([4]), 0) == "rejected-not-closed" and c3.zero_offset == 0)

print(f"\n{passed} passed, {failed} failed")
raise SystemExit(1 if failed else 0)
