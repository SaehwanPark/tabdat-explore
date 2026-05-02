# TabDat-Explore Architecture

TabDat-Explore has begun Phase 3 with executable inspection commands. This document records the
implemented core skeleton, command-language model, inspection slice, and the boundaries future
phases should preserve.

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

Owns user interaction, command input, script entry points in later phases, and terminal output
formatting. The current shell remains intentionally minimal and uses repeated `-c` commands for
smoke-testable workflows.

### Command Parser

Converts command text into internal command objects. The parser owns tokenization, varlist and
option parsing, `if` clauses, and expression AST construction. It may represent parsed-only future
commands, but execution remains an executor responsibility.

### Executor

Dispatches executable commands, maintains session state, and coordinates with the backend. For the
MVP, session state contains one active dataset. Parsed-only Phase 2 command forms must fail with an
unsupported-command execution error until a later command contract defines execution.

### DuckDB Backend

Owns data access and query execution. Parquet is the primary initial format. Backend operations
should avoid unnecessary materialization where practical. Current backend operations inspect Parquet
metadata, summarize numeric columns, profile columns for `codebook`, return row counts from
metadata, and preview rows for `head`/`tail`.

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
- Phase 3 inspection commands are executable: `codebook`, `count`, `head`, and `tail`.

## Development Boundaries

- Build vertical slices across parser, executor, backend, CLI output, tests, and docs.
- Do not add broad command grammar before a command contract needs it.
- Keep public behavior documented before implementation.
- Use 2-space tab size across project files.
- Run configured linting and formatting proactively before commits.
