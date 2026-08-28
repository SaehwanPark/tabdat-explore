# `use`

Load a Parquet, Stata `.dta`, CSV, Feather, or Arrow file, or named table into the active dataset slot.

!!! question "When to use"
    Open the data you want to inspect, transform, or model.

## Syntax

```text
use <path> or use <path>, lazy [engine=duckdb|polars]
use <path>, delimiter(<char>) has_header(true|false)
```

## Examples

```text
use patients.parquet
use patients.dta
use survey.csv, delimiter(",") has_header(true)
use data.feather
use https://example.com/patients.dta
use s3://bucket/patients.parquet, lazy
Notes:
lazy` mode remains Parquet-only.
delimiter` and `has_header` are only supported for CSV files.
use name` reactivates a session-local named table and restores its stored row sequence.
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
