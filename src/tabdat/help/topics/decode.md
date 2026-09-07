# decode

How to invoke:
`decode <numvar>, generate(<newvar>)`

What it does:
Convert a numeric variable that has attached value labels into a new string variable of those
labels. Codes without labels become missing.

What problem it answers:
How do I recover readable string categories from a labeled numeric variable?

Examples:
- `decode sex_n, generate(sex_str)`
