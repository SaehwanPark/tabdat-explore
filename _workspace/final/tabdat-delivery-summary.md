# Phase 19 Slice 8 Delivery Summary

## Outcome

Completed partial-linear DML for binary treatment effects: `dml linear` plus `estat dml`.

## Implemented

- `dml linear <y> <controls>, treat(<tvar>)` with cross-fitted Lasso nuisances and OLS ATE stage
- `estat dml` diagnostics for folds, treated/control counts, nuisance treatment-fit summary, and
  overlap checks
- Updated `SPEC.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `README.md`, and in-app help

## Validation

- `uv run basedpyright`
- `uv run mypy`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pytest`

Result: `834 passed`

## Remaining Phase 19 Slices

- General Bayesian MCMC command prefix
- Bayesian diagnostics and posterior predictive workflows
- Spatial weight matrix configuration and GIS ingestion
- Advanced spatial autoregressive models and diagnostics
- Broader spatial predictive workflows

## Residual Risk

- Same-sample cross-fitted partial-linear ATE only; broader DML semantics remain deferred.
