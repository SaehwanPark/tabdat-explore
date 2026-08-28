# `nbreg`

Fit a negative-binomial count-response model.

!!! question "When to use"
    How do I model overdispersed non-negative count outcomes as a function of predictors?

## Syntax

```text
nbreg y x1 x2 [, robust cluster(var) noconstant]
```

## Examples

```text
nbreg visits age income
nbreg claims age exposure, robust
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
