# `xtlogit`

Fit a bounded fixed-effects panel logit model for a binary outcome.

!!! question "When to use"
    How do I estimate within-entity binary-choice effects with panel data?

## Syntax

```text
xtlogit y xvars, fe [robust]
```

## Examples

```text
panel firm_id year
xtlogit promoted training tenure, fe
xtlogit promoted training tenure, fe robust
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
