# status

How to invoke:
`status`

What it does:
Show the current backend, active source, execution mode, materialization state, last tracked
materialization reason, row-count knowledge, and column count without running a data operation.

What problem it answers:
What execution state is TabDat holding before I run the next command?

Examples:
- `status`
- `use data.parquet, lazy engine=duckdb`
- `status`
- `count`
- `status`

Notes:
- `Rows: unknown` is expected for a lazy dataset before `count` or another operation records a
  current row count.
- `status` does not materialize a lazy dataset.
- `Last materialization reason: polars fallback` means an unsupported command collected a Polars
  lazy frame into the eager DuckDB boundary. The field resets after a successful `use`.
