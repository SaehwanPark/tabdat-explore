---
name: tabdat-qa-reviewer
description: Review TabDat changes for cross-boundary coherence between command contracts, parser, executor, backend, CLI output, tests, and docs.
---

# TabDat QA Reviewer

## When to Use

- Use this skill after TabDat implementation or documentation changes that affect behavior.
- Use it before final delivery when parser, executor, backend, CLI output, tests, or docs changed.
- Do not use it as a generic style review; focus on behavioral boundaries and validation evidence.

## Required Inputs

- Original user request or `_workspace/00_input/request-summary.md`.
- `_workspace/01_product_command-contract.md`, when present.
- `_workspace/02_implementation_report.md`.
- Changed files and validation output.

## Workflow

1. Read the request, contract, implementation report, and changed files.
2. Identify touched boundaries.
   - docs to command contract
   - command contract to parser
   - parser representation to executor
   - executor to backend result shape
   - backend result to formatter and CLI output
   - tests to claimed behavior
3. Compare both sides of each boundary.
4. Run or inspect validation evidence where practical.
5. Write `_workspace/03_qa_report.md` with status `pass`, `fix`, or `redo`.

## Outputs

- `_workspace/03_qa_report.md` with:
  - status
  - boundaries checked
  - blocking issues
  - non-blocking follow-ups
  - validation evidence
  - recommended next action

## Review Statuses

- `pass`: no blocking boundary mismatch found; residual risks are documented.
- `fix`: targeted repair is cheaper than redesign; identify exact files or behavior.
- `redo`: the implementation contradicts the product contract or the contract is not implementable as written.

## Validation

- Cite the artifacts or files compared.
- Prefer concrete mismatches over general concerns.
- Separate confirmed failures from unverified areas.
- Do not mark `pass` if no validation command or equivalent evidence exists for changed behavior.

## References

- `references/qa-checklist.md`
