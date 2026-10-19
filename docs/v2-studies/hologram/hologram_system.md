# NEXUS ONE v2.0 — HOLOGRAM SYSTEM (consolidated display-system design)

One workstream, three layers: what ships (light-field), what plugs in
(AirScreen module), what stays research (volumetric). Every number below is
computed by `calcs.py` in this directory — run it to reproduce.

Standing labels: **MAKEABLE** (light-field v2, AirScreen module),
**RESEARCH TRACK** (volumetric). The volumetric gap is stated at full size.

---

## 1. LIGHT-FIELD v2 — glasses-free 3D on the real panel (MAKEABLE)

v0.5 (Route C) proved the concept: real flexible AMOLED + lenticular film +
eye-tracking = glasses-free 3D, honestly labelled *light-field*, never called
a hologram. v2 adds the eye-tracking spec v1 was missing, and three real
improvements.

### Eye-tracking spec (new in v2)
- **Camera class (real):** IR global-shutter eye-tracking module,
  OmniVision OV2312 class (NIR-sensitive, used in real eye-tracking designs),
  120 fps. Plus one **850 nm pulsed IR illuminator** for dark-room tracking.
- **Where it lives:** embedded in the **leading bar** — the bar unrolls with the
  panel, so the camera always faces the viewer when the screen is deployed. It
  draws power/data from the stick's own electronics (it is not part of the
  removable sheet).
- **Latency budget (eye-to-photon):**

  | stage | ms |
  |---|---|
  | IR camera capture @120 fps | 8.3 |
  | pupil/face detection (DPU class) | 3.0 |
  | view-pair synthesis + interleave @60 Hz | 6.0 |
  | display refresh-to-photon (60 Hz) | 8.3 |
  | **TOTAL** | **25.6** |

  Tracking loop runs at **120 Hz**; the 3D view updates at the **60 Hz** display
  refresh. A head-move costs ~26 ms of view-switching dead time (~3 tracking
  frames) — 24 ms of margin under the ~50 ms annoyance bound. **ASSUMPTION:**
  3 ms pupil solve assumes a DPU/NPU-class accelerator; a pure-CPU solve would
  add ~5–10 ms and must be measured.
- **Power draw (active 3D mode):** camera 0.20 W + IR illuminator 0.25 W +
  tracking DSP 0.25 W = **0.70 W**. One hour of 3D mode costs 0.70 Wh — 5.1% of
  the 13.7 Wh pack. Standby (mode off): <1 mW (**ASSUMPTION**).

### Where the lenticular sheet lives (v0.6 finding, restated)
The 163 × 74.5 mm lenticular sheet **cannot store flat on the 34 mm stick** —
it lives in a **flat sleeve in the carry case** (tablet-cover precedent,
MECH_ROLL v0.6). Rail-mounts only at full panel deployment; the rails block
retraction while mounted, so the film can never be crushed by closing.

### v2 improvements over v1, with reasons
1. **Dedicated IR eye-tracker instead of the front camera.** v1 reused the
   selfie camera: visible-light, 30–60 fps, blind in the dark, and stealing the
   camera from calls. An IR module sees the pupil in any light and frees the
   front camera. *Reason: tracking that fails at night fails the product.*
2. **Dynamic view-pair steering instead of static 8 views.** v1 always rendered
   all 8 views; v2 renders only the 2 views bracketing each eye's position
   (8-view lenticular stays as the optical layer: 2400 px / 8 = **300 px/view**,
   lenticule pitch 0.543 mm = 47 LPI — inside the real 10–100 LPI film range).
   *Reason: cuts GPU render load ~4× and kills crosstalk for off-axis viewers.*
3. **Ambient-light gating.** IR washout in direct sunlight is real; v2 falls
   back to 2D automatically above the illuminator's usable contrast.
   *Reason: honest behaviour instead of a 3D mode that silently breaks
   outdoors.*

**Verdict: MAKEABLE.** Every part is a real part class; the physics is film
optics + a camera. NOT-VERIFIED: sunlight IR-washout threshold, actual pupil
solve latency on the target SoC, lenticular film supplier at 47 LPI on
flexible substrate.

---

## 2. AIRSCREEN PROJECTOR MODULE — mist + pico-DLP in the module bay (MAKEABLE)

