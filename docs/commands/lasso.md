# `lasso`

Fit a bounded L1-penalized linear model using a fixed penalty level.

!!! question "When to use"
    How do I shrink coefficients and perform basic linear regularization in one command?

## Syntax

```text
lasso linear y x1 x2 [, alpha(<num>) noconstant]
```

## Examples

```text
lasso linear wage educ exper
lasso linear wage educ exper, alpha(0.25)
lasso linear wage educ exper, noconstant
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
