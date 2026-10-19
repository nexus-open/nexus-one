#!/usr/bin/env python3
"""
NEXUS ONE v2.0 — OWN-BRAIN SPINE: power & thermal simulation.

Branch of the v1.0 freeze: Nexus gets its own application processor
(i.MX95-class SoM). v1.0 freeze is NOT modified.

Basis notes (see own_brain_spine.md for citations):
- SoC class: NXP i.MX 95-class (6x Cortex-A55 @2.0GHz, eIQ Neutron 2-TOPS NPU,
  8GB LPDDR5-6400, MIPI-DSI) — published specs via Advantech AOM-5521 / CNX.
- Suspend power: i.MX95 datasheet SUSPEND typical total 30.72 mW (NXP, EVK).
- Active SoC numbers are ASSUMPTIONS (scaled from A55-class norms) — flagged.
- Thermal law (v0.4/v0.6 sims, frozen): folded <=2.0 W, folded+batt <=1.5 W,
  open <=3.0 W sustained. Folded Rth = 8.8 K/W.
"""
import sys

# ---------------------------------------------------------------- constants
RTH_FOLDED   = 8.8    # K/W, from v0.4 thermal sims (frozen)
RTH_OPEN     = 4.0    # K/W, ASSUMPTION (open panel radiates; NOT-VERIFIED)
TJ_MAX       = 105.0  # C, i.MX95 industrial Tj max (NXP datasheet)
T_AMB        = 35.0   # C, worst-case pocket/hand ambient (ASSUMPTION)
CTH          = 15.0   # J/K, heat-spreader-local thermal mass (ASSUMPTION)

LAW_FOLDED        = 2.0
LAW_FOLDED_BATT   = 1.5
LAW_OPEN          = 3.0

BATT_WH        = 13.7   # internal, frozen
BATT_MODULE_WH = 10.0   # battery module, frozen

# Cooling-module effect: raises folded cap by this many watts.
# ASSUMPTION — replace with the modules workstream's delta-T number when known.
COOLING_DP_W = 1.0

# ---------------------------------------------------------------- mode defs
# component draws in watts; 'A' = ASSUMPTION, 'M' = measured/published basis
MODES = {
    "deep_sleep": {
        "desc": "SoC suspend (DDR off), ESP32-S3 light-sleep, all rails gated",
        "comp": [("SoC suspend",   0.031, "M"),   # NXP datasheet Table 20 typical
                 ("ESP32-S3",      0.010, "A"),
                 ("PMIC quiescent",0.005, "A")],
    },
    "stick_idle": {
        "desc": "SoC suspend-to-RAM, ESP32 managing drum/BLE, strip dim",
        "comp": [("SoC STR+DDR SR",0.100, "A"),
                 ("ESP32-S3 active",0.150,"A"),
                 ("strip display dim",0.050,"M"),  # v1.0 stick-idle class
                 ("PMIC+losses",   0.050, "A")],
    },
    "phone_active": {
        "desc": "Open, 4xA55@1.0GHz browsing, display mid, Wi-Fi/BT on",
        "comp": [("SoC 4xA55@1.0G",0.950, "A"),
                 ("GPU light",     0.200, "A"),
                 ("LPDDR5 active", 0.250, "A"),
                 ("display open mid",0.900,"M"),  # v1.0 'open browsing' class
                 ("Wi-Fi+BT",      0.350, "A"),
                 ("ESP32-S3",      0.100, "A"),
                 ("PMIC losses",   0.100, "A")],
    },
    "ai_burst": {
        "desc": "Open, 6xA55@2.0GHz + NPU 2TOPS + display full + Wi-Fi",
        "comp": [("SoC 6xA55@2.0G",3.200, "A"),
                 ("NPU 2 TOPS",    0.800, "A"),
                 ("LPDDR5 6400",   0.500, "A"),
                 ("display full",  1.600, "M"),  # v1.0 'open full bright' class
                 ("Wi-Fi",         0.400, "A"),
                 ("ESP32-S3",      0.100, "A"),
                 ("PMIC losses",   0.300, "A")],
    },
}

DERATED_FOLDED = {   # what folded AI-lite must become to respect the law
    "desc": "Folded AI-lite: 2xA55@800MHz, NPU OFF, strip display",
    "comp": [("SoC 2xA55@800M",0.450, "A"),
             ("LPDDR5 1600",   0.250, "A"),
             ("strip display", 0.250, "A"),
             ("BLE",           0.050, "A"),
             ("ESP32-S3",      0.100, "A"),
             ("PMIC losses",   0.100, "A")],
}

def total(mode):
    return sum(w for _, w, _ in mode["comp"])

def verdict(power, law):
    return "PASS" if power <= law + 1e-9 else "FAIL"

def burst_time(p_burst, p_cap, rth, cth=CTH):
    """Single-shot seconds before Tj hits TJ_MAX, starting from steady state
    at p_cap. Returns inf if burst <= cap."""
    if p_burst <= p_cap:
        return float("inf")
    dt_margin = (TJ_MAX - T_AMB) - p_cap * rth
    if dt_margin <= 0:
        return 0.0
    return cth * dt_margin / (p_burst - p_cap)

