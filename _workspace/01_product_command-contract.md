# Command Contract: Phase 19 — Richer Bayesian Prediction Workflows

## Request Summary
Extend the `predict` command after MCMC fits (`bayes:`) to allow predicting the standard deviation of the posterior predictive distribution, and exporting raw posterior predictive draws to a Parquet file.

## Roadmap Phase
Phase 19: Modern Extensions (Deferred items).

## Command Syntax
```stata
predict <newvar>, posterior_predictive [std] [interval [level(<num>)]] [saving(<path>)]
```

Where:
- `std`: Flag option to compute the posterior predictive standard deviation. Adds a column named `<newvar>_std` to the active dataset.
- `saving(<path>)`: Option to save the complete set of MCMC draws for the posterior predictive distribution. Outputs to a Parquet file at `<path>`. The active dataset is not modified when `saving()` is specified.
- `interval`: Flag option to compute credible intervals (adds `<newvar>_lower` and `<newvar>_upper`).
- `level(<num>)`: Specifies the probability level (default 95).

## Examples
- `predict y_pp, posterior_predictive std`
- `predict y_pp, posterior_predictive std interval level(90)`
- `predict y_pp, posterior_predictive saving(predictions.parquet)`

## Data Assumptions
- The estimation model must be a Bayesian MCMC model fitted via the `bayes:` prefix.
- The target dataset (active dataset at time of prediction) must contain all predictor columns used in the model.
- The outcome variable does not need to exist in the target dataset for prediction.

## Execution Semantics
- If `std` is requested, the standard deviation is calculated across MCMC draws (`predictive_samples.std(dim="__sample").values`) and added to the active dataset.
- If `saving` is requested:
  - Generate the simulated draws matrix `predictive_samples`.
  - Export it to a tidy Parquet table with columns `observation_index`, `chain`, `draw`, and `value`.
  - Return a command-line message indicating successful export: `"Saved posterior predictive draws to <path>"`.

## Acceptance Criteria
- [ ] `predict <newvar>, posterior_predictive std` generates standard deviations correctly.
- [ ] `predict <newvar>, posterior_predictive saving(<path>)` generates a tidy Parquet file at `<path>` containing all draws.
- [ ] Out-of-sample prediction succeeds when the outcome variable is missing from the active dataset.
- [ ] Missing values in predictors correctly propagate to missing values in outputs.
