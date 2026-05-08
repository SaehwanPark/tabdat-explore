# Phase 11 Implementation Report

## Summary

Implemented the first Phase 11 data workflow primitive on branch
`codex/tmp-phase11-join-merge`.

## Implemented Behavior

- Added `join <table> on <keylist>` command parsing.
- Added `how=inner|left`, defaulting to `inner`.
- Added `suffix(<suffix>)`, defaulting to `_right`, for right-side non-key column collisions.
- Joined the active dataset with an existing session-local named table.
- Replaced the active dataset with the materialized join result.
- Preserved named tables as session-local inputs that are not mutated by joins.
- Added deterministic left-row ordering for joined results.

## Files Changed

- `src/tabdat/models.py`
- `src/tabdat/parser.py`
- `src/tabdat/executor.py`
- `src/tabdat/backend.py`
- focused parser, executor/backend, and CLI tests
- `SPEC.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, and workspace artifacts

## Validation

- `uv run pytest tests/test_parser.py tests/test_executor.py tests/test_cli.py`
- `uv run mypy`
- `uv run ruff check .`

Final full validation is recorded in the delivery summary.

## Known Limits

- Only same-name equality keys are supported.
- Only `inner` and `left` joins are supported.
- Right-side inputs must be session-local named tables.
- No `_merge` indicator, cardinality validation, append/stack, reshape, panel metadata, remote data
  access, script variables, seeding, or control flow was added in this slice.
