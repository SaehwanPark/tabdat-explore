# Command Contract: encode / decode

## encode
`encode <strvar>, generate(<newvar>) [, label(<lblname>)]`

- Source must be string-domain.
- Target must not exist.
- Codes: integers 1..K in native sorted order of distinct nonmissing source values.
- Label set name defaults to `<newvar>`; if it exists, replace mappings (encode owns the set).
- Attach label set to the new variable.
- Copy source variable label to target if present.

## decode
`decode <numvar>, generate(<newvar>)`

- Source must be numeric.
- Source must have an attached value-label set.
- Target must not exist.
- Output strings are label texts; codes without labels → missing.

## Acceptance
Parser, executor, backend, help, command-reference, focused tests, docs alignment, ruff, basedpyright.
