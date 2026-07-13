# reshape

How to invoke:
`reshape long|wide varlist, i(idvars) j(jvar)`

What it does:
Convert between wide and long layouts.

What problem it answers:
How do I pivot repeated-measures data into the shape I need?

Long output follows source-row order. Its j-values scan requested stubs in command order, then matching
wide columns in schema order, keeping each suffix's first appearance once.
Wide output follows the first active row for each identifier group; existing generated-column and
duplicate-cell behavior remains unchanged.

Examples:
- `reshape long income cost, i(id) j(year)`
