# gsort

Stable-sort active rows by explicit per-key directions.

## Syntax

```text
gsort [+|-]varlist
```

Prefix a key with `+` for ascending or `-` for descending; an omitted prefix is ascending. Keys are
applied left-to-right, ties retain their previous row order, and null values are always last.

```text
tabdat> gsort -date +patient_id
tabdat> gsort +site -score
Sorted by: -date +patient_id
```

`gsort` changes active row order, preserves labels and valid panel metadata, and supports eager,
DuckDB-lazy, and Polars-lazy execution. It accepts no options, `if` clause, assignment, or `by:`
prefix. A quoted identifier is not interpreted as a direction prefix.
