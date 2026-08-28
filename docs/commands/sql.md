# `sql`

Run SQL against the active dataset exposed as `active`.

!!! question "When to use"
    How do I express a query that is easier in SQL than in command syntax?
    
    An explicit `order by` controls the listed-key sequence. Include tie-breaker keys for a reproducible
    
    total order. `sql ... into name` preserves that sequence in the active named table; SQL without
    
    `order by` has no row-order guarantee.

## Syntax

```text
sql <query> or sql """ ... """
```

## Examples

```text
sql select sex, avg(bmi) from active group by sex
sql """select * from active""" into summary
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
