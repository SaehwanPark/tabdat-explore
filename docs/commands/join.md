# `join`

Join the active dataset with a named table.

!!! question "When to use"
    How do I bring lookup fields into the current dataset?
    
    Rows are grouped by active-row order. For each active row, matching rows from the named table stay
    
    in their stored order, including duplicate matches.
    
    An inner join omits unmatched active rows; a left join keeps one row with missing right-side values for
    
    each unmatched active row.

## Syntax

```text
join table_name on keyvars [, how=inner|left suffix(_right)]
```

## Examples

```text
join lookup on id
join lookup on firm_id year, how=left
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
