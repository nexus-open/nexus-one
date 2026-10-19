# Bench Plan — first physical electronics (when parts access exists)

Wiring: `bench_wiring.svg`. Philosophy: test the Stage-1 architecture on a
bench before any housing exists. Every test has a pass line tied to a
simulator number — if reality disagrees, the simulator gets fixed, not the
other way around.

**Safety, always:** bench PSU current-limited for first power-ups; LiPo only
with its protection PCB, never punctured/bent, charged attended; no soldering
near the cell; if anything gets hot, smells, or swells — disconnect, stop.

| Test | Setup | Pass criteria (from sims) |
|---|---|---|
| B1 Panel power | Host phone → driver → panel, inline USB meter | Full-brightness draw within ±30% of the 2.6 W model (v0.8); strip/dim near 0.6 W |
| B2 Drum encoder | AS5600 + magnet on a hand drum mock (R8, marked degrees) | Reported angle within ±2° across 0–220°; monotonic, no dropouts |
| B3 Thermal soak | 2 W resistor load inside a foam box of housing volume, thermometer probe | Rise within ±25% of +17.6 K folded model (v0.4); repeat at 3 W vs +18.4 K device model (v0.6) |
| B4 Charge | Charger class board + gauge, 5 V/2 A in | Full charge 1.6 h ±30%; gauge % tracks a timed discharge within ±5% |
| B5 FPC loop flex | Panel tail FPC formed at R6 loop (v0.7), hand-flex rig | 500 cycles, then inspect under phone macro: no visible cracks/delamination; continuity stable |
| B6 BLE link | ESP32-S3 dev board + launcher skeleton on host phone | DrumAngle notifications at ≥1° changes; commands refused when unbonded (protocol security rule) |

Sequencing: B1 → B4 → B2 → B3 → B5 → B6. Record every result in a bench log;
any FAIL reopens the matching design version (that is what the freeze's
change rule is for).
