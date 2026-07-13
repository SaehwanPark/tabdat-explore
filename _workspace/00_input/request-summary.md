# Request Summary: Phase 24 Materialization-Reason Taxonomy

## Goal

Extend the existing `status` materialization reason with one additional deterministic category:
`eager operation` for a successful command that starts with a DuckDB-lazy active dataset and ends
with an eager active dataset.

## Phase Fit

Phase 24 P0 product-center stabilization. This follows the canonical workflow, status, Polars
fallback, and last-operation slices, and makes the remaining user-visible lazy-to-eager transition
explainable without introducing a backend-internal trace.

## Touched Surfaces

- `src/tabdat/executor.py` and `src/tabdat/models.py`: typed reason taxonomy and transition detection
- `src/tabdat/formatter.py`: public reason mapping
- `src/tabdat/help/topics/status.md`, `docs/command-reference.md`, and `docs/user-guide.md`
- `tests/test_executor.py` and `tests/test_cli.py`
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`

## Assumptions

- A successful transition from lazy DuckDB state to eager state is the authoritative `eager operation`
  signal for this slice.
- Polars fallback remains the more specific reason when the existing fallback hook staged it.
- New source/table activation resets the reason to `none`, as already contracted.

## Non-Goals

- A complete operation/materialization trace, timings, active progress, retained estimation samples,
  JSON/JSONL, explain/dry-run, or stable exit-code redesign.
- Changing lazy/eager semantics, backend behavior, command output beyond `status`, or adding new
  backends, estimators, connectors, plugins, or dependency layers.
