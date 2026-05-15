# Phase 15 Slice 6 Command Contract

## Roadmap Phase

- Phase 15 nonlinear estimation core
  - Slice 6: bounded sample-selection estimator entrypoint (`heckman`)

## `heckman`

### Syntax

```stata
heckman <y> <xvars>, selectdep(<var>) select(<vars>) [robust cluster(<var>) noconstant]
```

### Rules

- Requires one active dataset.
- Requires one outcome variable and one-or-more predictor variables.
- Requires `selectdep(<var>)` with exactly one variable.
- Requires `select(<vars>)` with one-or-more variables.
- Requires numeric outcome, outcome predictors, selection dependent variable, and selection
  predictors.
- Supports covariance modes:
  - nonrobust (default)
  - robust
  - cluster(`<var>`)
- `robust` and `cluster(<var>)` are mutually exclusive.
- `noconstant` disables intercept inclusion.
- Uses bounded R adapter (`sampleSelection`) via `rpy2`.
- On successful fit, returns deterministic model output with:
  - model identification (`heckman`, outcome, predictors, selection spec)
  - covariance label
  - observation count
  - coefficient tables for:
    - outcome equation
    - selection equation
  - each table columns: `Coef`, `Std Err`, `z`, `P>|z|`

## Error/guard behavior

- No active dataset:
  - `heckman requires an active dataset; run use <path> first`
- Invalid syntax/options:
  - parser errors consistent with existing command-family style
- Sample-selection prerequisites:
  - unknown/missing variables and non-numeric variable errors consistent with existing estimators
  - empty complete-observation sample:
    - `heckman requires at least one complete observation`
  - clustered mode with incomplete cluster values:
    - `heckman requires complete cluster values`
- Backend/adapter fit failures:
  - `heckman failed`

## State behavior

- Running `heckman` clears incompatible prior estimation-family state.
- Existing family boundaries remain:
  - `estat margins` remains tied to prior `logit`/`probit` model state.
  - existing `estat` linear/IV/panel/control-function behaviors remain unchanged.

## Acceptance Criteria

- `heckman` parses and executes with required `selectdep(...)`, required `select(...)`, and covariance
  modes.
- deterministic typed and formatted output includes outcome and selection equations.
- Focused parser/executor/CLI/shell coverage passes.
- Existing `regress`/`logit`/`probit`/`tobit`/`ivregress`/`cfregress`/`xtreg` behavior remains stable.
