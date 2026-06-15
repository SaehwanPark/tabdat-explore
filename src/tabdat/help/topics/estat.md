# estat

How to invoke:
`estat <subcommand>`

What it does:
Run postestimation diagnostics and model-specific summaries.

What problem it answers:
How do I check fit, identification, or marginal effects after estimation?

Examples:
- `estat vif`
- `estat residuals`
- `qreg claims age exposure` then `estat residuals`
- `estat margins`
- `estat gof`
- `estat bayes`
- `estat spatial, coord(lat lon) knn(5)`
- `estat spatial, weights(columbus.gal) id(neighborhood)`
- `nbreg claims age exposure` then `estat gof`
- `zinb claims age exposure, inflate(exposure)` then `estat gof`
- `did claims age exposure, treat(treated) post(post)` then `estat did`
- `xtabond wage exposure` then `estat overid`
- `bayes: regress wage educ exper` then `estat bayes`

`estat did` reports interaction estimate diagnostics plus deterministic DID cell counts, means,
and raw diff-in-diff contrasts.
`estat bayes` reports MCMC convergence and Monte Carlo error diagnostics from the retained
`bayes:` posterior state.
`estat spatial` reports Moran's I and five Lagrange Multiplier tests for spatial autocorrelation
in OLS residuals using a pre-computed weights file or on-the-fly KNN coordinate weights.

Links:
- `docs/microecometrics_topics.md`
