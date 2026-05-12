# Phase 14 Slice 1 Delivery Summary

## Outcome

Completed a bounded Phase 14 start on branch `codex/tmp-phase14-iv2sls-slice1` after closing
remaining Phase 13 hardening prerequisites.

## Implemented

- Prerequisite closure before Phase 14:
  - fixed integrated-E2E script export wording checks (`Exported:`)
  - added `s5_titanic_phase13_dogfood` to enforce real-dataset `regress`/`predict`/`estat`
    dogfooding
- Phase 14 slice 1 command:
  - `ivregress 2sls <y> [exog_vars], endog(<var>) iv(<vars>)[, robust cluster(<var>) noconstant]`
  - Python-first IV2SLS execution via `linearmodels`
  - deterministic formatter output and covariance labeling
- Added focused parser/executor/CLI/shell coverage for the new command.
- Updated SDD and user-facing docs:
  - `SPEC.md`
  - `ARCHITECTURE.md`
  - `README.md`
  - `CHANGELOG.md`

## Validation

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright`
- `uv run mypy`
- `uv run pytest -q`
- `uv run python integrated_testing/run_e2e.py`

All commands passed.

## Residual Risk

- Existing tiny-sample `statsmodels` warnings in legacy regression/predict tests remain unchanged
  and non-blocking.

## Suggested Follow-up

- Add weak-instrument and overidentification diagnostics as the next bounded Phase 14 slice.
