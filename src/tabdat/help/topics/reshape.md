# reshape

How to invoke:
`reshape long|wide varlist, i(idvars) j(jvar)`

What it does:
Convert between wide and long layouts.

What problem it answers:
How do I pivot repeated-measures data into the shape I need?

Examples:
- `reshape long income cost, i(id) j(year)`
