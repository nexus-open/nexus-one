# Licensing

NEXUS ONE is released under three licences, each covering a different layer of the project. This is deliberate:

| Layer | Licence | What it covers |
|---|---|---|
| Hardware designs | **CERN Open Hardware Licence Version 2 — Strongly Reciprocal** ([LICENSE-HARDWARE](LICENSE-HARDWARE)) | CAD sources (`cad/`), mechanism and module designs, material studies, schematics, design documents, the design freezes (`docs/`) |
| Firmware / software | **GNU General Public License v3** ([LICENSE](LICENSE)) | All Arduino/ESP32 firmware (`firmware/`), the Android launcher and BLE client (`os/android-launcher/`), Nexus OS prototypes (`os/prototypes/`), simulation and checker code, test suites |
| Renders, images, boards | **Creative Commons Attribution-ShareAlike 4.0** (CC BY-SA 4.0) | `renders/`, `vision/` — see note below |

## Why the strongly-reciprocal hardware licence

CERN-OHL-S v2 means: you may study, modify, make, and sell products based on these designs — but if you distribute a product or the modified design, the modified source must be shared under the same licence. **Nobody can take NEXUS ONE closed and commercialise it privately.** Improvements flow back to the community. This is the project's defensive position: the blueprint is public, the upgrades stay public.

GPLv3 does the same job for the software layer — firmware and OS changes stay free.

## CC BY-SA 4.0 note (renders and vision boards)

The images in `renders/` and `vision/` are licensed under [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by/4.0/). You may share and adapt them, provided you credit "NEXUS ONE by Fabulous" and license derivatives under the same terms.

## Notices

- The CERN-OHL-S v2 licence text in this repo is the unmodified SPDX-published text (copyright CERN 2020); use of it implies no endorsement by CERN.
- The GPLv3 text is the unmodified GNU-published text.
- All source and documentation is provided WITHOUT WARRANTY of any kind (see each licence's disclaimer sections). In particular: this is a simulated design — nothing here is a guarantee that a manufactured product works; see the NOT-VERIFIED register in `docs/freeze-v2/OPEN_ITEMS_v2_0.md`.
