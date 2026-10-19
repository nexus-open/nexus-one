# NEXUS ONE — BUILD RUNBOOK v2.x (after v2.0)

**Role:** Roadmap author · **Method:** `product-sprint-prioritizer` playbook —
MoSCoW + RICE (with confidence levels), value-vs-effort, dependency mapping,
risk scoring (P×I), definition-of-done gates, scope control, honest confidence
intervals.
**Authored:** 2026-10-19 · **State read from:** vision-map v1.8 (31 elements:
14 proven / 3 designed / 11 gap+route / 3 vision-only), COORDINATION.md,
and the DESIGN_v2_0 workstreams on disk at read time.
**Standing mandates:** DIGITAL-ONLY (bench B1–B6 parked as reference; nothing
physical) · HONEST LABELS (ASSUMPTION-tagged numbers stay tagged) ·
v1.0 freeze untouched (all of this is the v2 branch).

> **Read-time gap (recorded, not hidden):** COORDINATION.md references
> `DESIGN_v2_0/tablet/` (checker.py + design_report.md, WS1) — **that
> directory did not exist on disk at read time.** The tablet second-axis
> study is therefore an UNDELIVERED workstream, not a refinement. Item B1
> prices it as a full study. If WS1 surfaces later, its evidence replaces
> this row's assumptions.
>
> **Update 2026-10-19 (coordinator):** WS1 has since been delivered
> (`DESIGN_v2_0/tablet/`, checker PASS). B1 above is refreshed to the
> delivered numbers; the original read-time note is kept for the record.

---

## 0. HOW THE SCORES WORK (playbook faithful)

**RICE:** Score = (Reach × Impact × Confidence) ÷ Effort.

- **Reach** (this project has no users; adapted honestly): number of vision-map
  elements the work unlocks. Reach 1 = one element; Reach 2 = one element
  plus a cross-cutting dependency (e.g. thermal law, RF rule) that gates others.
- **Impact** (0.25–3 playbook scale): 3 = vision-critical element (tablet
  mode, own-brain, hologram); 2 = gates other work or completes a mode;
  1.5 = real value, narrow; lower values marked explicitly.
- **Confidence** (%): basis stated per row — "proven" numbers get higher
  confidence, novel mechanisms get lower. This is the playbook's
  confidence-level requirement.
- **Effort:** agent work-weeks (ww), stated as an **interval** (playbook:
  confidence intervals, not pulled-from-air dates). The RICE point uses the
  interval midpoint; the interval stays visible in the row.

**Value-vs-effort placement** is summarized per row: Quick Win / Major
Project / Fill-in / Time Sink.

**MoSCoW:** Must = the v2 branch cannot proceed without it; Should = planned,
not blocking; Could = value if capacity allows; Won't = explicitly out of
this horizon or out of engineering scope.

---

## 1. BACKLOG (after v2.0)

