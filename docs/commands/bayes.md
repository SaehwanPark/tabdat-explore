# `bayes`

Fit a Bayesian linear regression model using Bayesian Ridge estimation.

!!! question "When to use"
    How do I perform Bayesian linear regression and obtain posterior estimates for my coefficients?

## Syntax

```text
bayes linear y x1 x2 [, n_iter(<int>) tol(<num>) noconstant]
```

## Examples

```text
bayes linear wage educ exper
bayes linear wage educ exper, n_iter(500) tol(1e-4)
bayes linear wage educ exper, noconstant
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
