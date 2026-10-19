# Launch post drafts — NOT POSTED

These are drafts only, for the owner to review and post when ready. Do not publish on anyone's behalf.

---

## 1. Show HN (title)

Show HN: Nexus One — an open-source rollable phone/tablet/laptop with snap-on modules, designed entirely on a phone

## 1. Show HN (body)

NEXUS ONE is an open-source hardware project I'm releasing today: a rollable mobile device that carries as a stick (183.9 × 34 × 22 mm), unrolls into a phone (162.9 × 71.5 mm screen), expands into a tablet (opposed dual-roll, 162.9 × 142.8 mm), and docks into a laptop — with a magnetic bay of snap-on modules (battery, camera, storage up to 4 TB, cooling, keyboard, sensor, neural, satellite).

The whole thing was designed and simulated on a single phone: mechanics (OpenSCAD), physics/geometry checkers in Python, ESP32 firmware that compiles, an Android launcher (signed APK), and a Nexus OS prototype — all in the repo. There is no physical prototype yet, and the repo is honest about it: every element carries a label — PROVEN IN SIM, DESIGNED, ASSUMPTION, or NOT-VERIFIED — and there is a 16-item open register naming exactly what would close each one.

The interesting part for engineers: the thermal law was derived, then the premium shell failed it (titanium/carbon collapsed the folded cap to 0.44 W), and the fix (a graphite spreader ply) was chosen with numbers — including the RF shielding trap it creates, with quantified keep-outs. Everything is checkable.

Licences: CERN-OHL-S v2 (hardware, reciprocal — improvements stay open), GPLv3 (firmware/OS), CC BY-SA 4.0 (renders).

What I'd love from HN: tear the numbers apart, re-run the checkers, help build the prototype (bench plan B1–B6 is in the repo).

---

## 2. Reddit (r/hardware + r/opensource)

**Title:** I open-sourced my rollable phone design — every number is simulated and labelled, help me build the prototype

**Body:**

Designed and simulated entirely on a phone, in a single day — I'm releasing NEXUS ONE as fully open source: a rollable device concept with a frozen, simulated design. One flexible OLED wraps an internal drum; the screen unrolls into a phone, a dual-roll gives a tablet, a keyboard module + kickstand gives a laptop mode. Snap-on modules for battery/camera/storage/cooling/neural/satellite live on a magnetic pogo-pin bay.

The repo has: OpenSCAD CAD, Python checkers with evidence, ESP32 firmware that compiles, an Android launcher, the design freezes (v1.0 and v2.0), and a 16-item NOT-VERIFIED register that says plainly what isn't proven yet (panel roll-cycle rating, bench prototype, F5 hardware validation).

I built the entire thing on my phone — no laptop, zero budget — with AI assistance, and I keep saying so because the honest-labelling is the project's identity: nothing here is claimed past what was simulated.

Next milestones: community prototype (bench B1–B6), a panel-durability rig, and the firmware security merge. Licences: CERN-OHL-S v2 / GPLv3 / CC BY-SA 4.0.

---

## 3. X / LinkedIn (short)

Releasing NEXUS ONE as fully open source today ∞

A rollable stick → phone → tablet → laptop with snap-on modules, designed and simulated entirely on one phone: OpenSCAD CAD, Python physics checkers, ESP32 firmware, an Android launcher — all with honest labels (PROVEN IN SIM / DESIGNED / NOT-VERIFIED) and a 16-item open register.

CERN-OHL-S v2 + GPLv3. Help us build the prototype. Link in bio.