### B1 · Tablet second-axis prototype — opposed dual-roll (DELIVERED, refinement)
- **Status on the map:** GAP + ROUTE → **DESIGNED** (target #1). **Update
  2026-10-19:** the WS1 study has been delivered since read time
  (`DESIGN_v2_0/tablet/`: concepts.py + checker.py + design_report.md, checker
  PASS at 1001 poses/side, length conserved ~1e-14 mm). Winner: opposed
  dual-roll — one continuous panel, drum 1 (+Y, v1.0 phone mechanism untouched)
  + drum 2 (−Y, 71.3 mm tablet reserve, ≤1 full turn, R8, interleave film).
  Cost: stick 190×46×22 mm, 329 g (+88), pull ~2.9 N (manual).
- **What remains:** prototype refinement — interleave-film wear data, drum-2
  FPC loop fatigue at ~26 mm take-up, cam-interlock tolerance stack, RF
  near-field of the wider body (see tablet NOT-VERIFIED list).
- **RICE:** Reach 2 × Impact 3 × Confidence 85% (study delivered, checker
  green) ÷ Effort **3–5 ww** (mid 4) = **1.28**
- **MoSCoW:** MUST (engineering target #1) · **Value-vs-effort:** Quick Win
  (was Major Project at 8–14 ww before the study landed).

### B2 · Laptop integration — keyboard firmware-in-loop
- **Status:** designed on both sides; **contract already reconciled at read
  time** — WS2 `keyboard_kickstand_design.md` and WS3
  `keyboard_module.ino` + `bay_module_common.h` agree: MOD_KEYBOARD=6,
  ID 33 kΩ (2.533 V / 3143 ADC), I2C 0x2A, reg2=5 (0.5 W class), HID boot
  keyboard. The "CROSS-CHECK PENDING" note in COORDINATION.md is now CLOSED
  by this check.
- **What remains:** module firmware bring-up of the contract (ADC window
  2980–3300 counts measured, not asserted), 9 ms typing-latency budget
  verified, desktop-mode trigger (CH_BAY id=6 ∧ encoder ≥ 90%) end-to-end,
  forward-tip 0.45 N limit as a documented known limit.
- **RICE:** Reach 1 (laptop mode) × Impact 2 × Confidence 85% (contract is
  byte-level agreed) ÷ Effort **2–4 ww** (mid 3) = **0.57**
- **MoSCoW:** SHOULD · **Value-vs-effort:** Quick Win (designed, small lift).
- **Confidence basis:** high — the only open items are measurement and
  policy, not design.

### B3 · Neural-module bus decision — build the USB2-class NPU module
- **Status:** decision **already taken** in
  `modules/neural_module/NEURAL_DECISION.md` (2026-10-19): build USB2 now
  (Edge-TPU-class MCM, 4 TOPS, 2.0 W class, ID 7 / 47 kΩ — Coral-class
  precedent cited), USB3 over pogo **documented, not built** (needs 12-pogo
  bay revision + SI sim + re-cert).
- **What remains:** module design + supervisor sketch integration
  (`neural_module.ino` exists; wire to the decided architecture), model-load
  bandwidth budget (50 MB ≈ 1 s over USB2, stated), thermal throttle/cut at
  75/85 °C wired to the spine law table.
- **RICE:** Reach 1 × Impact 1.5 × Confidence 90% (USB NPU sticks are a
  shipping product class) ÷ Effort **3–6 ww** (mid 4.5) = **0.30**
- **MoSCoW:** SHOULD (target #3; decision documented) · **Value-vs-effort:**
  Fill-in (real value, bounded lift).
- **Confidence basis:** high — class is proven, only our silicon choice is
  ASSUMPTION-tagged.

### B4 · Own-brain SoM bring-up (custom Nexus Spine SoM, i.MX95 class)
- **Status:** designed (power_sim.py + own_brain_spine.md verified). No
  layout, no Linux, no governor yet.
- **What remains:** Linux client implementing the v1.0 protocol client role
  (byte-identical to the v1.7 host client; ESP32-S3 firmware ports unchanged);
  MIPI-DSI panel path for the 162.9×71.5 flexible panel; PMIC rail bring-up;
  NPU thermal governor enforcing burst-duty (~3.7 min at Cth=15 before
  Tj 105 °C); micro-CAMM SI sim at LPDDR5-6400; folded derate table
  (2×A55@800 MHz, NPU OFF, DDR1600, strip only).
- **RICE:** Reach 2 (own-AI-chip element + NPU path for the AI-assistant
  element) × Impact 3 × Confidence 60% (power basis i.MX95-class is
  ASSUMPTION-tagged; A1–A6 open) ÷ Effort **16–24 ww** (mid 20) = **0.18**
- **MoSCoW:** SHOULD (target #4; the largest planned lift) ·
  **Value-vs-effort:** Major Project.
- **Confidence basis:** medium-low — area budget (80.9% fill) and height
  stack (3.6 ≤ 4.5 mm) are computed; full-load SoC power, Cth, Rth_open are
  not.

### B5 · Hologram research track — the three advances
- **Status:** RESEARCH TRACK (volumetric gap **~1000×**: 938 traps needed vs
  1 demonstrated; ~192 W wall-plug; open-air eye-safety HARD BLOCKER,
  Class 3B/4 territory). Light-field v2 + AirScreen module are MAKEABLE
  separately (see B11).
- **What remains (the three named advances):**
  1. Massively parallel addressed traps (SLM/DMD time-multiplex, ~938 traps
     at kHz steering — undemonstrated).
  2. Faster steering / lower-drag particles (~0.5 → ~25 m/s via AOD +
     low-drag media, ~50× voxels/s per trap, array shrinks toward ~20).
  3. Persistent-emission particles (~10 ms phosphorescence, ~4× throughput
     per sweep, motion-blur physics to characterise).
- **RICE:** Reach 1 (free-space hologram; gesture-over-hologram rides on it)
  × Impact 3 × Confidence 30% (pure research; no lab commitment exists)
  ÷ Effort **60+ ww** (mid 60; multi-year standing track) = **0.015**
- **MoSCoW:** COULD (standing research; never on a product roadmap as
  anything but research) · **Value-vs-effort:** Time Sink **as hardware** —
  kept only as a paper track with honest gap accounting.
- **Confidence basis:** low — stated deliberately; inventing confidence here
  would violate HONEST LABELS.

### B6 · RF verification of the polymer cap windows
- **Status:** NOT-VERIFIED (standing since v1.0). Materials WS6 keeps caps
  polymer *by rule* (Faraday argument: metal/carbon caps = dead radios);
  the claim needs verification.
- **What remains:** RF model/measurement plan for the 2.4 GHz path through
  PC/ABS caps; coupling check for the CFRP shell near the 30×8 mm PC
  inserts; antenna keep-out compliance behind the caps; **the NTN satellite
  antenna for the satellite module must live in these windows** — satellite
  module study is explicitly gated on this item.
- **RICE:** Reach 2 (cap windows + satellite-module element) × Impact 2 ×
  Confidence 70% (EM physics standard; geometry assumptions open)
  ÷ Effort **3–5 ww** (mid 4) = **0.70**
- **MoSCoW:** MUST (gates satellite module + materials v2) ·
  **Value-vs-effort:** Quick Win.
- **Confidence basis:** medium — solvable as a sim + test-spec task, but no
  antenna class is locked yet.

### B7 · Panel dynamic roll-cycle rating
- **Status:** NOT-VERIFIED (standing since v1.0; maker datasheets don't
  publish it). FPC U-loop target 54,750 cycles at R6 is assumption-labelled.
- **What remains:** a defensible rating — vendor inquiry route, test
  specification, or a published-class derate study; folds into the panel
  selection constraint for v2. Digital-only: this is a *data acquisition*
  task, not a bench run.
- **RICE:** Reach 1 × Impact 2 × Confidence 50% (depends on vendor
  cooperation/data availability) ÷ Effort **2–4 ww** (mid 3) = **0.33**
- **MoSCoW:** SHOULD (durability claim is load-bearing for the product
  story) · **Value-vs-effort:** Fill-in.
- **Confidence basis:** low-medium — the answer may be "no public rating
  exists," which is itself an honest result.

### B8 · v2 thermal model — graphite spreader, 1-D resistance network
- **Status:** GAP (WS6 found the Ti/CFRP stack **conflicts with the 2 W
  folded law**: Ti ~6.7 W/m·K vs Al ~167 — 25× worse; the v2 shell path
  implies 100–250 K rise at 2 W, impossible handheld).
- **What remains:** build the 1-D thermal-resistance model with a graphite
  spreader layer in the shell layup (in-plane ~400 W/m·K class) — WS6
  recommendation (b); quantify whether the 2 W folded law survives, derates,
  or must drop toward the 0.9 W Pocket-Mode envelope; fold in the cooling
  module's measured ΔT (6.97 W folded cap @25 °C, from `thermal_calc.py` —
  replaces own-brain assumption A4); produce the v2 folded-law number.
- **RICE:** Reach 2 (thermal law + entire v2 materials stack) × Impact 2.5
  × Confidence 75% (path is clear, numbers computable) ÷ Effort **2–4 ww**
  (mid 3) = **1.25** ← highest RICE in the backlog.
- **MoSCoW:** MUST (no v2 freeze without it — the current design cannot hold
  the folded law in Ti/CFRP) · **Value-vs-effort:** Quick Win.
- **Confidence basis:** high-medium — the blocker is quantified; the route
  (graphite + 1-D model) is the WS6 lead's recommendation.

### B9 · Bench B1–B6 un-parking condition
- **Status:** parked by the DIGITAL-ONLY standing mandate (confirmed
  2026-10-19; the bench plan with sim-tied pass criteria exists as parked
  reference). This is a **condition, not a work item** — no RICE scored
  (effort is undefined until the rule changes).
- **MoSCoW:** WON'T (until the mandate changes).
- **Un-parking condition (all required):** (1) the user explicitly revokes
  or relaxes the digital-only rule; (2) the evidence gate in §4 is re-based
  from sim-checker outputs to physical pass criteria; (3) first articles of
  the tested parts exist (the 33 kΩ ADC window, magnet pull, hinge life and
  key-feel items in WS2's NOT-VERIFIED list are the natural B1 candidates).
  Until all three hold, physical claims stay parked and sim results stay
  the product.

### B10 · Manufacturing / commercial (BOM cost, CNC, launch)
- **Status:** VISION ONLY on the map (poster's $999–1,499 and 2028–2030
  launch).
- **MoSCoW:** WON'T — **explicitly out of engineering scope.** This project
  runs at ₹0, fully digital; no cost engineering is claimed or faked.
  Recorded here only so nobody quietly invents a price curve later.

### B11 · Light-field v2 cover + AirScreen module integration
- **Status:** both DESIGNED / MAKEABLE (light-field v2: 0.70 W, 25.6 ms
  eye-to-photon, 47 LPI in real film range; AirScreen: 6.4 W of the 10 W
  bay, 15 ml/15 min, stick side 2.5 W holds the 3 W OPEN law). Not built.
- **What remains:** eye-tracking module integration spec (OV2312-class +
  850 nm illuminator in the leading bar), lenticular sleeve accessory
  design, mist-plane stability spec for the 15 ml tank, module-shell vent
  temperature spec at sustained 6.4 W.
- **RICE:** Reach 1 (glasses-free-3D element) × Impact 1.5 × Confidence 80%
  (every part is a real part class) ÷ Effort **5–9 ww** (mid 7) = **0.17**
- **MoSCoW:** COULD (near-term accessory layer; stacks with — never
  competes with — the volumetric research track) · **Value-vs-effort:**
  Fill-in.
- **Confidence basis:** high-medium — optics + camera physics, no new
  science; supplier/sunlight items remain NOT-VERIFIED.

---

## 2. RICE RANKING (highest → lowest)

| Rank | Item | Score | MoSCoW | Effort (ww, interval) | V-E class |
|---|---|---|---|---|---|
| 1 | B8 v2 thermal model (graphite) | **1.25** | Must | 2–4 | Quick Win |
| 2 | B6 RF verification of cap windows | **0.70** | Must | 3–5 | Quick Win |
| 3 | B2 Laptop integration (firmware-in-loop) | **0.57** | Should | 2–4 | Quick Win |
| 4 | B1 Tablet second-axis study | **0.38** | Must | 8–14 | Major Project |
| 5 | B7 Panel dynamic roll-cycle rating | **0.33** | Should | 2–4 | Fill-in |
| 6 | B3 Neural module (USB2 build) | **0.30** | Should | 3–6 | Fill-in |
| 7 | B4 Own-brain SoM bring-up | **0.18** | Should | 16–24 | Major Project |
| 8 | B11 Light-field + AirScreen integration | **0.17** | Could | 5–9 | Fill-in |
| 9 | B5 Hologram research (3 advances) | **0.015** | Could | 60+ | Time Sink (hardware) |

B9 (bench un-park) and B10 (manufacturing) are unscored — conditional and
out-of-scope respectively.

**Reading the ranking honestly:** the top of the list is *unblocking work*
(B8, B6) and *designed work with small lift* (B2) — that is the correct
shape. The big value items (B1, B4) sit lower on RICE because their effort
is real; they are not deprioritized — they are scheduled as major projects
in the phase plan (§5), not denied.

---

## 3. DEPENDENCY GRAPH

```mermaid
graph TD
    B8[v2 thermal model<br/>graphite spreader] --> V2FROST[v2 freeze decision]
    B8 --> B4[Own-brain SoM bring-up<br/>NPU governor + derate table]
    B8 --> B3[Neural module<br/>thermal throttle policy]
    B6[RF verification<br/>cap windows] --> SAT[Satellite module study]
    B6 --> V2FROST
    B7[Panel roll-cycle rating] --> B4
    B7 --> B1[Tablet second-axis study]
    B1 --> V2FROST
    B2[Laptop integration<br/>KB firmware-in-loop] --> DESKMODE[Nexus OS desktop policy]
    B3 --> B4
    B11[Light-field + AirScreen] --> V2FROST
    B5[Hologram research] -.-> GEST[Gesture-over-hologram]
    B4 -.-> AILM[On-device LLM path]
    B9[Bench B1-B6<br/>parked] -.->|un-park cond| PHY[physical evidence]
    B10[Manufacturing] -.x NO[engineering scope]
```

**Dependency table (what blocks what):**

| Blocking item | Blocks | Nature |
|---|---|---|
| B8 v2 thermal model | v2 freeze decision; B4 governor tuning; B3 throttle policy | The folded law is the design law — nothing freezes without its number |
| B6 RF verification | Satellite module study; materials v2 cap rule | Antenna lives in the windows; NTN study explicitly gated |
| B7 roll-cycle rating | B4 DSI panel confidence; B1 second-axis mechanism (more cycles, more wear) | Durability claim is load-bearing |
| B1 tablet study | v2 freeze (envelope) | Second axis changes thickness/mass budgets |
| B4 own-brain | on-device LLM AI-assistant path | AI face rides on the hologram gap too (B5) |
| B5 hologram research | free-space hologram element; gesture-over-hologram | ~1000× gap; standing track, no product claims |
| B2 keyboard firmware | Nexus OS desktop-mode policy (§5 of WS2) | CH_BAY trigger contract is firmware-verified, not asserted |
| B9 condition | any physical claim | mandate change required |
| B10 | — | hard out-of-scope boundary |

**Cross-check already resolved:** WS2 ↔ WS3 keyboard contract (MOD_KEYBOARD=6,
33 kΩ, I2C 0x2A, 0.5 W class) verified identical on both sides at read time —
not a dependency anymore.

---

## 4. RISK REGISTER (Probability × Impact)

Impact scale: 1 = schedule slip · 2 = redesign of a subsystem · 3 = a vision
element or design law is invalidated. Sorted by score.

| ID | Risk | P | I | Score | Mitigation / honest note |
|---|---|---|---|---|---|
| R1 | Volumetric holography gap (~1000×) never closes in this horizon | 0.8 | 3 | **2.4** | Stacked layers: light-field v2 + AirScreen deliver real value; never list volumetric as product. The gap is stated at full size, not shaved. |
| R2 | Open-air eye-safety (Class 3B/4, ~25× over per beam, 938 beams) is not certifiable | 0.7 | 3 | **2.1** | Enclosure/interlock/eye-safe-wavelength requirement is a design precondition, not a hand-wave; lab-only until certified. |
| R3 | Ti/CFRP stack invalidates the 2 W folded law → forced derate below Pocket-Mode 0.9 W makes folded use unusable | 0.6 | 3 | **1.8** | B8 (graphite spreader + 1-D model) is the ranked-#1 backlog item for exactly this reason. |
| R4 | i.MX95-class full-load power exceeds ASSUMPTION A1 → NPU burst times collapse below 1 min | 0.5 | 3 | **1.5** | Replace A1 with EVK measurement per AN14449 (B4 first task); governor already schedules bursts with cool-down. |
| R5 | Tablet second-axis mechanism adds >40 g or breaks the pocketable envelope | 0.5 | 2 | **1.0** | B1 must price mass/thickness before any freeze; the map already carries the 241 g budget as a known risk. |
| R6 | micro-CAMM SI fails at LPDDR5-6400 | 0.4 | 2 | **0.8** | Fall back to 8 GB on-SoM only (16 GB was always expansion, not baseline). |
| R7 | Keyboard ADC window (2980–3300 counts) mis-identifies on real silicon | 0.3 | 2 | **0.6** | Firmware-in-loop measurement is a B2 task; window is firmware-adjustable. |
| R8 | Panel roll-cycle rating is unobtainable (no vendor publishes it) | 0.4 | 1 | **0.4** | Honest result: "no public rating exists" becomes the constraint; design conservatively. |
| R9 | Digital-only mandate hides a failure mode only physical test reveals (key feel, hinge life, pogo contact reliability) | 0.7 | 1 | **0.7** | Carried openly in every workstream's NOT-VERIFIED list; B9 defines the un-park condition. Impact capped at 1 because the mandate is his choice, recorded. |

**Highest-scored risk: R1 — the volumetric gap never closing (2.4).**
The mitigation is structural, not optimistic: the product roadmap never
promises the globe; the three advances are tracked as research.

---

## 5. PHASE PLAN WITH DEFINITION-OF-DONE GATES

### Phase 1 — Foundation (unblocking: B8, B6, B7)

| Item | Definition of DONE | Evidence artifact (named) |
|---|---|---|
| B8 thermal model | 1-D resistance network runs; v2 folded-law number stated (survive/derate/drop); cooling ΔT integrated; graphite spec named | `roadmap/evidence/thermal_v2_model.py` (runs clean) + `thermal_v2.md` (numbers match stdout) |
| B6 RF verification | Cap-window RF model run; keep-out compliance stated; CFRP coupling checked; NTN antenna class named | `rf_cap_windows.py` (runs clean) + `rf_verify.md` (numbers match stdout) |
| B7 roll-cycle | Vendor/data result recorded (rating obtained OR "no public rating exists" documented) | `panel_rollcycle.md` (sourced; no invented numbers) |

**Gate G1 (foundation done):** all three evidence artifacts exist and their
checker/simulation outputs match their docs line-by-line. Without G1, no v2
freeze discussion.

### Phase 2 — Modes (B1, B2, B11)

| Item | Definition of DONE | Evidence artifact (named) |
|---|---|---|
| B1 tablet study | Dual-drum L-expansion study; area ×2.0 path; mass/thickness cost; envelope decision | `tablet/design_report.md` + `tablet/checker.py` (runs clean) — replaces the missing WS1 |
| B2 laptop integration | Keyboard firmware compiles; ADC window measured-in-sim; 9 ms latency budget checked; desktop trigger end-to-end; 0.45 N tip limit documented | `keyboard_module.ino` (compiles) + firmware-in-loop test log + `check.py` PASS extended |
| B11 light-field/AirScreen | Eye-tracker spec wired to leading bar; sleeve design; mist/vent thermal spec | integration notes + `calcs.py` extension (runs clean) |

**Gate G2 (modes done):** the laptop KB contract is measured, not asserted;
the tablet study prices its grams. "Done" means numbers, not prose.

### Phase 3 — Brain (B3, B4)

| Item | Definition of DONE | Evidence artifact (named) |
|---|---|---|
| B3 neural module | USB2 NPU module design + supervisor wired to the NEURAL_DECISION architecture; 75/85 °C throttle wired to the spine law | `neural_module.ino` revision (compiles) + architecture compliance note |
| B4 own-brain | Linux v1.0-protocol client compiles (byte-identical frames); DSI timing doc; PMIC rail map; NPU governor with burst-duty rule from B8; A1 replaced by EVK measurement or still ASSUMPTION-tagged | client source (compiles) + `power_sim.py` re-run with B8 numbers + `own_brain_bringup.md` |

**Gate G3 (brain done):** the governor's burst rule is driven by B8's
measured law, not by the ASSUMPTION-tagged A1–A6. Any ASSUMPTION that survives
is listed, not laundered.

### Phase 4 — Vision layer (B5 standing)

| Item | Definition of DONE | Evidence artifact (named) |
|---|---|---|
| B5 research track | Standing log; the three advances tracked with dated entries; gap re-stated at full size each review | `hologram/research_log.md` (append-only, dated) |

**Gate G4:** there is no "done" for a research track — the gate is that the
log exists, is current, and no product doc claims the globe.

### Digital-only verification rule (applies to every gate)

**No phase is "done" without its evidence artifact.** For every simulation:
the `.py`/`.ino` runs clean and its stdout matches the doc's numbers.
For every compile: the build output is recorded. For every document: the doc
names its ASSUMPTIONs. A gate review checks the artifacts, not the prose.
This rule holds until B9's un-park condition changes it — it is never
relaxed by enthusiasm.

---

## 6. SCOPE CONTROL

1. **v1.0 freeze is a firewall.** All of this is the v2 branch. Nothing in
   the backlog touches the frozen 183.9×34×22 / 241 g / BLE-v1.0 / ESP32-S3
   core unless a v2 freeze decision (post-G1) explicitly re-baselines.
2. **Out of scope, enforced:** B10 manufacturing/commercial — no cost
   engineering, no launch planning, no price curves. If a future turn needs
   it, that is a new workstream, not scope creep in this one.
3. **Parked means parked:** B9 (bench B1–B6) does not re-enter as
   "background work" without all three un-park conditions. Physical claims
   without first articles stay in the NOT-VERIFIED lists where they are.
4. **The hologram rule:** volumetric work never appears on a product
   roadmap as anything but a research track with the ~1000× gap stated.
   Light-field and AirScreen are the product-layer answers.
5. **Labels are law:** ASSUMPTION stays ASSUMPTION; NOT-VERIFIED stays
   NOT-VERIFIED; MAKEABLE/RESEARCH TRACK are the only two hologram grades.
   A gate that finds a laundered assumption fails the phase.

---

## 7. CONFIDENCE INTERVALS, STATED ONCE

All effort intervals are honest ranges, not point estimates with a buffer
hidden inside. The widest intervals belong to the least-defined work —
that is the point of publishing them:

- B1 8–14 ww (±27%) — novel mechanism, missing workstream
- B4 16–24 ww (±20%) — largest lift, ASSUMPTION-tagged power basis
- B5 60+ ww — research; the "+" is the honest part
- B8 2–4 ww (±33%) — computable but unmodelled geometry
- B6 3–5 ww (±25%) — depends on antenna class lock
- B2/B7/B3/B11 ±25–33% — bounded, class-proven work

No dates are given because there is no team velocity to calibrate against
(the playbook forbids pulling dates from air). When capacity exists,
schedule in RICE order within the phase sequence: G1 before G2 before G3;
B5 runs as a standing background log regardless of phase.

---

*Roadmap authored 2026-10-19 under the v1.8 re-baseline: the posters are the
target and stay whole; engineering attaches status and works toward them.
This file lives at `~/workspace/nexus-one/DESIGN_v2_0/roadmap/ROADMAP_v2_x.md`
and is the build runbook for everything after v2.0.*
