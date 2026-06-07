# Phase 19 Slice 6 Implementation Report

## Scope

Implemented the bounded spatial predictive follow-up slice on branch
`temp/phase19-slice6-spregress-spatial-lag-predict`.

## What Changed

- Extended the shared `predict` surface to accept `spatial_lag` while preserving existing
  `xb`/`residuals`/`pr` behavior for other model families.
- Added same-sample spatial prediction state for `spregress` lag fits:
  - full reduced-form predictions stored explicitly
  - deterministic sample fingerprint checks before reuse
  - deterministic executor guard for `spregress ... model(error)`
- Preserved existing `predict ..., xb` behavior after `spregress`.
- Added failing-first parser, shell, executor, CLI, and help coverage for the new mode.
- Updated SDD docs (`SPEC.md`, `ARCHITECTURE.md`, `CHANGELOG.md`), README, and in-app help topics
  (`predict`, `spregress`).
- Left the pre-existing `uv.lock` version diff untouched.

## Milestones / Commits

- `1c78e67` — `feat(spregress): add spatial_lag predict mode`
- `bcc5383` — `docs(sdd): record spatial lag predict slice`
- Uncommitted at this report stage: review-driven regression tests and final report sync

## Validation Commands

- `uv run pytest tests/test_parser.py -q`
- `uv run pytest tests/test_shell.py -q`
- `uv run pytest tests/test_spregress.py -q`
- `uv run pytest tests/test_cli.py -q -k spregress`
- `uv run pytest tests/test_help.py -q`
- `uv run basedpyright`
- `uv run mypy`
- `uv run ruff check .`
- `uv run ruff format src/tabdat/executor.py`
- `uv run ruff format --check .`
- `uv run pytest`

## Notes

- The new `spatial_lag` mode is intentionally same-sample only in this slice.
- Out-of-sample spatial prediction and broader spatial model follow-ons remain in `SPEC.md`.
- Review follow-up added regression coverage for:
  - `predict ..., pr` still rejecting after non-binary regression
  - spatial fingerprint mismatch rejection
  - stale-state isolation across `ridge -> spregress -> predict ..., spatial_lag`
