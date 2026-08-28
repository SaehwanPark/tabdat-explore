# `append`

Append rows from a named table to the active dataset.

!!! question "When to use"
    How do I stack compatible datasets vertically?
    
    Rows from the active dataset remain first. Rows from the named table follow in their stored order;
    
    append does not sort, deduplicate, or interleave them.

## Syntax

```text
append table_name
```

## Examples

```text
append followup
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
