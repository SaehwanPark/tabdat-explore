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
