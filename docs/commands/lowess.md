# `lowess`

Generate a nonparametric LOWESS-smoothed fit column.

!!! question "When to use"
    How do I inspect a smooth nonlinear relationship without imposing a parametric form?

## Syntax

```text
lowess y x, gen(<newvar>) [bandwidth=<0,1>]
```

## Examples

```text
lowess wage exper, gen(wage_lowess)
lowess wage exper, gen(wage_lowess) bandwidth=0.5
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
