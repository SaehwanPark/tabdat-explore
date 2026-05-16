# Phase 16 Slice 2 Command Contract

## Roadmap Phase

- Phase 16 specialized likelihood models
  - Slice 2: bounded negative-binomial count-model semantics with deterministic post-estimation
    support

## `nbreg`

### Syntax

```stata
nbreg <y> <xvars>[, robust cluster(<var>) noconstant]
```

### Rules

- Requires one active dataset.
- Requires one outcome variable and one-or-more predictors.
- Requires numeric outcome and predictor variables.
- Outcome must be non-negative on complete observations.
- Supports covariance modes:
  - nonrobust (default)
  - robust
  - clustered via `cluster(<var>)`
- `robust` and `cluster(...)` cannot be combined.

## Post-estimation behavior

- `predict <newvar>[, xb residuals]` is supported after successful `nbreg`.
- `estat gof` is supported after successful `nbreg`.
- Existing `predict ..., pr` remains binary-choice-only.

## Error/guard behavior

- No active dataset:
  - `nbreg requires an active dataset; run use <path> first`
- Missing variables/non-numeric variables:
  - existing unknown-variable and numeric-type errors
- Empty complete-observation sample:
  - `nbreg requires at least one complete observation`
- Cluster mode with missing cluster values:
  - `nbreg requires complete cluster values`
- Negative outcomes:
  - `nbreg outcome must be non-negative`
- Fit failures:
  - `nbreg failed`
- `estat gof` without prior `nbreg` model:
  - `estat gof requires a prior nbreg model`

## State behavior

- Running `nbreg` clears incompatible prior estimation-family state.
- Existing `estat` and `predict` boundaries for other families remain unchanged.

## Acceptance Criteria

- `nbreg` parses and executes with required arguments and supported covariance modes.
- deterministic typed and formatted output includes coefficient rows and log-likelihood summary.
- `predict` supports `xb` and `residuals` after `nbreg`.
- `estat gof` returns deterministic GOF rows after `nbreg`.
- focused parser/executor/CLI/shell/help coverage passes.
