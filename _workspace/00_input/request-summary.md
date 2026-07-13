# Request Summary: Phase 24 Expression Coercion Contract

## Goal

Define and verify expression-domain compatibility so numeric/string mixing cannot diverge between
DuckDB and Polars or silently change replacement-column types.

## Phase Fit

Phase 24 P0 language semantics. This follows the identifier, write-target, and missing-value
contracts and makes existing expression syntax predictable before broader arithmetic expansion.

## Touched Surfaces

- `docs/language-semantics.md`: durable expression-domain and coercion policy
- `src/tabdat/backend.py`: expression-domain validation and target compatibility
- `src/tabdat/executor.py`: predicate validation before lazy fallback
- `tests/test_executor.py`, `tests/test_cli.py`: cross-engine and user-facing regressions
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`
  - record the stable contract and bounded follow-up scope

## Assumptions

- Numeric columns and numeric literals share one numeric domain; integer/float widening remains
  backend-native within that domain.
- String values compare only with string values. Numeric/string mixing is rejected, never parsed or
  stringified implicitly.
- Row conditions must be boolean or the existing explicit missing literal; numeric/string truthiness
  is not inferred.
- `replace` preserves the target's scalar domain, allowing null or same-domain expressions only.

## Non-Goals

- Adding new expression syntax, categorical conversion, string concatenation, new commands, machine
  output, exit codes, lineage, or estimator behavior.
