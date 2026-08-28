# `tobit`

Fit a censored regression model.

!!! question "When to use"
    How do I model an outcome that is censored at a lower or upper limit?

## Syntax

```text
tobit y x1 x2, ll(#) [ul(#)] [options]
```

## Examples

```text
tobit cost age bmi, ll(0)
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
