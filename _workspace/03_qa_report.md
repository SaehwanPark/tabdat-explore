# Phase 15 Slice 6 QA Report

## Status

pass

## Boundaries Checked

- Contract -> parser/shell:
  - `heckman` syntax/options and completion behavior match contract.
- Contract -> executor/backend:
  - `heckman` executes with required `selectdep(...)` and `select(...)`, covariance modes, and
    deterministic guard behavior.
- Contract -> formatter/CLI:
  - Heckman output formatting is deterministic and includes model/covariance and
    outcome/selection-equation coefficient tables.
  - CLI Heckman flows execute successfully.
- Regression boundaries:
  - existing `regress`/`logit`/`probit`/`tobit`/`ivregress`/`cfregress`/`xtreg` behavior remains
    stable.

## Blocking Issues

- None found in validation.

## Validation Evidence

- Full quality gates passed:
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run pyright`
  - `uv run mypy`
  - `uv run pytest -q`
- Integrated E2E scenarios (`s1` through `s5`) passed:
  - `uv run python integrated_testing/run_e2e.py`

## Recommended Next Action

Push `codex/tmp-phase15-slice6-heckman-sample-selection`, open one PR to `main`, and mark it ready
for review.
