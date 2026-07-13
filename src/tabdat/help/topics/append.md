# append

How to invoke:
`append table_name`

What it does:
Append rows from a named table to the active dataset.

What problem it answers:
How do I stack compatible datasets vertically?

Rows from the active dataset remain first. Rows from the named table follow in their stored order;
append does not sort, deduplicate, or interleave them.

Examples:
- `append followup`
