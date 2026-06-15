# Request Summary: Bayesian Posterior Predictive Intervals

## Goal

Continue Phase 19 Bayesian workflow development by extending existing `bayes:` posterior
predictive prediction with optional interval columns.

## Phase Fit

- Phase 19 modern extension: richer Bayesian posterior predictive workflows.
- Builds on existing `bayes: regress|logit`, `predict ..., posterior_predictive`, `estat bayes`,
  and `bayesplot` state.

## Touched Surfaces

- `predict` command model and parser options.
- Executor routing for `bayes:` MCMC posterior predictive draws.
- Backend active-dataset replacement for multi-column numeric prediction output.
- CLI smoke tests, shell completions, help, README, SPEC, architecture notes, changelog.

## Assumptions

- Existing `predict <newvar>, posterior_predictive` mean-only behavior must remain unchanged.
- Intervals are same-active-dataset only; no out-of-sample file syntax in this slice.
- Central quantile intervals are sufficient for this slice.

## Non-Goals

- No custom interval column names.
- No HDI/ETI option switch.
- No new Bayesian model families.
- No table export formatting changes.
