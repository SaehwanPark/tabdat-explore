# join

How to invoke:
`join table_name on keyvars [, how=inner|left suffix(_right)]`

What it does:
Join the active dataset with a named table.

What problem it answers:
How do I bring lookup fields into the current dataset?

Examples:
- `join lookup on id`
- `join lookup on firm_id year, how=left`
