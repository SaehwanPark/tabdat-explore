# Phase 14 Slice 1 Implementation Report

## Scope

Implemented the first Phase 14 endogeneity foundations slice (`ivregress 2sls`) after closing
remaining Phase 13 hardening prerequisites.

## What Changed

### Prerequisite hardening (before Phase 14)

- Fixed integrated-harness expectation drift in `s4_penguins_script_repro`:
  - `Saved:` -> `Exported:` for `export` output checks.
- Added integrated E2E scenario `s5_titanic_phase13_dogfood`:
  - runs real-dataset `regress`, `predict`, and `estat` flow.
- Updated integrated test-plan and harness docs to include Phase 13 dogfood coverage.

### Phase 14 command surface

- Added `IvRegressCommand` and `IvRegressionResult` typed models.
- Added parser support for:
  - `ivregress 2sls <y> [exog_vars], endog(<var>) iv(<vars>)`
  - covariance options: `robust` and `cluster(<var>)`
  - intercept control: `noconstant`
- Added bounded parse diagnostics for unsupported estimator tokens and malformed options.

### Executor and formatting behavior

- Added executor dispatch for `ivregress`.
- Implemented IV2SLS execution via `linearmodels` (Python-first policy).
- Added deterministic covariance labeling:
  - `nonrobust`, `robust`, `cluster(<var>)`.
- Added deterministic terminal formatting for IV output.

### Shell UX

- Added `ivregress` command completion.
- Added option completions:
  - `endog(`, `iv(`, `robust`, `cluster(`, `noconstant`.

### Tests

- Added/updated focused parser, executor, CLI, and shell tests for the new command.

### Documentation and SDD state

- Updated `SPEC.md`, `ARCHITECTURE.md`, `README.md`, and `CHANGELOG.md` for:
  - completed Phase 13 hardening
  - started Phase 14 with the `ivregress 2sls` slice.

## Files Changed

- `integrated_testing/run_e2e.py`
- `integrated_testing/README.md`
- `integrated_testing/RUN_REPORT.md`
- `docs/e2e_public_dataset_test_plan.md`
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
- `uv.lock`
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
- `uv run python integrated_testing/run_e2e.py`

## Notes

- Existing tiny-sample `statsmodels` warnings in pre-existing regression/predict tests remain
  non-blocking and unchanged in scope.
