# `recode`

Recode numeric or categorical variables in the active dataset based on value or range rules.

!!! question "When to use"
    Regroup or transform categorical boundaries or map values sequentially (e.g. mapping numeric ages to groups).

## Syntax

```text
recode <varlist> (<rule>) [ (<rule>) ...] [, generate(<new_varlist>) replace]
```

## Examples

```text
recode age (min/17 = 0) (18/max = 1), generate(adult)
recode score (90/100 = 4) (80/89 = 3) (else = 1), replace
recode grade (1 2 3 = 1) (4 5 = 2), replace
Notes:
Range syntax (e.g. `1/5`) is only allowed on numeric columns.
Exactly one of `generate()` or `replace` must be specified.
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
