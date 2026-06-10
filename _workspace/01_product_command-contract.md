# Phase 19 Command Contract: Bayesian Posterior Predictive `predict`

## Roadmap Phase

- Phase 19 modern extensions.
- Bayesian posterior predictive workflow after the completed `bayes:` MCMC prefix.

## Syntax

```stata
bayes [, options]: regress <y> <xvars>
predict <newvar>, posterior_predictive

bayes [, options]: logit <y> <xvars>
predict <newvar>, posterior_predictive
```

## Behavior

- `posterior_predictive` is a mutually exclusive `predict` mode.
- The option is available only after a successful `bayes:` prefix fit.
- The executor uses the retained Bambi model and ArviZ `InferenceData` to generate posterior
  predictive draws for the current active dataset.
- The output column contains the row-wise posterior predictive mean.
- Active row order is preserved.
- Rows with missing predictor values receive missing output rather than being dropped.

## Guards

- `predict ..., posterior_predictive` without a prior `bayes:` fit raises `ExecutionError`.
- `predict ..., xb|residuals|pr|spatial_lag` after `bayes:` raises `ExecutionError`.
- Combining `posterior_predictive` with other `predict` modes raises `ParseError`.
- Existing legacy `bayes linear` prediction behavior remains `xb` and `residuals` only.

## Acceptance Criteria

- Parser accepts `predict y_pp, posterior_predictive`.
- Parser rejects combinations with other `predict` modes.
- Executor appends posterior predictive mean columns after `bayes: regress` and `bayes: logit`.
- Missing active predictor rows are preserved with missing predicted values.
- CLI and shell completions expose the new option.
- Focused tests, `basedpyright`, and `ruff` checks pass.
