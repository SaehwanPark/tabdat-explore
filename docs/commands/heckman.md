# `heckman`

Fit a sample-selection model with an outcome equation and a selection equation.

!!! question "When to use"
    How do I correct for non-random selection into the observed sample?

## Syntax

```text
heckman y x1 x2, selectdep(z) select(z1 z2) [options]
```

## Examples

```text
heckman wage educ exper, selectdep(work) select(age kids)
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
