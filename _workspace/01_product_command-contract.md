# Product Contract: Phase 24 P0 — Last-Operation Transparency

## Request Summary

Extend the read-only `status` command with the canonical name of the last successfully executed
executor command.

## Roadmap Phase

Phase 24 P0, workstream 3: execution transparency before broader semantic and automation work.

## Command Syntax

```text
status
```

The command syntax is unchanged. `status` accepts no arguments, options, conditions, or assignment
syntax.

## Output Contract

The terminal output keeps the current fields and inserts one session field after `Active table`:

```text
Backend: duckdb
Source: <path-or-uri|none>
Active table: <name|none>
Last operation: <canonical-command-name|none>
Execution mode: <eager|lazy|none>
Lazy engine: <duckdb|polars|none>
Materialization: <materialized|deferred|none>
Last materialization reason: <polars fallback|none>
Rows: <integer|unknown|none>
Columns: <integer|none>
```

Canonical names are lower-case command families (`use`, `count`, `generate`, `sql`, and so on);
the Bayesian prefix is displayed as `bayes:`. The value is not a history and does not include
arguments, paths, timings, or nested operation details.

## State Semantics

- A new executor reports `Last operation: none`.
- A successfully completed command updates the field to its canonical command name.
- `status` does not update the field; repeated status calls report the prior operation.
- A failed command leaves the prior value unchanged, even if an earlier materialization boundary
  has already changed the active execution mode.
- Interactive, script, and `-c` execution use the same executor state transition.
- Existing materialization-reason behavior is unchanged.

## Execution Semantics

- `StatusResult` carries the optional last-operation value; the formatter renders only that result.
- The public executor wrapper commits the operation only after the command returns successfully,
  using the same success boundary that protects materialization-reason metadata.
- The command remains dispatched before lazy materialization and never queries the backend.

## Examples

```text
tabdat> use data.parquet, lazy engine=duckdb
tabdat> status
Active table: none
Last operation: use
Execution mode: lazy
...
tabdat> status
Active table: none
Last operation: use
```

```text
tabdat> count
Last operation: count
```

## Acceptance Criteria

- [x] `StatusResult` has an optional typed last-operation field and the formatter renders the exact
  label/order.
- [x] Successful representative commands update the canonical name; `status` does not.
- [x] Failed commands leave the prior operation unchanged.
- [x] No-active, eager, lazy, named-table, and post-count status states retain the correct
  last-operation value.
- [x] CLI, script, help, command-reference, user-guide, full tests, type/lint, and integrated
  workflow checks pass.

## Non-Goals For This Slice

- Full operation lineage/history, active-operation progress, timings, broader materialization
  taxonomy, retained estimation samples, machine-readable output, or explain/dry-run.
- Changes to lazy/eager behavior, backends, estimators, connectors, plugins, or exit codes.
