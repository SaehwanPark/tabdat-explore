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
- Began Phase 3 with the inspection command slice:
  - `codebook [varlist]` compact column profiling
  - `count` active dataset row counts
  - `head [n]` and `tail [n]` row previews
  - DuckDB-backed execution, deterministic terminal formatting, and focused parser/executor/CLI
    tests

## Present

- Phase 3 remains in progress beyond the first inspection slice. Transformations and grouping are
  not implemented yet.
- Parsed-only forms such as `keep if ...` and `generate ... = ...` are represented but
  intentionally not executed yet.
- The current runtime does not yet include prompt-toolkit UX, scripts, SQL, visualization, or lazy
  execution optimization.

## Future

- Phase 3: transformation and grouping commands from the v0 glossary.
- Phase 4: SQL escape hatch over the active dataset.
- Phase 5: prompt-toolkit UX with highlighting, history, and autocomplete.
- Phase 6: artifact-based visualization.
- Phase 7 and later: lazy execution optimization, scripting, configuration, and extensions.
