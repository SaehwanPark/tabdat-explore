# Delivery Summary: Spatial Autoregressive with Spatial Errors (`spregress ..., model(sarar)`)

## Result

Implemented on branch `feat/spregress-sarar`.

## Delivered

- Added `model(sarar)` GMM estimation support to the `spregress` command.
- Integrated PySAL's `GM_Combo` (non-robust combo) and `GM_Combo_Het` (heteroscedastic robust combo) estimators.
- Extracted and displayed both spatial parameters (`rho` for spatial lag, `lambda` for spatial error) in the regression output table.
- Handled GMM standard error omission by safely formatting unavailable statistics as `.`.
- Updated syntax validation, help topics, parser, executor, formatter, and tests.

## Validation

- `uv run pytest tests/test_spregress.py` (25 passed)
- `uv run basedpyright` (0 errors)
- `uv run ruff check` (passed)
- `uv run pytest` (928 passed)

## Review

- QA status: `pass` (recorded in `_workspace/03_qa_report.md`).

## Deferred

- Out-of-sample combo model predictions.
