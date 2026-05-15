# Phase 15 Slice 4-5 Implementation Report

## Scope

Implemented two bounded Phase 15 slices on branch `codex/tmp-phase15-slice4-5-binary-predict-tobit`:

- Slice 4: binary-choice prediction routing expansion for `predict`
- Slice 5: limited-dependent Tobit estimator entrypoint

## What Changed

### Parser and shell command surface

- Extended `predict` parsing to support `pr` with mutual-exclusion validation across
  `xb` / `residuals` / `pr`.
- Added `tobit <y> <xvars>, ll(<num>) [ul(<num>) robust cluster(<var>) noconstant]` parsing,
  option validation, and command completion support.
- Added shell completion entries for `tobit` command/options and `predict ... , pr`.

### Executor and backend behavior

- Added binary `predict` routing after `logit`/`probit`:
  - `predict ..., xb` returns linear predictor.
  - `predict ..., pr` returns fitted probabilities.
- Added deterministic binary predict guards:
  - `predict residuals is not available after logit or probit`
  - `predict option pr requires a prior logit or probit model`
- Added backend helper to append numeric prediction vectors as deterministic active-dataset columns.
- Added bounded Tobit execution with deterministic guard behavior:
  - requires active dataset and numeric variables
  - requires `ll(...)`
  - validates `ll < ul` when `ul(...)` is provided
  - supports `nonrobust`, `robust`, and `cluster(<var>)` covariance labels
  - rejects incomplete cluster values in clustered mode
- Implemented Tobit through R fallback adapter boundary (`survival::survreg` via `rpy2`) to follow
  Phase 15 policy when direct Python support is insufficient.

### State behavior

- Preserved existing family isolation behavior.
- `logit`/`probit` binary-model state now powers both `estat margins` and binary `predict` routes.
- `tobit` clears incompatible prior estimation-family state after successful fit.

### Tests

- Added focused parser tests for `predict ..., pr` and `tobit` valid/invalid forms.
- Added focused shell completion tests for `tobit` and `predict` options.
- Added focused executor tests for:
  - binary `predict` (`xb` + `pr`) and guards
  - Tobit result path, covariance modes, and prerequisite/guard errors
- Added focused CLI tests for:
  - binary `predict` flow after `logit`
  - Tobit nonrobust/robust/clustered flows

### Dependencies

- Added `rpy2` to `pyproject.toml` and refreshed `uv.lock`.

## Validation

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright`
- `uv run mypy`
- `uv run pytest -q`
- `uv run python integrated_testing/run_e2e.py`

All commands passed.