The v0.5 concept (ultrasonic mist sheet + pico-DLP, own power) redesigned as a
real **module-bay** product against the frozen bay spec: **120 × 24 mm bay,
8 pogo (USB2 data), 10 W bay power budget.**

### Power split (within the 10 W bay)

| consumer | W |
|---|---|
| TI DLP pico engine class (50–100 lm) | 4.0 |
| ultrasonic atomiser disc (throttled) | 2.0 |
| MCU + drivers + status LEDs | 0.4 |
| **module total** | **6.4** |

6.4 W of the 10 W bay = **64% used, 3.6 W headroom** for mist-peak drive.
The module is **bay-powered** (v2 change from v0.5's "own battery": the 10 W
bay exists precisely to fund modules like this; a battery would duplicate the
stick's 13.7 Wh). USB2 pogo carries video; 8-pogo also carries the 6.4 W.

### Mist reservoir and service interval
Atomiser throttled to **60 ml/h** (ASSUMPTION: atomiser-disc class at reduced
drive — v0.5's baseline):

| session length | reservoir |
|---|---|
| 5 min (v0.5 baseline, checks: 5 ml → 5.0 min ✓) | 5.0 ml |
| 10 min | 10.0 ml |
| **15 min (v2 design session)** | **15.0 ml** |
| 30 min | 30.0 ml |

v2 sizes the tank for a **15-minute session: 15 ml** in a
**50 × 20 × 15 mm tank** — fits the module envelope beside the DLP engine and
atomiser disc. Refill is a top-up port on the module (distilled water;
**ASSUMPTION:** user refills between sessions — service interval is per-session,
not per-day). Dry-run interlock cuts the atomiser when the tank empties.

### Optical alignment tolerance (to the stick body)
The projector and the mist generator are **co-located inside the module**, so
alignment to the stick body is only as good as the bay seating — the pogo +
latch interface. Internal spec: mist-plane flatness **±1.5 mm** over the
120 × 70 mm sheet, projector tilt **±1.0°**, keystone-corrected in the DLP.
Image: **120 × 70 mm** at ~150 mm throw, dim/indoor light only, breaks up in
wind > ~0.5 m/s (v0.5 finding, unchanged).

### Thermal vs the OPEN-mode law
- Stick side during projection: **2.5 W** (screen + OS, **ASSUMPTION**) ≤ **3 W
  OPEN law → HOLDS.** The module's 6.4 W never enters the stick: the module
  vents through its own aluminium shell to ambient.
- **Total system draw during projection: 8.9 W** (stick 2.5 + module 6.4).
  A 15-min session costs 2.23 Wh = 16.2% of the 13.7 Wh pack — the module is a
  deliberate, labelled power event, not background drain.

**Verdict: MAKEABLE as a module.** Real DLP class, real atomiser class,
bay budget respected, thermal law respected. NOT-VERIFIED: mist-plane
stability in humidity, DLP brightness sufficiency on mist (lab measurement),
module vent temperature under sustained 6.4 W.

---

## 3. VOLUMETRIC — photophoretic trap array (RESEARCH TRACK)

Precedent is real published science (BYU, Nature 2018): **one** laser-trapped
particle is steered while RGB lasers paint it — a true 360° volumetric image.
We invent the *array design*; we do not invent the physics. Trap math below is
recomputed from scratch (calcs.py), not copied from v0.5.

### Recomputed trap math
Assumptions (labelled): demonstrated-class steering speed **0.5 m/s**,
paint dwell **0.1 ms/voxel**, one trap = the BYU 2018 demonstrated class.

**(a) Wireframe baseline — v0.5's case, recomputed:**
2000 voxels/frame, 2.0 mm average travel → 4.10 ms/voxel →
**244 voxels/s per trap**. Required at 24 fps: 48,000 voxels/s →
**197 parallel traps** (v0.5 said 192 — **confirmed**; the small delta is the
0.1 ms dwell term v0.5 omitted). Gap vs the demonstrated single-trap system:
**~197×**.

**(b) Poster claim — filled 30 mm globe at 1.2 mm voxel pitch:**
15,625 voxels/frame → 375,000 voxels/s required at 24 fps; 2.50 ms/voxel =
400 voxels/s per trap → **938 parallel traps**.
Gap vs demonstrated: **~938×**.

So the honest numbers: the v0.5 "~100×" was conservative for a wireframe;
the poster's *filled globe* is a **~1000× gap** (938×, order of magnitude).
We report the larger number — the gap does not get shrunk to look good.

### Laser power per trap class and total optical power
- **Per trap:** ~50 mW IR trap beam (optical-tweezers class, ASSUMPTION) +
  shared RGB paint lasers ~1 W visible (ASSUMPTION).
- **Filled globe total:** 938 × 50 mW + 1 W = **47.9 W optical** →
  **~192 W wall-plug** at 25% laser efficiency (ASSUMPTION) — **96× over the
  2 W folded thermal law.** This needs bench/lab power; it is not a phone
  peripheral at this physics. Stated, not hidden.

### Eye-safety sanity check (order-of-magnitude, NOT a certification)
Per-trap beam 50 mW vs an order-of-magnitude Class-1-class accessible limit of
~2 mW in the NIR → **~25× over per beam**, with **938 beams** crossing an open
display volume. Open-air operation lands in **Class 3B/4 territory: a HARD
BLOCKER.** The design therefore requires, before any prototype: an enclosure
or beam-screen, an interlock, or a move to eye-safe wavelengths — engineered,
certified, and labelled. Not hand-waved, not "we'll be careful."

### The HONEST GAP STATEMENT
True volumetric video of a 30 mm globe at 24 fps needs **~938 independently
steered optical traps**; the published state of the art demonstrates **~1**.
That is a **~1000× parallelism gap** (order of magnitude), plus a ~192 W
wall-plug power gap and an unsolved open-air eye-safety envelope. Physics
allows it — nothing here violates optics or thermodynamics — but no lab on
earth has built the array, and this track must not appear on any v1/v2 product
roadmap as anything but research.

### Three concrete research advances that would close it
1. **Massively parallel addressed traps** — scale from 1 to ~938 independently
   steerable traps via SLM/DMD time-multiplexed holograms, each steerable at
   kHz. Today's SLM tweezer arrays address tens of traps; per-trap kHz
   steering at ~1000 traps is undemonstrated.
2. **Faster steering / lower-drag particles** — push single-trap scan speed
   from ~0.5 m/s toward ~25 m/s via resonant/AOD steering plus reduced-drag
   media (low-pressure chamber or low-viscosity gas): ~50× more voxels/s per
   trap, cutting the required array from ~938 toward ~20.
3. **Persistent-emission particles** — phosphorescent particles with ~10 ms
   glow decouple brightness from revisit rate: a trap paints ~4× more voxels
   per sweep than it must revisit, multiplying effective voxel throughput per
   trap (at the cost of motion blur physics that must be characterised).

**Verdict: RESEARCH TRACK.** Invented design, real physics, measured gap,
three named advances. Nothing is promised in hardware.

---

## 4. SYSTEM VIEW — product roadmap

| layer | status | poster claim it satisfies |
|---|---|---|
| **Light-field v2** (lenticular cover + IR eye-tracking) | **MAKEABLE now** — designable from real parts; cover ships as a carry-case-sleeve accessory | "3D interaction without glasses" — glasses-free 3D you can reach toward |
| **AirScreen module** (mist + pico-DLP in the bay) | **Near-term module** — 6.4 W of the 10 W bay, 15-min sessions, own venting | "Project 3D holograms" — a floating projected image, honestly a 2D image on a mist plane |
| **Volumetric trap array** | **Research track** — ~1000× gap, bench power, eye-safety blocker | Free-floating touchable globe — the true volumetric image; gesture-over-hologram rides on this gap too |

The three layers stack, they do not compete: the cover gives Fabulous glasses-free
3D on day one, the module gives him a floating projection as a bay accessory,
and the research track works the real physics toward the globe — with the gap
stated at full size until the day it closes.

## NOT-VERIFIED remainder (labelled, not hidden)
- Panel dynamic roll-cycle rating (standing v1.0 item) and RF behaviour of cap
  windows — unchanged.
- Light-field: IR-washout threshold in sunlight, pupil-solve latency on the
  target SoC, lenticular-film supplier at 47 LPI on flexible substrate.
- AirScreen: mist-plane stability in humidity, DLP brightness on mist
  (lab measurement), module shell temperature at sustained 6.4 W, 15 ml tank
  leak/ingress rating.
- Volumetric: everything past the BYU precedent — steering speed, trap power,
  persistent-particle behaviour, and any eye-safety certification — is
  unmeasured; the three advances are research targets, not commitments.
