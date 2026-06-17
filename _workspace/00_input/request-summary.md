# Request Summary: Spatial Autoregressive with Spatial Errors (SARAR / SAC) Support

## Goal

Extend the `spregress` command to support the SARAR/SAC model type (`model(sarar)`), which estimates spatial models with both spatial lag and spatial autoregressive errors using generalized moments (GMM).

## Phase Fit

- Phase 22: Advanced Spatial Autoregressive Models.
- Fits the priority of utilizing `pysal` (`spreg`) for spatial econometrics.

## Touched Surfaces

- `src/tabdat/models.py`: Update `SpregressCommand.model_type` to include `"sarar"`.
- `src/tabdat/parser.py`: Parse `model(sarar)` and validate option exclusivity/constraints.
- `src/tabdat/executor.py`: Call PySAL's GMM combo model estimator (`spreg.GM_Combo` or similar) and format both spatial lag and spatial error coefficients in the regression table.
- `src/tabdat/shell.py`: Update autocompletions for the `model(...)` option.
- `src/tabdat/help/topics/spregress.md`: Update help files.
- `tests/test_spregress.py`: Add syntax and integration tests.

## Assumptions

- We will estimate the GMM/IV-based combo model using `spreg.GM_Combo` from PySAL.
- Both spatial coefficients (rho for spatial lag, lambda for spatial error) will be displayed.
- Robust standard errors are supported if GMM is used (GM_Combo handles spatial heteroscedasticity if configured, or standard errors as reported by GMM combo).

## Non-Goals

- No out-of-sample prediction scope for `sarar` in this slice.
- No other spatial models (e.g., SEM/SAR with MLE, or other combo variants) in this slice.
