# NEXUS ONE v2.0 — OWN-BRAIN SPINE (design branch)

**Status:** v2 architecture branch. Paper design only. **Does not touch the v1.0 freeze**
(stick 183.9×34×22 mm, R8 drum, 13.7 Wh, 241 g, thermal law folded ≤2 W /
folded+batt ≤1.5 W / open ≤3 W, BLE protocol v1.0, ESP32-S3 safety controller).

**What changes in this branch:** Nexus One gets its own application processor — a
real SoM-class compute module on the spine tray — so the posters' "next-gen AI
chip" is a physical board, not a host-phone dependency.

---

## 1. SoM class — grounded in real products

Real SoM standards were surveyed against the 140×26 mm tray (4.5 mm height):

| Real class | Published dims | Fits 26 mm width? | Source |
|---|---|---|---|
| Variscite DART (i.MX-class, e.g. DART-MX91: 1.4 GHz Cortex-A55, ≤2 GB LPDDR4, Wi-Fi 6) | 55×30 mm | **No** (30 > 26) | electronicsforu.com news, Variscite DART-MX91 |
| SMARC 2.2 (e.g. Advantech AOM-5521, NXP i.MX 95) | 82×50 mm | **No** | CNX Software, 2025-08-04 |
| OSM Size L solder-on (Advantech AOM-2521, i.MX 95) | 45×45 mm | **No** | CNX Software, 2025-08-04 |
| Boardcon CM311Y3 (Amlogic A311Y3, 8 TOPS NPU, castellated) | 52×45 mm | **No** | CNX Software, 2026-09-03 |

**Honest verdict:** no standard SoM fits the 26 mm tray width. The v2 branch
therefore defines a **custom "Nexus Spine SoM" class in the DART/SMARC
mezzanine tradition** (same design language: SoC + LPDDR + eMMC + PMIC on a
mezzanine, carrier holds connectors/power), sized **60×24 mm**, solder-down
(OSM-family solder-on precedent, e.g. AOM-2521).

**SoC basis — NXP i.MX 95 class** (published specs, not assumptions):
- 6× Arm Cortex-A55 @ up to 2.0 GHz + Cortex-M7 @ 800 MHz + Cortex-M33 safety core
  (CNX Software i.MX 95 brief; Advantech AOM-5521 listing)
- NXP eIQ Neutron NPU, **2 TOPS** (Advantech AOM-5521 spec)
- x32 LPDDR5/LPDDR4x up to 6.4 GT/s; reference config **8 GB LPDDR5-6400**
  (Advantech AOM-5521)
- 4-lane MIPI-DSI (drives the flexible panel natively), 2× MIPI-CSI, USB 3.0
  Type-C, PCIe Gen3 (CNX i.MX 95 brief)
- Package 15×15 mm² (0.5 mm pitch) or 19×19 mm²; Tj consumer 0–95 °C,
  industrial −40–105 °C (CNX brief)
- **Published power basis:** i.MX 95 datasheet SUSPEND typical **30.72 mW**
  total (NXP, measured on EVK); power-measurement methodology per NXP AN14449
  (Feb 2026). Full-load active numbers were not recovered in this pass → used
  as ASSUMPTIONS in the sim, flagged.

Why i.MX 95-class and not a hotter AI SoC (e.g. Axera AX8860P-class, ~40 W
under load — CNX Software, 2026-10-19): 40 W-class parts cannot exist inside a
2 W-folded thermal law at all. The i.MX 95 class is the hottest *honest* choice —
it still must derate folded (Section 3), which proves the law rather than
hand-waving past it.

Citations:
- https://www.cnx-software.com/2025/08/04/advantech-unveils-nxp-i-mx-95-smarc-2-2-and-osm-size-l-system-on-modules/
- https://www.cnx-software.com/2023/01/05/nxp-i-mx-95-processor-arm-cortex-a55-cortex-m33-and-cortex-m7-cores-eiq-neutron-npu/?amp=1
- https://www.nxp.jp/docs/en/application-note/AN14449.pdf
- https://www.avnet.com/wcm/connect/287a3688-bfad-4713-a444-8f855120d24a/NXP-IMX95AEC-Automotive-Datasheet.pdf?MOD=AJPERES
- https://www.electronicsforu.com/news/system-on-module-with-2gb-low-power-memory

---

## 2. Board fit — 140×26 mm tray, ≤4.5 mm height

Tray area: 140×26 = **3640 mm²**. Drum, 2×6.85 Wh cells, and the FPC rolling
loop stay in place (cells co-located in the stick body per frozen mech; tray
envelope is the constraint).

### 2D area budget

