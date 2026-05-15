# Phase 15 Slice 6 Implementation Report

## Scope

Implemented one bounded Phase 15 slice on branch
`codex/tmp-phase15-slice6-heckman-sample-selection`:

- Slice 6: sample-selection Heckman estimator entrypoint

## What Changed

### Parser and shell command surface

- Added `heckman <y> <xvars>, selectdep(<var>) select(<vars>) [robust cluster(<var>) noconstant]`
  parsing, deterministic option validation, and command completion support.

### Executor and backend behavior

- Added bounded Heckman execution with deterministic guard behavior:
  - requires active dataset and numeric variables
  - requires one `selectdep(...)` variable and one-or-more `select(...)` variables
  - supports `nonrobust`, `robust`, and `cluster(<var>)` covariance labels
  - rejects incomplete cluster values in clustered mode
  - rejects non-binary selection-dependent variables
- Added deterministic typed result + formatting output for:
  - outcome equation coefficients
  - selection equation coefficients
- Added deterministic backend failure mapping:
  - `heckman failed`

### State behavior

- Preserved existing family isolation behavior.
- `heckman` clears incompatible prior estimation-family state after successful fit.

### Tests

- Added focused parser tests for `heckman` valid/invalid forms.
- Added focused shell completion tests for `heckman` options.
- Added focused executor tests for:
  - Heckman result path, covariance modes, and prerequisite/guard errors
- Added focused CLI tests for:
  - Heckman nonrobust/robust/clustered flows

## Validation

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright`
- `uv run mypy`
- `uv run pytest -q`
- `uv run python integrated_testing/run_e2e.py`

All commands passed.
