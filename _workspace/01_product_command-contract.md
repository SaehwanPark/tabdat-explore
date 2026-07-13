# Product Contract: Phase 24 P0 — Materialization-Reason Taxonomy

## Request Summary

Extend `status` with a deterministic `eager operation` reason for successful DuckDB-lazy to eager
command transitions, while preserving the existing `polars fallback` reason.

## Roadmap Phase

Phase 24 P0, workstream 3: execution transparency before broader semantic and automation work.

## Command Syntax

```text
status
```

The command syntax is unchanged. `status` accepts no arguments, options, conditions, or assignment
syntax.

## Output Contract

The status field remains in the existing position and expands its public taxonomy:

```text
Last materialization reason: <polars fallback|eager operation|none>
```

`polars fallback` means the existing Polars lazy frame was collected by the fallback hook.
`eager operation` means a successful command began with an active DuckDB-lazy dataset and ended
with an eager active dataset, outside the more-specific Polars fallback path. `none` means no
tracked reason is attached to the current session state.

## State Semantics

- A new session, successful source load, and named-table/`sql ... into` activation report `none`.
- DuckDB-lazy `status`, `count`, and other operations that preserve lazy state do not set a new
  reason.
- A successful DuckDB-lazy to eager command transition reports `eager operation`.
- A successful Polars fallback continues to report `polars fallback`, taking precedence over the
  generic eager transition.
- Failed commands do not commit a new reason; the active backend state may still reflect any
  physical transition that occurred before the failure.
- Existing last-operation behavior is unchanged.

## Execution Semantics

- `StatusResult` carries an optional typed reason value; the formatter maps it to exact public text.
- The executor compares the active dataset execution mode before and after a successful command.
- The existing success-only pending metadata boundary commits the specific reason after command
  completion, with reset operations taking precedence.
- `status` remains dispatched before lazy materialization and never queries the backend.

## Examples

```text
tabdat> use data.parquet, lazy engine=duckdb
tabdat> generate age2 = age + 1
tabdat> status
Execution mode: eager
Materialization: materialized
Last materialization reason: eager operation
```

```text
tabdat> use data.parquet, lazy engine=polars
tabdat> generate age2 = age + 1
tabdat> status
Last materialization reason: polars fallback
```

## Acceptance Criteria

- [x] The typed reason taxonomy includes `polars_fallback`, `eager_operation`, and `none`.
- [x] A successful DuckDB-lazy to eager command reports `eager operation`.
- [x] A successful Polars fallback still reports `polars fallback`.
- [x] Source/table activation resets the reason and status/count preserve existing semantics.
- [x] Failed commands do not commit a new reason.
- [x] CLI, script, help, command-reference, user-guide, full tests, type/lint, and integrated
  workflow checks pass.

## Non-Goals For This Slice

- Full operation lineage/history, active-operation progress, backend-internal traces, timings,
  retained estimation samples, machine-readable output, or explain/dry-run.
- Changes to lazy/eager behavior, backends, estimators, connectors, plugins, or exit codes.
