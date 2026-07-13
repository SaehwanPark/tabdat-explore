# Request Summary: Phase 24 Grouped-Result Ordering Contract

## Goal

Define and verify deterministic ordering for existing grouped outputs so numeric keys are ordered
numerically, text keys lexicographically, and missing keys last across tabulate and category-count
paths.

## Phase Fit

Phase 24 P0 language semantics. This is the smallest ordering slice after identifier, missing-value,
coercion, arithmetic-result, and overwrite contracts, and it adds no new command syntax.

## Touched Surfaces

- `docs/language-semantics.md`: durable grouped-output ordering policy
- `src/tabdat/backend.py`: tabulate-wide and bar category ordering
- `tests/test_executor.py`, `tests/test_cli.py`, `tests/test_help.py`: numeric, text, missing, and
  user-visible ordering regressions
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: roadmap and handoff state

## Assumptions

- Existing grouped commands retain their current syntax and output shapes.
- `by summarize`, `by count`, `collapse`, and long-form `tabulate` order grouping dimensions in
  native scalar order with missing values last.
- Wide-form `tabulate` uses the same native order for row keys and column headers; numeric labels
  are not sorted by their display strings.
- `bar` sorts nonmissing categories by descending count, then native category order for ties; the
  missing category is always last.
- Row-preserving active-dataset order, `head`/`tail` guarantees, arbitrary SQL `order by`, and
  categorical ordering remain separate contracts.

## Non-Goals

- Adding a `sort` command or ordering syntax, changing parser grammar, defining row-order metadata,
  rewriting user SQL order, category-level ordering, exact arithmetic widths, or estimator behavior.
