# Phase 13 Slice 1 Command Contract

## Request Summary

Implement the first executable Phase 13 linear-econometrics command slice with strict bounded scope.

## Roadmap Phase

- Phase 13 core linear econometrics (slice 1)

## Command Contracts

### `regress`

#### Syntax

```stata
regress <y> <xvars>
regress <y> <xvars>, robust
regress <y> <xvars>, cluster(<var>)
regress <y> <xvars>, noconstant
```

#### Rules

- Requires an active dataset.
- `<y>` and `<xvars>` must all be numeric columns.
- Uses Python-first `statsmodels` OLS fitting.
- Default covariance mode is non-robust.
- `robust` applies HC1 covariance.
- `cluster(<var>)` applies clustered covariance on `<var>`.
- `robust` and `cluster(...)` are mutually exclusive.
- `noconstant` removes the intercept term.
- Rows with missing outcome/predictor values are excluded from fitting.

#### User-Facing Errors

- Missing active dataset: existing `NoActiveDatasetError` shape.
- Unknown variable: `regress unknown variable: <vars>`.
- Non-numeric variable: `regress requires numeric variables: <vars>`.
- Invalid option combinations:
  - `regress cannot combine robust and cluster`
  - `regress option cluster expects one variable`

### `predict`

#### Syntax

```stata
predict <newvar>
predict <newvar>, residuals
predict <newvar>, xb
```

#### Rules

- Requires an active dataset.
- Requires a prior successful `regress` model in session state.
- Default prediction mode is `xb`.
- `residuals` computes `<y> - xb` using the model outcome variable.
- Adds `<newvar>` as a new column to the active dataset.
- Fails if `<newvar>` already exists.
- `xb` and `residuals` are mutually exclusive options.

#### User-Facing Errors

- Missing prior model: `predict requires a prior regress model`.
- Existing target column: `predict target already exists: <newvar>`.
- Invalid option combinations:
  - `predict options xb and residuals cannot be combined`

## Acceptance Criteria

- Parser supports valid `regress`/`predict` forms and rejects invalid option syntax.
- Executor and backend run `regress` and produce deterministic regression output metadata.
- `predict` mutates active dataset with either fitted values or residuals.
- CLI and shell tests cover the new command flows.
- SDD and changelog docs are synchronized with implemented scope and limits.
