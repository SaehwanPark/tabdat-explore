# Request Summary: Spatial Out-of-Sample Prediction Workflows

## Goal

Extend the `predict ..., spatial_lag` command after spatial regressions (`spregress`) to support out-of-sample datasets, allowing users to predict spatial lag values on active datasets that differ from the estimation sample.

## Phase Fit

- Phase 22: Advanced Spatial Autoregressive Models (Predictive Workflows extension).
- Fits the priority of utilizing `pysal` (`spreg`) for spatial econometrics.

## Touched Surfaces

- `src/tabdat/executor.py`: Modify `_execute_predict` to remove the strict same-sample fingerprint check for `spatial_lag` prediction, and implement out-of-sample weights reconstruction and solver equations.
- `tests/test_spregress.py`: Update tests to assert that out-of-sample predict works, and add validation tests for coordinate/weights variable mismatches.

## Assumptions

- Out-of-sample prediction for spatial lag models solves:
  $$\hat{y}_{\text{new}} = (I - \hat{\rho} W_{\text{new}})^{-1} (X_{\text{new}} \hat{\beta})$$
- We build $W_{\text{new}}$ dynamically from the target dataset (using either coords or loading and subsetting the weights file).
- The same-sample prediction check remains active and optimized to reuse precomputed values.

## Non-Goals

- No out-of-sample spatial error residuals prediction.
