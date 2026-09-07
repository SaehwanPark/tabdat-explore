# `gsort`

`gsort` provides stable per-key ascending and descending ordering for the active dataset. It is
inspired by Stata's `gsort`, SAS descending sort keys, and SPSS `SORT CASES`, while retaining
TabDat's native scalar ordering and explicit null semantics.

## Syntax

```text
gsort [+|-]varlist
```

Each key may begin with `+` (ascending), `-` (descending), or no prefix (ascending):

```text
gsort -date +patient_id
gsort +site -score
```

Keys are applied left-to-right. Ties preserve their previous active-row order. Quoted identifiers are
not interpreted as direction prefixes, so a variable literally named `-score` can be quoted.

## Semantics

- Numeric, text, boolean, date, timestamp, decimal, and other supported scalar keys use existing
  native comparison semantics.
- Missing/null keys are always placed after nonmissing values, including descending keys.
- Sorting is stable; an internal ordinal tie-breaker is not retained in the public schema.
- Unknown variables are rejected before any active-data change.
- Eager, DuckDB-lazy, and Polars-lazy execution use native stable backends. Polars-lazy remains lazy.
- Labels, valid panel metadata, named-table synchronization, and transform result behavior follow
  the existing `sort` command.

## Output

`gsort` returns the existing transform result:

```text
Sorted by: -group_id +label
```

JSON output uses `TransformResult` with the same message and updated dataset metadata.

## Invalid forms

```text
gsort
gsort group_id, stable
gsort group_id if active == true
gsort -
gsort --score
```

These forms fail with deterministic parse errors. An unknown key produces the standard execution
error without mutating the active dataset.
