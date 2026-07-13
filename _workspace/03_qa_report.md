# QA Report: Phase 24 P0 Join Row Order

Status: implementation validation complete; PR review pending

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, language semantics, join help, command reference, and the
  product contract agree on active-row grouping and named-table match order.
- **Combination semantics:** explicit left and right ordinals preserve duplicate matches and avoid
  backend join-planning order leaking into the public result sequence.
- **Join variants:** inner joins omit unmatched active rows; left joins retain one missing-right row.
- **Cross-engine behavior:** eager, DuckDB-lazy, and Polars-lazy inputs produce the same ordered
  preview after the existing join materialization boundary.
- **User-facing paths:** exact CLI row blocks and join help cover the contract.
- **Scope control:** no new syntax, row IDs, sort abstraction, append/reshape rewrite, categorical
  order, or estimator behavior was added.

## Blocking Issues

- None remain.

## Validation Evidence

- Cross-engine join regressions: 6 passed.
- CLI regression: 1 passed; focused help regression: 1 passed.
- `uv run pytest` — 1,087 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — exit 0; all integrated scenarios passed, including
  canonical replay.

## PR Review Loop

Review passes have not started; exactly three independent passes are required after the PR is opened.

## Non-Blocking Follow-Ups

Reshape ordering, unordered SQL, categorical ordering, exact arithmetic widths, overflow diagnostics,
randomness, estimation samples, errors and exits, lineage, differential assurance, and public-preview
readiness remain queued in `SPEC.md` Future.

## Recommended Next Action

Commit the validated join slice, push it, open the PR, and complete exactly three independent review
passes before any merge.
