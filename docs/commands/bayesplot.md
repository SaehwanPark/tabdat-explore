# `bayesplot`

Save Bayesian MCMC diagnostic plots after a successful `bayes:` prefix model.

!!! question "When to use"
    How do I visually inspect Bayesian chains after fitting an MCMC model?

## Syntax

```text
bayesplot trace [, saving(<path>) noopen]
bayesplot density [, saving(<path>) noopen]
bayesplot autocorrelation [, saving(<path>) noopen]
```

## Examples

```text
bayes: regress wage educ exper` then `bayesplot trace
bayes: regress wage educ exper` then `bayesplot density, saving(figures/posterior.svg)
bayes: logit union age educ` then `bayesplot autocorrelation, noopen
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
