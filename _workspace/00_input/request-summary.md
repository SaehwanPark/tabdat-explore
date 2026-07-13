# Request Summary: Phase 24 Materialization Reason Transparency

## Goal

Extend the merged read-only `status` command with one bounded execution-transparency signal: the
last tracked reason a Polars lazy relation crossed into the eager DuckDB boundary.

## Phase Fit

Phase 24 P0 product-center stabilization. This follows the merged canonical workflow and initial
status slice, and makes the existing lazy fallback boundary explainable without adding lineage or
machine output.

## Touched Surfaces

- `src/tabdat/executor.py` and `src/tabdat/models.py`: typed session/result metadata
- `src/tabdat/formatter.py`: one deterministic status field
- `src/tabdat/help/topics/status.md`, `docs/command-reference.md`, and `docs/user-guide.md`
- `tests/test_executor.py`, `tests/test_cli.py`, `tests/test_parser.py`, and `tests/test_shell.py`
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`

## Assumptions

- The existing `_materialize_polars_lazy_if_needed` hook is the authoritative tracked Polars
  fallback boundary.
- A reason is session metadata describing the last successful tracked fallback, not full operation
  lineage.
- The current backend remains DuckDB and the fallback reason is the literal `polars fallback`.

## Non-Goals

- Adding operation lineage, current-operation progress, retained estimation samples, JSON/JSONL,
  explain/dry-run, or stable exit-code redesign.
- Modeling every eager materialization path or changing lazy/eager semantics.
- Adding estimator families, connectors, plugins, or dependency-layer changes.
