# `drop`

Drop selected variables, or drop rows that satisfy a condition.

!!! question "When to use"
    How do I remove variables or observations I do not need?

## Syntax

```text
drop varlist or drop if <expression>
```

## Examples

```text
drop cost
drop if cost == null
null` is the explicit missing-value literal. Use `== null` to remove missing values; use `!= null
to remove nonmissing values.
Conditions must produce boolean or missing values; numeric and string truthiness is rejected.
Rows that remain are kept in their prior relative order.
If the condition contains exact integral arithmetic overflow, the successful result appends
overflow rows: N`; missing and false predicates retain their existing drop policy.
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
