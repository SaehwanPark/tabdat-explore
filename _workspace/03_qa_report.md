# QA Report: Phase 24 P0 Append Row Order

Status: local validation complete; PR review loop pending

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, language semantics, append help, and the product contract
  agree on active-left then named-table-right sequence and join/reshape non-goals.
- **Combination semantics:** eager, DuckDB-lazy, and Polars-lazy append paths preserve both input
  sequences without sorting, deduplicating, or interleaving.
- **Preview semantics:** head/tail of the combined active dataset retain left-then-right order.
- **Materialization:** existing eager/fallback state reporting remains visible after append.
- **User-facing paths:** script-mode CLI output and append help cover the contract.
- **Scope control:** no new syntax, row IDs, join/reshape rewrite, categorical order, or estimator
  behavior was added.

## Blocking Issues

- None found in local validation.

## Validation Evidence

- Cross-engine append regressions: 3 passed.
- Script-mode CLI regression: 1 passed; help suite: 8 passed.
- `uv run pytest` — 1,078 passed, 314 existing third-party warnings.
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
