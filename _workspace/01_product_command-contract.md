# Phase 15 Slice 4-5 Command Contract

## Roadmap Phase

- Phase 15 nonlinear estimation core
  - Slice 4: bounded nonlinear binary-choice prediction routing
  - Slice 5: bounded limited-dependent Tobit entrypoint

## `predict` extension for binary-choice models

### Syntax

```stata
predict <newvar>[, xb residuals pr]
```

### Rules

- Requires one active dataset.
- Existing behavior remains unchanged:
  - after `regress`/`cfregress`, `xb` and `residuals` continue to work as before.
- New binary-choice behavior:
  - after successful `logit` or `probit`, supports:
    - `xb` for linear predictor
    - `pr` for fitted probabilities
- For this slice, binary `predict` does not support `residuals`.
- Options `xb`, `residuals`, and `pr` are pairwise mutually exclusive.

## `tobit`

### Syntax

```stata
tobit <y> <xvars>, ll(<num>) [ul(<num>) robust cluster(<var>) noconstant]
```

### Rules

- Requires one active dataset.
- Requires one outcome variable and one-or-more predictor variables.
- Requires numeric outcome and predictor columns.
- `ll(<num>)` is required.
- `ul(<num>)` is optional.
- If `ul(<num>)` is present, `ll < ul` is required.
- Supports covariance modes:
  - nonrobust (default)
  - robust
  - cluster(`<var>`)
- `robust` and `cluster(<var>)` are mutually exclusive.
- `noconstant` disables intercept inclusion.
- Uses Python-first strategy; if direct Python support is insufficient, uses bounded R fallback via
  `rpy2` adapter.
- On successful fit, returns deterministic model output with:
  - model identification (`tobit`, outcome, predictors)
  - censoring limits summary (`ll`, `ul`/none)
  - covariance label
  - observation count
  - coefficient table (`Coef`, `Std Err`, `z`, `P>|z|`)

## Error/guard behavior

- No active dataset:
  - `predict requires an active dataset; run use <path> first`
  - `tobit requires an active dataset; run use <path> first`
- Invalid syntax/options:
  - parser errors consistent with existing command-family style
- Invalid `predict` option combos:
  - parse error for combined `xb`/`residuals`/`pr`
- Missing compatible model for `predict`:
  - unchanged existing linear/control-function error when applicable
  - `predict option pr requires a prior logit or probit model`
  - `predict residuals is not available after logit or probit`
- Tobit prerequisites:
  - unknown/missing variables and non-numeric variable errors consistent with existing estimators
  - `tobit requires at least one complete observation`
  - `tobit lower limit must be less than upper limit`
  - clustered mode with incomplete cluster values:
    - `tobit requires complete cluster values`
- Backend/adapter fit failures:
  - `tobit failed`

## State behavior

- Running `tobit` clears incompatible prior estimation-family state.
- Existing family boundaries remain:
  - `estat margins` remains tied to prior `logit`/`probit` model state.
  - existing `estat` linear/IV/panel/control-function behaviors remain unchanged.

## Acceptance Criteria

- `predict ..., pr` parses and executes after `logit` and `probit` with deterministic output.
- `predict` linear/control-function behavior remains stable.
- `tobit` parses and executes with `ll(...)`, optional `ul(...)`, and covariance modes.
- Focused parser/executor/CLI/shell coverage passes.
- Existing `regress`/`ivregress`/`cfregress`/`xtreg`/other `predict`/`estat` behavior remains stable.
