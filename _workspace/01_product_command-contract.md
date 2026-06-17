# Command Contract: Spatial Autoregressive with Spatial Errors (`spregress ..., model(sarar)`)

## Request Summary

Add `model(sarar)` support to the `spregress` spatial regression command. SARAR (also known as SAC or GMM Combo) estimates models with spatial lag and spatial autoregressive error structures.

## Roadmap Phase

Phase 22: Advanced Spatial Autoregressive Models.

## Command Syntax

```text
spregress <y> <xvars>, coord(<lat_var> <lon_var>) [knn(<k>)] model(sarar) [robust]
spregress <y> <xvars>, weights(<path>) id(<id_var>) model(sarar) [robust]
```

## Examples

- `spregress wage educ exper, coord(lat lon) model(sarar)`
- `spregress wage educ exper, weights(columbus.gal) id(neighborhood) model(sarar) robust`

## Data Assumptions

- Requires an active dataset and valid spatial configuration (either `coord` or `weights`).
- Excludes observations with missing values in regression or coordinate/id variables.
- Raises `ExecutionError` if estimation sample cannot be constructed or aligned.

## Execution Semantics

- Reconstructs sample and weights matrix `w` using existing alignment logic.
- Executes `spreg.GM_Combo(y, x, w=w, robust='white')` if `robust` option is passed, otherwise `spreg.GM_Combo(y, x, w=w)`.
- Extract coefficients:
  - Intercept and predictors.
  - Spatial lag coefficient ($\rho$ or `rho_` / `lambda_` in PySAL).
  - Spatial error coefficient ($\lambda$ or `rho_` / `lambda_` in PySAL).
- Format the output into a clean terminal table showing both spatial coefficients and their standard errors, stats, and p-values.

## Acceptance Criteria

- `spregress` parses `model(sarar)` correctly.
- Rejects invalid models via `ParseError`.
- Table shows spatial coefficients cleanly labeled (e.g., `W_wage` for spatial lag, and `lambda` or similar for spatial error).
- Standard errors, z-stats, and p-values are correctly populated.
- Autocomplete and help pages are updated.
- Existing tests for `model(lag)` and `model(error)` continue to pass.
