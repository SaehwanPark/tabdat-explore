# QA Report: Phase 24 P0 Append Row Order

Status: final; implementation validation and exactly three independent PR review passes complete

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, language semantics, append help, command reference, and
  the product contract agree on active-left then named-table-right sequence and join/reshape limits.
- **Combination semantics:** explicit per-input ordinals prevent interleaving; duplicate rows remain
  present; eager, DuckDB-lazy, and Polars-lazy append paths agree.
- **Preview semantics:** head/tail of the combined active dataset retain left-then-right order.
- **Failure atomicity:** unknown table, missing-column, and type-mismatch append failures preserve
  active execution state before Polars fallback materialization.
- **User-facing paths:** exact script-mode CLI row blocks and append help cover the contract.
- **Scope control:** no new syntax, row IDs, join/reshape rewrite, categorical order, or estimator
  behavior was added.

## Blocking Issues

- None remain.

## Validation Evidence

- Cross-engine append and failure regressions: 6 passed.
- Script-mode CLI regression: 1 passed; help suite: 8 passed.
- `uv run pytest` — 1,081 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — exit 0; all integrated scenarios passed, including
  canonical replay.

## PR Review Loop

Exactly three independent review passes completed before merge readiness:

- **Pass 1:** identified implicit append order, stale language caveats, command-reference syntax,
  and missing duplicate coverage. Fixed with explicit side/ordinal ordering, docs cleanup, command
  reference correction, and overlapping duplicate rows.
- **Pass 2:** identified the same ordering risk and failed Polars-lazy append mutation on validation
  errors. Fixed with pre-materialization append validation, type-alias normalization, and failure
  state tests across all execution modes.
- **Pass 3:** identified weak CLI/cardinality assertions, duplicate coverage, and stale deferred
  append wording. Fixed with exact ordered row-block assertions, duplicate preservation checks, and
  language-limit cleanup.

No Critical or unresolved High/Medium findings remain.

## Non-Blocking Follow-Ups

Join/reshape ordering, unordered SQL, categorical ordering, exact arithmetic widths, overflow
diagnostics, randomness, estimation samples, errors and exits, lineage, differential assurance, and
public-preview readiness remain queued in `SPEC.md`.

## Recommended Next Action

Push the review-fix commit, update PR #99, merge it, fast-forward `main`, and clean up the feature
branch.
