# assert

How to invoke:
`assert <boolean-expression>`

What it does:
Check every row of the active dataset against a boolean predicate. Rows where the predicate is false
or missing fail; an empty dataset passes.

Examples:
- `assert age >= 0`
- `assert bmi == null`
- `assert lower(sex) != "unknown"`

A successful check prints `assertion passed: N rows`. A failed check reports deterministic failed and
checked counts and leaves the active dataset unchanged. The command accepts no options, `if` clause,
assignment, row filtering, or row-level diagnostic output. It reuses TabDat's existing expression and
missing-value semantics and preserves Polars-lazy execution.
