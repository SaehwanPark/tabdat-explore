# `qreg`

Fit a bounded quantile regression model for a selected conditional quantile.

!!! question "When to use"
    How do I model conditional medians or other conditional quantiles instead of mean effects?

## Syntax

```text
qreg y x1 x2 [, quantile(<0,1>) robust noconstant]
```

## Examples

```text
qreg cost age bmi
qreg cost age bmi, quantile(0.25)
qreg cost age bmi, robust
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
