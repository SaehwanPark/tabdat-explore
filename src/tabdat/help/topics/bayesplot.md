# bayesplot

## How to invoke

`bayesplot trace [, saving(<path>) noopen]`
`bayesplot density [, saving(<path>) noopen]`
`bayesplot autocorrelation [, saving(<path>) noopen]`

## What it does

Save Bayesian MCMC diagnostic plots after a successful `bayes:` prefix model.

## Why use it

How do I visually inspect Bayesian chains after fitting an MCMC model?

## Examples

- `bayes: regress wage educ exper` then `bayesplot trace`
- `bayes: regress wage educ exper` then `bayesplot density, saving(figures/posterior.svg)`
- `bayes: logit union age educ` then `bayesplot autocorrelation, noopen`
