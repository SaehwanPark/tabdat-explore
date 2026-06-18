# Command Contract: Spatial Out-of-Sample Prediction Workflows

## Request Summary

Extend the `predict ..., spatial_lag` command to support out-of-sample datasets after spatial regressions (`spregress`).

## Roadmap Phase

Phase 22: Advanced Spatial Autoregressive Models (Predictive Workflows extension).

## Command Syntax

No change to syntax. The existing syntax `predict <newvar>, spatial_lag` is used.

## Examples

- `spregress wage educ exper, coord(lat lon) model(lag)`
- `use validation_data.parquet`
- `predict wage_lag_pred, spatial_lag`

## Data Assumptions

- The active dataset must contain all predictors from the regression model.
- The active dataset must contain the coordinates (`coord_variables` / `knn` matrix) or ID variable (`weights_file` matrix) used in the regression.
- Raises `ExecutionError` if variables are missing or if the weight matrix cannot be aligned/constructed.

## Execution Semantics

- If the active sample fingerprint matches the estimation sample, reuse `spatial_regression.full_predictions`.
- Otherwise:
  - Dynamically construct a new spatial weights matrix $W_{\text{new}}$ for the target sample.
  - Form the linear predictor $X_{\text{new}}\hat{\beta}$.
  - Calculate $(I - \hat{\rho} W_{\text{new}})^{-1} X_{\text{new}}\hat{\beta}$ using linear solvers.
  - Add the prediction column to the active dataset.

## Acceptance Criteria

- Out-of-sample `predict ..., spatial_lag` runs successfully.
- Rejects missing coordinates or predictor columns with `ExecutionError`.
- Same-sample predictions remain fast and correct.
- Existing tests continue to pass.
