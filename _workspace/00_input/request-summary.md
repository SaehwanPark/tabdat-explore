# Phase 11 Reshape Request Summary

## Goal

Continue Phase 11 data workflow primitives after the completed named-table join and append slices by
adding a narrow reshape wide/long checkpoint.

## Phase Fit

Phase 11 in `docs/dev_phase.md` covers estimation-ready data workflows, including join /
merge-style commands, append/stack, reshape wide/long, panel identifiers, script reproducibility
primitives, and narrow remote access. Join and append are already complete, so reshape is the next
data-shaping prerequisite before Phase 12 estimation substrate work.

## Touched Surfaces

- Command contract for `reshape long` and `reshape wide`.
- Parser and pydantic command models.
- Executor state transition and active dataset replacement.
- DuckDB backend materialization for wide-to-long and long-to-wide transforms.
- CLI and shell command coverage.
- Focused parser, executor/backend, CLI, and shell tests.
- SPEC, ARCHITECTURE, CHANGELOG, implementation report, QA report, and delivery summary.

## Assumptions

- Implement only local active-dataset reshape operations in this slice.
- `reshape long <stublist>, i(<id_vars>) j(<name_var>)` expects active columns named
  `<stub>_<j_value>`.
- `reshape wide <value_vars>, i(<id_vars>) j(<name_var>)` pivots long data into columns named
  `<value_var>_<j_value>`.
- Reshape results replace the active dataset and are materialized eagerly.

## Non-Goals

- No multi-table reshape, custom separators, aliases, wildcard stub discovery, type coercion
  policy, panel metadata, script variables/macros, seeding, control flow, remote access, or Phase 12
  estimation substrate work.
