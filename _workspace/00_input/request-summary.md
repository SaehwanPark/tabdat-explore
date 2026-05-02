# Phase 2 Request Summary

## Goal

Begin roadmap Phase 2 by implementing a command-language parser foundation for TabDat-Explore.
The parser should understand richer command shapes while preserving the Phase 1 executable
pipeline for `use`, `describe`, and `summarize`.

## User Requests

- Start from a temporary branch.
- Commit meaningful Phase 2 checkpoints.
- Open a GitHub PR with `gh` when complete.
- Include `@codex review` in the PR body because this phase adds code.

## Phase Fit

This is roadmap Phase 2: Command Language & Parser.

The work should add:

- Structured parsing for `command varlist, options`.
- Optional `if` clauses.
- Expression parsing for conditions and future generated expressions.
- Useful user-facing parse errors.
- Focused parser and CLI smoke tests.

## Non-Goals

- Do not execute dataset mutations for `keep`, `drop`, `generate`, or `replace` in Phase 2.
- Do not add Phase 3 EDA commands, SQL, visualization, prompt-toolkit UX, scripts, or lazy-mode
  optimization.
- Do not broaden the loader beyond local `.parquet` files.

## Expected Outputs

- Updated `_workspace/01_product_command-contract.md` for Phase 2 parser behavior.
- Parser/model changes under `src/tabdat/`.
- Focused tests for grammar, expressions, diagnostics, and existing command compatibility.
- Updated SDD state files and final handoff artifacts.
- PR opened from `temp/phase2-parser-foundation`.
