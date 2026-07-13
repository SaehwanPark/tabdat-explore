# QA Report: Phase 24 P0 Categorical Ordering

Status: implementation validation complete; PR review pending

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, language semantics, tabulate/bar help, command reference,
  and the product contract agree on native scalar order and missing placement.
- **Native values:** numeric labels are ordered numerically, text lexicographically, and booleans
  false before true rather than by rendered text.
- **Missing categories:** tabulate omission/inclusion and bar missing-last display are covered.
- **Bar ties:** descending counts are followed by native category order.
- **Cross-engine behavior:** eager, DuckDB-lazy, and Polars-lazy outputs agree.
- **Scope control:** no category metadata, level syntax, recoding, sort abstraction, relation-order
  rewrite, or estimator behavior was added.

## Blocking Issues

- None remain.

## Validation Evidence

- Cross-engine categorical regression: 3 passed.
- CLI regression: 1 passed; focused help regression: 1 passed.
- `uv run pytest` — 1,104 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — exit 0; all integrated scenarios passed, including
  canonical replay.

## PR Review Loop

Review passes have not started; exactly three independent passes are required after the PR is opened.

## Non-Blocking Follow-Ups

Unordered SQL, exact arithmetic widths, overflow diagnostics, randomness, estimation samples, errors
and exits, lineage, differential assurance, and public-preview readiness remain queued in `SPEC.md`
Future.

## Recommended Next Action

Commit the validated categorical slice, push it, open the PR, and complete exactly three independent
review passes before any merge.
