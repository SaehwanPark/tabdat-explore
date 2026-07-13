# Request Summary: Phase 24 Identifier Overwrite and Atomic Error Semantics

## Goal

Define and verify the first stable cross-command write policy for `generate`, `rename`, `replace`,
and `recode ... generate(...)`: explicit identifier target rules and no active-dataset mutation on
validation failure.

## Phase Fit

Phase 24 P0 language semantics. This follows the execution-transparency sequence and starts the
roadmap's cross-command semantic contract without changing successful command behavior.

## Touched Surfaces

- `docs/language-semantics.md` and `docs/user-guide.md`: durable write/atomicity policy
- `tests/test_executor.py`: collision, target, and schema-preservation regressions
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`

## Assumptions

- Existing command errors are the public policy; this slice documents and hardens them rather than
  redesigning error wording.
- Validation failures are atomic at the active-dataset boundary: schema, rows, execution metadata,
  and current active table remain unchanged.
- Identifier case, quoting, missing-value coercion, and ordering semantics remain separate slices.

## Non-Goals

- Adding commands, changing successful transformations, broad identifier grammar, missingness or
  coercion policy, machine output, exit codes, lineage, or estimator behavior.
