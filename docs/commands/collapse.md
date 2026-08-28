# `collapse`

Aggregate variables by groups using count, mean, sum, min, or max.

!!! question "When to use"
    How do I reduce a dataset to grouped summary statistics?

## Syntax

```text
collapse stat varlist, by(groupvars)
```

## Examples

```text
collapse mean age cost, by(sex)
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