# ---------------------------------------------------------------- report
def main():
    W = 72
    print("=" * W)
    print("NEXUS ONE v2.0 OWN-BRAIN SPINE — power & thermal simulation")
    print("Branch of v1.0 freeze (untouched). i.MX95-class SoM basis.")
    print("=" * W)

    print("\n[1] PER-MODE POWER  (M = measured/published basis, A = assumption)")
    print("-" * W)
    hdr = f"{'mode':<14}{'total W':>8}  {'vs folded 2.0W':>14}  {'vs open 3.0W':>12}  {'runtime 13.7Wh':>14}"
    print(hdr)
    print("-" * W)
    for name, m in MODES.items():
        p = total(m)
        rt = BATT_WH / p
        print(f"{name:<14}{p:>8.2f}  {verdict(p, LAW_FOLDED):>14}  "
              f"{verdict(p, LAW_OPEN):>12}  {rt:>10.1f} h")
    print("-" * W)
    for name, m in MODES.items():
        p = total(m)
        print(f"\n  {name} = {p:.2f} W — {m['desc']}")
        for comp, w, tag in m["comp"]:
            print(f"      [{tag}] {comp:<22} {w:5.3f} W")

    print("\n[2] FOLDED DERATE ANALYSIS  (law: <=2.0 W folded, Rth=8.8 K/W)")
    print("-" * W)
    p_ai = total(MODES["ai_burst"])
    p_der = total(DERATED_FOLDED)
    fixed_folded = 0.50  # strip+ESP32+BLE+PMIC with SoC essentially idle
    soc_budget = LAW_FOLDED - fixed_folded
    print(f"  AI burst wants {p_ai:.2f} W folded -> FAIL by {p_ai - LAW_FOLDED:.2f} W.")
    print(f"  Fixed folded loads (strip dim, ESP32, BLE, PMIC) ~= {fixed_folded:.2f} W")
    print(f"  -> SoC+DRAM budget folded = {soc_budget:.2f} W")
    print(f"  Derated folded AI-lite = {p_der:.2f} W -> {verdict(p_der, LAW_FOLDED)}")
    print("  Required clock drops (folded):")
    print("    CPU : 6x A55 @ 2.0 GHz  ->  2x A55 @ 800 MHz (4 cores power-gated)")
    print("    NPU : eIQ Neutron ON    ->  OFF (power-gated; 2 TOPS unavailable)")
    print("    DDR : LPDDR5 6400 MT/s  ->  1600 MT/s")
    print("    DISP: full panel 1.6 W   ->  strip only 0.25 W")
    print("    GPU : on                 ->  off")
    print(f"  Folded+battery-module law (<= {LAW_FOLDED_BATT} W): derate harder ->")
    print("    1x A55 @ 600 MHz, NPU off, strip display ~= 1.20 W -> PASS")

    print("\n[3] BURST-TIME BEFORE THERMAL CAP TRIPS")
    print(f"    (Tj_max={TJ_MAX:.0f}C, Tamb={T_AMB:.0f}C, Cth={CTH:.0f} J/K ASSUMPTION)")
    print("-" * W)
    for cth in (10.0, CTH, 25.0):
        tf = burst_time(p_ai, LAW_FOLDED, RTH_FOLDED, cth)
        to = burst_time(p_ai, LAW_OPEN, RTH_OPEN, cth)
        print(f"  Cth={cth:4.0f} J/K : folded burst {tf:6.1f} s ({tf/60:4.1f} min) | "
              f"open burst {to:6.1f} s ({to/60:4.1f} min)")
    print("  HONEST RESULT: full AI power is OPEN-MODE ONLY, and even open it is")
    print("  BURST-DUTY (3.7 min at Cth=15 before Tj hits 105C), not sustained.")

    print("\n[4] COOLING MODULE EFFECT  (ASSUMPTION: +%.1f W folded cap)" % COOLING_DP_W)
    print("-" * W)
    cap_c = LAW_FOLDED + COOLING_DP_W
    print(f"  Folded cap with cooler: {cap_c:.1f} W")
    print(f"  AI burst {p_ai:.2f} W vs {cap_c:.1f} W -> {verdict(p_ai, cap_c)} (still burst-only)")
    print(f"  Derated folded AI-lite {p_der:.2f} W -> {verdict(p_der, cap_c)} with headroom")
    tf_c = burst_time(p_ai, cap_c, RTH_FOLDED)
    print(f"  Cooled folded burst time: {tf_c:.1f} s ({tf_c/60:.1f} min) at Cth={CTH:.0f}")
    print("  NOTE: higher sustained cap -> higher steady-state temp -> less burst")
    print("  margin. Replace COOLING_DP_W with the modules workstream's number.")

    print("\n[5] BATTERY RUNTIME (13.7 Wh internal; +10 Wh module in parens)")
    print("-" * W)
    for name, m in MODES.items():
        p = total(m)
        print(f"  {name:<14} {BATT_WH/p:6.1f} h   ({(BATT_WH+BATT_MODULE_WH)/p:6.1f} h)")

    print("\n[6] ASSUMPTIONS (replace with measurements when hardware exists)")
    print("-" * W)
    print("  A1 SoC active draws scaled from A55-class norms (no i.MX95 full-load")
    print("     EVK number recovered from AN14449 in this pass).")
    print("  A2 Rth_open = 4.0 K/W (open panel radiates; needs v0.4-style sim).")
    print("  A3 Cth = 15 J/K local thermal mass (needs thermal test).")
    print("  A4 Cooling module raises folded cap by +1.0 W (pending modules agent).")
    print("  A5 Tamb = 35 C worst case (pocket/hand).")
    print("=" * W)
    return 0

if __name__ == "__main__":
    sys.exit(main())
