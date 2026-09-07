# label

How to invoke:
`label variable <varname> "text"`, `label variable <varname>, clear`,
`label define <lblname> <value> "text" ... [, replace]`,
`label values <varname> <lblname>`, `label values <varname>, clear`,
`label list`, `label list <lblname> ...`, `label drop <lblname> ...`

What it does:
Manage session-local variable labels and named value-label dictionaries on the active dataset.

What problem it answers:
How do I attach Stata/SPSS-style data-dictionary metadata for inspection in `describe` and `codebook`?

Examples:
- `label variable age "Age in years"`
- `label define sexlbl 0 "Male" 1 "Female"`
- `label values sex sexlbl`
- `label list`
- `label drop sexlbl`
