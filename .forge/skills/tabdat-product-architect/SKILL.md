---
name: tabdat-product-architect
description: Define TabDat command semantics, examples, phase fit, and acceptance criteria before implementation.
---

# TabDat Product Architect

## When to Use

- Use this skill for new or changed TabDat commands, options, command grammar, CLI output, error messages, or roadmap scope decisions.
- Use it before implementation when the request could otherwise force the coder to invent user-facing behavior.
- Do not use it for internal refactors that preserve existing command behavior.

## Required Inputs

- User request or `_workspace/00_input/request-summary.md`.
- `docs/project_proposal.md`.
- `docs/dev_phase.md`.
- Any existing command docs, tests, parser files, or CLI examples.

## Workflow

1. Place the request in the roadmap.
   - Prefer the smallest current-phase vertical slice.
   - Mark future-phase features as non-goals unless the user explicitly asks to jump ahead.
2. Define command syntax and examples.
   - Include valid forms, invalid forms, option behavior, and output shape.
3. Define data assumptions.
   - Active dataset rules, supported formats, lazy/eager expectations, and missing-column behavior.
4. Define execution semantics.
   - Say whether the command maps to DuckDB SQL, Polars, Arrow metadata, or a future abstraction.
5. Define acceptance criteria.
   - Include tests, smoke examples, and user-visible error expectations.
6. Write `_workspace/01_product_command-contract.md`.

## Outputs

- `_workspace/01_product_command-contract.md` with:
  - request summary
  - roadmap phase
  - command syntax
  - examples
  - non-goals
  - data assumptions
  - execution semantics
  - acceptance criteria
  - open questions, if any

## Validation

- Check that the command surface stays small and matches the roadmap.
- Check that every example has an expected result or error.
- Check that non-goals prevent accidental broad implementation.
- Check that implementation can proceed without making new user-facing decisions.

## References

- `references/command-language-principles.md`
