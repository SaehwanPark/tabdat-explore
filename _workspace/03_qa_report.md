# QA Report: Phase 24 P0 SQL and Named-Table Order

Status: final; implementation validation and exactly three independent PR review passes complete

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, language semantics, SQL/use help, user guide, and the
  product contract agree on explicit SQL ordering, tie-breakers, named-table restoration, activation
  reset semantics, and unordered SQL non-goals.
- **Direct SQL:** ordered result rows agree across eager, DuckDB-lazy, and Polars-lazy inputs; tied
  keys are deterministic only with an explicit secondary key.
- **Active transition:** `sql ... into` preserves query sequence through head/tail, and reactivation
  is tested after returning to the original source so a no-op activation cannot pass.
- **Materialization:** the existing DuckDB eager boundary and Polars fallback/reset behavior are
  asserted without adding hidden materialization behavior.
- **User-facing paths:** multiline parser coverage, script-mode CLI output, exact preview rows, and
  SQL/use help cover the contract.
- **Scope control:** no SQL rewriting, new syntax, row IDs, sort command, append/join/reshape order,
  categorical order, or estimator behavior was added.

## Blocking Issues

- None remain.

## Validation Evidence

- Ordered SQL executor regressions: 3 passed.
- Ordered SQL parser regression: 1 passed; script-mode CLI regression: 1 passed; help suite: 8 passed.
- `uv run pytest` — 1,074 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — exit 0; all integrated scenarios passed, including
  canonical replay.

## PR Review Loop

Exactly three independent review passes completed before merge readiness:

- **Pass 1:** identified stale arbitrary-SQL wording, missing tie-breaker semantics, and missing use
  help. Fixed the language/help wording and added tie-key/use-help coverage.
- **Pass 2:** identified the existing Polars fallback-reason reset contradiction and repeated the tie
  concern. Fixed the contract/docs to describe the activation reset and added a named-table status
  assertion plus tied-key regression.
- **Pass 3:** identified non-isolated reactivation coverage, missing multiline parser coverage, and
  brittle CLI assertions. Fixed by reloading the source before reactivation, adding the parser case,
  and asserting exact formatted rows in command-delimited output.

No Critical or unresolved High/Medium findings remain.

## Non-Blocking Follow-Ups

SQL without explicit ordering, append/join/reshape ordering, categorical ordering, exact arithmetic
widths, overflow diagnostics, randomness, estimation samples, errors and exits, lineage, differential
assurance, and public-preview readiness remain queued in `SPEC.md`.

## Recommended Next Action

Push the review-fix commit, update PR #98, merge it, fast-forward `main`, and clean up the feature
branch.
