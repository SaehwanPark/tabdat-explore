# Phase 11 Append Delivery Summary

## Summary

Implemented the second Phase 11 data workflow primitive on branch
`codex/tmp-phase11-append-stack`.

## Changed Behavior

- `append <table>` appends a session-local named table to the active dataset.
- The active dataset and appended named table must have the same column names and compatible types.
- Output column order follows the active dataset.
- Successful appends print `Appended <table>: N rows, M columns`.
- The append result replaces the active dataset for later commands.

## Validation

- `uv run pytest`
- `uv run mypy`
- `uv run ruff check .`
- `uv run ruff format --check .`

## Known Limits

- Only session-local named tables can be appended.
- `stack` is not an alias yet.
- Missing, extra, or mismatched-type columns are rejected.
- No source indicator, permissive missing-column filling, type coercion policy, file-path append,
  reshape, panel metadata, remote data access, script variables, seeding, or control flow was added
  in this slice.
