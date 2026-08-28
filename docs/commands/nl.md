# `nl`

Fit a nonlinear regression model.

!!! question "When to use"
    How do I estimate a nonlinear relationship that cannot be written as a linear model?

## Syntax

```text
nl y = <expression> [, params(name...) start(value...) options]
```

## Examples

```text
nl cost = a + b * exp(c * age), params(a b c) start(1 1 1)
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
