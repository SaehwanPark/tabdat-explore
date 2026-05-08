# TabDat-Explore Architecture

TabDat-Explore has started roadmap Phase 11 data workflow primitives after completing the Phase 10
execution and state foundations slice. This
document records the implemented shell UX, script runner, command-language model, active DuckDB
relation model, session-local named table registry, lazy load boundary, runtime configuration, plot
artifact boundary, persistence boundary, join and append boundaries, and the boundaries future
phases should preserve.

## Runtime Flow

```text
CLI Shell / prompt-toolkit UX
  -> Script Runner when executing files
  -> Command Parser
  -> Executor
  -> DuckDB Backend / Lazy Scan Boundary
  -> Visualization Artifact Renderer
  -> Formatter
  -> Terminal Output
```

## Component Responsibilities

### CLI Shell

Owns user interaction, command input, script entry points, and terminal output formatting.
Interactive shell UX lives in `src/tabdat/shell.py` and uses prompt-toolkit for history, inline
history suggestions, syntax highlighting, and context-aware completions. Repeated `-c` commands
bypass prompt-toolkit and remain the smoke-testable batch workflow. Script execution is available
through `tabdat -f <script>`, `tabdat <script>`, and `run <script>`. Config loading happens at
CLI startup from either `--config <path>` or project-local `.tabdat.toml`.

### Script Runner

Owns UTF-8 script file reads, line-oriented script parsing, deterministic metadata output, command
echoes, nested `run` path resolution, recursion rejection, and file/line diagnostics. Script files
support whole-line `#` comments, blank lines, one command per line, and multiline SQL blocks.
Script execution shares one executor state and disables plot auto-open so runs are reproducible in
batch contexts.

### Command Parser

Converts command text into internal command objects. The parser owns tokenization, varlist and
option parsing, `if` clauses, expression AST construction, and `run <script>` commands. `use
<path>, lazy` and `use <path>, lazy engine=duckdb|polars` are parsed into typed load-mode fields.
It may represent parsed-only future commands, but execution remains an executor or CLI-edge
responsibility. Recoverable parser failures compose through `comp-builders` `Result` values exposed
by the local `tabdat.monads` boundary. Parser internals convert those values back to user-facing
`ParseError` exceptions only at the public parser edge.

### Executor

Dispatches executable commands, maintains session state, and coordinates with the backend. For the
MVP, session state contains one active dataset, a session-local named table registry, and one typed
runtime config. Parsed-only Phase 2 command forms must fail with an unsupported-command execution
error until a later command contract defines execution. Runtime `set` commands update session config
and affect later commands in the same shell, command sequence, or script. `join` and `append`
validate active state and named-table lookup at the executor boundary before asking the backend to
materialize the next active relation.

### DuckDB Backend

Owns data access and query execution. Parquet is the primary initial format. Eager loading creates
a session-local active DuckDB table. Lazy loading creates a DuckDB `read_parquet(...)` scan view so
load-time projection, filtering, grouping, and terminal query operations can be pushed into DuckDB.
Session transformations replace the active relation for later commands. The optional `polars`
engine selector is accepted and recorded for Phase 7 workflows, while command execution continues
through the DuckDB relation boundary until deeper Polars-native lowering is designed. A
session-local named table registry stores SQL `into` results under safe internal DuckDB relation
names; `use <table>` reactivates a registered table, while the active relation remains the default
target for non-SQL commands. `join <table> on <keylist>` joins the active relation to a registered
named table using same-name equality keys, supports `inner` and `left` joins, suffixes right-side
non-key column collisions, and materializes the result as the new eager active relation.
`append <table>` vertically stacks a registered named table under the active relation after strict
same-column and compatible-type validation, preserving active-dataset column order and
materializing the result as the new eager active relation. No persistent registry exists, but
`save` / `export` can persist the active relation to local Parquet.
SQL commands bind the active relation as the user-facing DuckDB view `active`. Initial lazy loads
report an unknown row count until a live count or materializing operation runs.

For visualization commands, the backend extracts typed rows or frequency counts from the active
table. It does not construct charts or write artifact files.

