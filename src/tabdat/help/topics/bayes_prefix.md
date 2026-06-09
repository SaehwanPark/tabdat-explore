# bayes_prefix

How to invoke:
`bayes [, draws(<int>) burnin(<int>) chains(<int>) thin(<int>) seed(<int>) prior(<var>, <dist>)]: <regress|logit> ...`

What it does:
Fit a Bayesian model using MCMC sampling via Bambi and PyMC backends.

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
- `bayes, draws(2000) burnin(1000) chains(4) seed(42): regress wage educ exper`
- `bayes, prior(educ, normal(0,5)) prior(Intercept, normal(0,100)): logit union age educ`
