# Changelog

All notable project changes are tracked here.

## Unreleased

### Added

- Added Phase 11 panel metadata with `panel <id_var> <time_var>`, `panel`, and `panel clear`,
  DuckDB-backed missing-value and duplicate id/time validation, session-local metadata
  preservation/clearing across state-changing commands, deterministic CLI output, and focused
  parser, executor/backend, CLI, and shell coverage.
- Added the third Phase 11 data workflow primitive with `reshape long` and `reshape wide` over the
  active dataset, required `i(...)` and `j(...)` options, eager DuckDB materialization, active
  dataset replacement, deterministic output, and focused parser, executor/backend, CLI, and shell
  coverage.
- Added the second Phase 11 data workflow primitive with `append <table>`, strict same-column
  schema validation, active-dataset column order preservation, active dataset replacement, and
  focused parser, executor/backend, CLI, and shell coverage.
- Added the first Phase 11 data workflow primitive with `join <table> on <keylist>`, `how=inner|left`,
  right-side collision suffixing, active dataset replacement, and focused parser, executor/backend,
  and CLI coverage.
- Added Phase 10 execution and state foundations with a lightweight session-local named table
  registry, `use <table>` activation, typed execution error subclasses, executor state-handler
  extraction, and named table shell completions.
- Added `comp-builders` as the functional helper implementation behind `tabdat.monads`, including
  `Result`, `Option`, `Validation`, builder re-exports, and small edge conversion helpers.
- Reorganized the post-Phase-9 roadmap across `docs/dev_phase.md` and `SPEC.md` into an
  interleaved Phase 10-19 sequence that stages execution/state foundations, reproducibility and
  data-workflow primitives, core econometrics coverage, advanced empirical methods, and late
  ecosystem extensions coherently.
- Added an integrated public-dataset E2E harness and run documentation for the Titanic batch,
  interactive shell, NYC taxi lazy-scale, and Penguins script reproducibility scenarios.
- Added Phase 9 configuration and persistence with `.tabdat.toml`, `--config <path>`, runtime
  `set graph_format`, `set artifact_dir`, and `set graph_open`, config-aware plot defaults,
  live `count` execution for lazy datasets, and Parquet `save` / `export`.
- Added Phase 8 scripting and reproducibility with `tabdat -f <script>`, positional script
  execution, interactive and nested `run <script>`, deterministic script metadata, command
  transcripts, multiline SQL script blocks, line-numbered script errors, and script-mode plot
  auto-open suppression.
- Added local typed monad helpers for parser failure composition and pure-core absence handling.
- Added Phase 7 lazy execution entrypoint with `use <path>, lazy`, optional
  `engine=duckdb|polars` selection, DuckDB `read_parquet` scan views for lazy loading, typed
  execution-mode metadata, and CLI output that identifies lazy sessions.
- Added Phase 6 artifact-based visualization with `histogram`, `scatter`, and `bar` commands,
  Altair-backed SVG/PNG output, default `artifacts/plots/` paths, `saving(...)`, `noopen`, `bins=`,
  and `missing` options, plus interactive-only plot auto-open behavior.
- Added Phase 5 prompt-toolkit interactive shell UX with syntax highlighting, persistent command
  history, inline history suggestions, and context-aware autocomplete for commands, active dataset
  columns, common options, `by:` forms, and lightweight SQL helpers.
- Added Phase 4 SQL integration with `sql` queries over the active dataset exposed as `active`,
  multiline `sql """..."""` parsing, and `into <table>` active-dataset replacement.
- Completed the roadmap Phase 3 core EDA surface with executable transformations (`keep`, `drop`,
  `select`, `rename`, `generate`, `replace`), grouping (`by:` and `collapse`), and `tabulate`.
- Added session-local active DuckDB table state so transformations feed subsequent inspection and
  summary commands.
- Added the Phase 3 inspection slice with executable `codebook`, `count`, `head`, and `tail`
  commands over the active Parquet dataset.
- Added the Phase 2 parser foundation with structured command options, `if` clauses, expression
  ASTs, parsed-only future command forms, and focused diagnostics tests.
- Fixed Phase 2 parser regressions so `summarize` rejects assignment syntax and punctuated varlist
  names remain supported.
- Added Phase 1 `tabdat` CLI skeleton with `use`, `describe`, and `summarize`.
- Added DuckDB-backed local Parquet loading and numeric summary execution.
- Added focused parser, executor/backend, and CLI smoke tests.
- Added Phase 0 product guardrails for positioning, naming, MVP assumptions, non-goals, and contributor expectations.
- Added the v0 command glossary with the initial 12-command surface.
- Added SDD state files with feature status and planned architecture.
- Added repository guidance for 2-space tab size and proactive linting/formatting.

### Removed

- Removed the external PyMonad dependency in favor of local `tabdat.monads` helpers.

### Changed

- Changed structured parser failure composition from handwritten `Either` helpers to
  `comp-builders` `Result` values while preserving the public `ParseError` behavior.

### Fixed

- Fixed interactive shell Ctrl-C handling so prompt-toolkit completion interrupts return to the
  prompt instead of terminating with a traceback.
