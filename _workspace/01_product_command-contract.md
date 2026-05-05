# Phase 10 Execution And State Foundations Contract

## Roadmap Phase

Phase 10: Execution & State Foundations.

## Named Table Registry

Syntax:

```text
sql <select-or-with-query> into <table>
use <table>
```

- `sql ... into <table>` evaluates a result-producing query over the current active dataset exposed
  as `active`.
- The result is stored in a session-local named table registry under `<table>`.
- The created table becomes the active dataset immediately.
- Previously active named tables remain registered and can be reactivated with `use <table>`.
- `use <path>` continues to load local `.parquet` files and registers the loaded dataset as
  `active`.
- `use <table>` is only table activation when `<table>` matches an existing registered table name
  and does not resolve as a local file path.
- Valid table names use identifier syntax: letters, numbers, and underscores, starting with a
  letter or underscore.
- Reserved names are rejected for user-created tables: `active` and names beginning with
  `__tabdat_`.

## Output

- `sql ... into <table>` prints `Created <table>: N rows, M columns`.
- `use <table>` prints `Activated: <table> (N rows, M columns)`.
- Existing `use <path>` output remains `Loaded: <path> (...)`.
- Existing command error formatting remains `Error: <message>`.

## Execution Semantics

- Named tables are session-local DuckDB relations and are not written to disk unless `save` or
  `export` is run.
- The current active dataset remains the default target for inspection, transformation, SQL, plots,
  and persistence commands.
- Transformations replace the active relation and update active metadata.
- SQL can reference the current active dataset through `active`; arbitrary multi-table SQL over the
  registry is deferred.
- Lazy `use <path>, lazy` still creates a DuckDB scan view and reports an unknown row count until a
  live count or materializing command runs.
- Most transformations materialize the active relation after the first lazy transformation.
- `engine=polars` remains experimental metadata; command execution still uses the DuckDB relation
  boundary.

## Specific Execution Errors

- Missing active dataset uses `NoActiveDatasetError`.
- Missing columns use `UnknownVariableError`.
- Type-specific command failures use `TypeMismatchExecutionError`.
- Missing named tables use `UnknownTableError`.
- Reserved or invalid table names use `ReservedNameError`.
- Backend failures use `BackendExecutionError`.
- All subclasses inherit from `ExecutionError`, preserving current CLI behavior.

## Non-Goals

- No join, append, reshape, or broad multi-table workflow commands.
- No `use <table>, options`; named table activation accepts no `use` options.
- No persistent named table catalog across sessions.
- No Polars-native execution lowering.
- No plugin, R integration, or analytical command expansion.

## Acceptance Criteria

- Parser tests cover `use <table>` activation syntax and still cover valid/invalid `sql into`
  names.
- Executor/backend tests cover named table creation, activation, active metadata updates, and
  specific error subclasses.
- CLI tests cover repeated `-c` named-table workflows and deterministic output.
- Documentation states the registry is session-local and that `active` remains the primary command
  target.
- Full validation passes:
  - `uv run pytest`
  - `uv run mypy`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
