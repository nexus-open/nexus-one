# NEXUS ONE v2.0 — VERIFICATION REPORT
**Lead:** verification subagent · **Date:** 2026-10-19 (evening IST)
**Method:** testing-reality-checker + testing-evidence-collector + testing-test-automation-engineer + design-ux-researcher + product-manager playbooks
**Scope:** `~/workspace/nexus-one/DESIGN_v2_0/` (tablet, laptop, modules, own_brain, hologram, materials, roadmap, security + desktop-OS prototype review)
**Mandates:** DIGITAL-ONLY · HONEST LABELS · nothing written outside `verification/`, nothing touched under `ARCHIVE_*/` or `CODE_v1_*/`

> This is a **final gate, not a rubber stamp.** Default stance: NEEDS WORK until the evidence says otherwise. Every number below was re-run, re-compiled, or re-derived by this verifier — not taken from the workstream reports.

---

## 1. DETERMINISM RESULTS (test-automation-engineer bar: run twice, byte-identical)

| Script | run1 vs run2 | Verdict |
|---|---|---|
| tablet/concepts.py | identical | PASS |
| tablet/checker.py | identical | PASS |
| laptop/torque_calc.py | identical | PASS |
| laptop/check.py | identical | PASS |
| modules/thermal_calc.py | identical | PASS |
| modules/satellite_link.py | identical | PASS |
| own_brain/power_sim.py | identical | PASS |
| hologram/calcs.py | identical | PASS |
| materials/mass_calc.py | identical | PASS |

**9/9 scripts byte-identical across two runs.** Every number in the pack reproduces. (A number that doesn't reproduce doesn't ship — all of these reproduce.)

Evidence captures: `verification/evidence/` — 18 run files (`<workstream>_<script>_run{1,2}.txt`) plus `keyboard_recompile.txt`, `keyboard_compile_run2.txt`.

---

## 2. PER-WORKSTREAM VERDICTS

### 2.1 tablet/ — VERIFIED (1 minor finding)

- `checker.py` stdout is pasted **exactly** into `design_report.md` (compared byte-for-byte): `drum1_phone err=7.11e-15 … PASS`, `drum2_tablet err=1.42e-14 … PASS`, 190×46×22, 329 g — all match.
- Every `concepts.py` number quoted in the report matches the stdout: (b) +4.2 N / 27.9 mm / 102.2 mm / 2.28-turn wrap; (c) 3.0 mm seam / 44 mm / 341 g; (a′) +0.9 N → ~2.9 N / 190×46×22 / 329 g / 0 mm seam.
- Mass-add arithmetic in the report: 28+15+8+5+2+16+8+6 = 88 g ✓.
- **FINDING T-1 (minor):** the comparison table quotes concept (b) mass **"~286 g"** — `concepts.py` prints **no mass for (b)** (only (c) 341 g and (a′) 329 g). The number is untraceable to the script stdout. Either derive it in `concepts.py` or label it as a manual estimate.

### 2.2 laptop/ — VERIFIED (1 clarity note)

