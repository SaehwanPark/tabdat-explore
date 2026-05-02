---
name: tabdat-core-implementer
description: Implement TabDat vertical slices across CLI, parser, executor, backend, and tests while preserving command contracts.
---

# TabDat Core Implementer

## When to Use

- Use this skill to implement TabDat CLI, parser, executor, backend, command, test, or packaging changes.
- Use it when a task consumes `_workspace/01_product_command-contract.md`.
- Do not use it to decide new user-facing command semantics from scratch; run Product Architect first.

## Required Inputs

- `_workspace/01_product_command-contract.md` for user-facing behavior changes.
- Current repository files and tests.
- `AGENTS.md`, `docs/project_proposal.md`, and `docs/dev_phase.md`.

## Workflow

1. Inspect the existing code and package structure before editing.
2. Identify the smallest vertical slice needed for the contract.
   - Keep CLI, parser, executor, backend, and formatting responsibilities separate.
3. Add or update focused tests before or alongside implementation.
   - Test command parsing separately from backend execution when possible.
   - Add an end-to-end smoke test for user-visible command behavior.
4. Implement using repo conventions and `uv` commands.
5. Run targeted validation.
6. Write `_workspace/02_implementation_report.md`.

## Outputs

- Code and tests required by the task.
- `_workspace/02_implementation_report.md` with:
  - contract consumed
  - files changed
  - implementation notes by boundary
  - validation commands and outcomes
  - known gaps or follow-up work

## Validation

- Run the narrowest relevant test command first.
- Run broader tests when shared parser, executor, or backend contracts change.
- If a command cannot be run because dependencies or tests do not exist yet, record that explicitly and add the missing minimal validation path when in scope.

## References

- `references/implementation-boundaries.md`
