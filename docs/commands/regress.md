# `regress`

Fit an ordinary, weighted, or generalized least-squares regression.

!!! question "When to use"
    How do I model a continuous outcome with linear predictors?

## Syntax

```text
regress y x1 x2 [, robust cluster(var) noconstant wls(var) gls(var)]
```

## Examples

```text
regress cost age bmi
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
