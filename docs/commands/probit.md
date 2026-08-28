# `probit`

Fit a binary-response probit model.

!!! question "When to use"
    How do I model a 0/1 outcome with a normal-link specification?

## Syntax

```text
probit y x1 x2 [, robust cluster(var) noconstant]
```

## Examples

```text
probit insured age bmi
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
