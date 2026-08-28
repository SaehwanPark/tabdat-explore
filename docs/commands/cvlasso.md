# `cvlasso`

Perform K-fold cross-validation to select the optimal penalty parameter for an L1-penalized linear model, and save a detailed tuning report.

!!! question "When to use"
    How do I automatically tune the L1 penalty level via cross-validation?

## Syntax

```text
cvlasso linear y x1 x2 [, cv(<int>) noconstant]
```

## Examples

```text
cvlasso linear wage educ exper
cvlasso linear wage educ exper, cv(10)
cvlasso linear wage educ exper, noconstant
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
