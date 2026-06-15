# Command Contract: Spatial Autocorrelation Diagnostics (`estat spatial`)

## Request Summary

Add `estat spatial` post-estimation diagnostics for spatial autocorrelation on OLS residuals (Moran's I and Lagrange Multiplier tests) after a successful `regress` command.

## Roadmap Phase

Phase 19 modern extensions: advanced spatial autoregressive models & diagnostics.

## Command Syntax

```text
estat spatial, weights(<path>) id(<id_var>) [contiguity(queen|rook)]
estat spatial, coord(<lat_var> <lon_var>) [knn(<k>)]
```

## Examples

- `regress wage educ exper` then `estat spatial, coord(lat lon) knn(5)`
  - Computes spatial diagnostics using on-the-fly KNN weights.
- `regress wage educ exper` then `estat spatial, weights(columbus.gal) id(neighborhood)`
  - Computes spatial diagnostics using pre-computed spatial weights.

## Data Assumptions

- Requires an active dataset and a prior `regress` OLS model state.
- Raises `ExecutionError` if `self.state.regression` is None.
- Reuses weights construction logic from `spregress` (case-insensitive column names, shapefile kontiguity, gal/gwt matrix alignment).
- Excludes observations with missing values in regression variables or coordinate/id variables.
- Ensures the number of complete observations matches the OLS model's `nobs`.

## Execution Semantics

- Reconstructs OLS model using PySAL `spreg.BaseOLS(y, x)` on the complete estimation sample aligned with weights matrix `w`.
- Computes Moran's I on residuals using `spreg.MoranRes(ols, w, z=True)`.
- Computes Lagrange Multiplier (LM) tests using `spreg.LMtests(ols, w, tests=['lme', 'lml', 'rlme', 'rlml', 'sarma'])`.
- Formats outputs in a clean terminal table.

## Acceptance Criteria

- Moran's I results table shows `Moran's I (residual)`, `Expectation`, `Variance`, `z-statistic`, and `p-value`.
- LM tests table shows statistic value and p-value for:
  - Spatial error (LM error)
  - Spatial lag (LM lag)
  - Robust spatial error (Robust LM error)
  - Robust spatial lag (Robust LM lag)
  - Spatial SARMA (LM SARMA)
- Parser rejects options (like `weights`, `coord`, `knn`) on all other `estat` subcommands.
- Formatter prints clear headers and aligned columns.

## Open Questions

- None for this slice.
