# Phase 0 Product Guardrails

## Positioning

TabDat-Explore is a terminal-native exploratory data analysis tool for modern tabular data. It combines Stata-inspired command ergonomics with Parquet-first data access, DuckDB-oriented execution, and reproducible CLI workflows.

The project should feel concise for analysts who like command-driven workflows, while staying predictable and modern for engineers and data scientists working with columnar datasets.

## Naming

- Project name: TabDat-Explore.
- CLI command: `tabdat`.
- Package naming should stay aligned with the project while preserving the short CLI command.

## Core Principles

- Stata-inspired, not Stata-compatible.
- Predictable modern behavior is more important than legacy fidelity.
- Start with one active dataset for the MVP.
- Prefer a small set of reliable commands over a broad partial command surface.
- Build vertical slices across CLI, parser, executor, backend, tests, and docs.
- Keep DuckDB as the primary execution engine.
- Keep Parquet as the primary data format.
- Treat SQL as an escape hatch, not the primary interface.
- Treat terminal UX as core product value, not polish.

## Initial Non-Goals

Phase 0 and early MVP work should not include:

- advanced statistical modeling
- machine learning workflows
- distributed compute
- GUI or notebook interfaces
- collaborative multi-user features
- R integration
- plugin systems
- remote object storage
- broad Stata compatibility
- visualization before the core data workflow is stable

## Contributor Guardrails

- Use a tab size of 2 spaces across project files.
- Run configured linting and formatting proactively before commits.
- Use `uv` for environment and command execution.
- Add or update focused tests with implementation work.
- Keep public behavior aligned with `docs/project_proposal.md`, `docs/dev_phase.md`, and command contracts in `_workspace/`.

## Phase 0 Completion Criteria

Phase 0 is complete when the repository clearly records:

- the project and CLI names
- the product positioning
- the initial non-goals
- the v0 command set
- the main MVP architecture assumptions
- contributor style and validation expectations
