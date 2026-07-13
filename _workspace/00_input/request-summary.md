# Request Summary: Phase 24 Missing Predicate Semantics

## Goal

Define and verify missing-value behavior for row predicates and existing aggregate/profiling commands.

## Phase Fit

Phase 24 P0 language semantics. This follows the identifier and write-target contracts and gives
`keep if`, `drop if`, and `replace if` a consistent cross-engine missing-predicate policy.

## Touched Surfaces

- `docs/language-semantics.md`: durable missing-value and predicate policy
- `src/tabdat/backend.py`: eager/lazy filter predicate null handling
- `tests/test_executor.py`: cross-engine predicate and aggregate regressions
- `tests/test_cli.py`: user-facing missing-filter output
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`

## Assumptions

- Existing command errors and parser syntax are the public policy; this slice does not add missing
  predicates or null literals.
- Missing values are existing SQL NULL/Python None values; this slice defines how current commands
  handle them rather than adding a sentinel type.
- Aggregate and profiling output already exposes missingness; this slice documents and regression-tests
  that behavior while changing only the incorrect drop-if null handling.

## Non-Goals

- Adding commands or missing predicates, coercion/arithmetic policy, machine output, exit codes,
  lineage, or estimator behavior.