### Visualization Artifact Renderer

Owns Altair chart construction and SVG/PNG artifact writes. Default plot artifacts are written
under `<artifact_dir>/plots/` using `graph_format`, and explicit `saving(...)` paths create parent
directories as needed. Interactive shell auto-open is a CLI-edge behavior controlled by
`graph_open`; batch `-c` and script execution only print the artifact path.

### Formatter

Converts structured command results into deterministic terminal text. The backend should not own
display formatting.

## Current Repository State

- Product docs are in `docs/project_proposal.md`, `docs/dev_phase.md`, and `docs/phase0_product_guardrails.md`.
- Initial command scope is in `docs/command_glossary_v0.md`.
- Package metadata is in `pyproject.toml`.
- Phase handoff artifacts live under `_workspace/`.
- Integrated public-dataset E2E tooling lives under `integrated_testing/`; generated datasets,
  run logs, plots, and Parquet outputs are ignored.
- Runtime modules live under `src/tabdat/`.
- Functional helper imports live in `src/tabdat/monads.py`, which re-exports the project-approved
  `comp-builders` primitives and small edge conversion helpers.
- Focused tests live under `tests/`.
- The installed console script is `tabdat`.
- Phase 2 expression ASTs now compile to DuckDB SQL for Phase 3 transformations.
- Phase 3 commands are executable: `codebook`, `count`, `head`, `tail`, `keep`, `drop`, `select`,
  `rename`, `generate`, `replace`, `tabulate`, `collapse`, and supported `by:` forms.
- The supported `by:` child commands are `summarize` and `count`.
- Phase 4 SQL is executable for result-producing `select` and `with` queries through `sql`.
- Multiline SQL can be entered with `sql """..."""`.
- `sql ... into <table>` creates a session-local named table and makes it active.
- `use <table>` reactivates a registered named table; `use <path>` remains local Parquet loading.
- `join <table> on <keylist>` joins the active dataset with a registered named table and replaces
  the active dataset with the joined result.
- `append <table>` appends a registered named table to the active dataset and replaces the active
  dataset with the appended result.
- Phase 5 prompt-toolkit UX is available for interactive sessions.
- Phase 6 plot commands are executable: `histogram`, `scatter`, and `bar`.
- Phase 7 lazy loading is executable through `use <path>, lazy` and
  `use <path>, lazy engine=duckdb|polars`; plain `use <path>` remains eager.
- Phase 8 scripting is executable through `tabdat -f <script>`, `tabdat <script>`, and
  `run <script>`.
- Phase 9 config is executable through `.tabdat.toml`, `--config <path>`, and runtime `set`
  commands.
- Phase 9 persistence is executable through `save <path>[, replace]` and
  `export <path>[, replace]` for local Parquet.
- Plot artifacts support SVG and PNG output through Altair and `vl-convert-python`.
- Autocomplete reads active dataset and named table metadata from executor state but does not
  validate or mutate session state.
- Inline suggestions are history-based and persisted via `~/.tabdat_history`.

## Development Boundaries

- Build vertical slices across parser, executor, backend, CLI output, tests, and docs.
- Do not add broad command grammar before a command contract needs it.
- Keep public behavior documented before implementation.
- Import `Result`, `Option`, and `Validation` through `tabdat.monads`; do not import
  `comp-builders` directly from feature modules unless a future design records a reason to bypass
  the local boundary.
- Keep transformation state session-local except for explicit `save` / `export`.
- Keep chart rendering separate from backend data extraction.
- Keep script orchestration at the CLI edge; command semantics should still enter through the
  parser/executor boundary.
- Keep named tables session-local until a future persistence/catalog contract exists.
- Keep `join` scoped to named-table inputs and same-name equality keys until a broader multi-table
  workflow contract is written.
- Keep `append` scoped to named-table inputs with strict same-column schemas until a broader stack
  or union contract is written.
- Treat `engine=polars` as experimental user-facing metadata until a Polars-native execution
  contract exists.
- Use 2-space tab size across project files.
- Run configured linting and formatting proactively before commits.
