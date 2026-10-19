# Changelog

Built from the git history. Dates are commit dates. The project has no version numbers or releases, so entries are
grouped by date.

## 2026-10-19

- Rewrote the README as a product case study; the code layout, Python usage and engineering design notes moved to
  `docs/TECHNICAL.md`.
- Added `docs/PRD.md` (each requirement in the full PRD checked against the code), `docs/decisions.md` and this
  changelog.
- `docs/product/RISKS.md` and `docs/product/ROADMAP.md`: marked the spend cap, dashboard and run history as built.

## 2026-10-18

- Hosted demo on Vercel, Demo mode only (#4 to #8): ASGI entrypoint and config, Python preset, downloads packed into
  their links, live link in the README.
- Demo mode made honest: it replays one fictional candidate, hides uploads and saves under the sample's own name.
- `PUBLIC_DEPLOYMENT` switch: nothing stored and history off on a shared server; no database file is created.
- Renamed the "Success Rate" card to "Marked Ready".
- Reserved contact details in the fictional sample resume.
- Removed an unsourced "6–8 hours" figure; fixed a broken docs link; added a note to the presentation folder.
- Offline smoke test, run in GitHub Actions on every push.
- README rewritten for a general reader, with a demo screenshot.

## 2026-07-11

- Merged the July build (PR #3).

## 2026-07-10

- Hard spend cap that stops a Live run as soon as it is reached.
- Narrated demo video and voiceover script.
- Optional passcode for Live mode.
- Dev container (added by the owner).
- Business presentation deck (HTML and PDF).
- Streamlit dashboard with Plotly charts and SQLite history.
- Project docs, per-agent docs, portfolio materials, opt-in run logging and an eval harness scaffold.
- `pipeline.py`: runs all 18 agents end to end in dependency order.
- The 18 agents, one per commit: 15 specialists, then the Planner (with the shared agent registry), the Critic and
  the Supervisor. The Critic's review found and fixed a wrong total in the learning-plan sample.

## 2026-07-04

- Initial commit.
