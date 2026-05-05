# Phase 8 Request Summary

## Goal

Implement roadmap Phase 8: scripting and reproducibility, after a small lazy-mode honesty pass.

## Requested Workflow

- Use a temporary branch.
- Commit meaningful implementation checkpoints.
- Document carefully.
- Open a PR when fully done.

## Phase Fit

Roadmap Phase 8 covers:

- script execution from files
- a script parser layer for command sequences
- deterministic batch output and reproducibility metadata
- golden-output tests for complete mini sessions
- documentation of lazy-mode materialization limits and Polars experimental status

## Touched Surfaces

- CLI argument handling and batch runner
- parser and command models for `run <script>`
- script parsing and execution layer
- executor integration for interactive or nested `run`
- formatter output for script metadata
- focused parser, CLI, script, and golden-output tests
- SDD state docs and workspace delivery artifacts

## Assumptions

- Script files are UTF-8 text.
- Empty lines and whole-line `#` comments are ignored.
- Inline comments, macros, loops, and script-level conditionals are deferred.
- Multiline `sql """..."""` blocks are supported.
- Scripts fail fast on the first parse or execution error.
- `exit` and `quit` stop the current script successfully.
- Plot auto-open is disabled for scripts.
