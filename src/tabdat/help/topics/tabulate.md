# tabulate

How to invoke:
`tabulate varlist [if expr] [, row col missing]`

`tabulate [if expr], rows(varlist) [columns(varlist)] [values(var) stat(count|mean|sum|min|max)] [row col missing]`

What it does:
Show one-way, two-way, and multi-level frequency tables. With `values()` and `stat()`, fill
cells with an aggregate instead of a frequency count.

What problem it answers:
How are categorical values distributed, or how does a numeric value aggregate across row and
column categories?

`if` conditions must produce boolean or missing values; numeric and string truthiness is rejected.

Grouped keys use native ordering: numeric values sort numerically, text values lexicographically,
and booleans false before true; numeric labels are not ordered by rendered text. Missing values are excluded by default; they appear last with `missing`. Wide table headers follow the same order.

Examples:
- `tabulate sex`
- `tabulate sex outcome, row col`
- `tabulate sex if age >= 18`
- `tabulate, rows(region sex) columns(outcome year)`
- `tabulate, rows(region) columns(sex) values(cost) stat(mean)`
- `by region: tabulate, rows(sex) columns(outcome) values(cost) stat(sum)`
