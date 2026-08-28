# `zinb`

Fit a zero-inflated negative-binomial count-response model with a logit inflation equation.

!!! question "When to use"
    How do I model overdispersed count outcomes with excess zeros and a separate zero process?

## Syntax

```text
zinb y x1 x2, inflate(z1 z2) [robust cluster(var) noconstant]
```

## Examples

```text
zinb visits age income, inflate(age income)
zinb claims age exposure, inflate(exposure) cluster(firm_id)
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
