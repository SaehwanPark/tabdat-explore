# Product Contract: Phase 24 P0 — Read-Only Status Transparency

## Request Summary

Expose the current execution boundary through a deterministic, read-only `status` command that
does not trigger a backend scan or lazy materialization.

## Roadmap Phase

Phase 24 P0, workstream 3: execution transparency before command-catalog expansion.

## Command Syntax

```text
status
```

`status` accepts no arguments, options, conditions, or assignment syntax.

## Output Contract

The terminal output is a stable labeled summary with these fields, in this order:

```text
Backend: duckdb
Source: <path-or-uri|none>
Active table: <name|none>
Execution mode: <eager|lazy|none>
Lazy engine: <duckdb|polars|none>
Materialization: <materialized|deferred|none>
Rows: <integer|unknown|none>
Columns: <integer|none>
```

For an eager active dataset, materialization is `materialized`; for a lazy active dataset it is
`deferred`. `Rows: unknown` reports an active lazy dataset whose row count has not been recorded.
After `count`, the executor records the live count in session metadata and `status` reports that
integer without changing the existing `count` output.

With no active dataset, backend remains `duckdb` and the remaining dataset fields are `none`.

## Product Outcome

TabDat demonstrates that it is the fastest, clearest, and most reproducible terminal workflow for
first-pass exploration of modern tabular data. Conventional statistics remain available, while
specialized integrations no longer determine the installation or product narrative of the core;
users can see the current execution boundary before choosing a potentially materializing command.

## Execution Semantics

- The parser creates a `StatusCommand` with no backend access.
- The executor builds `StatusResult` from `SessionState.active_dataset`,
  `SessionState.active_table_name`, and the fixed DuckDB backend identity.
- `status` is dispatched before the existing Polars lazy materialization hook.
- The formatter renders only the structured result; it does not inspect or count the backend.
- The command is valid in interactive, script, and `-c` execution modes.

## Examples

```text
tabdat> status
Backend: duckdb
Source: none
Active table: none
Execution mode: none
Lazy engine: none
Materialization: none
Rows: none
Columns: none
```

```text
tabdat> use data.parquet, lazy engine=duckdb
tabdat> status
Backend: duckdb
Source: data.parquet
Active table: none
Execution mode: lazy
Lazy engine: duckdb
Materialization: deferred
Rows: unknown
Columns: 4
```

## Acceptance Criteria

- [x] `parse_command("status")` returns `StatusCommand()` and invalid extra input has a command-
  level parse error.
- [x] No-active, eager, lazy DuckDB, lazy Polars, named-table, and post-`count` states render the
  contracted fields.
- [x] `status` after lazy load leaves the dataset lazy and the row count unknown; it does not invoke
  a materialization or row-count backend operation.
- [x] CLI, script, shell completion, help, and command-reference coverage exist.
- [x] Full tests, type checks, lint/format checks, and a CLI smoke flow pass.

## Non-Goals For This Slice

- Implementing `explain`, operation lineage, materialization reasons, retained estimation samples,
  machine-readable output, or stable exit-code redesign.
- Changing lazy/eager execution or adding backend implementations.
- Adding estimators, connectors, plugins, or dependency-layer changes.
