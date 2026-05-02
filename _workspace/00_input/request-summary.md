# Phase 3 Inspection Request Summary

## Goal

Begin roadmap Phase 3 with a focused inspection slice that makes TabDat-Explore useful for
first-pass EDA without starting transformations, grouping, SQL, visualization, or prompt-toolkit UX.

## User Requests

- Read the project documents and begin Phase 3.
- Start from a temporary branch.
- Commit meaningful checkpoints during the phase.
- Open a GitHub PR with `gh` when complete.
- Include `@codex review` in the PR body because this phase adds code.

## Phase Fit

This is roadmap Phase 3: Core EDA Functionality.

The first PR should add executable inspection commands from the v0 glossary:

- `codebook`
- `count`
- `head`
- `tail`

## Non-Goals

- Do not implement `keep`, `drop`, `rename`, `generate`, `replace`, `select`, `collapse`,
  `tabulate`, or `by:` in this slice.
- Do not add SQL, visualization, prompt-toolkit UX, scripting, non-Parquet loaders, remote paths, or
  lazy execution optimization.
- Do not change Phase 1 behavior for `use`, `describe`, or `summarize`.

## Expected Outputs

- Updated `_workspace/01_product_command-contract.md` for Phase 3 inspection behavior.
- Parser, model, executor, backend, formatter, and CLI test changes under `src/tabdat/` and
  `tests/`.
- Updated SDD state files and final handoff artifacts.
- PR opened from `phase3-inspection-slice`.
