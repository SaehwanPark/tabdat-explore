# Full Phase 3 Request Summary

## Goal

Complete the full roadmap Phase 3 core EDA surface so a user can load a local Parquet dataset,
inspect it, transform rows and columns, create or update columns, tabulate frequencies, and run
basic grouped summaries without leaving the tool.

## User Requests

- Read the project documents and complete Phase 3.
- Start from a temporary branch.
- Commit meaningful checkpoints during the phase.
- Open a GitHub PR with `gh` when complete.
- Include `@codex review` in the PR body because this phase adds code.

## Phase Fit

This is roadmap Phase 3: Core EDA Functionality. The requested scope is the full roadmap Phase 3
list, including commands deferred by the v0 glossary:

- transformations: `keep`, `drop`, `select`, `rename`, `generate`, `replace`
- grouping: `by:`, `collapse`, `tabulate`
- existing inspection: `describe`, `summarize`, `codebook`, `count`, `head`, `tail`

## Assumptions

- The active dataset is still loaded from one local `.parquet` file with `use`.
- Transformations mutate the active dataset for the current session only; no save/write command is
  added.
- Active data is represented as a DuckDB relation query so later commands see prior
  transformations.
- DuckDB remains the only backend dependency in this phase.
- Lazy execution optimization is best-effort through DuckDB query composition and remains a future
  Phase 7 concern.

## Non-Goals

- Do not add the `sql` command, visualization, scripting, prompt-toolkit UX, config, remote paths,
  non-Parquet loading, or persistent write/save behavior.
- Do not attempt broad Stata compatibility beyond the documented Stata-inspired forms.

## Expected Outputs

- Updated `_workspace/01_product_command-contract.md` for full Phase 3 behavior.
- Parser, model, executor, backend, formatter, and CLI test changes under `src/tabdat/` and
  `tests/`.
- Updated SDD state files and final handoff artifacts.
- PR opened from `tmp/phase3-core-eda`.
