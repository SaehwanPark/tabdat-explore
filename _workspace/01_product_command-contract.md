# Command Contract: Bayesian Posterior Predictive Intervals

## Request Summary

Add optional posterior predictive interval columns after a successful `bayes:` MCMC fit while
preserving existing mean-only posterior predictive prediction.

## Roadmap Phase

Phase 19 modern extensions: richer Bayesian posterior predictive workflows.

## Command Syntax

```text
predict <newvar>, posterior_predictive
predict <newvar>, posterior_predictive interval
predict <newvar>, posterior_predictive interval level(<num>)
```

## Examples

- `bayes: regress wage educ exper` then `predict wage_pp, posterior_predictive`
  - Adds `wage_pp` with row-wise posterior predictive means.
- `bayes: regress wage educ exper` then `predict wage_pp, posterior_predictive interval`
  - Adds `wage_pp`, `wage_pp_lower`, and `wage_pp_upper` using the default 95% interval.
- `bayes: logit union age educ` then `predict union_pp, posterior_predictive interval level(90)`
  - Adds probability-scale mean/lower/upper columns using a 90% central interval.

## Data Assumptions

- Requires an active dataset and a prior `bayes:` prefix model state.
- Predictor rows with missing values receive missing output values in every generated column.
- `level(<num>)` must be greater than 0 and less than 100.
- All target columns must be absent before mutation; any collision rejects the whole prediction.

## Execution Semantics

- Reuse the retained Bambi model and ArviZ inference data from `bayes:`.
- Generate posterior predictive draws over complete active rows with `kind="response"`.
- Mean-only mode writes one numeric column.
- Interval mode writes the mean column plus central quantile lower/upper numeric columns.
- Active dataset row order must be preserved.

## Acceptance Criteria

- Existing `predict <newvar>, posterior_predictive` tests and output remain valid.
- Interval mode adds exactly `<newvar>`, `<newvar>_lower`, and `<newvar>_upper`.
- Logit interval outputs remain within `[0, 1]`.
- Missing predictor rows propagate missing values across all interval output columns.
- Parser rejects invalid levels and interval options without `posterior_predictive`.
- CLI smoke output shows the new interval columns.

## Open Questions

- None for this slice.
