# Request Summary: Phase 24 Arithmetic Overflow Diagnostics Contract

## Goal

Report deterministic row-level counts for exact integral arithmetic overflow while preserving the
existing missing-result policy and command syntax.

## Phase Fit

Phase 24 P0 language semantics. This follows the completed exact integer-width slice and adds a narrow
user-visible diagnostic without changing arithmetic values, missingness, or command grammar.

## Touched Surfaces

- `src/tabdat/models.py`, `src/tabdat/executor.py`, `src/tabdat/formatter.py`: typed transform
  diagnostics and stable terminal output
- `src/tabdat/backend.py`: pure expression classification plus bounded overflow-row counting
- `src/tabdat/help/topics/generate.md`, `src/tabdat/help/topics/replace.md`,
  `docs/language-semantics.md`, `docs/command-reference.md`: user-facing semantics
- `tests/test_executor.py`, `tests/test_cli.py`, `tests/test_help.py`: cross-engine diagnostics and
  non-misclassification coverage
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: roadmap and handoff state

## Assumptions

- Exact integral arithmetic already uses `DECIMAL(38,0)` and turns out-of-domain values into missing;
  this slice reports the affected row count after a successful command.
- `generate`, `replace`, `keep`, and `drop` report overflow counts only for exact integral arithmetic
  evaluated by those commands. Missing operands, false/missing predicates, division by zero,
  non-finite values, and scale-bearing decimal/floating arithmetic are not integer overflow.
- A zero overflow count preserves existing transform output text; a positive count appends a stable
  `overflow rows: N` diagnostic.
- Eager, DuckDB-lazy, and Polars-lazy paths retain their existing state and fallback behavior.

## Non-Goals

- Changing overflow missingness, arbitrary precision, decimal-scale/floating diagnostics, SQL-only
  diagnostics, machine-readable output, operation lineage, new syntax, estimators, or exit codes.
