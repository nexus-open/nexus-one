# NEXUS ONE v2.0 — Laptop Mode: Keyboard Module + Tail-Cap Kickstand

Workstream: LAPTOP MODE (keyboard module hardware + kickstand + Nexus OS desktop mode).
Companion files: `nexus_os_desktop.html` (desktop-mode OS prototype), `torque_calc.py`
(statics source — re-run it to reproduce every number below), `check.py` (HTML sanity check).

Frozen v1.0 core is referenced, not modified. All numbers below are either computed
in `torque_calc.py` / stated design targets, or marked **ASSUMPTION**.

---

## 1. Laptop-mode pose (design decision)

The stick lies flat on the desk as the base bar. The panel is unrolled to full
162.9 × 71.5 and rises from the stick's front slot at **75° above the desk**
(15° recline — standard laptop screen angle), held by the panel detent with the
tail-cap kickstand as the rear prop / positive angle stop. The keyboard module
stays docked in the bay on the stick's top face — keys face straight up in front
of the screen, typed like a normal low-profile keyboard. Typing force is
downward onto the base, which *increases* stability (see §4).

Why this pose: the bay is on the stick's back face, so any propped-tablet pose
puts the keys facing away from the user. The flat-base easel is the only pose
where docked pogo-pin USB typing is ergonomically coherent. Stated as a decision,
not a freeze — a detachable BLE keyboard is a possible v2.1 alternative.

---

## 2. Keyboard module — hardware spec

### 2.1 Envelope & docking

| Item | Spec |
|---|---|
| Bay rail (frozen) | 120 × 24 mm, 8 pogo pins, 10 W max |
| Module footprint | 118 × 22.5 mm (1 mm rail clearance per side) |
| Docked thickness | **7.5 mm** (1.5 base + 0.8 PCB + 4.2 key stack + 1.0 bezel) |
| Docked stack | 22 mm stick + 7.5 mm = 29.5 mm max |
| Docking | Slide-in along the 120 mm rail, end-stop detent |
| Lock | Magnetic: 4× N52 4×2×1 mm in module base → steel strike plates in bay; ≈10 N total pull (**ASSUMPTION** — pull-force calc, verify on first article) |
| Electrical | Gold contact pads on module mate to stick-side pogo pins per frozen POGO MAP (1:VCC5 2:GND 3:USB2_D− 4:USB2_D+ 5:I2C_SDA 6:I2C_SCL 7:ID 8:GND) |

### 2.2 Key layout (fits 120 mm)

3 rows × 10 columns = **30 keys**, row pitch 6.5 mm, column pitch 11.4 mm,
keycap 9.6 × 5.4 mm. Compact thumb/board layout — honest about what fits:

- R0: `Q W E R T Y U I O P` (Fn → `1 2 3 4 5 6 7 8 9 0`)
- R1: `A S D F G H J K L ⏎` (Fn → symbols)
- R2: `FN Z X C V B N M ⌫ SPACE`

Matrix: 10 columns driven × 3 rows sensed, 1 kHz full-matrix scan.

### 2.3 Switch

Low-profile **scissor** mechanism, travel **0.8 mm** (**ASSUMPTION** — typical
low-profile scissor range 0.5–1.2 mm; confirm against chosen part datasheet),
actuation ≈1.6 N ± 0.3 N (**ASSUMPTION**, BlackBerry-class dome), rated 5 M
cycles (**ASSUMPTION**). No backlight — a backlight does not fit the 0.5 W
budget; omitted deliberately.

### 2.4 Power budget (VCC5 = 5 V)

| State | Current | Power | Note |
|---|---|---|---|
| Boot / enumerating | < 50 mA | < 0.25 W | frozen contract limit (bay_module_common.h) |
| Idle, USB suspend, scan off | 1.5 mA | 7.5 mW | design target |
| Idle, USB active, 250 Hz scan | 6 mA | 30 mW | design target |
| Typing (1 kHz scan + reports) | 18 mA | 90 mW | design target |
| Worst burst (full rollover) | 40 mA | 0.20 W | design target |
| **Declared class (I2C reg 2)** | **100 mA** | **0.5 W** | **contract** — matches vision-map "<0.5 W of the 10 W bay budget" |

Folded check (frozen thermal law): 0.6 (display folded) + 0.1 (controller) +
0.5 (keyboard) = 1.2 W < 2.0 W folded budget ✓.
Open/laptop check: display up to 2.6 + 0.35 + 0.5 = 3.45 W > 3.0 W open budget →
the OS dims the display to fit (desktop prototype caps brightness at 78%:
2.15 + 0.35 + 0.5 = 3.0 W exactly — mirrors firmware `budgetState = 1`
"ask OS to dim"). This policy is implemented in `nexus_os_desktop.html`.

### 2.5 Mass breakdown (**ASSUMPTION** ±5 g — weigh on first article)

| Part | Mass |
|---|---|
| 30× keycap + scissor + dome @ 0.55 g | 16.5 g |
| PCB 118×22.5×0.8 mm FR4 | 3.9 g |
| MCU + passives + USB ESD | 2.0 g |
| Mg-alloy frame / bezel | 6.5 g |
| 4× N52 magnets + keeper | 1.2 g |
| POM slide rails | 1.0 g |
| **Total** | **≈ 31 g** |

