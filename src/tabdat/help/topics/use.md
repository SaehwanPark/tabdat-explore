# use

How to invoke:
`use <path>` or `use <path>, lazy [engine=duckdb|polars]`

What it does:
Load a Parquet file or named table into the active dataset slot.

What problem it answers:
Open the data you want to inspect, transform, or model.

Examples:
- `use patients.parquet`
- `use s3://bucket/patients.parquet, lazy`

Links:
- `docs/project_proposal.md`
