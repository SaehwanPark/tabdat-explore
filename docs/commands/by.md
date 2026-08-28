# `by`

Run a supported command separately within each group.

!!! question "When to use"
    How do I repeat an analysis by subgroup?

## Syntax

```text
by groupvars: command
```

## Examples

```text
by sex: summarize age
by firm_id year: count
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
