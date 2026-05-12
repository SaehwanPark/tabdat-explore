# Phase 14 Slice 2+3 Implementation Report

## Scope

Implemented Phase 14 Slice 2 (IV diagnostics) and Slice 3 (panel FE/RE starter with Hausman)
on one bounded branch using Python-first libraries.

## What Changed

### Slice 2: IV diagnostics

- Extended `estat` parser surface with:
  - `estat firststage`
  - `estat overid`
- Added IV estimation-state tracking from `ivregress` execution.
- Added deterministic executor outputs for:
  - first-stage diagnostics
  - overidentification diagnostics (`sargan`, `wooldridge_overid`)
- Added deterministic handling for exactly identified models where overid tests are unavailable.

### Slice 3: panel FE/RE starter and Hausman

- Added parser support for:
  - `xtreg <y> <xvars>, fe|re[, robust cluster(<var>)]`
- Added executor support for FE/RE estimation through `linearmodels` panel estimators.
- Required panel metadata precondition (`panel <id_var> <time_var>`) for `xtreg`.
- Added `estat hausman` over matching FE/RE model states.
- Implemented bounded Hausman constraints for this slice:
  - supports non-cluster and robust mode pairs
  - rejects clustered covariance pairs for Hausman

### State safety

- Added explicit cross-family invalidation so stale model states cannot leak across:
  - `regress`
  - `ivregress`
  - `xtreg`

### Formatting and UX

- Added deterministic terminal formatting for `xtreg` results.
- Extended shell completions for:
  - `xtreg`
  - expanded `estat` subcommands

### Tests

- Added/updated focused parser, executor, CLI, and shell tests for all new surfaces.

### Documentation and SDD state

- Updated `SPEC.md`, `ARCHITECTURE.md`, `README.md`, and `CHANGELOG.md`.
- Updated `_workspace` handoff artifacts for this delivery.

## Files Changed

- `src/tabdat/models.py`
- `src/tabdat/parser.py`
- `src/tabdat/executor.py`
- `src/tabdat/formatter.py`
- `src/tabdat/shell.py`
- `tests/test_parser.py`
- `tests/test_executor.py`
- `tests/test_cli.py`
- `tests/test_shell.py`
- `pyproject.toml`
- `SPEC.md`
- `ARCHITECTURE.md`
- `README.md`
- `CHANGELOG.md`
- `_workspace/00_input/request-summary.md`
- `_workspace/01_product_command-contract.md`
- `_workspace/02_implementation_report.md`
- `_workspace/03_qa_report.md`
- `_workspace/final/tabdat-delivery-summary.md`

## Validation Commands

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright`
- `uv run mypy`
- `uv run pytest -q`

## Notes

- Existing tiny-sample `statsmodels` warnings in legacy regression/predict tests remain unchanged
  and non-blocking.
