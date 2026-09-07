# encode

How to invoke:
`encode <strvar>, generate(<newvar>) [, label(<lblname>)]`

What it does:
Convert a string variable into a new integer-coded variable (1..K for sorted unique
nonmissing values), create a matching value-label set, and attach it.

What problem it answers:
How do I turn string categories into numeric codes with value labels for tabulate and modeling?

Examples:
- `encode sex, generate(sex_n)`
- `encode region, generate(region_id) label(regionlbl)`
