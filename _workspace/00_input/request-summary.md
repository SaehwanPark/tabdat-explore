# Phase 1 Request Summary

## Goal

Begin roadmap Phase 1 by implementing the smallest end-to-end TabDat-Explore runtime slice:
a `tabdat` CLI that can load a local Parquet file and run `describe` and `summarize`
against a single active dataset.

## User Requests

- Start from a temporary branch.
- Commit meaningful Phase 1 checkpoints.
- Open a GitHub PR with `gh` when complete.
- Include `@codex review` in the PR body because this phase adds code.

## Phase Fit

This is roadmap Phase 1: Core Skeleton (Vertical Slice).

The work should add:

- CLI entry point and basic interactive shell.
- Minimal parser for Phase 1 commands.
- Executor with one active dataset.
- DuckDB-backed local Parquet loading and summary operations.
- Focused tests and validation commands.

## Non-Goals

- No autocomplete, syntax highlighting, history, or prompt-toolkit UX.
- No scripts, `if` conditions, options, SQL, transformations, visualization, or lazy-mode toggle.
- No broad Stata compatibility.
- No support for non-Parquet loading in Phase 1.

## Expected Outputs

- `_workspace/01_product_command-contract.md` for `use`, `describe`, and `summarize`.
- Runtime package modules under `src/`.
- Focused tests for parser, executor/backend, and CLI-visible behavior.
- Updated SDD state files and final handoff artifacts.
- PR opened from `temp/phase1-core-skeleton`.
