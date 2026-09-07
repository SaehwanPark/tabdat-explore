# duplicates

How to invoke:
`duplicates [report] [varlist]`

What it does:
Report duplicate groups using all public columns by default, or the requested key variables. Null
key values are grouped together intentionally. The command is read-only and preserves eager,
DuckDB-lazy, and Polars-lazy execution.

Examples:
- `duplicates`
- `duplicates report id`
- `duplicates id name`

The report includes total rows, unique key groups, duplicate groups, rows in duplicate groups, extra
rows after retaining one representative per group, and the largest group size. This bounded command
does not list, tag, or drop duplicate rows and accepts no options or `if` clause.
