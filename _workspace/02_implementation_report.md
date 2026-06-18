# Implementation Report: Spatial Out-of-Sample Prediction Workflows

## Contract Consumed

- `_workspace/01_product_command-contract.md` (Design for spatial out-of-sample prediction workflows).

## Files Changed

- [src/tabdat/executor.py](file:///home/saehwan/repos/tabdat-explore-dev/src/tabdat/executor.py):
  - Updated `_execute_predict` for `spatial_lag` prediction.
  - Implemented same-sample check using fingerprinting (preserving value reuse).
  - Implemented out-of-sample prediction by dynamically building/subsetting new row-standardized weights matrix ($W_{\text{new}}$) and using `np.linalg.solve` to solve $(I - \hat{\rho} W_{\text{new}})\hat{y} = X_{\text{new}}\hat{\beta}$.
- [tests/test_spregress.py](file:///home/saehwan/repos/tabdat-explore-dev/tests/test_spregress.py):
  - Updated `test_execute_spregress_predict_supports_mismatched_sample` to assert success.
  - Added `test_execute_spregress_predict_mismatched_variables` to check variable missingness.
  - Added `test_execute_spregress_predict_sarar_out_of_sample` to verify out-of-sample prediction for combo models.

## Validation Commands and Outcomes

1. **Basedpyright Type Safety**:
   - Command: `uv run basedpyright`
   - Outcome: `0 errors, 0 warnings, 0 notes`
2. **Pytest Target Integration Tests**:
   - Command: `uv run pytest tests/test_spregress.py`
   - Outcome: `27 passed`
3. **Full Test Suite Validation**:
   - Command: `uv run pytest`
   - Outcome: `930 passed`
