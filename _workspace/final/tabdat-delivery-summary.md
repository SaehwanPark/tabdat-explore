# Phase 11 Delivery Summary

## Summary

Implemented the first Phase 11 data workflow primitive on branch
`codex/tmp-phase11-join-merge`.

## Changed Behavior

- `join <table> on <keylist>` joins the active dataset to a session-local named table.
- `how=inner|left` selects the join kind, with `inner` as the default.
- `suffix(<suffix>)` controls right-side non-key column collision names, defaulting to `_right`.
- Successful joins print `Joined <table>: N rows, M columns`.
- The join result replaces the active dataset for later commands.

## Validation

- `uv run pytest`
- `uv run mypy`
- `uv run ruff check .`
- `uv run ruff format --check .`

## Known Limits

- Only same-name equality keys are supported.
- Only session-local named tables can be right-side join inputs.
- No append/stack, reshape, panel metadata, remote data access, script variables, seeding, or
  control flow was added in this slice.
