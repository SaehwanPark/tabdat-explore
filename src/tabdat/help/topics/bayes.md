# bayes

How to invoke:
`bayes linear y x1 x2 [, n_iter(<int>) tol(<num>) noconstant]`

What it does:
Fit a Bayesian linear regression model using Bayesian Ridge estimation.

What problem it answers:
How do I perform Bayesian linear regression and obtain posterior estimates for my coefficients?

Examples:
- `bayes linear wage educ exper`
- `bayes linear wage educ exper, n_iter(500) tol(1e-4)`
- `bayes linear wage educ exper, noconstant`

Links:
- `docs/microecometrics_topics.md`
