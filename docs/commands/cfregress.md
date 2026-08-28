# `cfregress`

Fit a control-function regression for endogenous predictors.

!!! question "When to use"
    How do I address endogeneity with a residual-inclusion approach?

## Syntax

```text
cfregress y exog..., endog(x) iv(z...) [options]
```

## Examples

```text
cfregress wage educ, endog(experience) iv(distance)
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
