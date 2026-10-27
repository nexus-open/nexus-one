#!/usr/bin/env python3
"""
Logic model of nexus_controller.ino v2.1 (security branch) — the firmware's
decision rules replicated 1:1 so they can be EXECUTED here.
Mirrors: DESIGN_v2_1/firmware/nexus_controller/nexus_controller.ino
New vs the v1.3 model: pairing window, moduleId 0..9 validation, F3 watchdog
gating, bay identify-before-power contract, absolute calibrate + debounced
detents, TX-permit gate.
"""
DRUM_MAX, OPEN_TH = 220.0, 198.0
DRAW = {0: 0.0, 1: 0.0, 2: 2.5, 3: 1.2, 4: 0.3, 5: 0.6,
        6: 0.5, 7: 2.0, 8: 3.0, 9: 6.4}
ID_R = {1: 1000, 2: 2200, 3: 4700, 4: 10000, 5: 22000,
        6: 33000, 7: 47000, 8: 68000, 9: 150000}
ADC_MAX = 4095


def adc_nominal(r_ohms):
    """Nominal 12-bit code for a coding resistor (10k pull-up, 3V3 ref); open -> 4095."""
    return ADC_MAX if r_ohms == 0 else int(round(ADC_MAX * r_ohms / (10000 + r_ohms)))


def divider_id(raw):
    """Mirror of bayDividerId(): thresholds at midpoints between nominals."""
    if raw > 3967: return 0
    if raw > 3704: return 9   # [v2.1] 150k projector
    if raw > 3473: return 8
    if raw > 3259: return 7
    if raw > 2978: return 6
    if raw > 2430: return 5
    if raw > 1678: return 4
    if raw > 1024: return 3
    if raw > 555:  return 2
    if raw > 120:  return 1
    return 255  # shorted/invalid


