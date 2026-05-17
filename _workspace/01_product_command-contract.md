# Phase 17 Slice 1 Command Contract

## Roadmap Phase

- Phase 17 advanced empirical methods
  - Slice 1: bounded quantile-regression semantics (`qreg`) with deterministic post-estimation
    support

## `qreg`

### Syntax

```stata
qreg <y> <xvars>[, quantile(<0,1>) robust noconstant]
```

### Rules

- Requires one active dataset.
- Requires one outcome variable and one-or-more predictor variables.
- Requires numeric outcome and predictors.
- Supports covariance modes:
  - nonrobust (default)
  - robust
- `quantile(...)` must be strictly between 0 and 1.
- `noconstant` removes the intercept term.

## Post-estimation behavior

- `predict <newvar>[, xb residuals]` is supported after successful `qreg`.
- `predict ..., pr` remains binary-choice-only.
- `estat residuals` is supported after successful `qreg`.
- `estat ovtest` and `estat vif` remain regress-only diagnostics.

## Error/guard behavior

- No active dataset:
  - `qreg requires an active dataset; run use <path> first`
- Missing variables/non-numeric variables:
  - existing unknown-variable and numeric-type errors
- Empty complete-observation sample:
  - `qreg requires at least one complete observation`
- Quantile range violations:
  - `qreg option quantile must be between 0 and 1`
- Fit failures:
  - `qreg failed`
- `estat residuals` without prior regress/qreg:
  - `estat residuals requires a prior regress or qreg model`

## State behavior

- Running `qreg` clears incompatible prior estimation-family state.
- Existing `predict` and `estat` boundaries for other families remain unchanged.

## Acceptance Criteria

- `qreg` parses and executes with supported options and strict quantile validation.
- deterministic typed and formatted output includes quantile metadata and coefficient rows.
- `predict` supports `xb` and `residuals` after `qreg`.
- `estat residuals` returns deterministic residual summary rows after `qreg`.
- focused parser/executor/CLI/shell/help coverage passes.