### 2.6 USB / HID

- Module = USB Full-Speed **HID keyboard device**; the spine AP is the USB host
  (pogo pins 3/4 = USB2_D−/D+). The ESP32 controller does NOT forward keys —
  it only does ID / power / thermal.
- HID 1.11 boot-keyboard compatible. Report: 1-byte modifier + 1 reserved +
  6 keycodes (8-byte boot report); Report ID 2 = 4-byte Fn-layer consumer keys.
- `bInterval` = 1 ms (1000 Hz poll).
- **Latency estimate:** 1 ms scan + 5 ms debounce (**ASSUMPTION** — firmware
  agent owns debounce tuning) + 1 ms USB poll + ≈2 ms AP HID stack
  (**ASSUMPTION**) ≈ **9 ms typical, < 15 ms worst**. Measure at bring-up.

---

## 3. Interface contract — for the keyboard firmware agent

The firmware agent owns the module firmware; the hardware guarantees this side:

- **Module ID:** `MOD_KEYBOARD = 6` (new; add to the `ModuleId` enum —
  do NOT renumber 0–5).
- **ID resistor:** **33 kΩ**, 1% metal film, pin 7 → GND. 33 kΩ was free in
  the v1.4 table (1 k / 2.2 k / 4.7 k / 10 k / 22 k used). Spine divider is
  10 k pull-up to 3V3 → keyboard reads **2.533 V / 3143 ADC counts (12-bit)**,
  328 counts clear of cooling (22 kΩ → 2.269 V / 2815). Suggested ADC window
  for ID 6: 2980–3300 counts (firmware agent to confirm).
- **I2C:** addr `0x2A`; reg 0 = `6` (ID), reg 1 = `0x10` (firmware v1.0),
  reg 2 = `5` (draw class, 0.1 W units → 0.5 W), reg 3 bit 0 = fault
  (spine cuts bay power within one poll cycle per frozen contract).
- **Boot:** < 50 mA until identified over I2C; only then full class current.
- **Power class:** add `MODULE_DRAW_W[6] = 0.5f` to the spine firmware table
  (frozen file — firmware agent edits; thermal law then covers the keyboard
  automatically: folded 1.2 W < 2.0 W ✓, open dim-to-fit per §2.4).
- **BLE bay characteristic** (CH_BAY, `…-0004`, 4 bytes `{id, power, mA_lo,
  mA_hi}`): keyboard docked + powered → `{6, 1, 100, 0}` (100 mA class).
  **Nexus OS enters desktop mode when CH_BAY reports id = 6 with power = 1
  and the drum encoder reads ≥ 90% deployment** (see §5). Undock → id returns
  to 0 → OS drops back to phone/stick mode.
- **HID descriptor class:** boot keyboard (8-byte reports) + Report ID 2
  consumer page for the Fn layer; `bInterval` 1 ms.

---

## 4. Tail-cap kickstand — 0–75°

### 4.1 Mechanism

- Single 2-stage telescopic leg, **deployed 52.3 mm** (computed — foot lands
  exactly on the desk at 75°), **stowed 34 mm** in a 36×14×8 mm channel milled
  into the tail cap's back-face corner (z ∈ [2,16] mm of the 25 mm tail cap;
  clear of the keyboard's z ∈ [32,152] span and of the bay rail).
- **Retracted envelope:** flush — 0 mm added to the frozen 183.9×34×22
  (channel is internal; a 34×14 mm cover plate sits flush on the back face).
- **Deployed envelope:** footprint grows to 183.9 × 84 mm (foot 63.6 mm behind
  the stick, 10.6 mm front overhang), height 102 mm.