- `torque_calc.py` stdout matches the block pasted in `keyboard_kickstand_design.md` **verbatim** (all 22 lines).
- `check.py` stdout: "OK: all 33 JS-referenced ids exist… PASS" — matches the report's claim exactly.
- Formula verified against source: REQUIRED = (1.33 + 0.25×31.5)×2.0 = **18.4 mN·m** ✓ (the 25% disturbance allowance is on the *device-weight moment about H*, per the script's own comment).
- ADC sanity numbers verified: 22 kΩ → 2.269 V/2815; 33 kΩ → 2.533 V/3143 (328 counts clear of cooling ✓); window 2980–3300 straddles the 2979 midpoint ✓.
- CoM / support-polygon / tip-margin arithmetic: polygon [−63.6, +10.6], CoM −6.63 → rear margin 57.0 / front 17.2 ✓; foot height 102 mm ✓; Pmax 0.45 N formula consistent.
- **NOTE L-1 (clarity, not a mismatch):** §4.3 prose reads "1.33 mN·m static leg moment → 18.4 mN·m required with disturbance allowance × SF 2.0", which omits that the allowance is 25% of the 31.5 mN·m device moment. Numbers are correct; the gloss is compressed. One-line clarification suggested.

### 2.3 modules/ — NEEDS WORK (1 medium cross-workstream defect + 2 minor notes)

- **Independent `--clean` recompiles (real toolchain: arduino-cli 1.1.1, ESP32 core 3.3.12, fqbn `esp32:esp32:esp32s3`):**
  | Sketch | Report | Independent recompile | Flash | RAM |
  |---|---|---|---|---|
  | cooling_module | 336,721 B / 24,560 B | **336,721 B / 24,560 B** | byte-exact | byte-exact |
  | satellite_module | 335,906 B / 23,816 B | **335,906 B / 23,816 B** | byte-exact | byte-exact |
  | neural_module | 326,026 B / 23,816 B | **326,026 B / 23,816 B** | byte-exact | byte-exact |
  | keyboard_module | 388,662 B / 56,504 B | **388,662 B / 56,504 B** | byte-exact | byte-exact |
- The report's keyboard build-cache-staleness story was **independently reproduced by this verifier**: first recompile failed with the identical `Error during build: open …/keyboard_module.ino.cpp: no such file or directory` (stale `~/.cache/arduino/sketches/`), succeeding only after the cache was cleared — confirming the diagnosis (cache, not code). One retry after the wipe also hit a transient `xtensa-esp-elf-g++: fatal error: cannot specify '-o' …` before succeeding on the next attempt; environment toolchain flakiness, not source.
- Thermal/satellite stdout matches the report's pasted blocks; independent physics spot-checks: air heat-carry 12.06 W ✓, R_conv = 1/0.864 = 1.157 K/W ✓, parallel Rth 2.586 K/W ✓, cap @25 °C = 18/2.58 = 6.98 W ✓, TEC-vs-blower ~23× ✓. Satellite FSPL math: Pr values consistent.
- **FINDING M-1 (medium — cross-workstream defect, blocks integration, not the pack):** the keyboard firmware does **not** match the laptop hardware spec.
  - WS2 `keyboard_kickstand_design.md` §2.2: **3 rows × 10 cols = 30 keys**, row pitch 6.5 mm / col pitch 11.4 mm, keycap 9.6×5.4 mm; §2.4/§2.6 power and latency budgets built on a **"1 kHz full-matrix scan"** (latency model: 1 ms scan + 5 ms debounce + 1 ms USB + ~2 ms stack ≈ 9 ms typical).
  - WS3 `keyboard_module.ino`: **5 rows × 12 cols = 60 keys** — a desktop-style layout (ESC row, F1–F10 Fn layer, Tab/Caps/Shift, arrow cluster) vs the spec's 30-key thumb board (`QWERTYUIOP / ASDFGHJKL⏎ / FNZXCVBNM⌫SPACE`). A 5-row matrix cannot physically fit the 22.5 mm module height (5 × 9.6 mm pitch = 48 mm) and 12 columns exceed the 118 mm footprint at the spec'd pitch.
  - Scan loop is `scanMatrix(); delay(5);` → **≈170–200 Hz actual**, not 1 kHz. The laptop doc's 9 ms latency estimate and its "Typing (1 kHz scan)" 18 mA power row rest on a scan rate the firmware does not implement.
  - The bay *electrical/ID* contract (MOD_KEYBOARD=6, 33 kΩ, I2C 0x2A, reg2=5, HID boot) is reconciled on both sides ✓ (verified in source); the **key geometry and scan timing are not**. `modules_report.md` §2 and roadmap B2's "contract already reconciled" both miss this. Fix direction: rewrite the firmware matrix to the 30-key thumb layout and align the scan-rate/latency/power assumptions, or revise the hardware spec — one of the two, before B2's firmware-in-loop work proceeds.
- **FINDING M-2 (minor):** `modules_report.md` §2 says "~100 Hz scan" — the code's `delay(5)` yields ≈170–200 Hz. Report understates the actual rate.
- **FINDING M-3 (minor):** report claims thermal/satellite stdout "pasted verbatim", but trailing paragraphs are truncated (thermal: module self-heat + NOTE paragraph; satellite: NOT-VERIFIED paragraph). What is shown matches; the "verbatim" label overclaims. Suggest "stdout (excerpt)" or paste the full blocks.

### 2.4 own_brain/ — VERIFIED (2 minor notes)

- All power-sim table values in `own_brain_spine.md` match stdout exactly: deep_sleep 0.05 W / 297.8 h, stick_idle 0.35 W / 39.1 h, phone_active 2.85 W / 4.8 h, ai_burst 6.90 W / 2.0 h; derate 1.20 W; "FAIL by 4.90 W" ✓; burst times 2.7/3.7/2.8 min ✓; cooled-burst note ✓.
- Area budget re-derived: 1440+196+459+260+90+60+140+50+250 = 2945 mm² = **80.9%** of 3640 ✓; every row percentage checks. Height stack 1.0+0.8+1.3+0.4+0.1 = 3.6 ≤ 4.5, margin 0.9 ✓.
- **NOTE O-1 (minor):** the table pairs "0.05 W" with "297.8 h", but 13.7/0.05 = 274 h. The components sum to **0.046 W** (0.031+0.010+0.005) and the runtime is computed from the unrounded total (13.7/0.046 = 297.8 ✓). The rounding artifact lives in the sim's own table and was copied faithfully. Suggest showing "0.046 W (→0.05 shown)" or three-decimal totals.
- **NOTE O-2 (minor, cross-workstream):** `COOLING_DP_W = +1.0 W` (assumption A4) is still a placeholder in the sim, while the modules workstream has since produced the measured number (folded cap 2.045 → 6.97 W @25 °C, i.e. **+4.97 W**). Roadmap B8 already schedules the replacement — fine — but `power_sim.py`/`own_brain_spine.md` should cite the new figure and its source rather than the placeholder. No numeric mismatch with the sim's own output.

### 2.5 hologram/ — VERIFIED (no mismatches)

- Every number in `hologram_system.md` matches `calcs.py` stdout: 300 px/view ✓; 0.543 mm = 47 LPI (25.4/0.543 = 46.8 ✓); latency total 25.6 ms ✓ (8.3+3+6+8.3); 24.4 ms margin ✓; 0.70 W → 0.70 Wh = 5.1% ✓; AirScreen 4.0+2.0+0.4 = 6.4 W = 64% of bay ✓; 15 ml tank ✓; 50×20×15 mm = 15 ml ✓; stick-side 2.5 W ≤ 3 W ✓; 8.9 W total → 2.23 Wh = 16.2% ✓; volumetric 197 / 938 traps ✓; 47.9 W optical → 191.6 ≈ 192 W wall-plug ✓; 96× over law ✓; eye-safety 50 mW / 2 mW ≈ 25× per beam ✓.
- Honest labels intact: MAKEABLE vs RESEARCH TRACK used correctly; the ~1000× gap is stated at full size; eye-safety is a stated HARD BLOCKER (Class 3B/4), not hand-waved; light-field is never called a hologram *in this doc* (see UX finding U-2 for the prototype button).

### 2.6 materials/ — VERIFIED (no mismatches)

- `mass_calc.py` stdout is pasted **exactly** into `materials_v2.md` (byte-for-byte); the pre-existing `mass_stdout.txt` is byte-identical to this verifier's fresh run.
- Derived claims re-checked: +19.98 g → 261.0 g, +8.3% ✓; Ti rails +24.83 g vs CFRP −9.52 g ✓; section-thinning math 0.6×63.57 = 38.14 vs Al 38.75 ✓; specific stiffness 25.7/43.8/25.5/6.6/2.0/2.2/94.9 ✓; CFRP +71.4% over Al ✓.

### 2.7 roadmap/ — STRUCTURALLY SOUND (1 staleness finding)

- All 9 RICE scores independently recomputed — **exact**: 1.25, 0.70, 0.57, 0.38, 0.33, 0.30, 0.18, 0.17, 0.015; ranking order correct; risk register P×I arithmetic and sort order correct.
- File exists; internal cross-references resolve (mermaid graph, dependency table, phase gates). No fantasy numbers: effort is intervals, confidence is stated, B10 explicitly out of scope.
- **FINDING R-1 (medium — stale, but self-documented):** B1 was authored when `DESIGN_v2_0/tablet/` "did not exist on disk at read time" and prices the tablet work as an **undelivered full study** (8–14 ww). The tablet study has since been delivered (COORDINATION.md 13:15 UTC: opposed dual-roll winner, 190×46×22, 329 g, checker PASS). The roadmap *anticipates* this ("If WS1 surfaces later, its evidence replaces this row's assumptions") — the refresh now needs to happen: B1's scope note, RICE basis, and effort interval are superseded by the delivered evidence. Numeric claims marked as of read-time; marked NOT INDEPENDENTLY RE-RUN where applicable (RICE inputs are author estimates, not computations).

### 2.8 security/ — STRUCTURALLY SOUND (1 count finding)

- File exists; internal cross-references resolve; verdicts cite file:line. The review is explicitly review-only, NOT-CHECKED scope honestly listed (no target runtime, no OTA testing, no Android device).
- **Spot-check by this verifier (read-only):** cited lines in `CODE_v1_6/firmware/nexus_controller/nexus_controller.ino` confirmed — `PIN_PAIR_BTN = 0` declared and never referenced again (F1); unconditional `getAdvertising()->start()` (F1/F7); unchecked `moduleId = v[1]` at `case 0x02` (F2); `onConnect` unconditionally resetting `lastHeartbeatMs` (F3). The line references are accurate.
- **FINDING S-1 (minor):** the verdict header says "**4 Medium**, … **2 Informational**" but the body lists **F5–F9 (5 Medium)** and **I1–I4 (4 Informational)**. Header counts don't match the body.
- Numeric/technical claims in the review are **NOT INDEPENDENTLY RE-RUN** (no ESP32 target in this environment — the review itself flags F5 as heuristic; this verifier did not execute firmware).

### 2.9 UX / product review — `laptop/nexus_os_desktop.html` (static review ONLY; no browser execution)

Method: full static read of the 16.9 KB single-file prototype (HTML+CSS+JS), checked against its design doc (§5) and the phone-mode prototype (`ARCHIVE_v1_7/…/os/nexus_os.html`) for consistency. **Findings only; no edits made.**

**Confirmed good:**
- `check.py` PASS corroborated: all 33 JS-referenced ids exist in the file; zero external http/https references.
- Desktop trigger matches the spec: `desktop = kb && u >= 0.9`; CH_BAY renders `[6, 1, 100, 0]` — byte-consistent with the bay contract.
- The brightness-cap policy implements the design doc exactly: cap lands at 78% → 2.15 + 0.35 + 0.5 = 3.0 W (verified in the JS formula).
- Telemetry uses the v0.8 model numbers from the doc (0.6→2.6 W display, 0.35/0.10 controller, module classes, 13.7+10 Wh, Wh/W runtime, thermal budgets) — no invented values found.
- Consistent with the phone-mode prototype: same element-ID family (bBright/bField/modeName/osnote/sBatt/sRun/sScr/sTherm/sW/strip/u/dev/deg), same "Stick / Expanding… / Smartphone" mode vocabulary, same strip clock idiom. Desktop is a clean extension, not a fork.

**Findings (UX / product):**
- **U-1 (medium, messaging contradiction):** the brightness-cap note says "display brightness capped at X% so total draw stays ≤ 3.0 W (firmware budgetState = 1)". With a heavy module docked (e.g. camera 2.5 W + keyboard 0.5 W), the cap floor (5%) still leaves draw ≈ 4.05 W > 3.0 W — and the thermal pill simultaneously shows **OVER**. The note's "stays ≤ 3.0 W" guarantee contradicts the visible OVER state. Fix: qualify the note ("brightness capped at minimum; total still over budget") — the "ask OS to dim" policy cannot fix a module-over-budget condition; there is no OS policy to shed a docked module.
- **U-2 (medium, honest-labels tension):** the button reads "Light-Field (Hologram) Mode". The hologram workstream's standing doctrine is *light-field, never called a hologram* — the parenthetical violates it. Inherited from the phone-mode prototype (so it's consistent with the phone OS, but in tension with the v2.0 doctrine). One side has to give; the doctrine is the newer, deliberate decision.
- **U-3 (low):** the window min (–) and close (×) buttons are behaviorally identical (both just hide the window). Two visually distinct controls with one behavior.
- **U-4 (low, accessibility):** window drag/resize is pointer-only — no keyboard operability (focus, Escape to cancel, arrow keys); no `aria-live` on the thermal pill, which is a safety-relevant state change.
- **U-5 (low):** arming light-field at <99% deployment gives no feedback — the mode silently requires full unroll (holo layer stays hidden until u=1.0). A "full deployment required" hint would close the gap.
- **U-6 (product observation):** the thermal OVER state (camera-class module docked) has no recovery affordance beyond dimming to 5% brightness — the prototype honestly surfaces the limit, which is good, but a production policy needs a module-shedding rule (firmware `budgetState`, not just OS dimming).
- **Static-only caveat:** interaction behavior (drag physics, resize bounds, taskbar toggles) was **not executed in a browser** — code-read only. `nexus_os_desktop.html` is therefore **NOT TESTED as behavior**, per the evidence-collector rule.

