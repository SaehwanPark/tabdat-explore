# `ivregress`

Fit an instrumental-variables regression.

!!! question "When to use"
    How do I estimate a relationship when a predictor is endogenous?

## Syntax

```text
ivregress 2sls|gmm y exog..., endog(x) iv(z...) [options]
```

## Examples

```text
ivregress 2sls wage educ, endog(experience) iv(distance)
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
