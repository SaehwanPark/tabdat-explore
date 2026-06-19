# bayes_prefix

How to invoke:
`bayes [, draws(<int>) burnin(<int>) chains(<int>) thin(<int>) seed(<int>) prior(<var>, <dist>)]: <regress|logit> ...`

What it does:
Fit a Bayesian model using MCMC sampling via Bambi and PyMC backends.
After fitting:
- `predict <newvar>, posterior_predictive` adds row-wise posterior predictive means to the active dataset.
- Add `std` to create a posterior predictive standard deviation column.
- Add `interval [level(<num>)]` to also create lower and upper posterior predictive interval columns.
- Add `saving(<path>)` to export the raw MCMC draws to a Parquet file without modifying the active dataset.
- `estat bayes` reports bounded in-terminal MCMC diagnostics.
- `bayesplot <trace|density|autocorrelation>` saves diagnostic plot artifacts.

What problem it answers:
How do I perform MCMC sampling for linear or logistic regression models with custom priors and MCMC specifications?

Options:
- `draws`: Number of post-warmup MCMC draws per chain (default 1000)
- `burnin` or `tune`: Number of warm-up/tuning draws (default 1000)
- `chains`: Number of independent chains (default 4)
- `thin`: Thinning interval for posterior draws (default 1)
- `seed` or `rseed`: Random number seed for reproducibility
- `prior`: Custom prior distributions, e.g. `prior(x, normal(0,10))` or `prior(Intercept, uniform(-5,5))`

Examples:
- `bayes: regress wage educ exper`
- `bayes: regress wage educ exper` then `predict wage_pp, posterior_predictive`
- `bayes: regress wage educ exper` then `predict wage_pp, posterior_predictive std interval`
- `bayes: regress wage educ exper` then `predict wage_pp, posterior_predictive saving(draws.parquet)`
- `bayes: regress wage educ exper` then `estat bayes`
- `bayes: regress wage educ exper` then `bayesplot trace`
- `bayes, draws(2000) burnin(1000) chains(4) seed(42): regress wage educ exper`
- `bayes, prior(educ, normal(0,5)) prior(Intercept, normal(0,100)): logit union age educ`