| Subsystem | Footprint | mm² | % of tray |
|---|---|---|---|
| Nexus Spine SoM (custom mezzanine) | 60×24 | 1440 | 39.6 |
| micro-CAMM slot + 10.5×10.5 module keep | 14×14 | 196 | 5.4 |
| ESP32-S3-WROOM-1 (safety controller, unchanged) | 18×25.5 | 459 | 12.6 |
| Power: BQ25890-class charger + PMIC + TPS61088-class boost + MAX17048-class gauge | — | 260 | 7.1 |
| USB-C receptacle + PD controller | — | 90 | 2.5 |
| AS5600 encoder + 2× DRV5032 + magnet keep-out | — | 60 | 1.6 |
| Bay pogo connector + 2× TPS229-class load switches | — | 140 | 3.8 |
| MIPI-DSI mux/ESD + level shifting | — | 50 | 1.4 |
| Keep-outs (drum shaft bearing, FPC sweep zone, battery tabs) | — | 250 | 6.9 |
| **Total** | | **2945** | **80.9** |

**Verdict: FITS** at ~81% fill. Dense — requires 4-layer HDI routing — but
inside the frozen envelope with the drum, cells, and FPC loop untouched. No
envelope change required. (Caveat: keep-out map must be overlaid on the v0.7
mech model before layout; see NOT-VERIFIED.)

### Height stack (≤4.5 mm) — solder-down SoM variant (recommended)

| Layer | mm |
|---|---|
| Carrier PCB | 1.0 |
| SoM PCB (solder-down, no B2B connector — OSM solder-on precedent) | 0.8 |
| i.MX95 FCBGA 15×15 package (ASSUMPTION: 1.3 mm pkg height) | 1.3 |
| Shield can over SoC+PMIC+LPDDR5 zone (ASSUMPTION) | 0.4 |
| Solder-joint allowance | 0.1 |
| **Stack total** | **3.6** ≤ 4.5 ✓ (0.9 mm margin) |

Carrier-top discretes: tallest = ESP32-S3 module 3.1 mm (from v0.8 — unchanged),
USB-C receptacle ~3.2 mm → both ≤ 4.5 ✓.
**Rejected variant:** B2B-connector SoM (+0.8 mm mated = 4.4 mm stack, 0.1 mm
margin — too tight; solder-down is the branch choice).

---

## 3. Power modes vs thermal law (from `power_sim.py` — run it)

Sim: `python3 power_sim.py` (prints mode table, derate, burst times, assumptions).

| Mode | Total | vs folded ≤2 W | vs open ≤3 W | Runtime (13.7 Wh) |
|---|---|---|---|---|
| deep_sleep | **0.05 W** | PASS | PASS | ~298 h |
| stick_idle | **0.35 W** | PASS | PASS | ~39 h |
| phone_active (open, 4×A55@1.0 GHz, display mid) | **2.85 W** | FAIL (open-only) | PASS | ~4.8 h |
| ai_burst (open, 6×A55@2.0 GHz + NPU + display full) | **6.90 W** | FAIL | FAIL (burst-duty) | ~2.0 h |

### The folded derate, quantified

Full AI wants 6.90 W folded against a 2.0 W law → fails by 4.90 W. Fixed folded
loads (strip dim, ESP32-S3, BLE, PMIC) ≈ 0.50 W, leaving a **SoC+DRAM budget of
1.50 W**. The folded AI-lite configuration that passes (1.20 W):

- **CPU:** 6× A55 @ 2.0 GHz → **2× A55 @ 800 MHz** (4 cores power-gated)
- **NPU:** eIQ Neutron **ON → OFF** (power-gated; 2 TOPS unavailable folded)
- **DDR:** LPDDR5 6400 MT/s → **1600 MT/s**
- **Display:** full panel 1.6 W → **strip only** 0.25 W
- **GPU:** on → off

Folded + battery module (law ≤1.5 W): derate harder → **1× A55 @ 600 MHz**,
NPU off, strip display ≈ 1.20 W → PASS.

### Burst time before the thermal cap trips

Rth folded = 8.8 K/W (frozen); Tj_max = 105 °C (i.MX95 industrial); Tamb = 35 °C
(pocket worst case, ASSUMPTION); Cth = 15 J/K local thermal mass (ASSUMPTION,
sensitivity-printed).

| Cth | Folded burst (6.9 W vs 2 W cap) | Open burst (6.9 W vs 3 W cap) |
|---|---|---|
| 10 J/K | 1.8 min | 2.5 min |
| **15 J/K** | **2.7 min** | **3.7 min** |
| 25 J/K | 4.5 min | 6.2 min |

**Honest result, as expected: full AI power is OPEN-MODE ONLY — and even open
it is burst-duty (~3.7 min at Cth=15 before Tj hits 105 °C), never sustained.**
The OS thermal governor (same law-enforcement role as v1.0 Nexus OS) must
schedule NPU workloads as bursts with cool-down, exactly as v1.0 treated the
camera module.

### Cooling module effect (optional row)

