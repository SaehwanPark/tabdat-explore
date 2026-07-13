# Product Contract: Phase 24 P0 — Materialization Reason Transparency

## Request Summary

Extend the existing read-only `status` command with a deterministic explanation for the tracked
Polars lazy-to-eager fallback boundary.

## Roadmap Phase

Phase 24 P0, workstream 3: execution transparency before broader semantic and automation work.

## Command Syntax

```text
status
```

The command syntax is unchanged. `status` accepts no arguments, options, conditions, or assignment
syntax.

## Output Contract

The terminal output keeps the existing fields and inserts one field after `Materialization`:

```text
Backend: duckdb
Source: <path-or-uri|none>
Active table: <name|none>
Execution mode: <eager|lazy|none>
Lazy engine: <duckdb|polars|none>
Materialization: <materialized|deferred|none>
Last materialization reason: <polars fallback|none>
Rows: <integer|unknown|none>
Columns: <integer|none>
```

`polars fallback` means an unsupported command caused the existing Polars lazy frame to be
collected and replaced by the eager DuckDB relation. The field is session metadata for the last
successful tracked fallback, not a complete operation lineage.

## State Semantics

- A new executor, eager `use`, lazy DuckDB `use`, and lazy Polars `use` report `none`.
- `status`, `count`, and Polars-supported lazy operations do not set or change the reason.
- After an unsupported Polars-lazy command materializes successfully, `status` reports eager mode,
  materialized state, and `Last materialization reason: polars fallback`.
- A successful source load, named-table activation, or `sql ... into <table>` activation resets the
  reason to `none`.
- Failed commands do not claim a successful fallback.
- Unsupported `by ...: status` is rejected during parsing; direct unsupported `ByCommand` values
  are rejected before the materialization hook.

## Execution Semantics

- `StatusResult` carries the typed reason value; the formatter only renders that result.
- `_materialize_polars_lazy_if_needed` stages the reason after backend materialization succeeds;
  the executor commits it only after the requested command succeeds.
- `status` remains dispatched before the materialization hook and never queries the backend.
- The command remains valid in interactive, script, and `-c` execution modes.

## Examples

Before a fallback:

```text
tabdat> use data.parquet, lazy engine=polars
tabdat> status
Execution mode: lazy
Lazy engine: polars
Materialization: deferred
Last materialization reason: none
```

After an unsupported Polars-lazy command:

```text
tabdat> generate age2 = age + 1
tabdat> status
Execution mode: eager
Lazy engine: none
Materialization: materialized
Last materialization reason: polars fallback
```

## Acceptance Criteria

- [x] `StatusResult` has a typed optional fallback-reason field and the formatter renders the exact
  label/order.
- [x] New/eager/DuckDB-lazy/Polars-lazy states report `none`.
- [x] A successful unsupported Polars-lazy command reports `polars fallback` after materializing.
- [x] Successful `use` and named-table activation reset the reason; failed fallback does not set it.
- [x] `status` remains non-materializing and unsupported nested `by ...: status` remains
  state-preserving.
- [x] CLI, script, parser, shell/help, command-reference, user-guide, full tests, type/lint, and
  integrated workflow checks pass.

## Non-Goals For This Slice

- Full operation lineage, active-operation progress, broader materialization-cause taxonomy,
  retained estimation samples, machine-readable output, or explain/dry-run.
- Changes to lazy/eager behavior, backends, estimators, connectors, plugins, or exit codes.
