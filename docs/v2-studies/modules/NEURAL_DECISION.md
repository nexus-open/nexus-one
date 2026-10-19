# NEXUS ONE v2.0 — Neural module: DECISION

## Decision: BUILD the USB2-class NPU module NOW (v2.0)

**Rationale.** USB NPU sticks are a real, shipping product class — no
invention required:

- **Google Coral USB Accelerator** (G950-01456-01): Edge TPU, **4 TOPS
  (int8), ~2 TOPS/W**, 5 V USB, typical **~2 W**, peak ~900 mA; MobileNet
  V2 ~400 FPS. Datasheet v1.4.
  Sources: https://www.electromaker.io/blog/article/coral-usb-accelerator-add-fast-edge-ai-to-any-host
  and https://www.mouser.com.gt/datasheet/3/6072/1/Coral-USB-Accelerator-datasheet.pdf
- **Coral Accelerator Module (SMT/LGA MCM)** — the same Edge TPU silicon
  as a 15.0 × 10.0 × 1.5 mm, 0.67 g module with **PCIe Gen2 x1 or USB 2.0**
  interface. USB 2.0 is natively supported — exactly our bay's USB2 pogo
  pair. Sources: https://br.mouser.com/new/google-coral/coral-accelerator-mod-Edge-TPU/
  and https://www.murata.com/products/connectivitymodule/edge-ai/overview/lineup/type1wv

So the v2.0 module is: an Edge-TPU-class MCM (USB2 device) on pogo
D-/D+, plus an ESP32-S3 supervisor (this sketch) that owns the bay
contract — boot <50 mA → identify (ID 7, 47 kΩ) → sequence the NPU rail
→ thermal throttle/cut at 75/85 °C. The spine enumerates a standard USB
device; Nexus OS runs the vendor TFLite runtime. No custom driver.

**Class numbers (ASSUMPTION-labelled — the class is proven, our exact
silicon choice is not):** 4 TOPS int8, ~2 TOPS/W, 2.0 W draw class
(reg2 = 20). Fits the 10 W bay and the open-mode ≤3 W thermal law; in
folded mode the supervisor enforces the throttle/cut, and the spine's
law table governs as with every module.

**USB2 bottleneck, stated honestly:** 480 Mbps bounds *model-load*
bandwidth (a 50 MB model takes ~1 s to push), not steady-state
inference streaming (tensors in/out are small). For the v2.0 use cases
— on-device vision, voice, photo enhance — this is sufficient.

## v2 bay-bus upgrade path: USB3 over pogo (DOCUMENTED, not built)

If a future bay revision wants USB 3.x SuperSpeed to the module:

1. **Pins:** USB3 needs SSTX± and SSRX± — 4 extra signal pairs on top
   of the existing 8 pogo (VCC5/GND/D-/D+/SDA/SCL/ID/GND) → **12 pogo
   minimum**. The v0.7 8-pogo rail cannot carry it; this is a bay
   mechanical revision, not a firmware change.
2. **Signal integrity:** 5 Gbps over spring pogo contacts at ~120 mm
   module length. Pogo = impedance discontinuity (target 90 Ω
   differential, ±10%); contact bounce under vibration; crosstalk from
   the SS pairs into the USB2 pair and I2C at these edge rates.
   Requires a controlled-impedance flex + pogo barrel redesign and
   SI simulation (HyperLynx-class) — NOT-VERIFIED.
3. **Re-certification:** a 5 Gbps radiator inside the bay changes the
   EMC profile → FCC Part 15 / CE-EMC re-test of every module + spine
   combination. Budget it as a program cost, not a free upgrade.
4. **Alternative that avoids all of this:** keep USB2 for control +
   put a second NPU MCM on the module (dual-TPU-class, still USB2) —
   doubles TOPS with zero bay changes. Recommended before any USB3
   bay revision.

**Recommendation:** ship v2.0 on USB2 (this design). Revisit USB3 only
with the 12-pogo bay revision as a v2.1+ program, after SI simulation
and with re-cert budgeted.
