# Phase 11 Reshape Command Contract

## Request Summary

Add the next Phase 11 data workflow primitive: narrow active-dataset reshape commands for
estimation-ready data preparation.

## Roadmap Phase

Phase 11: Data Workflow & Reproducibility Primitives.

## Command Syntax

```stata
reshape long <stublist>, i(<id_vars>) j(<name_var>)
reshape wide <value_vars>, i(<id_vars>) j(<name_var>)
```

Rules:

- `long` and `wide` are the only supported reshape directions.
- `i(...)` is required and must contain one or more identifier variables.
- `j(...)` is required and must contain exactly one output/input variable name.
- `reshape long` requires one or more stubs. Each stub matches active columns named
  `<stub>_<j_value>`.
- `reshape wide` requires one or more value variables. Output columns are named
  `<value_var>_<j_value>`.
- `if` clauses, assignment syntax, duplicate variables, duplicate options, and unknown options are
  rejected.

## Examples

```stata
reshape long income cost, i(id) j(year)
```

Turns `income_2020`, `income_2021`, `cost_2020`, and `cost_2021` into rows containing `id`,
`year`, `income`, and `cost`.

```stata
reshape wide income cost, i(id) j(year)
```

Turns rows containing `id`, `year`, `income`, and `cost` into one row per `id` with columns such as
`income_2020`, `income_2021`, `cost_2020`, and `cost_2021`.

## Execution Semantics

- Requires an active dataset.
- Uses DuckDB SQL over the active relation.
- Replaces the active dataset with the reshape result.
- Materializes the reshape result eagerly, including after lazy inputs.
- `reshape long` preserves id columns first, then the `j` column, then stub value columns.
- `reshape wide` preserves id columns first, then generated value columns ordered by observed
  `j` values.

## User-Facing Output

- Long success: `Reshaped long: N rows, M columns`.
- Wide success: `Reshaped wide: N rows, M columns`.

## User-Facing Errors

- Missing active dataset: `reshape requires an active dataset; run use <path> first`.
- Missing variable: `reshape unknown variable: <name>`.
- Missing long stub columns: `reshape long found no columns for stub: <stub>`.
- Incomplete long stub groups: `reshape long missing column: <stub>_<j_value>`.
- Wide output conflict: `reshape wide output column already exists: <name>`.
- Unsupported malformed syntax uses parser errors beginning with `reshape expects syntax:`.

## Non-Goals

- No custom separators, wildcard stub discovery, automatic panel metadata, file or named-table
  inputs, permissive type coercion, aliases, script macros, seeding, control flow, or remote access.

## Acceptance Criteria

- Parser tests cover valid long/wide syntax and malformed syntax/options.
- Executor/backend tests cover successful long and wide reshapes, missing active datasets, missing
  variables, missing stub columns, incomplete stub groups, and output-name conflicts.
- CLI smoke tests cover a repeated `-c` reshape workflow with deterministic output.
- Shell tests confirm `reshape` command completion.
- Documentation records the Phase 11 reshape boundary and remaining future Phase 11 work.
