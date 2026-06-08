# Phase 19 Slice 8 Command Contract: `dml linear` and `estat dml`

## Roadmap Phase

- Phase 19 modern extensions
- Double/debiased machine learning starter for binary treatment effects

## Syntax

```stata
dml linear <y> <controls>, treat(<tvar>) [folds(<int>) alpha(<num>) robust seed(<int>) noconstant]
estat dml
```

## Behavior

- `dml linear` estimates a partial-linear average treatment effect (ATE) for a binary treatment
  using K-fold cross-fitted Lasso nuisances on the active dataset.
- Nuisance models:
  - outcome nuisance `E[Y|X]` via Lasso on controls
  - treatment nuisance `E[D|X]` via Lasso on controls
- Final stage: OLS of orthogonalized outcome on orthogonalized treatment without intercept.
- Required option: `treat(<tvar>)`.
- Defaults: `folds(5)`, `alpha(1.0)`, intercept on unless `noconstant`.
- `robust` uses HC1 standard errors on the final stage.
- `seed(<int>)` fixes fold shuffling.

## Option Rules

- `treat(<tvar>)` is required.
- `folds` must be an integer >= 2.
- `alpha` must be positive.
- `treat`, `folds`, `alpha`, `robust`, `seed`, and `noconstant` are the only supported options.
- Treatment must differ from outcome and controls.

## Data/State Rules

- Requires an active dataset with complete numeric observations for outcome, treatment, and controls.
- Treatment must be binary with values 0 and 1.
- At least one control variable is required.
- Clears prior estimation state before fitting; stores DML state for `estat dml`.

## Output Contract

- Estimation header includes model line, `Estimator: dml`, covariance label, observation count,
  fold count, and alpha.
- Coefficient table includes one `ATE` row with Coef, Std Err, t, P>|t|, and 95% CI.
- `estat dml` reports method, fold count, treated/control counts, nuisance observation count,
  and overlap summary (nuisance treatment-fit min/mean/max with overlap pass/warning).

## Acceptance Criteria

- Parser, executor, CLI, shell, help, and registry tests cover the new behavior.
- Invalid syntax and guards fail deterministically.
- Full validation suite passes.
- SDD docs record slice completion.

## Non-goals

- No `dml logistic`, IV, causal forests, CATE, or `predict` routing.
- No panel precondition or `did`/`drdid` integration.
- No new runtime dependencies or R fallback.
