---
name: tabdat-orchestrator
description: Coordinate TabDat-Explore development tasks through command contracts, implementation reports, QA review, and deterministic handoffs.
---

# TabDat Orchestrator

## When to Use

- Use this skill for TabDat-Explore feature development, command-language design, implementation planning, or multi-surface changes.
- Use it when a task may touch product semantics, parser behavior, executor contracts, backend data handling, CLI output, tests, or docs.
- Do not use it for trivial repository questions that can be answered by reading one file.

## Required Inputs

- User request or issue.
- Current repository state.
- `AGENTS.md`, `docs/project_proposal.md`, and `docs/dev_phase.md`.
- Any existing `_workspace/` artifacts for the same task.

## Workflow

1. Capture the request in `_workspace/00_input/request-summary.md`.
   - Identify goal, phase fit, touched surfaces, assumptions, and non-goals.
2. Decide whether the Product Architect phase is needed.
   - Required for new commands, changed syntax, output behavior, or user-facing errors.
   - Optional for mechanical refactors that do not affect behavior.
3. Produce or update `_workspace/01_product_command-contract.md`.
   - Use `.agents/skills/tabdat-product-architect/SKILL.md` for command semantics.
4. Implement the smallest vertical slice that satisfies the contract.
   - Use `.agents/skills/tabdat-core-implementer/SKILL.md`.
   - Preserve parser, executor, backend, and CLI boundaries.
5. Run QA after meaningful implementation.
   - Use `.agents/skills/tabdat-qa-reviewer/SKILL.md`.
   - Write `_workspace/03_qa_report.md` with `pass`, `fix`, or `redo`.
6. Synthesize delivery in `_workspace/final/tabdat-delivery-summary.md`.
   - Include changed files, validation commands, known limits, and next useful work.

## Outputs

- `_workspace/00_input/request-summary.md`
- `_workspace/01_product_command-contract.md` when user-facing behavior is involved
- `_workspace/02_implementation_report.md`
- `_workspace/03_qa_report.md`
- `_workspace/final/tabdat-delivery-summary.md`
- Code, tests, and docs required by the request

## Delegation Rules

- Default to one main agent for early-stage vertical slices.
- Spawn workers only for bounded independent surfaces after the command contract exists.
- Give each worker disjoint ownership and remind them not to revert others' edits.
- The orchestrator owns final synthesis and conflict resolution.

## Failure Policy

- If product semantics are unclear, write the smallest supported assumption into the command contract before implementation.
- If implementation discovers the contract is technically infeasible, update `_workspace/02_implementation_report.md` and return to the Product Architect phase.
- If QA returns `fix`, apply targeted repairs and rerun the relevant checks once.
- If QA returns `redo`, restart from the phase named by the QA report.

## Validation

- Confirm all referenced paths exist.
- Confirm every changed user-facing behavior has a command contract entry.
- Confirm implementation reports exact commands run.
- Confirm QA compares both sides of touched boundaries, not just file presence.

## References

- `docs/harness/tabdat/team-spec.md`
- `.agents/skills/tabdat-product-architect/SKILL.md`
- `.agents/skills/tabdat-core-implementer/SKILL.md`
- `.agents/skills/tabdat-qa-reviewer/SKILL.md`
