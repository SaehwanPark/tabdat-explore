# Phase 4 SQL Command Contract

## Request Summary

Add SQL integration as an escape hatch over the active dataset. `into <table>` updates the active
dataset with the SQL result.

## Roadmap Phase

Phase 4: SQL Integration.

## Syntax

```text
sql <select-or-with-query>
sql <select-or-with-query> into <table>
sql """<select-or-with-query>"""
sql """<select-or-with-query>""" into <table>
```

## Semantics

- `active` is a DuckDB view over the current active dataset.
- SQL without `into` returns a formatted table and does not change active state.
- SQL with `into <table>` replaces the active dataset with the query result.
- The `into` table name appears in output: `Created <table>: <rows> rows, <columns> columns`.
- `use` remains path-only.
- SQL is limited to result-producing `select` or `with` queries.
- `into` names must be identifiers and cannot be `active` or internal `__tabdat_*` names.

## Error Behavior

- `sql` requires an active dataset.
- Empty SQL, unterminated triple quotes, malformed `into`, and invalid table names are parse errors.
- Unsupported SQL statement types and DuckDB failures are user-facing execution errors.

## Acceptance Criteria

- Parser tests cover valid single-line, multiline, and `into` SQL forms plus malformed forms.
- Executor/backend tests cover active SQL queries, `into` replacement, post-`into` active inspection,
  missing active dataset, unsupported statements, and invalid SQL.
- CLI smoke test covers a Phase 4 SQL flow.
- Validation passes:
  - `uv run pytest`
  - `uv run mypy src tests`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
