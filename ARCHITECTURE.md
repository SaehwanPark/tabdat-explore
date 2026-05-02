# TabDat-Explore Architecture

TabDat-Explore has completed the roadmap Phase 3 core EDA surface. This document records the
implemented core skeleton, command-language model, active DuckDB relation model, and the boundaries
future phases should preserve.

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

Owns data access and query execution. Parquet is the primary initial format. Loading creates a
session-local active DuckDB table. Transformations replace that active table in the current session,
so later inspection, summary, tabulation, and grouping commands see prior command results. No
persistent write/save behavior exists yet.

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
- Phase 2 expression ASTs now compile to DuckDB SQL for Phase 3 transformations.
- Phase 3 commands are executable: `codebook`, `count`, `head`, `tail`, `keep`, `drop`, `select`,
  `rename`, `generate`, `replace`, `tabulate`, `collapse`, and supported `by:` forms.
- The supported `by:` child commands are `summarize` and `count`.

## Development Boundaries

- Build vertical slices across parser, executor, backend, CLI output, tests, and docs.
- Do not add broad command grammar before a command contract needs it.
- Keep public behavior documented before implementation.
- Keep transformation state session-local until a save/write command is explicitly designed.
- Use 2-space tab size across project files.
- Run configured linting and formatting proactively before commits.
