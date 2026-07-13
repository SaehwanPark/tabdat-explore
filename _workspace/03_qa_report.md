# QA Report: Phase 24 P0 Join Row Order

Status: final; implementation validation and exactly three independent PR review passes complete

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, language semantics, join help, command reference, and the
  product contract agree on active-row grouping and named-table match order.
- **Combination semantics:** explicit left and right ordinals preserve duplicate matches and avoid
  backend join-planning order leaking into the public result sequence; aliases are collision-safe.
- **Join variants:** inner joins omit unmatched active rows; left joins retain one missing-right row.
- **Cross-engine behavior:** eager, DuckDB-lazy, and Polars-lazy inputs produce the same ordered
  preview after the existing join materialization boundary.
- **Failure atomicity:** unknown table and missing-key validation preserve active rows, execution mode,
  and materialization metadata before Polars fallback.
- **User-facing paths:** exact CLI row blocks and join help cover the contract.
- **Scope control:** no new syntax, row IDs, sort abstraction, append/reshape rewrite, categorical
  order, or estimator behavior was added.

## Blocking Issues

- None remain.

## Validation Evidence

- Cross-engine join, collision, and failure-state regressions: 10 passed.
- CLI regression: 1 passed; focused help regression: 1 passed.
- `uv run pytest` — 1,091 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — exit 0; all integrated scenarios passed, including
  canonical replay.

## PR Review Loop

Exactly three independent review passes completed before merge readiness:

- **Pass 1:** found fixed `__tabdat_join_order` collision risk; fixed with case-insensitive
  collision-safe aliases, quoting, and a regression with user columns using both internal base names.
- **Pass 2:** found failed Polars-lazy join validation mutating execution state and independently
  confirmed the alias risk; fixed with pre-materialization table/key validation and cross-engine
  failure-state tests.
- **Pass 3:** found weak CLI/help unmatched-row assertions; fixed with a CLI missing-right fixture,
  exact duplicate/missing row assertions, and explicit inner/left/duplicate help checks.

No Critical or unresolved High/Medium findings remain.

## Non-Blocking Follow-Ups

Reshape ordering, unordered SQL, categorical ordering, exact arithmetic widths, overflow diagnostics,
randomness, estimation samples, errors and exits, lineage, differential assurance, and public-preview
readiness remain queued in `SPEC.md` Future.

## Recommended Next Action

Push the review-fix commit, update PR #100, merge it, fast-forward `main`, and clean up the feature
branch.
