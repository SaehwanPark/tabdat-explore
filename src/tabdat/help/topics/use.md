# use

How to invoke:
`use <path>` or `use <path>, lazy [engine=duckdb|polars]`
`use <path>, delimiter(<char>) has_header(true|false)`

What it does:
Load a Parquet, Stata `.dta`, CSV, Feather, or Arrow file, or named table into the active dataset slot.

What problem it answers:
Open the data you want to inspect, transform, or model.

Examples:
- `use patients.parquet`
- `use patients.dta`
- `use survey.csv, delimiter(",") has_header(true)`
- `use data.feather`
- `use https://example.com/patients.dta`
- `use s3://bucket/patients.parquet, lazy`

Notes:
- `lazy` mode remains Parquet-only.
- `delimiter` and `has_header` are only supported for CSV files.
- `use name` reactivates a session-local named table and restores its stored row sequence.

Links:
- `docs/project_proposal.md`
