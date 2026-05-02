# TabDat-Explore Architecture

TabDat-Explore is currently in Phase 0. This document records the intended architecture so Phase 1 can implement a small vertical slice without widening scope.

## Planned Runtime Flow

```text
CLI Shell
  -> Command Parser
  -> Executor
  -> DuckDB Backend
  -> Terminal Output
```

## Component Responsibilities

### CLI Shell

Owns user interaction, command input, script entry points in later phases, and terminal output formatting. Early Phase 1 should keep this minimal.

### Command Parser

Converts command text into small internal command objects. Early parsing should support only the command forms required by the current command contract.

### Executor

Dispatches parsed commands, maintains session state, and coordinates with the backend. For the MVP, session state should contain one active dataset.

### DuckDB Backend

Owns data access and query execution. Parquet is the primary initial format. Backend operations should avoid unnecessary materialization where practical.

## Current Repository State

- Product docs are in `docs/project_proposal.md`, `docs/dev_phase.md`, and `docs/phase0_product_guardrails.md`.
- Initial command scope is in `docs/command_glossary_v0.md`.
- Package metadata is in `pyproject.toml`.
- Phase handoff artifacts live under `_workspace/`.
- Runtime modules have not been created yet.

## Development Boundaries

- Build vertical slices across parser, executor, backend, CLI output, tests, and docs.
- Do not add broad command grammar before a command contract needs it.
- Keep public behavior documented before implementation.
- Use 2-space tab size across project files.
- Run configured linting and formatting proactively before commits.
