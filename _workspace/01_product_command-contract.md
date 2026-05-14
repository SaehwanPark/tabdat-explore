# Phase 15 Slice 2-3 Command Contract

## Roadmap Phase

- Phase 15 nonlinear estimation core
  - Slice 2: bounded binary-choice `probit` estimator foundation
  - Slice 3: bounded binary-choice `estat margins` diagnostics

## `probit`

### Syntax

```stata
probit <y> <xvars>[, robust cluster(<var>) noconstant]
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
  - model identification (`probit`, outcome, predictors)
  - covariance label
  - observation count
  - pseudo R-squared
  - coefficient table (`Coef`, `Std Err`, `z`, `P>|z|`)

## `estat margins`

### Syntax

```stata
estat margins
```

### Rules

- Requires one active dataset.
- Requires successful prior binary-choice model state from `logit` or `probit`.
- Returns deterministic predictor-level rows with columns:
  - `Variable`, `Metric`, `Value`
- Supported metrics per predictor:
  - `dy_dx`, `std_error`, `statistic`, `p_value`, `ci_lower`, `ci_upper`

## Error/guard behavior

- No active dataset:
  - `probit requires an active dataset; run use <path> first`
  - `estat requires an active dataset; run use <path> first`
- Invalid syntax/options:
  - parser errors consistent with existing command-family style
- Non-binary outcome on complete-case sample:
  - `probit outcome must be binary with values 0 and 1`
- No complete-case observations:
  - `probit requires at least one complete observation`
- Cluster option with incomplete cluster values on retained sample:
  - `probit requires complete cluster values`
- Backend fit failures:
  - `probit failed`
- Missing binary-model prerequisite for margins:
  - `estat margins requires a prior logit or probit model`
- Marginal effects extraction failures:
  - `estat margins failed for current model`

## State behavior

- Running `probit` clears incompatible prior estimation family state to prevent stale post-estimation
  use from other model families.
- Running `logit` or `probit` registers binary-model state for `estat margins`.
- This slice pair does not add new nonlinear `predict` behavior.

## Acceptance Criteria

- `probit` parses and executes with nonrobust, robust, and clustered covariance modes.
- `estat margins` parses and executes after `logit` and `probit` with deterministic output.
- Focused parser/executor/CLI/shell coverage passes.
- Existing `regress`/`ivregress`/`cfregress`/`xtreg`/`predict`/other `estat` behavior remains stable.
