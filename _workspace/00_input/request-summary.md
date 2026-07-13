# Request Summary: Phase 24 Explicit Missing Predicates

## Goal

Define and verify explicit missing-value predicates without introducing backend-dependent null
coercion or broad arithmetic policy.

## Phase Fit

Phase 24 P0 language semantics. This follows the identifier, write-target, and implicit
missing-predicate contracts and gives users a stable way to select missing or nonmissing rows.

## Touched Surfaces

- `docs/language-semantics.md`: durable explicit-null syntax and policy
- `src/tabdat/models.py`, `src/tabdat/parser.py`: null-literal AST and parsing
- `src/tabdat/backend.py`: null-aware equality/inequality compilation across engines
- `tests/test_parser.py`, `tests/test_executor.py`: parser and cross-engine regressions
- `tests/test_cli.py`: user-facing explicit-missing filter output
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`

## Assumptions

- Missing values remain SQL NULL/Python None; the new `null` token is only an expression literal.
- `null` is case-insensitive when unquoted. A quoted `` `null` `` continues to identify a column
  named exactly `null`.
- Null-aware equality and inequality are expressed as `value == null` and `value != null`, with
  either operand order accepted.
- Existing keep/drop/replace true/false/missing predicate rules remain unchanged.

## Non-Goals

- Adding `is null`, `missing()`, or `nonmissing()` syntax.
- Defining implicit numeric/string coercion, null arithmetic, new commands, machine output, exit
  codes, lineage, or estimator behavior.
