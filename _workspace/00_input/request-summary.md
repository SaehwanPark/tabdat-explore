# Phase 11 Append/Stack Request Summary

## Goal

Continue Phase 11 data workflow primitives after the completed same-name equality join slice by
adding a narrow append/stack checkpoint.

## Requested Workflow

- Begin on a temporary branch.
- Commit meaningful checkpoints during implementation.
- Document completed work carefully.
- Open a PR and mark it ready for review when done.

## Phase Fit

Phase 11 in `docs/dev_phase.md` covers estimation-ready data workflows, including join /
merge-style commands, append/stack, reshape, panel identifiers, script reproducibility primitives,
and narrow remote access. Phase 11 has already started with named-table joins, and append/stack is
the next selected unfinished primitive.

## Touched Surfaces

- Parser and command models for `append <table>` syntax.
- Executor session state and active dataset replacement after append.
- DuckDB backend named-table vertical stacking with schema validation.
- Formatter output through existing transform results.
- Focused parser, executor/backend, and CLI tests.
- SDD and workspace documentation.

## Assumptions

- Implement `append <table>` first, not a broader `stack` alias.
- Append inputs are session-local named tables created by `sql ... into <table>`.
- Appended datasets must have the same column names and compatible DuckDB types.
- Column order follows the active dataset.
- Reshape, panel metadata, remote data access, script variables, seeding, and control flow remain
  later Phase 11 slices.

## Non-Goals

- No permissive missing-column filling, source indicator, type coercion policy, file-path append,
  persistent table catalog, reshape, panel metadata, remote access, or script-level primitives.
