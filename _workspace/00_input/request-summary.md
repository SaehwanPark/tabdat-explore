# Request Summary: Phase 24 Identifier Spelling and Quoted Identifiers

## Goal

Define and verify exact variable spelling and backtick-quoted identifiers for command targets,
variable lists, and expression references.

## Phase Fit

Phase 24 P0 language semantics. This follows the write-target contract and makes identifier grammar
usable for real column names without changing successful behavior for existing bare identifiers.

## Touched Surfaces

- `docs/language-semantics.md`: durable identifier spelling and quoting policy
- `src/tabdat/parser.py`: quoted identifier tokenization and keyword boundaries
- `tests/test_parser.py` and `tests/test_executor.py`: parser/backend boundary regressions
- `SPEC.md`, `CHANGELOG.md`, and `_workspace/`

## Assumptions

- Existing command errors are the public policy; this slice does not redesign error wording.
- Bare identifiers already resolve by exact spelling; this slice makes that behavior explicit and
  adds backtick quoting without case folding.
- Backtick quoting is limited to variable positions and expression references; SQL retains its own
  parser and quoting semantics.

## Non-Goals

- Adding commands, missingness or coercion policy, machine output, exit codes, lineage, or estimator
  behavior.
