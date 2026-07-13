# QA Report: Phase 24 P0 Reshape Row Order

Status: final; implementation validation and exactly three independent PR review passes complete

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, language semantics, reshape help, command reference, and
  the product contract agree on long source-row/j-value order and wide first-group order.
- **Long semantics:** non-sorted source rows and wide-column j order are preserved.
- **Wide semantics:** identifier groups follow the first active row belonging to each group.
- **Internal safety:** public identifiers and generated columns cannot be renamed by internal order
  aliases.
- **Cross-engine behavior:** eager, DuckDB-lazy, and Polars-lazy inputs produce the same reshape
  preview sequence after the existing materialization boundary.
- **Failure atomicity:** invalid long/wide identifiers, stubs, j-values, and output conflicts preserve
  active rows, execution mode, and materialization metadata before Polars fallback.
- **Regression safety:** existing wide/long column layout and duplicate-cell aggregation tests stay
  green.
- **Scope control:** no new syntax, row IDs, sort abstraction, append/join rewrite, categorical order,
  or estimator behavior was added.

## Blocking Issues

- None remain.

## Validation Evidence

- Cross-engine reshape regression: 3 passed; review-fix regression set: 10 passed; reshape-focused
  executor/CLI suite: 15 passed.
- CLI regression: 1 passed; focused help regression: 1 passed.
- `uv run pytest` — 1,101 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — exit 0; all integrated scenarios passed, including
  canonical replay.

## PR Review Loop

Exactly three independent review passes completed before merge readiness:

- **Pass 1:** found long-reshape aliases colliding with valid generated output names; fixed by
  reserving identifiers, j names, and stubs before allocating ordinals, with collision tests.
- **Pass 2:** found Polars-lazy validation mutation and public alias collisions; fixed with pure
  long/wide prevalidation, Polars j-value discovery, and cross-engine failure-state tests.
- **Pass 3:** found underspecified j-value discovery, weak null/duplicate coverage, and missing
  command-reference guidance; fixed with an exact scan-order contract, edge fixtures, and reference
  documentation.

No Critical or unresolved High/Medium findings remain.

## Non-Blocking Follow-Ups

Categorical ordering, unordered SQL, exact arithmetic widths, overflow diagnostics, randomness,
estimation samples, errors and exits, lineage, differential assurance, and public-preview readiness
remain queued in `SPEC.md` Future.

## Recommended Next Action

The reshape slice is merged. Bind the categorical-order contract in the new feature branch and
continue the SPEC loop.
