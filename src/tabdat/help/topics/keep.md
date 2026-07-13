# keep

How to invoke:
`keep varlist` or `keep if <expression>`

What it does:
Keep selected variables, or keep rows that satisfy a condition.

What problem it answers:
How do I reduce the active dataset to the variables or rows I want?

Examples:
- `keep age bmi`
- `keep if age >= 18`
- `keep if cost == null`

`null` is the explicit missing-value literal. Use `== null` to keep missing values; use `!= null`
to keep nonmissing values.

Conditions must produce boolean or missing values; numeric and string truthiness is rejected.
