# Phase 14 Slice 5 Implementation Report

## Scope

Implemented Phase 14 Slice 5 (`cfregress` control-function core) on one bounded branch using
Python-first execution and existing estimation boundaries.

## What Changed

### Parser/model/shell surface

- Added typed `CfRegressCommand` and `CfRegressionResult`.
- Added parser support for:
  - `cfregress <y> [exog_vars], endog(<var>) iv(<vars>)`
  - optional `robust`, `cluster(<var>)`, and `noconstant`
- Added shell completions for `cfregress` and its options.

### Executor/formatter behavior

- Added `cfregress` executor dispatch with deterministic guards:
  - active dataset required
  - numeric variable requirements
  - option and command-shape constraints from command contract
- Added bounded two-step residual-inclusion execution:
  - first stage: endogenous on exogenous + instruments
  - second stage: outcome on exogenous + endogenous + first-stage residual
- Added covariance handling for nonrobust, robust, and clustered modes.
- Added deterministic terminal formatting for `cfregress` results.
- Added cross-family estimation-state invalidation so stale model-state reuse is blocked.

### Tests

- Added/updated focused parser, executor, CLI, and shell tests for the new surface and guardrails.

### Documentation and SDD state

- Updated `SPEC.md`, `ARCHITECTURE.md`, `README.md`, and `CHANGELOG.md`.
- Updated `_workspace` handoff artifacts for this delivery.

## Files Changed

- `src/tabdat/models.py`
- `src/tabdat/parser.py`
- `src/tabdat/shell.py`
- `src/tabdat/executor.py`
- `src/tabdat/formatter.py`
- `tests/test_parser.py`
- `tests/test_executor.py`
- `tests/test_cli.py`
- `tests/test_shell.py`
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
