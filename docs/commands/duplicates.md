# duplicates

Report repeated key combinations without changing the active dataset.

## Syntax

```text
duplicates [report] [varlist]
```

With no variables, all public columns in schema order define the key. The optional `report` word is
an ergonomic alias, so `duplicates id` and `duplicates report id` are equivalent. Backtick-quoted
identifiers use the normal TabDat identifier rules.

## Output

The report includes:

- total active rows;
- distinct key groups;
- groups with two or more rows;
- rows belonging to duplicate groups;
- surplus rows after keeping one representative per group; and
- the largest group size.

Null key values compare equal for this quality report, so rows with the same missing key values form
a duplicate group. Empty datasets return zero counts. Unknown variables fail before scanning or
changing session state.

## Execution

`duplicates` is read-only. DuckDB eager/lazy and Polars-lazy modes use aggregate grouping; the
Polars plan remains lazy because only aggregate output is collected. The command does not list, tag,
or drop rows, and does not accept options or an `if` clause.

## Examples

```text
use patients.parquet, lazy engine=polars
duplicates report patient_id visit_date
duplicates patient_id
```
