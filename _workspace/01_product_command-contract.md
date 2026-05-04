# Phase 7 Lazy Execution Contract

## Request Summary

Add opt-in lazy loading for large local Parquet workflows while preserving the existing single active
dataset model.

## Roadmap Phase

Phase 7: Lazy Execution & Performance Optimization.

## Command Surface

### `use`

Syntax:

```text
use <path>
use <path>, lazy
use <path>, lazy engine=duckdb
use <path>, lazy engine=polars
```

- `use <path>` remains eager and preserves existing behavior.
- `lazy` is an explicit mode flag.
- `engine=duckdb|polars` is valid only when `lazy` is present.
- `engine=duckdb` is the default when `lazy` is present and no engine is specified.
- Local `.parquet` remains the only supported input format in this phase.

## Execution Behavior

- Eager mode creates the current active DuckDB temp table.
- Lazy mode creates a DuckDB `read_parquet(...)` scan view for the active dataset.
- Terminal commands such as `describe`, `count`, `head`, `summarize`, `tabulate`, `collapse`,
  grouped commands, SQL, and plot extraction run through the backend relation boundary.
- Session transformations preserve the active dataset model for subsequent commands.
- Load output identifies lazy sessions as `lazy=<engine>`.

## Non-Goals

- No save/write command.
- No scripting or `.do` execution.
- No non-Parquet input expansion.
- No default switch from eager to lazy.
- No full Polars-native command lowering beyond accepting and recording the lazy engine selector.

## Acceptance Criteria

- Parser tests cover valid and invalid lazy `use` syntax.
- Executor tests verify eager compatibility and lazy command composition.
- CLI smoke tests verify lazy command mode output.
- Documentation records Phase 7 as complete and notes current limitations.
- Validation passes:
  - `uv run pytest`
  - `uv run mypy`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
