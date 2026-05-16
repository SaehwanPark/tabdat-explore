# Phase 16 Slice 1 Command Contract

## Roadmap Phase

- Phase 16 specialized likelihood models
  - Slice 1: bounded Poisson count-model semantics with minimal post-estimation support

## `poisson`

### Syntax

```stata
poisson <y> <xvars>[, robust cluster(<var>) noconstant]
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

- `predict <newvar>[, xb residuals]` is supported after successful `poisson`.
- `estat gof` is supported after successful `poisson`.
- Existing `predict ..., pr` remains binary-choice-only.

## Error/guard behavior

- No active dataset:
  - `poisson requires an active dataset; run use <path> first`
- Missing variables/non-numeric variables:
  - existing unknown-variable and numeric-type errors
- Empty complete-observation sample:
  - `poisson requires at least one complete observation`
- Cluster mode with missing cluster values:
  - `poisson requires complete cluster values`
- Negative outcomes:
  - `poisson outcome must be non-negative`
- Fit failures:
  - `poisson failed`
- `estat gof` without prior `poisson` model:
  - `estat gof requires a prior poisson model`

## State behavior

- Running `poisson` clears incompatible prior estimation-family state.
- Existing `estat` and `predict` boundaries for other families remain unchanged.

## Acceptance Criteria

- `poisson` parses and executes with required arguments and supported covariance modes.
- deterministic typed and formatted output includes coefficient rows and log-likelihood summary.
- `predict` supports `xb` and `residuals` after `poisson`.
- `estat gof` returns deterministic GOF rows after `poisson`.
- focused parser/executor/CLI/shell/help coverage passes.
