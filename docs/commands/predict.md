# `predict`

Create fitted values, residuals, predicted probabilities, same-sample spatial-lag predictions, or Bayesian posterior predictive summaries after a model.

!!! question "When to use"
    How do I turn a fitted model into observation-level outputs or save raw Bayesian MCMC draws?

## Syntax

```text
predict newvar [, xb residuals pr spatial_lag posterior_predictive std interval level(<num>) saving(<path>)]
```

## Examples

```text
predict yhat, xb
predict p, pr
predict resid, residuals
bayes: regress wage educ exper` then `predict wage_pp, posterior_predictive
bayes: regress wage educ exper` then `predict wage_pp, posterior_predictive interval level(90)
bayes: regress wage educ exper` then `predict wage_pp, posterior_predictive std
bayes: regress wage educ exper` then `predict wage_pp, posterior_predictive saving(draws.parquet)
bayes: logit union age educ` then `predict union_pp, posterior_predictive
spregress claims age, coord(lat lon)` then `predict spillover_hat, spatial_lag
qreg claims age exposure` then `predict qhat, xb
did claims age exposure, treat(treated) post(post)` then `predict did_hat, xb
nbreg claims age exposure` then `predict mu_hat, xb
zip claims age exposure, inflate(exposure)` then `predict mu_hat, residuals
xtabond wage exposure` then `predict dxb, xb
xtabond wage exposure` then `predict dresid, residuals
Notes:
posterior_predictive` requires a prior `bayes:` prefix model.
std` adds `<newvar>_std` to the active dataset containing standard deviations of MCMC draws.
interval` adds `<newvar>_lower` and `<newvar>_upper` columns in addition to the mean column.
level(<num>)` sets the central posterior predictive interval level; the default is 95.
saving(<path>)` writes the raw MCMC posterior predictive draws (with columns observation_index, chain, draw, value) to a Parquet file at `<path>` without modifying the active dataset.
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
