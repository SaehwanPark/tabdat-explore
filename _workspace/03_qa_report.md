# QA Report: Phase 24 P0 SQL and Named-Table Order

Status: local validation complete; PR review loop pending

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, `docs/language-semantics.md`, SQL help, and the product
  contract agree on explicit SQL ordering, named-table preservation, and unordered SQL non-goals.
- **Direct SQL:** ordered result rows agree across eager, DuckDB-lazy, and Polars-lazy inputs.
- **Active transition:** `sql ... into` preserves the query sequence through head/tail, and named-table
  reactivation restores the same sequence.
- **Materialization:** the existing DuckDB eager boundary and Polars fallback reason remain visible
  and are asserted without adding hidden materialization behavior.
- **User-facing paths:** script-mode CLI and help text cover the contract.
- **Scope control:** no SQL rewriting, new syntax, row IDs, sort command, append/join/reshape order,
  categorical order, or estimator behavior was added.

## Blocking Issues

- None found in local validation.

## Validation Evidence

- Ordered SQL executor regressions: 3 passed.
- Script-mode CLI regression: 1 passed; help suite: 8 passed.
- `uv run pytest` — 1,074 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — exit 0; all integrated scenarios passed, including
  canonical replay.

## PR Review Loop

Pending. The delivery protocol requires exactly three independent review passes after the PR is
opened; any actionable findings will be fixed and rechecked before merge.

## Recommended Next Action

Commit the validated slice, open the PR, and run the three independent review passes.
