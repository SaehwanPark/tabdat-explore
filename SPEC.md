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

## Present

- Prepare for Phase 1: a minimal vertical CLI slice that can load a Parquet file and run `describe` and `summarize`.
- Before Phase 1 implementation, write command contracts for the commands being implemented.

## Future

- Phase 1: CLI shell, `use`, `describe`, `summarize`, minimal parser, executor, and DuckDB integration.
- Phase 2: command grammar, `if` conditions, expression parsing, and user-facing error handling.
- Phase 3: core EDA and transformation commands from the v0 glossary.
- Phase 4: SQL escape hatch over the active dataset.
- Phase 5: prompt-toolkit UX with highlighting, history, and autocomplete.
- Phase 6: artifact-based visualization.
- Phase 7 and later: lazy execution optimization, scripting, configuration, and extensions.
