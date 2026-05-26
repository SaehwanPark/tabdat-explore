# Phase 19 Slice 1 Command Contract: `lasso linear`

## Roadmap Phase

- Phase 19 modern extensions
- Slice 1: bounded machine-learning starter over stable tabular boundaries

## Syntax

```stata
lasso linear <y> <xvars>[, alpha(<num>) noconstant]
```

## Behavior

- Fits an L1-penalized linear model using fixed `alpha`.
- Requires active dataset.
- Requires numeric `<y>` and numeric `<xvars>`.
- Requires at least one complete observation.
- Defaults:
  - `alpha=1.0`
  - intercept included unless `noconstant`.

## Option Rules

- `alpha(<num>)`:
  - optional
  - numeric and strictly positive
  - may be supplied once
- `noconstant`:
  - optional flag
- unsupported options fail with deterministic parser errors.

## Predict Integration

- `predict <newvar>` and `predict <newvar>, xb` are supported after `lasso`.
- `predict ..., residuals` and `predict ..., pr` fail deterministically after `lasso`.
- Existing predict behavior for all prior model families remains unchanged.

## Output Contract

- Deterministic header:
  - `Model: lasso linear ...`
  - `Estimator: lasso`
  - `Alpha: ...`
  - `Observations: ...`
  - `R-squared: ...`
- Coefficient table follows shared formatter conventions.

## Help Contract

- Add `help lasso` topic with invoke/what-it-does/problem/examples/links sections.
- `tests/test_help.py` command coverage gate must pass.

## Acceptance Criteria

- Parser/executor/CLI/shell/help/registry tests cover new behavior.
- Full suite and static checks pass.
- `SPEC.md` and SDD docs reflect Phase 19 status (ML slice done; Bayesian/spatial remain).
