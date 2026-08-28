# `cvelasticnet`

Perform K-fold cross-validation to select the optimal penalty and mixing parameters for a combined L1/L2-penalized linear model, and save a detailed tuning report.

!!! question "When to use"
    How do I automatically tune the penalty and l1_ratio levels via cross-validation?

## Syntax

```text
cvelasticnet linear y x1 x2 [, cv(<int>) l1_ratio(<list_or_val>) noconstant]
```

## Examples

```text
cvelasticnet linear wage educ exper
cvelasticnet linear wage educ exper, cv(5) l1_ratio(0.1 0.5 0.9)
cvelasticnet linear wage educ exper, noconstant
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