- Hinge: transverse axis (along the stick's long axis z) at the tail-cap
  back-top corner; **friction hinge, 0–75°, detent-free, 20 mN·m nominal**
  (see torque calc). Foot: TPU rubber pad, μ ≈ 0.4 (**ASSUMPTION**).
- **ASSUMPTION:** 50 mm of axial space is free at the tail end of the stick
  interior for the channel + hinge (drum R8 + batteries + boards occupy the
  rest — confirm against the mechanical CAD).

### 4.2 Statics — computed in `torque_calc.py` (output pasted verbatim)

```
=== NEXUS ONE v2.0 kickstand statics (laptop / easel pose) ===
propped mass = 272 g  (241 device + 31 keyboard)
CoM: x = -6.63 mm, y = 18.23 mm  (x from stick bottom-front edge)
  stick      229 g  @ (  -4.40,  16.42) mm
  panel       12 g  @ ( -18.05,  67.37) mm
  keyboard    31 g  @ ( -18.65,  12.60) mm
hinge H = (-18.39, 26.13) mm
leg L = 52.3 mm (2-stage telescopic; stowed 34 mm) -> foot F = (-63.65, -0.00) mm
support polygon x in [-63.6, 10.6] mm
tip margins: rear 57.0 mm / front 17.2 mm -> NO TIP-OVER
max forward push at screen top before tip-over: 0.45 N
note: typing force is downward on the keyboard deck -> stabilising, not tipping
static leg load ~ 0 N (device self-stable on base; leg = rear prop / angle stop)
hinge torque: leg self-weight moment = 1.33 mN.m
hinge torque: device-weight moment about H = 31.5 mN.m
REQUIRED = (leg + 25% disturbance allowance) x SF2.0 = 18.4 mN.m
SPECIFY: 20 mN.m nominal micro friction hinge, 0-75 deg, detent-free
         holding margin on static leg load: 15.0x
ID cooling  R=  22.0 k -> 2.269 V (2815 ADC counts @12b)
ID keyboard R=  33.0 k -> 2.533 V (3143 ADC counts @12b)
ID open     R=1000000.0 k -> 3.300 V (4095 ADC counts @12b)
```

### 4.3 What the numbers mean

- **No tip-over, proven:** CoM x = −6.63 mm sits inside the support polygon
  [−63.6, +10.6] mm with 57.0 mm rear / 17.2 mm front margin.
- **Honest correction to the naive brief:** the hinge does NOT carry the
  272 g device — the desk does (the slab is self-stable on its 21.2 mm deep
  base; the CoM sits only 6.6 mm behind the front edge). The leg is a rear
  prop / positive 75° stop, ~unloaded in static equilibrium; it engages on
  backward bumps. The friction hinge therefore sizes on **pose-holding**:
  1.33 mN·m static leg moment → 18.4 mN·m required with disturbance
  allowance × SF 2.0 → **specify 20 mN·m** (15× margin on the static load).
  Full formula (torque_calc.py): (1.33 leg + 0.25 × 31.5 device-moment about H)
  × 2.0 = 18.4 mN·m.
- **Forward-tip limit (measured, not assumed):** 0.45 N push at the screen top
  tips it forward. Typing is fine (downward force stabilises); firm touch taps
  near the top of the propped screen must stay light — recorded as a known
  limit, candidate v2.1 tweak (e.g. forward secondary foot).

---

## 5. Nexus OS desktop mode — trigger & policy

Implemented in `nexus_os_desktop.html` (offline, single file, no network):

- **Trigger:** CH_BAY notification `{id:6, power:1}` (keyboard docked and
  spine-powered) **AND** drum encoder ≥ 90% deployment. Either condition lost
  → immediate fallback to phone/stick mode. Keyboard docked while folded →
  banner: "Keyboard docked — unroll to ≥90% for desktop mode".
- **UI:** landscape multi-window desktop on the open screen: 3
  draggable/resizable windows (Terminal, Files, System Monitor), taskbar with
  window buttons, live clock, KB status pill (`KB:ID6`), thermal pill.
- **Telemetry:** the exact v0.8 sim model — display 0.6→2.6 W by deployment,
  controller 0.35/0.10 W, modules (camera 2.5 / storage 1.2 / sensor 0.3 /
  keyboard 0.5), battery 13.7 Wh (+10 module), runtime = Wh/W, thermal law
  folded 2.0 / folded+battery-module 1.5 / open 3.0 W, screen 28→71.5 mm,
  drum 220°. No new telemetry values invented.
- **Thermal policy:** in desktop mode the OS auto-caps display brightness so
  total draw ≤ 3.0 W (2.15 + 0.35 + 0.5 at 78% brightness) and shows the cap —
  the software side of the firmware's `budgetState = 1` "ask OS to dim".
- `check.py` statically verifies the HTML (all JS-referenced element ids
  exist; zero external http/https references). Result: **PASS**
  (static only — not executed in a browser).

---

## ASSUMPTIONS

1. Panel + bezel = 12 g (stick remainder 229 g of the frozen 241 g).
2. Keyboard module mass ≈ 31 g (±5 g) — weigh on first article.
3. Scissor travel 0.8 mm, actuation 1.6 N ± 0.3 N, 5 M cycles — confirm vs part datasheet.
4. Magnet pull ≈ 10 N total (4× N52 4×2×1 mm) — pull-force calc, verify on first article.
5. Kickstand leg 6 g; foot μ ≈ 0.4 (TPU on desk).
6. 50 mm axial space free at the tail end for the kickstand channel + hinge — confirm vs mechanical CAD.
7. 20 mN·m micro friction hinge is a COTS class — source before EVT.
8. USB HID stack latency ≈ 2 ms; debounce 5 ms (firmware agent tunes).
9. Desktop brightness-cap policy (78%) is the OS side of firmware `budgetState=1`.

## NOT-VERIFIED

- Key feel / travel / actuation (no parts in hand; values are class-typical).
- 33 kΩ ADC window (2980–3300 counts) — needs firmware-in-the-loop ADC measurement.
- Magnet retention under drop/shake; pogo-pin contact reliability over dock cycles.
- Hinge life at 20 mN·m over deployment cycles; telescopic leg jam resistance.
- Forward-tip 0.45 N limit is a rigid-body calc — real compliance (rubber foot,
  desk surface) not modelled.
- `nexus_os_desktop.html` is statically checked only, not executed in a browser.
- Whole design: simulation/concept only — no hardware exists yet.
