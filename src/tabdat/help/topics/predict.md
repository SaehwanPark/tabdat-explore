# predict

How to invoke:
`predict newvar [, xb residuals pr spatial_lag]`

What it does:
Create fitted values, residuals, predicted probabilities, or same-sample spatial-lag predictions
after a model.

What problem it answers:
How do I turn a fitted model into observation-level outputs?

Examples:
- `predict yhat, xb`
- `predict p, pr`
- `predict resid, residuals`
- `spregress claims age, coord(lat lon)` then `predict spillover_hat, spatial_lag`
- `qreg claims age exposure` then `predict qhat, xb`
- `did claims age exposure, treat(treated) post(post)` then `predict did_hat, xb`
- `nbreg claims age exposure` then `predict mu_hat, xb`
- `zip claims age exposure, inflate(exposure)` then `predict mu_hat, residuals`
- `xtabond wage exposure` then `predict dxb, xb`
- `xtabond wage exposure` then `predict dresid, residuals`
