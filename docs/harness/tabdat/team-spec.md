# TabDat Development Harness Team Spec

## Domain Summary

TabDat-Explore is an early-stage Python CLI for exploratory analysis of tabular data. Its durable product direction is documented in `docs/project_proposal.md` and `docs/dev_phase.md`: build a Stata-inspired but not Stata-compatible command workflow over modern data infrastructure, starting with a vertical slice that can load data and run a few reliable EDA commands.

The harness is optimized for development tasks where product semantics, parser/executor boundaries, and validation can drift if they are handled only in transient chat. It preserves decisions in `_workspace/` before code changes and keeps QA focused on cross-boundary coherence.

## Task Inventory

Primary reusable task types:

- define or revise command semantics, options, examples, and error behavior
- design a vertical implementation slice across CLI, parser, executor, and backend
- implement parser, command, backend, or CLI UX features without expanding scope prematurely
- add tests and smoke checks for command behavior
- review boundary coherence between docs, parser AST, executor contracts, backend results, and CLI output

Out of scope for this harness:

- autonomous benchmark or experiment loops unless a future request defines a fixed metric and immutable evaluation surface
- broad product marketing or landing-page work
- advanced statistics, plugins, or R integration before the core CLI workflow is stable

## Reuse Notes

Existing durable sources:

- `docs/project_proposal.md` for product purpose, target users, command examples, stack direction, and UX expectations
- `docs/dev_phase.md` for phased development order and success criteria
- `pyproject.toml` for Python and packaging assumptions
- `AGENTS.md` for repo-wide guidance loaded on every task

## Architecture Pattern

Chosen pattern: **Pipeline + Producer-Reviewer**.

The default flow is sequential because implementation should consume a product command contract before code changes, and QA should compare the produced behavior against that contract. Producer-reviewer is added only at the validation edge because parser, executor, backend, and CLI output can each look correct while disagreeing at their boundaries.

Parallel workers are optional and bounded. Use them only after `_workspace/01_product_command-contract.md` exists and the slices are independent, such as implementing separate commands with disjoint parser and executor ownership.

## Roles

| Role | Responsibility | Skill | Writes |
| --- | --- | --- | --- |
| Orchestrator | route the task, preserve handoffs, enforce phase order, synthesize delivery | `.agents/skills/tabdat-orchestrator/SKILL.md` | `_workspace/00_input/request-summary.md`, `_workspace/final/tabdat-delivery-summary.md` |
| Product Architect | define command semantics, UX examples, phase fit, and acceptance criteria | `.agents/skills/tabdat-product-architect/SKILL.md` | `_workspace/01_product_command-contract.md` |
| Core Implementer | implement the agreed vertical slice and tests using repo conventions | `.agents/skills/tabdat-core-implementer/SKILL.md` | `_workspace/02_implementation_report.md` |
| QA Reviewer | verify cross-boundary coherence and validation evidence | `.agents/skills/tabdat-qa-reviewer/SKILL.md` | `_workspace/03_qa_report.md` |

## Phase Order

### Phase 0: Request Capture

- Inputs: user request, current repository, `AGENTS.md`, project docs
- Actions: summarize goal, constraints, touched surfaces, and assumed phase
- Output: `_workspace/00_input/request-summary.md`
- Completion criteria: another agent can understand the requested outcome without rereading the entire chat

### Phase 1: Command Contract

- Inputs: request summary, project proposal, roadmap
- Actions: define user-facing syntax, examples, non-goals, data assumptions, error cases, and acceptance criteria
- Output: `_workspace/01_product_command-contract.md`
- Completion criteria: implementation can proceed without inventing command semantics

### Phase 2: Implementation

- Inputs: command contract and current code
- Actions: inspect existing structure, choose the smallest vertical slice, implement, and add focused tests
- Output: code changes plus `_workspace/02_implementation_report.md`
- Completion criteria: code follows the contract and records exact validation commands

### Phase 3: QA Review

- Inputs: original request, command contract, implementation report, changed files, test output
- Actions: compare docs to command contract, parser to executor, executor to backend, and CLI output to examples
- Output: `_workspace/03_qa_report.md`
- Completion criteria: report marks `pass`, `fix`, or `redo` with concrete evidence

### Phase 4: Delivery Synthesis

- Inputs: all prior handoffs and final repository state
- Actions: summarize changes, validation, residual risks, and follow-up work
- Output: `_workspace/final/tabdat-delivery-summary.md`
- Completion criteria: final response can cite what changed and how it was checked

## Handoff Files

| From | To | File | Purpose |
| --- | --- | --- | --- |
| Orchestrator | Product Architect | `_workspace/00_input/request-summary.md` | fixes the goal and assumptions |
| Product Architect | Core Implementer | `_workspace/01_product_command-contract.md` | prevents semantic drift during coding |
| Core Implementer | QA Reviewer | `_workspace/02_implementation_report.md` | lists changed surfaces and validation commands |
| QA Reviewer | Orchestrator | `_workspace/03_qa_report.md` | provides pass/fix/redo evidence |
| Orchestrator | User | `_workspace/final/tabdat-delivery-summary.md` | preserves final synthesis for audit and continuation |

## Failure Policy

- Missing product semantics: pause implementation and write the open question in `_workspace/01_product_command-contract.md`; make the narrowest repo-local assumption only when the roadmap already supports it.
- Implementation blocker: record the blocker, affected files, attempted commands, and smallest next step in `_workspace/02_implementation_report.md`.
- QA `fix`: apply targeted repairs and rerun the relevant checks once.
- QA `redo`: return to Phase 1 if semantics are wrong, or Phase 2 if implementation contradicts a valid contract.
- Conflicting docs: prefer `docs/dev_phase.md` for phase order and `docs/project_proposal.md` for product intent; record the conflict in the contract.

## Artifact Naming Convention

- `_workspace/00_input/request-summary.md`
- `_workspace/01_product_command-contract.md`
- `_workspace/02_implementation_report.md`
- `_workspace/03_qa_report.md`
- `_workspace/final/tabdat-delivery-summary.md`

Use `_workspace/experiments/{run}/` only for a future autonomous experiment request with a declared metric, baseline, mutable surface, and immutable evaluation surface.

## Optional Worker Delegation

Safe parallel slices:

- independent command implementations after shared parser rules are stable
- documentation examples and tests for already-implemented commands
- QA exploration across disjoint boundaries such as parser/executor and CLI/output

Forbidden overlaps:

- multiple workers editing the same parser grammar or AST contracts
- implementation before a command contract exists
- QA that reviews only file presence without comparing both sides of a boundary

The orchestrator owns synthesis and must preserve all worker artifacts.

## Validation Checklist

- generated skills include YAML frontmatter with `name` and `description`
- all skill and team-spec paths exist
- every phase has a named output
- command contract includes examples, non-goals, and acceptance criteria
- implementation report includes changed files and exact validation commands
- QA report compares at least two sides of each touched boundary
- final delivery summary distinguishes completed work from residual risk

## Test Scenarios

### Normal Flow

Request: "Implement `summarize age` for a loaded Parquet file."

Expected outputs:

- request summary identifies Phase 1 vertical-slice work
- command contract defines syntax, output shape, missing-column behavior, and tests
- implementation report lists parser, executor, backend, and tests changed
- QA report verifies CLI output matches the contract and backend aggregation

### Failure Flow

Failure point: a request asks for `by:` grouping before the parser supports core `command varlist, options`.

Expected behavior:

- product contract marks the request as beyond current phase
- implementer either proposes the smaller parser prerequisite or implements a minimal supported slice
- QA report checks that the final behavior does not claim unsupported grouping support