---

## 3. MISMATCH / FINDINGS LIST (consolidated)

| ID | Workstream | Severity | Finding |
|---|---|---|---|
| T-1 | tablet | minor | Concept (b) "~286 g" quoted in report table is not computed by `concepts.py` (no mass printed for (b)) — untraceable. |
| L-1 | laptop | clarity | Hinge-torque prose compresses the formula; 25% allowance is on the 31.5 mN·m device moment. Numbers correct. |
| **M-1** | **modules** | **medium** | **Keyboard firmware (5×12=60-key desktop layout, ~170–200 Hz scan) does not match the laptop hardware spec (3×10=30-key thumb layout, 1 kHz scan assumed in power/latency budgets).** Bay electrical contract agrees; geometry and timing do not. |
| M-2 | modules | minor | Report says "~100 Hz scan"; code does `scanMatrix(); delay(5);` ≈ 170–200 Hz. |
| M-3 | modules | minor | Thermal/satellite stdout labelled "pasted verbatim" but trailing paragraphs truncated. |
| O-1 | own_brain | minor | deep_sleep "0.05 W" displayed with "297.8 h" runtime — exact total is 0.046 W; rounding artifact. |
| O-2 | own_brain | minor | `COOLING_DP_W = +1.0 W` placeholder predates the modules workstream's measured +4.97 W cap raise. |
| **R-1** | **roadmap** | **medium** | **B1 row is stale: authored when tablet/ was absent; the tablet study is now delivered.** Roadmap's own instruction says WS1 evidence replaces the row — the refresh is outstanding. |
| S-1 | security | minor | Verdict header counts (4 Medium / 2 Informational) don't match the body (5 Medium / 4 Informational). |
| U-1 | desktop OS | medium | Brightness-cap note's "stays ≤ 3.0 W" guarantee contradicts the simultaneous OVER state when a heavy module is docked. |
| U-2 | desktop OS | medium | "Light-Field (Hologram) Mode" button label contradicts the never-called-a-hologram doctrine. |
| U-3…U-6 | desktop OS | low | min/close identical; pointer-only window management; silent light-field arming; no module-shedding recovery policy. |

