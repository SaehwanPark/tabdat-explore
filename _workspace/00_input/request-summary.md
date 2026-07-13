# Request Summary: Phase 24 Exact Integer Arithmetic Contract

## Goal

Define and verify exact result widths and deterministic overflow behavior for existing integral
arithmetic expressions without adding command syntax.

## Phase Fit

Phase 24 P0 language semantics. This follows the completed identifier, missingness, coercion,
arithmetic-result, ordering, and categorical-ordering slices and closes the bounded integer-width
boundary before broader numeric policy.

## Touched Surfaces

- `docs/language-semantics.md`, `src/tabdat/help/topics/generate.md`,
  `src/tabdat/help/topics/replace.md`: exact integer result and overflow policy
- `src/tabdat/backend.py`: typed arithmetic compilation across DuckDB and Polars validation
- `tests/test_executor.py`, `tests/test_cli.py`, `tests/test_help.py`: cross-engine exactness and
  user-visible regression coverage
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: roadmap and handoff state

## Assumptions

- Integral `+`, `-`, `*`, and unary minus results use `DECIMAL(38,0)` as the bounded exact domain.
- Values within that domain remain exact; values outside it become missing for the affected row
  rather than wrapping or aborting the entire row-preserving transformation.
- Real division, floating arithmetic, decimal-scale arithmetic, and existing invalid-function and
  non-finite policies remain unchanged.
- Existing `generate`, `replace`, and predicate syntax is reused; no new arithmetic commands or
  options are introduced.

## Non-Goals

- Stable overflow error/warning output, arbitrary-precision arithmetic, decimal-scale/precision
  redesign, float-width guarantees, new operators/functions, estimator behavior, or execution
  lineage.
