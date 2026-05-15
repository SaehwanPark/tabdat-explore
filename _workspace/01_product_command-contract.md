# Phase 15 Slice 7 Command Contract

## Roadmap Phase

- Phase 15 nonlinear estimation core
  - Slice 7: bounded general nonlinear-regression command semantics (`nl`)

## `nl`

### Syntax

```stata
nl <y> = <expr>, params(<params>) start(<values>) [robust noconstant]
```

### Rules

- Requires one active dataset.
- Requires one outcome variable.
- Requires an assignment expression that can reference:
  - data variables from the active dataset
  - parameter names declared in `params(...)`
- Requires `params(<params>)` with one-or-more unique parameter names.
- Requires `start(<values>)` with numeric start values matching `params(...)` count.
- Supports covariance modes:
  - nonrobust (default)
  - robust
- `noconstant` is accepted for command-surface consistency.
- Uses bounded nonlinear least-squares fit over `scipy.optimize` with deterministic guards.
- On successful fit, returns deterministic model output with:
  - model identification (`nl`, outcome, expression)
  - covariance label
  - observation count
  - RSS
  - coefficient table (`Coef`, `Std Err`, `z`, `P>|z|`)

## Error/guard behavior

- No active dataset:
  - `nl requires an active dataset; run use <path> first`
- Invalid syntax/options:
  - parser errors consistent with existing command-family style
- Prerequisites:
  - unknown/missing variables and non-numeric variable errors consistent with existing estimators
  - empty complete-observation sample:
    - `nl requires at least one complete observation`
- Fit failures:
  - `nl failed`

## State behavior

- Running `nl` clears incompatible prior estimation-family state.
- Existing family boundaries remain:
  - `estat margins` remains tied to prior `logit`/`probit` model state.
  - existing `estat` linear/IV/panel/control-function behaviors remain unchanged.
  - `predict <newvar>[, xb residuals]` is supported after `nl`.

## Acceptance Criteria

- `nl` parses and executes with required `params(...)` and `start(...)`, and nonrobust/robust
  covariance modes.
- deterministic typed and formatted output includes expression metadata and coefficient rows.
- `predict` supports `xb` and `residuals` after `nl`.
- Focused parser/executor/CLI/shell coverage passes.
- Existing `regress`/`logit`/`probit`/`tobit`/`heckman`/`ivregress`/`cfregress`/`xtreg` behavior
  remains stable.
