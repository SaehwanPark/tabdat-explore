# `elasticnet`

Fit a bounded L1- and L2-penalized linear model using a fixed penalty level.

!!! question "When to use"
    How do I combine L1 and L2 penalties to perform elastic net regularization?

## Syntax

```text
elasticnet linear y x1 x2 [, alpha(<num>) l1_ratio(<num>) noconstant]
```

## Examples

```text
elasticnet linear wage educ exper
elasticnet linear wage educ exper, alpha(0.25) l1_ratio(0.75)
elasticnet linear wage educ exper, noconstant
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
