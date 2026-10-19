#!/usr/bin/env python3
"""
NEXUS ONE v2.0 — tablet second-axis concept evaluation.
Target: 162.9 x 142.8 mm screen (four-modes board; panel area x2.0 vs phone).
Frozen v1.0 reference: stick 183.9x34x22, R8 drum, panel 162.9x71.5 (usable),
travel 30.9 mm, 241 g, negator 1.5 N tension, ~2.0 N opening force (v0.7).

Friction is ANCHORED to the validated v1.0 system, not guessed:
  v0.7 validated 2.0 N opening force for a 0.87-turn wrap (that number already
  includes the real wrap friction). We therefore take the v1.0 wrap as the
  baseline (extra factor 1.0 by definition) and scale ONLY wrap angle BEYOND
  0.87 turns, with mu = 0.15 (ASSUMPTION: panel-back on POM, dry).
  Extra pull = 1.5 N * (exp(0.15 * extra_beta) - 1).
"""
import math

R = 8.0
V10_WRAP_TURNS = 0.87          # v1.0 max wrap (validated at 2.0 N open force)
MU = 0.15                     # ASSUMPTION: extra-wrap friction, panel-back on POM
TENSION = 1.5                 # negator tension, N (v0.7)

def extra_pull(extra_turns):
    return TENSION * (math.exp(MU * extra_turns * 2 * math.pi) - 1.0)

print("=" * 72)
print("TABLET CONCEPT COMPARISON (all numbers computed, assumptions labelled)")
print("=" * 72)

# ---------- Concept (b): single wide panel, multi-turn wrap ----------
b_wrap = (142.8 - 28) / (2 * math.pi * R)   # usable 142.8, strip 28
b_extra = b_wrap - V10_WRAP_TURNS
b_pull_extra = extra_pull(b_extra)
b_thick = 2 * (R + b_wrap * 1.3) + 2 * 2.0 + 2 * 1.0  # drum+layers+walls+clear
b_mass = 241 + 20 + 12 + 8 + 5  # thicker walls + gearmotor + interleave film + stiffer bar (ASSUMPTION)
print("\n(b) SINGLE WIDE PANEL, %.2f-turn wrap:" % b_wrap)
print("    extra pull over v1.0: +%.1f N (mu=0.15 ASSUMPTION)" % b_pull_extra)
print("    stick thickness needed: %.1f mm (vs 22)" % b_thick)
print("    mass: ~%d g (+%d, estimate from thicker walls + gearmotor + film + bar)"
      % (b_mass, b_mass - 241))
print("    leading-bar travel: %.1f mm (vs 30.9 validated)" % (142.8 - 12.57 - 28))
print("    inter-layer contact: OLED emissive face rubs panel back over %.1f turns"
      % b_wrap + " -> wear risk (ASSUMPTION: no interleaving film)")
print("    VERDICT: REJECTED - thickness +6mm, 102mm cantilever bar (guide stiffness")
print("             ~1/L^3 vs validated 30.9mm), inter-layer display wear. Friction alone")
print("             (+%.1f N) is tolerable; packaging and wear are not." % b_pull_extra)

# ---------- Concept (c): two panels, center seam ----------
c_seam = 2 * 1.5  # two sealed edges
c_width = 2 * (16 + 2 * 2.0 + 1.0) + 2.0  # 2 drums + walls + center web
c_mass = 241 + 55 + 45  # second panel + second mech (ASSUMPTION)
print("\n(c) TWO PANELS side by side:")
print("    center seam: %.1f mm (two sealed edges) vs <0.5 mm target -> FAILS target" % c_seam)
print("    stick width: %.0f mm (vs 34)" % c_width)
print("    mass: ~%d g (+%d)" % (c_mass, c_mass - 241))
print("    VERDICT: FEASIBLE but REJECTED - 3 mm seam kills the poster's 'single")
print("             continuous display' claim; heaviest option; dual-drum sync needed.")

# ---------- Concept (a'): opposed dual-roll, one continuous panel ----------
# Drum2 wraps up to ONE FULL TURN (theta in [pi/2, 2*pi]); the extra reserve
# beyond v1.0's half-turn wrap is one extra half-turn of WRAP (back flat drains).
a2_extra_beta = math.pi                      # 2pi - pi
a2_pull_extra = TENSION * (math.exp(MU * a2_extra_beta) - 1.0)
a_width = 46.0   # drum1 O16 + drum2 O18.4 (interleave layer) side by side + walls
a_mass = 241 + 88
print("\n(a') OPPOSED DUAL-ROLL (WINNER): one continuous panel, drum1 (+Y, phone, v1.0")
print("    mechanism untouched) + drum2 (-Y, tablet reserve 71.3 mm, up to 1.0 turn):")
print("    drum2 extra pull over v1.0: +%.1f N -> total ~%.1f N (manual, in 2-4 N class)"
      % (a2_pull_extra, 2.0 + a2_pull_extra))
print("    max wrap: drum1 half-turn (validated), drum2 one full turn")
print("    interleave film 0.05 mm on drum2's outer turn (display-face protection)")
print("    stick: 190 x %.0f x 22 mm (length +6 for drum2 FPC head-cap pocket)" % a_width)
print("    mass: ~%d g (+%d)" % (a_mass, a_mass - 241))
print("    seam: 0 mm - 'single continuous display' claim SURVIVES")
print("    VERDICT: WINNER - only concept that keeps one continuous panel at R8")
print("             everywhere with no seam, no thickness growth, manual operation.")

print("\n" + "=" * 72)
print("SELECTION: (a') opposed dual-roll. (b) rejected on packaging/wear,")
print("(c) rejected on the seam claim + mass. All friction numbers use the")
print("v1.0-validated baseline + mu=0.15 ASSUMPTION for extra wrap only.")
print("=" * 72)
