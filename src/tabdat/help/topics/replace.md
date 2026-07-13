# replace

How to invoke:
`replace varname = <expression> [if <condition>]`

What it does:
Overwrite values in an existing variable, optionally for a subset of rows.

What problem it answers:
How do I update a column in place?

Examples:
- `replace cost = 0 if sex == 'F'`
- `replace cost = 0 if cost != null`

`null` is the explicit missing-value literal. Use `== null` or `!= null` for missingness checks.

Replacement expressions must stay in the target variable's domain; numeric/string conversion is not
implicit.

`if` conditions must produce boolean or missing values; numeric and string truthiness is rejected.

Missing operands produce missing results. Division by zero and invalid `sqrt`, `ln`, or `log`
domains produce missing values for those rows; computed `inf` and `nan` are normalized to missing.
Integral `+`, `-`, `*`, and unary minus results use exact `DECIMAL(38,0)` storage. Results outside
that width become missing for the affected row rather than wrapping; machine-readable overflow
diagnostics and decimal-scale/float-width guarantees are not yet defined.
When exact integral overflow occurs, the successful transform result appends `overflow rows: N`;
zero-count results keep the existing output shape.
