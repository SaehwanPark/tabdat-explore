# Phase 14 Slice 8 Implementation Report

## Scope

Implemented Phase 14 Slice 8 (expanded `estat endogenous` diagnostics after `cfregress`) on one
bounded branch using the existing `estat` command surface and Python-first execution.

## What Changed

### Executor/model-state behavior

- Extended control-function session state to persist deterministic residual-inclusion coefficient
  value and standard error for `cf_residual`.
- Expanded `estat endogenous` table output rows to include:
  - `estimate`
  - `std_error`
  while preserving existing `test`, `statistic`, and `p_value` rows.
- Preserved existing missing-prior-model error:
  - `estat endogenous requires a prior cfregress model`
- Preserved bounded failure guard when residual-inclusion diagnostics are unavailable:
  - `estat endogenous failed for current model`

### Parser/shell command surface

- No parser or shell command-surface changes.
- `estat endogenous` syntax/options remain unchanged.

### Tests

- Expanded focused executor coverage for `estat endogenous` row shape and value/SE consistency with
  residual-inclusion coefficient slots.
- Expanded CLI Phase 14 flow coverage to assert `estimate` and `std_error` output rows.

### Documentation and SDD state

- Updated `SPEC.md`, `ARCHITECTURE.md`, `README.md`, and `CHANGELOG.md`.
- Updated `_workspace` handoff artifacts for this delivery.

## Files Changed

- `src/tabdat/executor.py`
- `tests/test_executor.py`
- `tests/test_cli.py`
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

- `uv run pytest -q tests/test_executor.py -k "estat_endogenous"`
- `uv run pytest -q tests/test_cli.py -k "phase_14_cfregress_flow"`
- `uv run pytest -q tests/test_executor.py -k "cfregress or estat"`
- `uv run pytest -q tests/test_cli.py -k "cfregress_flow or estat"`
- `uv run pytest -q tests/test_parser.py -k "estat"`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright`
- `uv run mypy`
- `uv run pytest -q`
- `uv run python integrated_testing/run_e2e.py`
