# NEXUS ONE v2.0 — Tablet second-axis design (target #1)

**Winner: opposed dual-roll.** One continuous panel (162.9 × 145.8 × 1.2, usable
162.9 × 142.8); drum 1 (+Y) is the untouched v1.0 phone mechanism; drum 2 (−Y)
carries the 71.3 mm tablet reserve (up to one full turn, R8). No seam, no
thickness growth, manual operation.

## Concept comparison (all numbers computed — see concepts.py)

| | (b) single wide panel | (c) two panels | (a′) opposed dual-roll — WINNER |
|---|---|---|---|
| Panel | one, 2.28-turn wrap | two 162.9×71.4, 3.0 mm seam | one continuous, ≤1 turn/side |
| Bend radius | R8 (ok) | R8 (ok) | R8 everywhere (ok) |
| Extra pull | +4.2 N | n/a (two v1.0 pulls) | +0.9 N → ~2.9 N total |
| Stick | 183.9×34×~28 (+6 thick) | 183.9×44×22 | 190×46×22 |
| Mass | ~286 g | ~341 g | ~329 g (+88) |
| "Single continuous display" | yes, but 2.3-turn display-face wear | **NO — 3 mm seam** | **yes** |
| Verdict | REJECTED: thickness, 102 mm cantilever bar, inter-layer wear | REJECTED: seam kills the poster claim; heaviest | **WINNER** |

Why (a′) wins: it is the only concept that keeps the poster's "single continuous
display" claim — zero seam — at R8 everywhere, with no thickness growth and a
~2.9 N pull inside the validated 2–4 N comfort class. (b) is rejected on
packaging (27.9 mm thick, 102 mm bar cantilever vs 30.9 mm validated) and
inter-layer OLED wear over 2.28 turns, not on friction. (c) is feasible but
rejected on the seam and mass.

## Geometry (winner)

- Drum 1: R8, axis along X at y=+10 — v1.0 phone reserve 43.5 mm, wrap ≤ half turn.
- Drum 2: R8, axis along X at y=−10.5 — tablet reserve 71.3 mm, wrap ≤ one full
  turn; 0.05 mm interleave film on the outer turn (display-face protection,
  standard rollable practice).
- Cross-section (Y–Z): drums side by side → width 46 mm; thickness stays 22 mm.
- Length 183.9 → 190 mm: head cap deepens 8 → 14 mm for drum 2's FPC rolling
  U-loop pocket (R6, ~26 mm take-up, same v0.7 pattern).
- Deployment sequence: drum 1 to ≥90% before drum 2's bar releases (mechanical
  cam interlock on the phone bar + BLE logic: controller reads both encoders —
  second AS5600 on the second I2C bus per the v1.3 lesson — and reports
  asymmetric state to Nexus OS).

## Checker evidence (checker.py, v0.6 contract — stdout pasted)

```
drum1_phone: err=7.11e-15 mm theta=[1.571, 3.142] travel=30.93 mm visible=43.50 mm -> PASS
drum2_tablet: err=1.42e-14 mm theta=[1.571, 6.283] travel=58.73 mm visible=71.30 mm -> PASS
phone screen: 162.9 x 71.5 mm (target 71.5)
tablet screen: 162.9 x 142.8 mm (target 142.8)
device: 190 x 46 x 22 mm (v1.0: 183.9 x 34 x 22)
mass: 241 + 88 = 329 g
OVERALL: PASS
```

1001 poses per side; panel length conserved to ~1e-14 mm; bend radius ≥ R8 at
every pose; theta monotonic and within [π/2, π] (drum 1) / [π/2, 2π] (drum 2).

## Failure modes (embedded-playbook analysis)

- **Drum stall mid-deploy** (either axis): the two axes are independent —
  detents (≥3 N per side, v0.6 spec) hold position; the negator is
  constant-force so there is no snap-back. Safe state = hold position.
- **Asymmetric deploy** (tablet pulled with phone closed): mechanically
  impossible — the tablet bar's release latch is cam-blocked until the phone
  bar passes 90%. BLE cross-check reports it if forced.
- **Interleave film jam**: film is captive on drum 2's outer turn (bonded
  leader); a jam stalls the axis → detents hold → user closes and reopens.
  Film wear is NOT-VERIFIED (see below).
- **FPC loop 2 fatigue**: same R6 U-loop pattern as v0.7, take-up ~26 mm;
  cycle rating of the loop at this take-up is NOT-VERIFIED.

## ASSUMPTIONS

1. Extra-wrap friction mu=0.15 (panel-back on POM, dry) applied ONLY beyond the
   v1.0-validated 0.87-turn wrap; v0.7's 2.0 N open force is the friction
   baseline (validated, not assumed).
2. Mass adds (drum2 28 g, bar2 15 g, negator2 8 g, FPC loop2 5 g, film 2 g,
   wider housing 16 g, detents 8 g, head-cap deepen 6 g) — part estimates from
   v0.6/v0.7 mass model, ±20%.
3. Negator springs available in 2–3 N constant-force in this envelope
   (catalog class, not a sourced part number).
4. 0.05 mm interleave film survives the wrap (standard practice; unverified here).

## NOT-VERIFIED

1. Dynamic roll-cycle rating of a real AMOLED at R8 on TWO axes (standing v1.0 item).
2. Interleave-film wear over the outer turn (no test data).
3. Drum-2 FPC loop fatigue at ~26 mm take-up.
4. Cam-interlock tolerance stack (paper design; no tolerance sim run).
5. RF: wider 46 mm body changes the antenna keep-outs — cap windows unchanged
   (still polymer), but near-field of the second drum/bar unmodeled.
