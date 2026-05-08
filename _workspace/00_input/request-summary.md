# Phase 11 Request Summary

## Goal

Move from the completed Phase 10 execution/state foundations into the first Phase 11 data workflow
primitive: named-table joins.

## Requested Workflow

- Begin on a temporary branch.
- Commit meaningful checkpoints during implementation.
- Document completed work carefully.
- Open a PR and mark it ready for review when done.

## Phase Fit

Phase 11 in `docs/dev_phase.md` covers estimation-ready data workflows, including join /
merge-style commands for multi-table workflows. The first slice should build directly on the Phase
10 session-local named table registry.

## Touched Surfaces

- Parser and command models for `join <table> on <keylist>` syntax.
- Executor session state and active dataset replacement after a join.
- DuckDB backend named-table joins, key validation, and collision suffixing.
- Formatter output, focused parser/executor/CLI tests, SDD docs, and handoff artifacts.

## Assumptions

- Implement `join`, not a Stata-compatible `merge` command.
- Right-side inputs are existing session-local named tables only.
- Only same-name equality keys are supported in this slice.
- Supported join kinds are `inner` and `left`; `inner` is the default.
- Append/stack, reshape, panel metadata, remote data access, script variables, seeding, and control
  flow remain later Phase 11 slices.
