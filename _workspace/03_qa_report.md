# Phase 15 Slice 2-3 QA Report

## Status

pass

## Boundaries Checked

- Contract -> parser/shell:
  - `probit` syntax and option validations match the command contract.
  - `estat margins` subcommand routing and completion behavior match the command contract.
- Contract -> executor/model routing:
  - `probit` executes with nonrobust, robust, and clustered covariance modes.
  - `estat margins` executes after `logit` and `probit`, and rejects missing prerequisites.
- Contract -> formatter/CLI:
  - `probit` output includes deterministic pseudo R-squared and coefficient rows.
  - `estat margins` output includes deterministic `Variable/Metric/Value` rows.
- Guard behavior:
  - missing active dataset, missing variables, non-binary outcomes, and missing cluster values
    return deterministic errors for `probit`.
  - missing binary-model state returns deterministic prerequisite error for `estat margins`.
- Estimation-family isolation:
  - existing `predict` and non-margins `estat` boundaries remain intact.
- SDD/docs -> implementation:
  - `SPEC.md`, `ARCHITECTURE.md`, `README.md`, and `CHANGELOG.md` align with delivered scope.

## Blocking Issues

- None found in validation.

## Validation Evidence

- Focused tests for parser/shell/executor/CLI `probit` + `estat margins` surfaces passed.
- Full quality gates passed:
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run pyright`
  - `uv run mypy`
  - `uv run pytest -q`
- Integrated E2E scenarios (`s1` through `s5`) passed:
  - `uv run python integrated_testing/run_e2e.py`

## Recommended Next Action

Push `codex/tmp-phase15-slice2-3-probit-estat-margins`, open one PR to `main`, and mark it ready
for review.
