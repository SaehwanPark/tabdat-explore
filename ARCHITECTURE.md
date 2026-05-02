# TabDat-Explore Architecture

TabDat-Explore is currently past the Phase 2 parser foundation. This document records the
implemented core skeleton, command-language model, and the boundaries future phases should
preserve.

## Runtime Flow

```text
CLI Shell
  -> Command Parser
  -> Executor
  -> DuckDB Backend
  -> Formatter
  -> Terminal Output
```

## Component Responsibilities

### CLI Shell

Owns user interaction, command input, script entry points in later phases, and terminal output formatting. Early Phase 1 should keep this minimal.

### Command Parser

Converts command text into internal command objects. The parser owns tokenization, varlist and
option parsing, `if` clauses, and expression AST construction. It may represent parsed-only future
commands, but execution remains an executor responsibility.

### Executor

Dispatches executable commands, maintains session state, and coordinates with the backend. For the
MVP, session state should contain one active dataset. Parsed-only Phase 2 command forms must fail
with an unsupported-command execution error until a later command contract defines execution.

### DuckDB Backend

Owns data access and query execution. Parquet is the primary initial format. Backend operations should avoid unnecessary materialization where practical.

### Formatter

Converts structured command results into deterministic terminal text. The backend should not own
display formatting.

## Current Repository State

- Product docs are in `docs/project_proposal.md`, `docs/dev_phase.md`, and `docs/phase0_product_guardrails.md`.
- Initial command scope is in `docs/command_glossary_v0.md`.
- Package metadata is in `pyproject.toml`.
- Phase handoff artifacts live under `_workspace/`.
- Runtime modules live under `src/tabdat/`.
- Focused tests live under `tests/`.
- The installed console script is `tabdat`.
- Phase 2 parser models include command options and expression ASTs for future command execution.

## Development Boundaries

- Build vertical slices across parser, executor, backend, CLI output, tests, and docs.
- Do not add broad command grammar before a command contract needs it.
- Keep public behavior documented before implementation.
- Use 2-space tab size across project files.
- Run configured linting and formatting proactively before commits.
