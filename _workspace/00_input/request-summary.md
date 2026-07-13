# Request Summary: Phase 24 Last-Operation Transparency

## Goal

Extend the merged read-only `status` command with one bounded session signal: the canonical name
of the last successfully executed command. `status` itself remains read-only and does not replace
the previous operation value.

## Phase Fit

Phase 24 P0 product-center stabilization. This follows the canonical workflow, initial status, and
tracked Polars-fallback reason slices, and starts operation transparency without introducing full
lineage or progress machinery.

## Touched Surfaces

- `src/tabdat/executor.py` and `src/tabdat/models.py`: typed session/result metadata and successful
  command commit boundary
- `src/tabdat/formatter.py`: one deterministic status field
- `src/tabdat/help/topics/status.md`, `docs/command-reference.md`, and `docs/user-guide.md`
- `tests/test_executor.py`, `tests/test_cli.py`, and `tests/test_shell.py`
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`

## Assumptions

- The last operation is session metadata, not a durable operation log or lineage graph.
- Only successfully completed executor commands update it; failed commands leave the previous value.
- The canonical display name is derived from the command family, with `bayes:` represented as
  `bayes:` and ordinary command classes rendered in lowercase.

## Non-Goals

- Adding operation history, active-operation progress, timing, materialization-cause expansion,
  retained estimation samples, JSON/JSONL, explain/dry-run, or stable exit-code redesign.
- Changing command semantics, lazy/eager behavior, backends, estimators, connectors, plugins, or
  dependency layers.