Parameterized as `COOLING_DP_W` in the sim, default **+1.0 W folded cap
(ASSUMPTION — replace with the modules workstream's ΔT-derived number)**:
folded cap → 3.0 W. AI burst (6.9 W) still FAILs sustained — still burst-only
(2.8 min); the derated folded AI-lite passes with headroom. Note the subtlety
the sim prints: a higher sustained cap means higher steady-state temperature,
so burst margin *shrinks* — the cooling module buys sustained throughput, not
longer bursts.

---

## 4. Expandable RAM — micro-CAMM applied to the spine

From the v0.5 invention pack (INVENTIONS_v0_5): linear CAMM at 44 mm fails the
module edge; the answer is the **area array: 220 contacts, 15×15 grid @
0.7 mm = 10.5×10.5 mm footprint. Fits.**

Applied to the own-brain spine:
- **Base:** 8 GB LPDDR5-6400 soldered on the SoM (matches the published
  AOM-5521 reference config; i.MX95 x32 LPDDR5 @ up to 6.4 GT/s).
- **Expansion:** one micro-CAMM slot on the carrier (14×14 mm keep in the area
  budget) accepting a **10.5×10.5 mm micro-CAMM module with 8 GB LPDDR5X** →
  **16 GB total**.
- The slot sits beside the SoM (not under it) so the height stack is unchanged.

---

## 5. Architecture delta vs v1.0

**What changes:**
- The brain moves on-board: i.MX95-class SoM runs Nexus OS natively (apps, AI
  inference on the 2-TOPS NPU, media). No host phone required for the device
  to be a phone.
- **USB-C video goes internal:** SoC 4-lane MIPI-DSI → panel driver directly.
  The v1.0 path (host phone → USB-C DP Alt-Mode → driver HDMI input) is deleted.
- **The host phone becomes an optional peripheral:** it pairs over BLE/USB-C as
  a companion — cellular tether source, camera donor, casting target — instead
  of being the compute brain.
- BLE protocol v1.0's *peer* changes: the controller's GATT client is now the
  on-board SoC (via its BLE stack / UART to ESP32), not the user's phone. The
  protocol frames themselves are byte-identical.

**What stays:**
- **ESP32-S3 remains the mechanism safety owner** per protocol v1.0: drum
  motor/brake, AS5600 + end-stop Halls, 30 s heartbeat watchdog, thermal-law
  enforcement, bay power gating. Unchanged silicon, unchanged role.
- Thermal law unchanged (≤2 / ≤1.5 / ≤3 W); module bay rail + 8 pogo (USB2)
  unchanged; 10 W bay max unchanged; micro-CAMM from the v0.5 pack.

**Firmware migration (v1.6/v1.7):** The ESP32-S3 controller firmware from
v1.6/v1.7 ports **unchanged** — it was designed brain-agnostic, exposing the
same GATT characteristics and protocol-v1.0 frames regardless of who the peer
is; no controller code changes are needed, only re-pointing the BLE peer from
the host phone to the on-board SoC (or a UART/SPI link presenting the same
client role). The new work is all on the SoM side: a Linux userspace client
implementing the v1.0 protocol client role (byte-identical to the v1.7 host
client), plus device-tree/bring-up for the SoC's MIPI-DSI panel path, PMIC
rails, and the NPU thermal-governor hooks that enforce the burst-duty rule
from Section 3.

---

## ASSUMPTIONS

- A1: SoC active draws (3.2 W CPU full-load, 0.8 W NPU, 0.5 W LPDDR5) scaled
  from A55-class norms — no i.MX95 full-load EVK number recovered (AN14449
  covers use-case methodology, not a single headline number).
- A2: Rth_open = 4.0 K/W (open panel radiates; needs a v0.4-style sim).
- A3: Cth = 15 J/K local thermal mass (needs thermal test; sim prints 10/25
  sensitivity).
- A4: Cooling module raises the folded cap by +1.0 W (pending the modules
  workstream's ΔT number; parameterized as `COOLING_DP_W`).
- A5: Tamb = 35 °C worst case (pocket/hand).
- A6: FCBGA package height 1.3 mm, shield can 0.4 mm.

## NOT-VERIFIED

1. i.MX95 full-load power on EVK (measure per AN14449; replaces A1).
2. Rth_open and Cth (thermal sim + physical test; replaces A2/A3).
3. micro-CAMM signal integrity at LPDDR5 6400 MT/s over the 10.5 mm area-array
   connector + i.MX95 dual-rank memory-controller support (SI sim required).
4. Carrier routing feasibility at 81% fill with keep-outs overlaid on the v0.7
   mech model (layout study).
5. SoM RF: Wi-Fi/BT antenna placement and coexistence inside the stick
   (antenna geometry study).
6. Panel-driver MIPI-DSI timing for the 162.9×71.5 flexible panel on the i.MX95
   DSI controller (driver-board spec needed).
7. Battery cycle life under the v2 load profile (deeper, hotter bursts).
8. Cooling module's real ΔT / cap raise (modules workstream).

## Deliverables in this directory

- `power_sim.py` — runs, prints mode table + derate + burst times + assumptions.
- `own_brain_spine.md` — this file.
