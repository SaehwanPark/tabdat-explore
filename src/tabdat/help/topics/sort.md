# sort

How to invoke:
`sort <varlist>`

What it does:
Stable-sort active rows by one or more ascending columns. Numeric values use numeric order, text
values use lexicographic order, booleans use false-before-true order, and nulls sort last.

What problem it answers:
How do I arrange the active dataset before inspecting, exporting, or analyzing it?

Examples:
- `sort treatment age`
- `sort household_id visit`

Ties preserve their prior active-row order. `sort` preserves columns, labels, panel metadata, and
Polars-lazy execution mode. Descending sort and expression keys are not part of this command; use SQL
for those cases.
