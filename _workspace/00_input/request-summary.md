# Request Summary: Phase 19 — Out-of-Sample Bayesian Prediction

## Goal
Extend the MCMC Bayesian prefix prediction workflow (`predict`) to support richer out-of-sample predictions:
1. Support standard deviation of predictions (`std` option) written to the active dataset.
2. Support exporting raw posterior predictive MCMC draws (`saving()` option) to an external Parquet file.
3. Validate and verify that these predictions function out-of-sample, including on datasets where the outcome variable is missing.

## Phase Fit
Phase 19: Modern Extensions (deferred items).

## Touched Surfaces
- `models.py` (PredictCommand model updates)
- `parser.py` (predict command option parsing)
- `executor.py` (predict execution mapping and Bambi integration)
- `shell.py` (predict option autocompletions)
- Help topics (`predict.md`, `bayes_prefix.md`)
- Tests (`test_executor.py`)

## Assumptions
- Estimation model is MCMC-based (`bayes:` prefix regress/logit).
- Predictors exist in target dataset; outcome variable does not need to exist.

## Non-Goals
- Adding out-of-sample options to frequentist estimators.
- Storing MCMC draws inside the active dataset (must be exported to external file).
