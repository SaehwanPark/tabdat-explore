# `status`

Show the current backend, active source, last successful operation, execution mode, materialization

state, last tracked materialization reason, row-count knowledge, and column count without running a

data operation.

## Syntax

```text
status
```

## Examples

```text
status
use data.parquet, lazy engine=duckdb
status
count
status
Notes:
Rows: unknown` is expected for a lazy dataset before `count` or another operation records a
current row count.
status` does not materialize a lazy dataset.
Last operation` is the previous successful command family; calling `status` does not replace it,
and a failed command leaves it unchanged.
Last materialization reason: polars fallback` means an unsupported command collected a Polars
lazy frame into the eager DuckDB boundary.
Last materialization reason: eager operation` means a successful command changed an active
DuckDB-lazy dataset to eager. The field resets after a successful `use` or named-table activation.
```

## See also

- [Command Reference Index](../command-reference/index.md)
- [User Guide](../user-guide/index.md)
- [In-App Help System](../getting-started/interactive-shell.md#in-app-help)
