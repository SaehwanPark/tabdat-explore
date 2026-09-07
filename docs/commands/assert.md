# assert

Validate a boolean quality condition across all rows without changing the active dataset.

## Syntax

```text
assert <boolean-expression>
```

True rows pass. False or missing predicate results fail. An empty dataset passes. A successful check
prints `assertion passed: N rows`; a failure reports checked and failed row counts and preserves the
active relation.

## Examples

```text
assert age >= 0
assert bmi == null
assert lower(sex) != "unknown"
```

The expression uses TabDat's existing identifiers, operators, functions, and explicit-null semantics.
Options, `if` clauses, assignment, row filtering, and row-level diagnostics are not part of this
bounded command. Aggregate scans preserve Polars-lazy execution.
