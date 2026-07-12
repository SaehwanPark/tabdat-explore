# Request Summary: Phase 24 Read-Only Status Transparency

## Goal

Implement the next Phase 24 stabilization slice: add a read-only `status` command that makes the
current backend and active-dataset execution state visible without hidden materialization.

## Phase Fit

Phase 24 P0 product-center stabilization. This follows the merged canonical Parquet workflow slice
and is the first execution-transparency increment.

## Touched Surfaces

- `src/tabdat/models.py`: `StatusCommand` and typed `StatusResult`
- `src/tabdat/parser.py` and `src/tabdat/executor.py`: parsing and state-only dispatch
- `src/tabdat/formatter.py`, `src/tabdat/shell.py`, and help topic: terminal UX
- `tests/test_parser.py`, `tests/test_executor.py`, `tests/test_cli.py`, and `tests/test_shell.py`
- `docs/command-reference.md`, `docs/user-guide.md`, `SPEC.md`, `CHANGELOG.md`, and `_workspace/`

## Assumptions

- `DatasetInfo` and `SessionState` already contain the authoritative current source, mode, engine,
  schema, and cached row-count metadata.
- The current runtime backend is DuckDB; the status result names that backend explicitly.
- A lazy dataset's row count is `unknown` until an existing command such as `count` records it in
  session metadata.

## Non-Goals

- Adding `explain`, operation lineage, materialization reasons, retained estimation samples, or
  machine-readable output.
- Changing backend selection, lazy execution semantics, or estimator behavior.
- Adding estimator families, broader connectors, or dependency-layer changes.
