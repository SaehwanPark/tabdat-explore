# recode

How to invoke:
`recode <varlist> (<rule>) [ (<rule>) ...] [, generate(<new_varlist>) replace]`

What it does:
Recode numeric or categorical variables in the active dataset based on value or range rules.

What problem it answers:
Regroup or transform categorical boundaries or map values sequentially (e.g. mapping numeric ages to groups).

Examples:
- `recode age (min/17 = 0) (18/max = 1), generate(adult)`
- `recode score (90/100 = 4) (80/89 = 3) (else = 1), replace`
- `recode grade (1 2 3 = 1) (4 5 = 2), replace`

Notes:
- Range syntax (e.g. `1/5`) is only allowed on numeric columns.
- Exactly one of `generate()` or `replace` must be specified.
