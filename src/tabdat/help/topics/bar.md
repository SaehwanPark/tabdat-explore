# bar

How to invoke:
`bar varname [, missing saving(path) noopen]`

What it does:
Save a bar chart for a categorical variable.

What problem it answers:
How are category counts distributed?

Nonmissing bars are ordered by descending count; ties use the category's native order and the missing category is always last when `missing` is requested. Numeric labels use numeric order rather than rendered text, and missing displays as `<missing>`.

Examples:
- `bar sex`
