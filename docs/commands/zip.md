# `zip`

Fit a zero-inflated Poisson count-response model with a logit inflation equation.

!!! question "When to use"
    How do I model count outcomes with excess zeros and a separate zero-generation process?

## Syntax

```text
zip y x1 x2, inflate(z1 z2) [robust cluster(var) noconstant]
```

## Examples

```text
zip visits age income, inflate(age income)
zip claims age exposure, inflate(exposure) robust
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
