# Phase 11 Panel Metadata Command Contract

## Request Summary

Add the next unfinished Phase 11 data workflow primitive: session-local panel identifier metadata
for estimation-ready datasets.

## Roadmap Phase

Phase 11: Data Workflow & Reproducibility Primitives.

## Command Syntax

```stata
panel <id_var> <time_var>
panel
panel clear
```

Rules:

- `panel <id_var> <time_var>` records the active dataset's panel identifier and time variable.
- `panel` reports the active dataset's current panel metadata.
- `panel clear` removes panel metadata from the active dataset.
- `panel` forms do not accept `if` clauses, assignment syntax, comma options, or extra arguments.
- `<id_var>` and `<time_var>` must be distinct valid variable names.

## Examples

```stata
panel firm_id year
panel
panel clear
```

## Execution Semantics

- Requires an active dataset for every `panel` form.
- Validates both variables exist in the active dataset.
- Rejects missing values in either panel variable.
- Rejects duplicate `(id_var, time_var)` pairs.
- Stores metadata in session state only. `save` and `export` remain data-only Parquet persistence.
- `use <path>` starts with no panel metadata.
- `use <table>` restores panel metadata from the named table snapshot.
- `panel` updates the active dataset and active named-table snapshot when applicable.
- Row filters preserve panel metadata.
- `rename` updates metadata if renaming the id or time variable.
- `generate` preserves metadata.
- `replace` preserves metadata and revalidates if replacing the id or time variable.
- `keep`, `drop`, and `select` preserve metadata only when both panel variables remain; otherwise
  they clear it.
- `join`, `append`, `reshape`, `collapse`, and `sql ... into` clear panel metadata conservatively.

## User-Facing Output

- Set: `Panel set: id=<id_var>, time=<time_var>`.
- Report: `Panel: id=<id_var>, time=<time_var>`.
- No panel: `Panel: none`.
- Clear: `Panel cleared`.

## User-Facing Errors

- Missing active dataset: `panel requires an active dataset; run use <path> first`.
- Missing variable: `panel unknown variable: <name>`.
- Missing values: `panel variables cannot contain missing values: <name>`.
- Duplicate keys: `panel id/time pairs must be unique`.

## Non-Goals

- No `xtset` compatibility alias.
- No durable metadata persistence.
- No panel-balancedness diagnostics.
- No estimation commands.
- No script variables/macros, seeding, control flow, remote access, or Phase 12 estimation
  substrate work.

## Acceptance Criteria

- Parser tests cover valid report/set/clear syntax and malformed syntax/options.
- Executor/backend tests cover successful set/report/clear, missing active data, unknown variables,
  missing values, duplicate pairs, metadata preservation, and conservative clearing.
- CLI smoke tests cover a repeated `-c` panel workflow with deterministic output.
- Shell tests confirm `panel` command completion and active column completions.
- Documentation records the Phase 11 panel boundary and remaining future Phase 11 work.
