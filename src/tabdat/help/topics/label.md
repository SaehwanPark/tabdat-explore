# label

How to invoke:
`label variable <varname> "text"`, `label variable <varname>, clear`,
`label define <lblname> <value> "text" ... [, replace]`,
`label values <varname> <lblname>`, `label values <varname>, clear`,
`label list`, `label list <lblname> ...`, `label drop <lblname> ...`,
`label save <path> [, replace]`, `label use <path>`

What it does:
Manage variable labels and named value-label dictionaries on the active dataset. `label save` and
`label use` persist this metadata as a deterministic, versioned TabDat JSON dictionary; they do not
claim compatibility with Stata, SAS, or SPSS metadata files.

What problem it answers:
How do I attach and reuse Stata/SAS/SPSS-inspired data-dictionary metadata for inspection in
`describe` and `codebook`?

Examples:
- `label variable age "Age in years"`
- `label define sexlbl 0 "Male" 1 "Female"`
- `label values sex sexlbl`
- `label list`
- `label save labels.json, replace`
- `label use labels.json`
- `label drop sexlbl`
