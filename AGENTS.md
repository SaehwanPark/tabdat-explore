# Repository Agents Guide

Keep this file short and repo-wide. Detailed reusable workflows live under `.agents/skills/` and `docs/harness/`.

## What
- TabDat-Explore is a Python 3.13 CLI EDA tool concept: Stata-inspired commands, modern tabular formats, DuckDB/Arrow-oriented execution, and terminal-native UX.
- Canonical product docs are `docs/project_proposal.md` and `docs/dev_phase.md`; keep implementation choices aligned with those documents unless a task explicitly changes direction.
- Current package metadata is in `pyproject.toml`; use `uv` for environment and command execution.
- Phase 0 guardrails are in `docs/phase0_product_guardrails.md`; the initial command set is in `docs/command_glossary_v0.md`.

## Why
- The project should grow by vertical slices: a small working shell, parser, executor, and backend before broad command coverage.
- The command language is Stata-inspired, not Stata-compatible. Prefer predictable modern behavior over legacy fidelity.
- Keep the command surface small until each command has clear syntax, tests, useful errors, and documented behavior.

## How
- Install/sync with `uv sync`.
- Run project commands through `uv run ...`.
- Until a test suite exists, every implementation task should add or update focused tests and record the exact validation command in the final response.
- Use a tab size of 2 spaces across project files.
- Run configured linting and formatting proactively before commits.
- For reusable agent workflows, use `.agents/skills/tabdat-orchestrator/SKILL.md` and `docs/harness/tabdat/team-spec.md`.
- Note this project should follow: FP-style (use `fp-developer` skill whenever writing or editing codebase), SDD (spec-driven), TDD (test-driven)
- Focus on type safety via `pyright` and `pydantic`: Use `pyright` to prevent bugs by analyzing code for errors before execution, use `pydantic` to ensure data integrity by ensuring data structures conform to defined types.
- Use local `tabdat.monads` helpers for explicit functional error and absence handling.

## Recommended Tools
- `pytest`
- `pyright`: you may install via `uv`
- `pydantic`: you may install via `uv`
- `gh`
- `hf`

## Tooling Troubleshoot
- When essential tools like `uv`, `gh`, `hf` are not found, check paths: `which uv`, `which gh`, `which hf`
- You may also know the tokens via `gh auth token` and/or `hf auth token`
