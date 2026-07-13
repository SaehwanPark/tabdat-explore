# Request Summary: Phase 24 Arithmetic Result Contract

## Goal

Define and verify arithmetic result behavior so missing values, zero denominators, invalid numeric
function domains, and computed non-finite values cannot diverge between DuckDB and Polars.

## Phase Fit

Phase 24 P0 language semantics. This follows the identifier, write-target, missing-value, and
expression-coercion contracts and makes existing arithmetic syntax predictable before broader
command and estimator expansion.

## Touched Surfaces

- `docs/language-semantics.md`: durable arithmetic result and non-finite-value policy
- `src/tabdat/backend.py`: safe numeric expression compilation for DuckDB and Polars
- `tests/test_executor.py`, `tests/test_cli.py`: cross-engine and user-facing regressions
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`
  - record the stable contract and bounded follow-up scope

## Assumptions

- Numeric expression nodes return numeric values or missing values; exact storage widening remains
  backend-native within the existing numeric domain.
- Any missing operand propagates to a missing arithmetic/function result. The explicit `null`
  literal remains subject to its existing comparison-only rule.
- Division by zero and invalid `sqrt`, `ln`, or `log` domains produce missing values for the
  affected rows rather than infinity, NaN, or a backend error.
- Computed NaN and infinity from supported arithmetic or numeric functions are normalized to
  missing. Direct source values are not rewritten merely by being read.
- Subtraction and unary minus on unsigned numeric columns are rejected before execution so
  underflow and signedness behavior cannot diverge between backends.

## Non-Goals

- Adding new expression syntax, categorical conversion, string concatenation, exact arithmetic
  storage-width guarantees, overflow reporting, new commands, machine output, exit codes, lineage,
  or estimator behavior.
