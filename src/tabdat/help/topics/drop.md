# drop

How to invoke:
`drop varlist` or `drop if <expression>`

What it does:
Drop selected variables, or drop rows that satisfy a condition.

What problem it answers:
How do I remove variables or observations I do not need?

Examples:
- `drop cost`
- `drop if cost == null`

`null` is the explicit missing-value literal. Use `== null` to remove missing values; use `!= null`
to remove nonmissing values.

Conditions must produce boolean or missing values; numeric and string truthiness is rejected.
Rows that remain are kept in their prior relative order.
If the condition contains exact integral arithmetic overflow, the successful result appends
`overflow rows: N`; missing and false predicates retain their existing drop policy.
