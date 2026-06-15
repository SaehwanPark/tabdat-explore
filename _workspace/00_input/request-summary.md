# Request Summary: Spatial Diagnostics on OLS Residuals (`estat spatial`)

## Goal

Continue Phase 19/20 developments by implementing `estat spatial` post-estimation diagnostics for spatial autocorrelation on OLS residuals (Moran's I and Lagrange Multiplier tests) after a linear regression model.

## Phase Fit

- Phase 19 modern extension: advanced spatial autoregressive models & diagnostics.
- Builds on existing `spregress` spatial weight configuration (weights file and KNN coordinates).

## Touched Surfaces

- `src/tabdat/models.py`: add `spatial` subcommand and weights/coordinates configuration parameters to `EstatCommand`.
- `src/tabdat/parser.py`: parse `estat spatial` options.
- `src/tabdat/executor.py`: execute `estat spatial` and format the resulting diagnostics table.
- `tests/`: add focused parser, executor, and CLI tests.

## Assumptions

- Standard Moran's I and five LM tests (`lme`, `lml`, `rlme`, `rlml`, `sarma`) are sufficient.
- The spatial weight matrix construction and alignment logic from `spregress` is reused.
- The OLS model must be the prior estimated model.

## Non-Goals

- No out-of-sample prediction scope in this slice.
- No general spatial regressions in this slice (keeps focus on `estat spatial` diagnostics).
