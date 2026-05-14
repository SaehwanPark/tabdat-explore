# Phase 15 Slice 1 Command Contract

## Roadmap Phase

- Phase 15 nonlinear estimation core
  - Slice 1: bounded binary-choice `logit` estimator foundation

## `logit`

### Syntax

```stata
logit <y> <xvars>[, robust cluster(<var>) noconstant]
```

### Rules

- Requires one active dataset.
- Requires one outcome variable and one-or-more predictor variables.
- Requires numeric outcome and predictor columns.
- Outcome must be binary on complete-case rows (`0/1`).
- Supports covariance modes:
  - nonrobust (default)
  - robust
  - cluster(`<var>`)
- `robust` and `cluster(<var>)` are mutually exclusive.
- `noconstant` disables intercept inclusion.
- On successful fit, returns deterministic model output with:
  - model identification (`logit`, outcome, predictors)
  - covariance label
  - observation count
  - pseudo R-squared
  - coefficient table (`Coef`, `Std Err`, `z`, `P>|z|`)

## Error/guard behavior

- No active dataset:
  - `logit requires an active dataset; run use <path> first`
- Invalid syntax/options:
  - parser errors consistent with existing command-family style
- Non-binary outcome on complete-case sample:
  - `logit outcome must be binary with values 0 and 1`
- No complete-case observations:
  - `logit requires at least one complete observation`
- Cluster option with incomplete cluster values on retained sample:
  - `logit requires complete cluster values`
- Backend fit failures:
  - `logit failed`

## State behavior

- Running `logit` clears incompatible prior estimation family state to prevent stale post-estimation
  use from other model families.
- This slice does not add new `predict` or `estat` behaviors for `logit`.

## Acceptance Criteria

- `logit` parses and executes with nonrobust, robust, and clustered covariance modes.
- Deterministic CLI formatting is available for `logit` results.
- Focused parser/executor/CLI/shell coverage passes.
- Existing `regress`/`ivregress`/`cfregress`/`xtreg`/`predict`/`estat` behavior remains stable.
