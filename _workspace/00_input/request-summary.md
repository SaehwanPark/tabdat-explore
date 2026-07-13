# Request Summary: Phase 24 Categorical Ordering Contract

## Goal

Define and verify how categorical labels are ordered and displayed by existing `tabulate` and `bar`
commands without adding category-management syntax.

## Phase Fit

Phase 24 P0 language semantics. This follows the completed grouped-result, active-row, SQL, append,
join, and reshape ordering slices and closes the remaining basic label-order boundary.

## Touched Surfaces

- `docs/language-semantics.md`: durable categorical order and missing-label policy
- `src/tabdat/help/topics/tabulate.md`, `src/tabdat/help/topics/bar.md`, `docs/command-reference.md`:
  user guidance
- `tests/test_executor.py`, `tests/test_cli.py`, `tests/test_help.py`: cross-engine native-order and
  missing-placement regressions
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`: roadmap and handoff state

## Assumptions

- Categorical labels use native scalar order: numeric values numerically, text lexicographically, and
  booleans false before true; rendered text is not used to compare numeric labels.
- `tabulate` omits missing categories by default and places them last when `missing` is requested.
- `bar` orders nonmissing categories by descending count, then native category order for ties; an
  included missing category is always last and displays as `<missing>`.
- No user-defined category levels or metadata exist in this slice; source arrival order is not a
  category-order contract.

## Non-Goals

- Adding category metadata/level syntax, recoding, sort syntax, append/join/reshape order, unordered
  SQL guarantees, or estimator behavior.
