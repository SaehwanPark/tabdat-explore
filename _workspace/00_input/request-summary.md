# Phase 11 Script Primitives Request Summary

## Goal

Implement the next unfinished Phase 11 prerequisite before moving to Phase 12: small script-level
reproducibility primitives.

## Phase Fit

Roadmap Phase 11: Data Workflow & Reproducibility Primitives.

Prior phases and completed Phase 11 slices were validated before implementation:

- `uv run pytest`
- `uv run mypy`
- `uv run ruff check .`
- `uv run ruff format --check .`

## Scope

- Add script-only `seed <integer>` for deterministic reproducibility metadata.
- Add script-only `let <name> = <value>` macros.
- Expand `$name` macro references in later script entries, including nested `run` scripts.
- Keep macro and seed state scoped to one top-level script run.
- Update script parsing/execution, focused tests, and durable docs.

## Non-Goals

- No script loops, conditionals, or inline comments.
- No random behavior or simulation commands.
- No remote data access.
- No Phase 12 estimation substrate work.
