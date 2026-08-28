# `keep`

Keep selected variables, or keep rows that satisfy a condition.

!!! question "When to use"
    How do I reduce the active dataset to the variables or rows I want?

## Syntax

```text
keep varlist or keep if <expression>
```

## Examples

```text
keep age bmi
keep if age >= 18
keep if cost == null
null` is the explicit missing-value literal. Use `== null` to keep missing values; use `!= null
to keep nonmissing values.
Conditions must produce boolean or missing values; numeric and string truthiness is rejected.
Rows that remain are kept in their prior relative order.
If the condition contains exact integral arithmetic overflow, the successful result appends
overflow rows: N`; missing and false predicates retain their existing keep policy.
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
