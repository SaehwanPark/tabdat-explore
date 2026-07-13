# QA Report: Phase 24 P0 Reshape Row Order

Status: implementation validation complete; PR review pending

## Boundaries Checked

- **Roadmap/docs to contract:** `SPEC.md`, language semantics, reshape help, command reference, and
  the product contract agree on long source-row/j-value order and wide first-group order.
- **Long semantics:** non-sorted source rows and wide-column j order are preserved.
- **Wide semantics:** identifier groups follow the first active row belonging to each group.
- **Cross-engine behavior:** eager, DuckDB-lazy, and Polars-lazy inputs produce the same reshape
  preview sequence after the existing materialization boundary.
- **Regression safety:** existing wide/long column layout and duplicate-cell aggregation tests stay
  green.
- **Scope control:** no new syntax, row IDs, sort abstraction, append/join rewrite, categorical order,
  or estimator behavior was added.

## Blocking Issues

- None remain.

## Validation Evidence

- Cross-engine reshape regression: 3 passed; reshape-focused executor/CLI suite: 8 passed.
- CLI regression: 1 passed; focused help regression: 1 passed.
- `uv run pytest` — 1,094 passed, 314 existing third-party warnings.
- `uv run basedpyright` — 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `git diff --check` — passed.
- `uv run python integrated_testing/run_e2e.py` — exit 0; all integrated scenarios passed, including
  canonical replay.

## PR Review Loop

Review passes have not started; exactly three independent passes are required after the PR is opened.

## Non-Blocking Follow-Ups

Categorical ordering, unordered SQL, exact arithmetic widths, overflow diagnostics, randomness,
estimation samples, errors and exits, lineage, differential assurance, and public-preview readiness
remain queued in `SPEC.md` Future.

## Recommended Next Action

Commit the validated reshape slice, push it, open the PR, and complete exactly three independent review
passes before any merge.
