# TabDat-Explore Architecture

TabDat-Explore has completed the roadmap Phase 7 lazy execution entrypoint slice. This document
records the implemented shell UX, command-language model, active DuckDB relation model, lazy load
boundary, plot artifact boundary, and the boundaries future phases should preserve.

## Runtime Flow

```text
CLI Shell / prompt-toolkit UX
  -> Command Parser
  -> Executor
  -> DuckDB Backend / Lazy Scan Boundary
  -> Visualization Artifact Renderer
  -> Formatter
  -> Terminal Output
```

## Component Responsibilities

### CLI Shell

Owns user interaction, command input, script entry points in later phases, and terminal output
formatting. Interactive shell UX lives in `src/tabdat/shell.py` and uses prompt-toolkit for
history, inline history suggestions, syntax highlighting, and context-aware completions. Repeated
`-c` commands bypass prompt-toolkit and remain the smoke-testable batch workflow.

### Command Parser

Converts command text into internal command objects. The parser owns tokenization, varlist and
option parsing, `if` clauses, and expression AST construction. `use <path>, lazy` and
`use <path>, lazy engine=duckdb|polars` are parsed into typed load-mode fields. It may represent
parsed-only future commands, but execution remains an executor responsibility.

### Executor

Dispatches executable commands, maintains session state, and coordinates with the backend. For the
MVP, session state contains one active dataset. Parsed-only Phase 2 command forms must fail with an
unsupported-command execution error until a later command contract defines execution.

### DuckDB Backend

Owns data access and query execution. Parquet is the primary initial format. Eager loading creates
a session-local active DuckDB table. Lazy loading creates a DuckDB `read_parquet(...)` scan view so
load-time projection, filtering, grouping, and terminal query operations can be pushed into DuckDB.
Session transformations replace the active relation for later commands. The optional `polars`
engine selector is accepted and recorded for Phase 7 workflows, while command execution continues
through the DuckDB relation boundary until deeper Polars-native lowering is designed. No persistent
write/save behavior exists yet. SQL commands bind the active relation as the user-facing DuckDB view
`active`; `sql ... into <table>` replaces the active dataset with the query result while using
`<table>` as the displayed result name.

For visualization commands, the backend extracts typed rows or frequency counts from the active
table. It does not construct charts or write artifact files.

### Visualization Artifact Renderer

Owns Altair chart construction and SVG/PNG artifact writes. Default plot artifacts are written
under `artifacts/plots/`, and explicit `saving(...)` paths create parent directories as needed.
Interactive shell auto-open is a CLI-edge behavior; batch `-c` execution only prints the artifact
path.

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
- Phase 4 SQL is executable for result-producing `select` and `with` queries through `sql`.
- Multiline SQL can be entered with `sql """..."""`.
- `sql ... into <table>` replaces the active dataset with the SQL result; `use` remains path-only.
- Phase 5 prompt-toolkit UX is available for interactive sessions.
- Phase 6 plot commands are executable: `histogram`, `scatter`, and `bar`.
- Phase 7 lazy loading is executable through `use <path>, lazy` and
  `use <path>, lazy engine=duckdb|polars`; plain `use <path>` remains eager.
- Plot artifacts support SVG and PNG output through Altair and `vl-convert-python`.
- Autocomplete reads active dataset metadata from executor state but does not validate or mutate
  session state.
- Inline suggestions are history-based and persisted via `~/.tabdat_history`.

## Development Boundaries

- Build vertical slices across parser, executor, backend, CLI output, tests, and docs.
- Do not add broad command grammar before a command contract needs it.
- Keep public behavior documented before implementation.
- Keep transformation state session-local until a save/write command is explicitly designed.
- Keep chart rendering separate from backend data extraction.
- Use 2-space tab size across project files.
- Run configured linting and formatting proactively before commits.
