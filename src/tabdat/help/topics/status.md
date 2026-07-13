# status

How to invoke:
`status`

What it does:
Show the current backend, active source, last successful operation, execution mode, materialization
state, last tracked materialization reason, row-count knowledge, and column count without running a
data operation.

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
- `Last operation` is the previous successful command family; calling `status` does not replace it,
  and a failed command leaves it unchanged.
- `Last materialization reason: polars fallback` means an unsupported command collected a Polars
  lazy frame into the eager DuckDB boundary.
- `Last materialization reason: eager operation` means a successful command changed an active
  DuckDB-lazy dataset to eager. The field resets after a successful `use` or named-table activation.