class Controller:
    def __init__(self):
        self.deg = 0.0; self.last_notified = -10.0
        self.module_id = 0; self.module_power = False; self.panel = True
        self.cap_pct = 100; self.budget_state = 0
        # [v2.1/U-6] shed latch + re-arm gate (mirror of nexus_controller.ino):
        # shed_latched survives power-off toggles; it clears only on a
        # passing re-arm or a different-module request. now_ms tracks the
        # last command timestamp (the model's millis()).
        self.shed_latched = False; self.shed_module_id = 0; self.shed_at_ms = 0
        self.now_ms = 0
        self.bonded = False; self.encrypted = False; self.connected = False
        self.last_hb = 0; self.zero_offset = 0.0
        # debounced detents: 3 consecutive agreeing reads; start closed
        self._det_last = None; self._det_agree = 0; self.detents = 0b010
        # pairing window
        self.adv_mode = "bonded-only"; self._hold_start = None
        self._window_until = None
        # bay contract
        self.bay_state = "OFF"          # OFF / ON / FAULT
        self.bay_requested = 0
        self.bay_identified = 0
        self.bay_fault = 0
        self.docked = None             # physical module or None
        self.tx_permit = False
        self.tx_writes = []            # log of reg 0x20 writes (for tests)
        self.bay_requested_power = False

    # ---- sensors / detents ----
    def detent_read(self, raw):
        """One raw GPIO read; mirrors detentBitsDebounced()."""
        if raw == self._det_last:
            self._det_agree += 1
        else:
            self._det_last = raw; self._det_agree = 1
        if self._det_agree >= 3:
            self.detents = raw

    # ---- thermal law (unchanged) ----
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
        # [v2.1/U-6] latched shed reports state 2 even with the module off
        # and the draw back inside budget — "waiting for re-arm", not "OK".
        if self.shed_latched:
            self.budget_state = 2; return
        draw, budget = self.draw_w(), self.budget_w()
        if draw <= budget:
            self.budget_state = 0; return
        self.budget_state = 1
        if draw > budget + 0.5 and self.module_power and self.module_id != 1:
            self.shed_latched = True; self.shed_module_id = self.module_id
            self.shed_at_ms = self.now_ms
            self.set_module_power(False); self.budget_state = 2

    def _projected_draw_w(self):
        """Draw if the requested module were on now (pose + cap + table)."""
        disp = (0.6 + 2.0 * (self.deg / DRUM_MAX)) * (self.cap_pct / 100) if self.panel else 0.0
        return disp + 0.35 + DRAW[self.module_id]

    # ---- bay contract (F4) ----
    def dock(self, mod_id, draw_w=None, fault=False, reg0=None, i2c_ok=True):
        """Physically dock a module: divider resistor + I2C regs 0-3."""
        self.docked = {
            "divider_id": mod_id,
            "reg0": mod_id if reg0 is None else reg0,
            "reg1": 0x01,
            "reg2": int(round((DRAW[mod_id] if draw_w is None else draw_w) * 10)),
            "reg3": 0x01 if fault else 0x00,
            "i2c_ok": i2c_ok,
        }

    def undock(self):
        self.docked = None

    def _bay_identify(self):
        d = self.docked
        if d is None:
            return False  # no module -> request stays pending, rail stays off
        div = divider_id(adc_nominal(ID_R[d["divider_id"]]))
        if div in (0, 255):
            self.bay_fault |= 0x01; return False
        if not d["i2c_ok"]:
            self.bay_fault |= 0x04; return False
        if d["reg0"] != div:
            self.bay_fault |= 0x01; return False
        if self.bay_requested != 0 and d["reg0"] != self.bay_requested:
            self.bay_fault |= 0x08; return False
        if abs(d["reg2"] * 0.1 - DRAW[d["reg0"]]) > 0.15:
            self.bay_fault |= 0x01; return False
        if d["reg3"] & 0x01:
            self.bay_fault |= 0x02; return False
        self.bay_identified = d["reg0"]
        return True

    def bay_tick(self):
        """Mirror of bayTick(): identify on request, re-poll while ON."""
        if self.bay_state == "OFF":
            if self.bay_requested_power and self.docked is not None:
                self.bay_fault = 0
                if self._bay_identify():
                    self.bay_state = "ON"
                    self.module_id = self.bay_identified
                    self.module_power = True
                else:
                    self.bay_state = "FAULT"
                    self.module_power = False
            return
        if self.bay_state == "ON":
            d = self.docked
            if d is None or not d["i2c_ok"]:
                self.bay_fault |= 0x04; self._bay_cut(); return
            if d["reg0"] != self.bay_identified:
                self.bay_fault |= 0x01; self._bay_cut(); return
            if d["reg3"] & 0x01:
                self.bay_fault |= 0x02; self._bay_cut(); return
            permit = self.deg >= OPEN_TH
            if permit != self.tx_permit:
                self.tx_permit = permit
                self.tx_writes.append((0x20, 1 if permit else 0))
            self.module_power = True

    def _bay_cut(self):
        self.bay_state = "FAULT"; self.module_power = False
        self.tx_permit = False

    def set_module_power(self, on):
        # [v2.1/U-6] re-arm gate (mirror of setModulePower(true) in the .ino):
        # same-module re-arm needs cooldown + projected draw <= budget-0.25;
        # a failed gate leaves the rail off and the latch set. Returns a
        # refusal string on gate failure, None otherwise.
        if on and self.shed_latched:
            if self.module_id != self.shed_module_id:
                self.shed_latched = False      # different module: fresh start
            else:
                if (self.now_ms - self.shed_at_ms < 30000
                        or self._projected_draw_w() > self.budget_w() - 0.25):
                    self.budget_state = 2
                    return ("refused-shed-cooldown" if self.now_ms - self.shed_at_ms < 30000
                            else "refused-shed-projected-over")
                self.shed_latched = False      # gate passed: re-arm proceeds
        self.bay_requested_power = on
        if not on:
            self.bay_state = "OFF"; self.module_power = False
            self.bay_fault = 0; self.tx_permit = False
        return None

    def usb_may_enumerate(self):
        return self.bay_state == "ON"

    # ---- BLE connection / pairing window (F1/F3/F7) ----
    def on_connect(self, bonded, encrypted, now_ms):
        if self.connected:
            return "rejected-slot-busy"   # F7: single connection
        self.connected = True
        self.bonded, self.encrypted = bonded, encrypted
        if bonded and encrypted:          # F3: only authenticated refresh
            self.last_hb = now_ms
        return "ok"

    def on_auth_complete(self, bonded, encrypted, now_ms):
        self.bonded, self.encrypted = bonded, encrypted
        if bonded and encrypted:          # F3
            self.last_hb = now_ms

    def on_disconnect(self):
        self.connected = False; self.bonded = False; self.encrypted = False
        self.adv_mode = "bonded-only"

    def pair_button(self, held_ms, now_ms):
        """2 s debounced hold opens a 60 s window; call tick() to age it."""
        if held_ms >= 2000:
            self.adv_mode = "open"
            self._window_until = now_ms + 60000

    def tick(self, now_ms):
        if self._window_until is not None and now_ms >= self._window_until:
            self._window_until = None
            self.adv_mode = "bonded-only"

    # ---- commands ----
    def command(self, data, now_ms):
        self.now_ms = now_ms                 # model millis() for shed timing
        if not (self.bonded and self.encrypted):
            return "rejected-unsecured"
        op = data[0]
        if op == 0x00:
            self.last_hb = now_ms
        elif op == 0x01:
            self.panel = data[1] != 0
        elif op == 0x02:
            mid = data[1]
            if mid > 9:                        # F2: refuse unknown IDs (0..9 known)
                return "refused-bad-module-id"
            power_on = data[2] != 0
            if power_on and (self.bay_state != "ON" or self.bay_identified != mid):
                # (re-)identify: rail off until the cross-check proves the ID
                self.bay_state = "OFF"; self.module_power = False
                self.tx_permit = False
            self.bay_requested = mid
            self.module_id = mid
            refused = self.set_module_power(power_on)
            if refused is not None:
                return refused               # [v2.1/U-6] re-arm gate refused
            if power_on:
                self.bay_tick()                # identify runs on the poll cycle
        elif op == 0x03:
            self.cap_pct = min(data[1], 100)
        elif op == 0x04:
            if self.detents & 0b010:
                self.zero_offset = self.deg   # F13: absolute, not accumulating
            else:
                return "rejected-not-closed"
        return "ok"

    def watchdog(self, now_ms):
        if self.module_power and (not self.connected or now_ms - self.last_hb > 30000):
            self.set_module_power(False); return "bay-powered-down"
        return "ok"
