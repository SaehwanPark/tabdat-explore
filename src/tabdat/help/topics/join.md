# join

How to invoke:
`join table_name on keyvars [, how=inner|left suffix(_right)]`

What it does:
Join the active dataset with a named table.

What problem it answers:
How do I bring lookup fields into the current dataset?

Rows are grouped by active-row order. For each active row, matching rows from the named table stay
in their stored order, including duplicate matches. An inner join omits unmatched active rows; a left
join keeps one row with missing right-side values for each unmatched active row.

Examples:
- `join lookup on id`
- `join lookup on firm_id year, how=left`
