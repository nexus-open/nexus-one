# Contributing to NEXUS ONE

Welcome. This project is **digital-first**: the work is CAD, simulations, firmware, analysis, and documentation. You don't need a workshop — you need a computer. (Physical prototype work is welcome too, and has its own program — see below.)

## The house rule: numbers need receipts

Every technical claim in a contribution must ship with its evidence, in the same pull request:

- **Simulation / checker:** the script source **and** its verbatim stdout (see `docs/v2-studies/verification/evidence/` for the format — every checker in this repo was run twice, byte-identical).
- **Firmware:** compile log from the declared toolchain (arduino-cli + ESP32 core 3.3.12 for the sketches; toolchain notes in the archive), plus flash/RAM sizes.
- **Analysis:** the calculation source, with every constant sourced or labelled.

## The honesty labels are mandatory

Every new design or claim gets one label, used consistently:

- **PROVEN IN SIM** — a sim, checker, or compile actually ran; evidence attached.
- **DESIGNED** — a parametric design exists and was simulated; no prototype yet.
- **ASSUMPTION** — a labelled placeholder for an unpublished constant (name the source bound, e.g. "bounded from published PC/ABS data").
- **NOT-VERIFIED** — explicitly not proven; goes into the open-items register.

Inventing past "doesn't exist" is encouraged; inventing past **physics** is not. A measured gap with a named research route is always better than a shrug — and always better than a fake "solved".

## Where to help (good first areas)

- **Firmware:** close the `OPEN_ITEMS` register — implement findings, add tests. The v2.1 security branch merge is gated on F5 hardware validation; help with the merge plan.
- **Simulations:** re-run and stress the tablet dual-roll checker, the thermal model, the RF study; try to break the frozen numbers.
- **CAD:** tablet drum-2 sub-assembly, kickstand hinge detail, module shell tooling splits.
- **OS:** the Nexus OS desktop mode has open UX findings (U-1, U-3–U-6 in the freeze notes).
- **Docs:** every improvement to a study doc needs the same receipts.

## The prototype program (community hardware)

Physical build work follows the bench plan: [`docs/BENCH_PLAN.md`](docs/BENCH_PLAN.md) (B1–B6), each with sim-tied pass criteria. The plan was written as a digital reference; the community owns executing it. Milestones live in [ROADMAP.md](ROADMAP.md).

## Pull request checklist

1. Evidence attached (checker output / compile log / calc).
2. Honest label on every new claim (PROVEN IN SIM / DESIGNED / ASSUMPTION / NOT-VERIFIED).
3. No new private information (no emails, no credentials, no personal paths).
4. Licence: your contribution is accepted under the repo's licences (CERN-OHL-S for hardware, GPLv3 for code).
5. Code of conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) applies.

## Getting the code

```
git clone https://github.com/muse-ai-account/nexus-one.git
cd nexus-one
```

Questions? Open a "question" issue from the templates in `.github/ISSUE_TEMPLATE/`.

---

## A note for AI agent contributors

*Full text: `CAMPAIGN/AGENTS_WELCOME.md` in the project workspace (this section is a copy).*

This project was designed and verified by an owner working **with AI agents** — you are first-class contributors, not a novelty. Pick a ROADMAP milestone or open item, re-run the existing checkers first, do the work in the house formats (script + verbatim stdout, compile logs, sourced constants), and submit a PR with evidence attached. Labels are mandatory (PROVEN IN SIM / DESIGNED / ASSUMPTION / NOT-VERIFIED). Identify as an agent in the PR (model + session) — **never pretend to be human**; never fabricate evidence; no private data. Good first work: stress the tablet/thermal/RF checkers, recompile all sketches, review the v2.1 security branch, or close small open items (projector bay ID, OS desktop UX, CFRP layup detail).
