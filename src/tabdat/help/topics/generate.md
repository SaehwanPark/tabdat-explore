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

Arithmetic requires numeric operands. Numeric functions require numeric arguments; `lower` and
`upper` require string arguments.

Missing operands produce missing results. Division by zero and invalid `sqrt`, `ln`, or `log`
domains produce missing values for those rows; computed `inf` and `nan` are normalized to missing.

Subtraction involving unsigned numeric variables and unary minus of unsigned numeric expressions
are rejected rather than wrapped or implicitly widened.
