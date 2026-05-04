# TabDat-Explore Spec

This file tracks feature state for spec-driven development. Product intent lives in `docs/project_proposal.md`; roadmap order lives in `docs/dev_phase.md`.

## Past

- Created the initial project proposal and development roadmap.
- Added the repository development harness and agent workflows.
- Established Phase 0 product guardrails:
  - project name: TabDat-Explore
  - CLI command: `tabdat`
  - command language: Stata-inspired, not Stata-compatible
  - MVP model: single active dataset
  - backend direction: DuckDB primary, Parquet first
  - contributor style: 2-space tab size and proactive linting/formatting
- Defined the v0 command glossary with 12 initial commands.
- Implemented the Phase 1 core skeleton:
  - `tabdat` console script and basic shell
  - minimal parser for `use`, `describe`, `summarize`, `exit`, and `quit`
  - executor with one active dataset
  - DuckDB-backed local Parquet loading and summaries
  - focused parser, executor/backend, and CLI smoke tests
- Implemented the Phase 2 parser foundation:
  - structured parser models for future command forms
  - command varlists, comma options, `if` clauses, and expression ASTs
  - expression parsing for identifiers, literals, arithmetic, comparisons, grouping, unary minus,
    and function calls
  - user-facing parse diagnostics for malformed Phase 2 syntax
  - focused parser coverage while preserving Phase 1 executable behavior
- Implemented the full Phase 3 core EDA command surface:
  - `codebook [varlist]` compact column profiling
  - `count` active dataset row counts
  - `head [n]` and `tail [n]` row previews
  - `keep`, `drop`, and `select` column projection and row filtering
  - `rename`, `generate`, and `replace` session-local transformations
  - `tabulate` one-way and two-way frequency tables
  - `collapse` grouped aggregate datasets
  - `by group_vars: summarize` and `by group_vars: count`
  - DuckDB-backed active relation execution, deterministic terminal formatting, and focused
    parser/executor/CLI tests
- Implemented Phase 4 SQL integration:
  - `sql <select-or-with-query>` as an escape hatch over the active dataset exposed as `active`
  - `sql """..."""` multiline query parsing and minimal shell continuation
  - `into <table>` support that replaces the active dataset with the SQL result
  - focused parser, executor/backend, and CLI smoke tests
- Implemented Phase 5 CLI UX:
  - prompt-toolkit interactive shell
  - syntax highlighting for command-oriented input
  - context-aware completions for commands, active dataset columns, options, `by:` forms, and SQL
    helpers
  - persistent command history and inline history suggestions
  - focused shell UX tests while preserving `-c` command mode
- Implemented Phase 6 artifact-based visualization:
  - `histogram`, `scatter`, and `bar` plot commands
  - Altair-backed SVG/PNG artifact rendering
  - default artifact output under `artifacts/plots/`
  - `saving(...)`, `noopen`, `bins=`, and `missing` plot options
  - interactive auto-open behavior while preserving deterministic `-c` batch output
  - focused parser, executor, CLI, and shell UX tests
- Implemented Phase 7 lazy execution entrypoint:
  - `use <path>, lazy` opt-in loading while preserving eager `use <path>` defaults
  - `engine=duckdb|polars` lazy engine selection with DuckDB as the default
  - DuckDB `read_parquet` scan views for lazy load-time pushdown
  - typed dataset execution-mode metadata and CLI output for lazy sessions
  - focused parser, executor, and CLI tests for lazy command flows

## Present

- Phase 7 is complete for the first lazy execution slice.
- The current runtime does not yet include scripts.
- Accepted reviewer feedback is being folded into Phase 8+ planning only; completed Phase 0-7
  behavior remains historical unless a future task explicitly revisits it.

## Future

- Phase 8 scripting and reproducibility:
  - add script execution from files via `tabdat -f <script>`, `tabdat <script>`, and interactive
    `run <script>`
  - introduce a script parser layer for command sequences, with AST room for later loops,
    macros, script-level conditionals, and error-control constructs
  - keep row-level `if` expressions separate from future script-level `if` / `else`
  - add deterministic logging, script-run metadata, and golden-output tests for complete mini
    sessions
  - dogfood a complete public-dataset EDA using only `tabdat` before adding many more commands
- Phase 8 lazy and backend honesty:
  - avoid lazy load-time full counts unless requested
  - document which commands preserve lazy scans and which commands materialize intermediate
    results
  - either hide `engine=polars` until Polars has real execution coverage or mark it clearly
    experimental in help, metadata, and docs
- Phase 9 configuration and persistence:
  - define configuration behavior for graph format, artifact directory, and auto-open defaults
  - add a `save` / `export` command contract for persisting session-local transformations
  - define plot artifact naming policy for both reproducible scripts and interactive reruns
- Phase 10+ architecture candidates:
  - consider a lightweight named table registry that augments the single active dataset model
  - consider executor handler registration or another dispatch refactor if script meta-commands
    make the central executor difficult to maintain
  - add specific execution error subclasses when CLI or script diagnostics need
    context-sensitive handling
  - continue deeper Polars-native lazy lowering only after the user-facing backend contract is
    honest and test-covered
