# predict

How to invoke:
`predict newvar [, xb residuals pr spatial_lag posterior_predictive interval level(<num>)]`

What it does:
Create fitted values, residuals, predicted probabilities, or same-sample spatial-lag predictions
after a model.

What problem it answers:
How do I turn a fitted model into observation-level outputs?

Examples:
- `predict yhat, xb`
- `predict p, pr`
- `predict resid, residuals`
- `bayes: regress wage educ exper` then `predict wage_pp, posterior_predictive`
- `bayes: regress wage educ exper` then `predict wage_pp, posterior_predictive interval level(90)`
- `bayes: logit union age educ` then `predict union_pp, posterior_predictive`
- `spregress claims age, coord(lat lon)` then `predict spillover_hat, spatial_lag`
- `qreg claims age exposure` then `predict qhat, xb`
- `did claims age exposure, treat(treated) post(post)` then `predict did_hat, xb`
- `nbreg claims age exposure` then `predict mu_hat, xb`
- `zip claims age exposure, inflate(exposure)` then `predict mu_hat, residuals`
- `xtabond wage exposure` then `predict dxb, xb`
- `xtabond wage exposure` then `predict dresid, residuals`

Notes:
- `posterior_predictive` requires a prior `bayes:` prefix model.
- `interval` adds `<newvar>_lower` and `<newvar>_upper` columns in addition to the mean column.
- `level(<num>)` sets the central posterior predictive interval level; the default is 95.
