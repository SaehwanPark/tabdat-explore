# generate

How to invoke:
`generate new_name = <expression>`

What it does:
Create a new variable from an expression.

What problem it answers:
How do I compute a derived column?

Examples:
- `generate log_cost = log(cost)`
- `generate age2 = age * 2`
- `generate missing_cost = null`

`null` creates an all-missing value. Null-aware `==` and `!=` comparisons are supported; null
arithmetic and null function arguments are rejected.
