# `ridge`

Fit a bounded L2-penalized linear model using a fixed penalty level.

!!! question "When to use"
    How do I perform ridge regression to handle multicollinearity and shrink coefficients?

## Syntax

```text
ridge linear y x1 x2 [, alpha(<num>) noconstant]
```

## Examples

```text
ridge linear wage educ exper
ridge linear wage educ exper, alpha(0.25)
ridge linear wage educ exper, noconstant
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
