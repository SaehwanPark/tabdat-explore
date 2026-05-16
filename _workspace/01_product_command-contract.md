# Phase 16 Slice 3 Command Contract

## Roadmap Phase

- Phase 16 specialized likelihood models
  - Slice 3: bounded zero-inflated count-model semantics with deterministic post-estimation support

## `zip`

### Syntax

```stata
zip <y> <xvars>, inflate(<zvars>) [robust cluster(<var>) noconstant]
```

## `zinb`

### Syntax

```stata
zinb <y> <xvars>, inflate(<zvars>) [robust cluster(<var>) noconstant]
```

### Rules

- Requires one active dataset.
- Requires one outcome variable, one-or-more count predictors, and one-or-more inflation predictors.
- Requires numeric outcome, count predictors, and inflation predictors.
- Outcome must be non-negative on complete observations.
- Supports covariance modes:
  - nonrobust (default)
  - robust
  - clustered via `cluster(<var>)`
- `robust` and `cluster(...)` cannot be combined.

## Post-estimation behavior

- `predict <newvar>[, xb residuals]` is supported after successful `zip`.
- `predict <newvar>[, xb residuals]` is supported after successful `zinb`.
- `estat gof` is supported after successful `zip` or `zinb`.
- Existing `predict ..., pr` remains binary-choice-only.

## Error/guard behavior

- No active dataset:
  - `zip requires an active dataset; run use <path> first`
  - `zinb requires an active dataset; run use <path> first`
- Missing variables/non-numeric variables:
  - existing unknown-variable and numeric-type errors
- Empty complete-observation sample:
  - `zip requires at least one complete observation`
  - `zinb requires at least one complete observation`
- Cluster mode with missing cluster values:
  - `zip requires complete cluster values`
  - `zinb requires complete cluster values`
- Negative outcomes:
  - `zip outcome must be non-negative`
  - `zinb outcome must be non-negative`
- Fit failures:
  - `zip failed`
  - `zinb failed`
- `estat gof` without prior ZIP/ZINB/Poisson/NB model:
  - `estat gof requires a prior poisson, nbreg, zip, or zinb model`

## State behavior

- Running `zip` or `zinb` clears incompatible prior estimation-family state.
- Existing `estat` and `predict` boundaries for other families remain unchanged.

## Acceptance Criteria

- `zip` and `zinb` parse and execute with required `inflate(...)` arguments and supported covariance
  modes.
- deterministic typed and formatted output includes coefficient rows and log-likelihood summary.
- `predict` supports `xb` and `residuals` after `zip` and `zinb`.
- `estat gof` returns deterministic GOF rows after `zip` and `zinb`.
- focused parser/executor/CLI/shell/help coverage passes.
