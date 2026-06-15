# Delivery Summary: Spatial Autocorrelation Diagnostics (`estat spatial`)

## Result

Implemented on `feat/estat-spatial`.

## Delivered

- Added `estat spatial` post-estimation diagnostics for spatial autocorrelation on OLS residuals after a linear regression (`regress`).
- Supports option parsing and validation for coordinate-based weights (`coord(lat lon) [knn(k)]`) and file-based weights (`weights(w.gal) id(neighborhood) [contiguity(queen|rook)]`).
- Handles OLS estimation sample size verification and alignment check, raising an `ExecutionError` on mismatch.
- Computes Moran's I (`MoranRes`) and 5 LM tests (`LMtests` for simple/robust error/lag and SARMA).
- Formats outputs in a clean terminal `TableResult`.
- Updated parser, executor, help files, shell autocompletions, `SPEC.md`, `ARCHITECTURE.md`, and `CHANGELOG.md`.

## Validation

- `uv run pytest tests/test_parser.py -k spatial`
- `uv run pytest tests/test_spregress.py -k spatial`
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run basedpyright`
- `uv run pytest` (917 passed)

## Review

- QA status: `pass` (recorded in `_workspace/03_qa_report.md`).
- All boundaries (contract-to-parser, parser-to-executor, executor-to-backend, CLI) verified.

## Deferred

- Out-of-sample spatial predictive workflows.
- Joint LM tests (like LM for WX, SDM joint tests).
