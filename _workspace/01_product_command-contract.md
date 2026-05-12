# Phase 13 Slice 2 Command Contract

## Request Summary

Implement the next executable Phase 13 linear-econometrics slice by extending `regress` with
weighted estimator modes while preserving existing `predict` behavior.

## Roadmap Phase

- Phase 13 core linear econometrics (slice 2)

## Command Contracts

### `regress`

#### Syntax

```stata
regress <y> <xvars>
regress <y> <xvars>, robust
regress <y> <xvars>, cluster(<var>)
regress <y> <xvars>, noconstant
regress <y> <xvars>, wls(<weight_var>)
regress <y> <xvars>, gls(<sigma_var>)
```

#### Rules

- Requires an active dataset.
- `<y>` and `<xvars>` must be numeric columns.
- `wls(<weight_var>)` and `gls(<sigma_var>)` variables must be numeric columns.
- Estimator mode defaults to OLS when neither `wls(...)` nor `gls(...)` is provided.
- `wls(...)` and `gls(...)` are mutually exclusive.
- Covariance defaults to non-robust.
- `robust` applies HC1 covariance.
- `cluster(<var>)` applies clustered covariance on `<var>`.
- `robust` and `cluster(...)` remain mutually exclusive.
- Covariance options apply to OLS, WLS, and GLS estimator modes.
- Rows with missing outcome/predictor values are excluded from fitting.
- Rows with missing cluster values are excluded when clustered covariance is requested.
- Rows with missing weight/sigma values are excluded for WLS/GLS.
- Any retained WLS weight or GLS sigma value must be strictly positive.

#### User-Facing Errors

- Missing active dataset: existing `NoActiveDatasetError` shape.
- Unknown variable: `regress unknown variable: <vars>`.
- Non-numeric variable: `regress requires numeric variables: <vars>`.
- Invalid option combinations:
  - `regress cannot combine robust and cluster`
  - `regress cannot combine wls and gls`
- Invalid weighted option arity:
  - `regress option wls expects one variable`
  - `regress option gls expects one variable`
- Non-positive retained weighted inputs:
  - `regress requires positive weights values`
  - `regress requires positive sigma values`

### `predict`

#### Syntax

```stata
predict <newvar>
predict <newvar>, residuals
predict <newvar>, xb
```

#### Rules

- Requires an active dataset.
- Requires a prior successful `regress` model in session state (OLS, WLS, or GLS).
- Default prediction mode is `xb`.
- `residuals` computes `<y> - xb` using the model outcome variable.
- Adds `<newvar>` as a new column to the active dataset.
- Fails if `<newvar>` already exists.
- `xb` and `residuals` are mutually exclusive options.

## Acceptance Criteria

- Parser accepts valid weighted `regress` forms and rejects conflicting/malformed options.
- Executor and backend run OLS/WLS/GLS through Python-first `statsmodels` path.
- `predict` works after weighted and unweighted regressions.
- CLI output includes deterministic estimator metadata and covariance mode.
- CLI and shell tests cover weighted success/failure flows and option completion.
- SDD/changelog docs are synchronized with implemented scope and limits.
