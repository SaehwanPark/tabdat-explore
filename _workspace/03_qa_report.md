# Spatial Combo Regression (`model(sarar)`) QA Report

## Status

pass

## Boundaries Checked

- **Contract to parser**: Validated that `model(sarar)` parses correctly and rejects invalid model types.
- **Parser representation to executor**: Verified that `model_type` is correctly forwarded to the GMM estimators.
- **Executor to backend**: Verified GMM estimations with PySAL `GM_Combo` and `GM_Combo_Het` and standard error extraction.
- **Backend result to formatter & CLI**: Verified that the formatter prints both spatial coefficients (`rho` and `lambda`), representing missing standard errors safely as `.`.

## Blocking Issues

- None.

## PR Review Loop

- PR: (Local repository feature branch `feat/spregress-sarar`)
- Pass 1 verified parser syntax and model literal extensions.
- Pass 2 verified PySAL combo model estimators convergence and robust vs non-robust standard error extraction.
- Pass 3 verified formatter handling of optional standard error values.

## Validation Evidence

- Target tests passed: `uv run pytest tests/test_spregress.py` (25 passed)
- Full suite passed: `uv run pytest` (928 passed)
- Static validation: `uv run basedpyright` (0 errors)
- Lint validation: `uv run ruff check` (passed)
