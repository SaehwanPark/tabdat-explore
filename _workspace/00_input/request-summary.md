# Phase 0 Request Summary

## Goal

Begin roadmap Phase 0 for TabDat-Explore by turning the existing proposal and roadmap into durable product guardrails before runtime implementation begins.

## User Requests

- Start from a temporary branch.
- Commit meaningful changes during the phase as low-level checkpoints.
- Open a GitHub PR with `gh` when finished.
- Add `@codex review` to the PR only if the changes include actual code edits or updates.
- Make the project explicitly use a 2-space tab size.
- Make proactive linter and formatter use an explicit project expectation.

## Phase Fit

This is roadmap Phase 0: Product Definition & Guardrails.

The work should lock down:

- positioning statement
- non-goals
- initial command set of 10-15 commands
- naming decision for project and CLI command
- key MVP guardrails

## Decisions

- Project name: TabDat-Explore.
- CLI command: `tabdat`.
- Command language: Stata-inspired, not Stata-compatible.
- MVP dataset model: one active dataset.
- Primary execution engine: DuckDB.
- Primary data format: Parquet.
- Contributor style: 2-space tab size and proactive configured linting/formatting before commits.

## Non-Goals

- No parser, executor, backend, CLI shell, package entry point, or command implementation in Phase 0.
- No broad dependency installation solely for future phases.
- No detailed command contracts beyond a v0 glossary; detailed contracts should precede Phase 1 implementation.

## Expected Outputs

- Root SDD state files: `SPEC.md`, `ARCHITECTURE.md`, and `CHANGELOG.md`.
- Phase 0 guardrails doc.
- v0 command glossary.
- Updated contributor pointers in `README.md` and `AGENTS.md`.
- PR opened from `temp/phase0-product-guardrails`.
