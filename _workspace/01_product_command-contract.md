# Product Contract: Phase 24 P0 — Identifier Overwrite and Atomic Error Semantics

## Request Summary

Document and regression-test the initial cross-command write contract for generated, renamed,
replaced, and recode-generated identifiers.

## Roadmap Phase

Phase 24 P0, workstream 2: stable language semantics before broader command and estimator expansion.

## Stable Write Policy

- `generate <name> = <expression>` requires a new output identifier. Existing targets are rejected.
- `rename <old> <new>` requires an existing source and a destination that does not already exist.
- `replace <name> = <expression>` requires an existing target; it never implicitly creates a column.
- `recode ..., generate(<names>)` requires one output per input and rejects output collisions before
  changing the active dataset.
- Validation failures leave the active dataset's schema and rows unchanged.

## Error Contract

Existing command-specific errors remain the public diagnostics. The contract requires the failure
to identify the command and target/source problem; exact wording remains covered by focused tests
and may be refined only through a future language-error policy slice.

## Execution Semantics

- Validation happens before the active relation is replaced.
- A failed write command does not update the last successful operation or materialization reason.
- The policy applies in eager and supported lazy paths; no lazy/eager behavior changes are introduced.

## Acceptance Criteria

- [x] Durable language-semantics documentation covers all four write families and atomic failure.
- [x] Existing-target generate and recode-generate collisions are covered.
- [x] Rename source/destination errors and replace missing-target errors are covered.
- [x] Tests compare active schema/rows before and after representative failures.
- [x] Full tests, type/lint/format checks, and integrated workflow checks pass.

## Non-Goals For This Slice

- Identifier case/quoting grammar, missing values, coercion, arithmetic, categories, ordering,
  randomness, estimation samples, machine output, exit codes, or new commands.