**Empty-mismatch areas (explicitly):** hologram — zero mismatches. materials — zero mismatches. own_brain sim-vs-doc numbers — zero mismatches. tablet checker block — zero mismatches. All RICE/risk arithmetic — zero mismatches.

---

## 4. UNTESTED SCOPE (honest labels)

- `nexus_os_desktop.html` behavior — static review only, **NOT TESTED** as executed behavior.
- Security review's numeric/technical claims — **NOT INDEPENDENTLY RE-RUN** (no ESP32 target; review is static).
- Roadmap RICE inputs (reach/impact/confidence/effort) — author estimates, **NOT INDEPENDENTLY RE-RUN**; only the arithmetic was verified.
- Sketch RAM/flash numbers beyond the four confirmed — n/a (all four confirmed).
- Physical/bench anything — parked by the DIGITAL-ONLY mandate; every NOT-VERIFIED list in the workstreams stands.

---

## 5. FINAL VERDICT: **GO (with conditions)** for the v2.0 design pack

The evidence gate **passes**: all 9 scripts reproduce byte-identically; all 4 sketches recompile `--clean` with byte-exact sizes; every pasted stdout block checks out; no fabricated numbers were found anywhere in the pack.

**Conditions before any downstream decision (integration / freeze / B1 / B2):**
1. **M-1 (medium):** reconcile the keyboard firmware matrix/layout/scan-rate with the laptop hardware spec — bay contract is agreed; geometry and timing are not.
2. **R-1 (medium):** refresh roadmap B1 against the delivered tablet study (the roadmap's own instruction).
3. **Security review (standing):** its F1–F4/F6/F9 fix-before-merge items remain the precondition for any firmware/app merge — unchanged by this gate.
4. Minor items (T-1, M-2, M-3, O-1, S-1, U-1…U-6): fix in the next edit pass; none withhold the pack.

**Blocking items for *this pack*: none.** This is a design-evidence release, not a hardware merge — and as evidence, it holds.
